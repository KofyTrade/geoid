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
 * Diferencias con el de sing-box: aqui no hay proxy ni reglas; se crea el TUN y
 * se le pasa el descriptor al motor Go, que cifra y ofusca todo el trafico IP.
 * Por eso UDP y QUIC funcionan de forma nativa.
 */
class AwgTunnelService : VpnService() {

    companion object {
        const val ACTION_CONNECT = "com.geoid.vpn.AWG_CONNECT"
        const val ACTION_DISCONNECT = "com.geoid.vpn.AWG_DISCONNECT"
        const val ACTION_STATE = "com.geoid.vpn.STATE"
        const val EXTRA_ACTIVE = "activo"

        private const val CANAL = "vpn"
        private const val NOTIF_ID = 1
        private const val TAG = "VlessGen"
    }

    private var tun: ParcelFileDescriptor? = null

    // El motor Go bloquea al arrancar y al parar (espera a que el dispositivo
    // se cierre). Si eso ocurre en el hilo principal, Android cierra la app por
    // "no responde": por eso todo el trabajo va en este hilo aparte.
    private val trabajador = java.util.concurrent.Executors.newSingleThreadExecutor()

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_DISCONNECT -> trabajador.execute { desconectar() }
            else -> {
                // El foreground hay que declararlo enseguida (regla de Android).
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
            val texto = Perfiles.activo(this)?.conf.orEmpty()
            val cfg = AwgConfig.parse(texto)
                ?: throw IllegalStateException(getString(R.string.error_config))

            // MTU: se respeta el del .conf. El instalador usa 1280 a proposito:
            // AmneziaWG anade hasta 128 bytes de relleno por paquete, asi que
            // 1280 + 128 + 60 = 1468 y siempre cabe en los 1500 del enlace.
            // Subirlo a 1400 hacia que los paquetes grandes no cupieran y el
            // tunel se atascara a ratos (picos de 2 s).
            val mtu = cfg.mtu

            val builder = Builder()
                .setSession("Geoid")
                .setMtu(mtu)

            for (d in cfg.direcciones) {
                val partes = d.split("/")
                val ip = partes[0]
                val prefijo = partes.getOrNull(1)?.toIntOrNull() ?: 32
                builder.addAddress(ip, prefijo)
            }
            // DNS: la puerta del tunel (10.9.9.1) es nuestro dnsmasq, que filtra
            // publicidad. Si el bloqueador esta apagado, se usa un DNS limpio.
            val conFiltro = getSharedPreferences("ajustes", MODE_PRIVATE)
                .getBoolean("bloquearAnuncios", true)
            val puerta = cfg.direcciones.firstOrNull()?.substringBefore("/")?.let { ip ->
                val partes = ip.split(".")
                if (partes.size == 4) partes[0] + "." + partes[1] + "." + partes[2] + ".1" else null
            }
            val dnsLimpio = cfg.dns.firstOrNull() ?: "1.1.1.1"
            val dns = if (conFiltro) (puerta ?: dnsLimpio) else dnsLimpio
            builder.addDnsServer(dns)
            builder.addRoute("0.0.0.0", 0)

            // El socket del handshake no queda "protected" (el motor Go no lo
            // expone), asi que excluimos la IP del servidor de las rutas del
            // tunel: esos paquetes salen por la red normal y el handshake llega.
            if (Build.VERSION.SDK_INT >= 33) {
                try {
                    val destino = java.net.InetAddress.getByName(cfg.ipServidor)
                    builder.excludeRoute(android.net.IpPrefix(destino, 32))
                } catch (e: Exception) {
                    Log.w(TAG, "no se pudo excluir la IP del servidor", e)
                }
            }

            // Lista blanca de apps (misma preferencia que usa sing-box)
            val marcadas = getSharedPreferences("apps", MODE_PRIVATE)
                .getStringSet("seleccion", emptySet())
                .orEmpty()
                .filter { it != packageName }
            for (p in marcadas) {
                try {
                    builder.addAllowedApplication(p)
                } catch (e: Exception) {
                    // app desinstalada
                }
            }

            val descriptor = builder.establish()
                ?: throw IllegalStateException(getString(R.string.error_tun))
            tun = descriptor

            // El motor Go se queda con el descriptor y lo cierra al parar. Si le
            // pasamos el original, Android (fdsan) detecta que Java y Go se pelean
            // por el mismo fd y aborta el proceso al desconectar. Le damos una
            // copia desligada: cada uno tiene la suya.
            val copia = ParcelFileDescriptor.dup(descriptor.fileDescriptor)
            val fdGo = copia.detachFd()

            Awg.start(fdGo, mtu, cfg.uapi)

            Estado.activo = true
            val resumen = cfg.uapi.lines().joinToString(" | ") { linea ->
                if (linea.startsWith("private_key=") || linea.startsWith("public_key=") ||
                    linea.startsWith("preshared_key=")
                ) linea.substringBefore("=") + "=[" + linea.substringAfter("=").length + " hex]"
                else linea
            }
            Log.i(TAG, "uapi: $resumen")
            Log.i(TAG, "AmneziaWG arrancado (mtu=$mtu, dns=$dns)")
        } catch (e: Exception) {
            Log.e(TAG, "error arrancando AmneziaWG", e)
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
            .setContentTitle("Geoid")
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
        sendBroadcast(i)
    }
}
