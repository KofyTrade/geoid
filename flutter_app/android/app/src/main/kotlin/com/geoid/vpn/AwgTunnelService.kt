package com.geoid.vpn

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.net.VpnService
import android.os.Build
import android.os.ParcelFileDescriptor
import android.util.Log
import androidx.core.app.NotificationCompat
import com.geoid.awg.Awg

/**
 * Servicio VPN con AmneziaWG como motor (WireGuard ofuscado).
 *
 * La configuracion llega desde Flutter en los extras del Intent, para que la
 * capa nativa no dependa de preferencias ni de ficheros.
 */
class AwgTunnelService : VpnService() {

    companion object {
        const val ACTION_CONNECT = "com.geoid.vpn.AWG_CONNECT"
        const val ACTION_DISCONNECT = "com.geoid.vpn.AWG_DISCONNECT"
        const val ACTION_STATE = "com.geoid.vpn.STATE"
        const val EXTRA_ACTIVE = "activo"
        const val EXTRA_CONFIG = "conf"
        const val EXTRA_MTU = "mtu"
        const val EXTRA_DNS = "dns"
        const val EXTRA_APPS = "apps"
        const val EXTRA_FILTRAR = "filtrar"

        private const val CANAL = "vpn"
        private const val NOTIF_ID = 1
        private const val TAG = "GeoidAwg"
    }

    private var tun: ParcelFileDescriptor? = null

    // El motor Go bloquea al arrancar y al parar; si ocurre en el hilo
    // principal Android cierra la app por "no responde".
    private val trabajador = java.util.concurrent.Executors.newSingleThreadExecutor()

    private var ajustes: Intent? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_DISCONNECT -> trabajador.execute { desconectar() }
            else -> {
                ajustes = intent
                crearCanal()
                startForeground(NOTIF_ID, construirNotificacion())
                trabajador.execute { conectar() }
            }
        }
        return START_STICKY
    }

    override fun onDestroy() {
        try {
            Awg.stop()
        } catch (e: Exception) {
        }
        try {
            tun?.close()
        } catch (e: Exception) {
        }
        tun = null
        Estado.activo = false
        trabajador.shutdown()
        super.onDestroy()
    }

    private fun conectar() {
        if (tun != null) return

        try {
            val datos = ajustes
            val texto = datos?.getStringExtra(EXTRA_CONFIG).orEmpty()
            val cfg = AwgConfig.parse(texto)
                ?: throw IllegalStateException("config invalida")

            val mtu = datos?.getIntExtra(EXTRA_MTU, 1280)?.takeIf { it > 0 } ?: cfg.mtu

            val builder = Builder()
                .setSession(getString(R.string.app_name))
                .setMtu(mtu)

            for (d in cfg.direcciones) {
                val partes = d.split("/")
                val ip = partes[0]
                val prefijo = partes.getOrNull(1)?.toIntOrNull() ?: 32
                builder.addAddress(ip, prefijo)
            }

            // DNS: la puerta del tunel es nuestro dnsmasq, que filtra publicidad.
            val filtrar = datos?.getBooleanExtra(EXTRA_FILTRAR, true) ?: true
            val puerta = cfg.direcciones.firstOrNull()?.substringBefore("/")?.let { ip ->
                val partes = ip.split(".")
                if (partes.size == 4) partes[0] + "." + partes[1] + "." + partes[2] + ".1" else null
            }
            val dnsLimpio = datos?.getStringExtra(EXTRA_DNS)?.takeIf { it.isNotEmpty() }
                ?: cfg.dns.firstOrNull()
                ?: "1.1.1.1"
            val dns = if (filtrar) (puerta ?: dnsLimpio) else dnsLimpio
            builder.addDnsServer(dns)
            builder.addRoute("0.0.0.0", 0)

            // El socket del handshake no se puede proteger desde Go, asi que la
            // IP del servidor queda fuera del tunel y sale por la red normal.
            if (Build.VERSION.SDK_INT >= 33) {
                try {
                    val destino = java.net.InetAddress.getByName(cfg.ipServidor)
                    builder.excludeRoute(android.net.IpPrefix(destino, 32))
                } catch (e: Exception) {
                    Log.w(TAG, "no se pudo excluir la IP del servidor", e)
                }
            }

            // Lista blanca de aplicaciones (si esta vacia, pasa todo).
            val marcadas = datos?.getStringArrayListExtra(EXTRA_APPS).orEmpty()
                .filter { it != packageName }
            for (p in marcadas) {
                try {
                    builder.addAllowedApplication(p)
                } catch (e: Exception) {
                    // aplicacion desinstalada
                }
            }

            val descriptor = builder.establish()
                ?: throw IllegalStateException("no se pudo crear el tunel")
            tun = descriptor

            // El motor Go se queda con el descriptor y lo cierra al parar: hay
            // que darle una copia desligada o Android (fdsan) aborta el proceso.
            val copia = ParcelFileDescriptor.dup(descriptor.fileDescriptor)
            val fdGo = copia.detachFd()

            Awg.start(fdGo, mtu, cfg.uapi)

            Estado.activo = true
            Estado.error = null
            Log.i(TAG, "AmneziaWG arrancado (mtu=$mtu, dns=$dns)")
        } catch (e: Exception) {
            Log.e(TAG, "error arrancando AmneziaWG", e)
            Estado.error = e.message ?: e.javaClass.simpleName
            fallar()
            return
        }

        avisarEstado()
    }

    private fun desconectar() {
        try {
            Awg.stop()
        } catch (e: Exception) {
        }
        try {
            tun?.close()
        } catch (e: Exception) {
        }
        tun = null
        Estado.activo = false
        avisarEstado()
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private fun fallar() {
        Estado.activo = false
        avisarEstado()
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    override fun onRevoke() {
        trabajador.execute { desconectar() }
        super.onRevoke()
    }

    private fun crearCanal() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val nm = getSystemService(NotificationManager::class.java)
        val canal = NotificationChannel(CANAL, "VPN", NotificationManager.IMPORTANCE_LOW)
        canal.description = getString(R.string.canal_desc)
        nm.createNotificationChannel(canal)
    }

    private fun construirNotificacion(): Notification {
        val abrir = PendingIntent.getActivity(
            this, 0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
        return NotificationCompat.Builder(this, CANAL)
            .setContentTitle(getString(R.string.app_name))
            .setContentText(getString(R.string.notificacion_texto))
            .setSmallIcon(android.R.drawable.ic_lock_lock)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setContentIntent(abrir)
            .build()
    }

    private fun avisarEstado() {
        val i = Intent(ACTION_STATE)
            .setPackage(packageName)
            .putExtra(EXTRA_ACTIVE, Estado.activo)
            .putExtra("error", Estado.error)
        sendBroadcast(i)
    }
}
