package com.kofy.vlessgen

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.net.VpnService
import android.os.Build
import android.util.Log
import androidx.core.app.NotificationCompat
import io.nekohasekai.libbox.CommandServer
import io.nekohasekai.libbox.CommandServerHandler
import io.nekohasekai.libbox.Libbox
import io.nekohasekai.libbox.OverrideOptions
import io.nekohasekai.libbox.SetupOptions
import io.nekohasekai.libbox.SystemProxyStatus
import java.io.File

/**
 * v1.0 — Servicio VPN con sing-box (libbox) como motor real.
 *
 * Flujo:
 *   1. Libbox.setup()  -> prepara el core Go
 *   2. PlatformInterfaceImpl  -> implementa openTun(): sing-box nos pedira el TUN
 *   3. CommandServer.start() + startOrReloadService(json) -> arranca el tunel
 */
class VpnTunnelService : VpnService() {

    companion object {
        const val ACTION_CONNECT = "com.kofy.vlessgen.CONNECT"
        const val ACTION_DISCONNECT = "com.kofy.vlessgen.DISCONNECT"
        const val ACTION_STATE = "com.kofy.vlessgen.STATE"
        const val EXTRA_ACTIVE = "activo"

        private const val CHANNEL_ID = "vpn"
        private const val NOTIF_ID = 1
        private const val TAG = "VlessGen"

        @Volatile
        var activo: Boolean = false
            private set
    }

    private var server: CommandServer? = null
    private var platform: PlatformInterfaceImpl? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_DISCONNECT -> desconectar()
            else -> conectar()
        }
        return START_STICKY
    }

    private fun conectar() {
        if (server != null) return

        crearCanal()
        startForeground(NOTIF_ID, construirNotificacion())

        try {
            val opciones = SetupOptions()
            opciones.basePath = filesDir.absolutePath
            val trabajo = File(filesDir, "working")
            trabajo.mkdirs()
            opciones.workingPath = trabajo.absolutePath
            opciones.tempPath = cacheDir.absolutePath
            opciones.fixAndroidStack = true
            opciones.logMaxLines = 500
            Libbox.setup(opciones)

            val config = leerConfig()
            if (config == null) {
                Log.e(TAG, "faltan datos del servidor en SharedPreferences")
                fallar()
                return
            }
            Log.d(TAG, "config sing-box: $config")

            val plataforma = PlatformInterfaceImpl(this)
            platform = plataforma

            val srv = Libbox.newCommandServer(Manejador(), plataforma)
            srv.start()
            // OJO: pasar null aqui provoca un nil pointer en Go (command_server.go:204).
            srv.startOrReloadService(config, OverrideOptions())

            server = srv
            activo = true
            Log.i(TAG, "sing-box arrancado correctamente")
        } catch (e: Exception) {
            Log.e(TAG, "error arrancando sing-box", e)
            fallar()
            return
        }

        avisarEstado()
    }

    private fun leerConfig(): String? {
        val p = getSharedPreferences("vless", MODE_PRIVATE)
        val host = p.getString("host", "").orEmpty().trim()
        val uuid = p.getString("uuid", "").orEmpty().trim()
        val pbk = p.getString("pbk", "").orEmpty().trim()

        if (host.isEmpty() || uuid.isEmpty() || pbk.isEmpty()) return null

        val puerto = p.getString("puerto", "443")?.toIntOrNull() ?: 443
        val sid = p.getString("sid", "").orEmpty().trim()
        val sni = p.getString("sni", "www.microsoft.com").orEmpty().trim()
            .ifEmpty { "www.microsoft.com" }

        val apps = getSharedPreferences("apps", MODE_PRIVATE)
            .getStringSet("seleccion", emptySet())
            .orEmpty()
            .filter { it != packageName }
            .toSet()

        val bloquear = getSharedPreferences("ajustes", MODE_PRIVATE)
            .getBoolean("bloquearAnuncios", true)
        val listaAnuncios = if (bloquear) prepararListaAnuncios() else null

        return SingBoxConfig.json(
            host, puerto, uuid, pbk, sid, sni, apps,
            File(filesDir, "singbox.log").absolutePath,
            bloquear,
            listaAnuncios
        )
    }

    /**
     * Copia la lista de dominios de anuncios desde assets a filesDir.
     * sing-box necesita leerla como fichero, no desde el APK.
     */
    private fun prepararListaAnuncios(): String? {
        return try {
            val destino = File(filesDir, "ads.json")
            if (!destino.exists() || destino.length() == 0L) {
                assets.open("ads.json").use { entrada ->
                    destino.outputStream().use { salida -> entrada.copyTo(salida) }
                }
            }
            destino.absolutePath
        } catch (e: Exception) {
            Log.e(TAG, "no pude preparar ads.json", e)
            null
        }
    }

    private fun desconectar() {
        try {
            server?.closeService()
        } catch (e: Exception) {
            // ya cerrado
        }
        try {
            server?.close()
        } catch (e: Exception) {
        }
        server = null

        try {
            platform?.tun?.close()
        } catch (e: Exception) {
        }
        platform = null

        activo = false
        avisarEstado()
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private fun fallar() {
        activo = false
        avisarEstado()
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    override fun onRevoke() {
        desconectar()
        super.onRevoke()
    }

    override fun onDestroy() {
        try {
            server?.close()
        } catch (e: Exception) {
        }
        server = null
        try {
            platform?.tun?.close()
        } catch (e: Exception) {
        }
        platform = null
        activo = false
        super.onDestroy()
    }

    private inner class Manejador : CommandServerHandler {
        override fun serviceStop() {
            desconectar()
        }

        override fun serviceReload() {
        }

        override fun getSystemProxyStatus(): SystemProxyStatus? = null

        override fun setSystemProxyEnabled(enabled: Boolean) {
        }

        override fun writeDebugMessage(message: String?) {
            Log.d("sing-box", message ?: "")
        }

        override fun connectSSHAgent(): Int = -1

        override fun triggerNativeCrash() {
        }
    }

    // ------------------------------------------------------------ notificacion

    private fun crearCanal() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val nm = getSystemService(NotificationManager::class.java)
        val canal = NotificationChannel(
            CHANNEL_ID,
            "VPN",
            NotificationManager.IMPORTANCE_LOW
        )
        canal.description = "Estado de la conexion VPN"
        nm.createNotificationChannel(canal)
    }

    private fun construirNotificacion(): Notification {
        val abrir = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("VlessGen")
            .setContentText("VPN conectada")
            .setSmallIcon(android.R.drawable.ic_lock_lock)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setContentIntent(abrir)
            .build()
    }

    private fun avisarEstado() {
        Estado.activo = activo
        val i = Intent(ACTION_STATE)
            .setPackage(packageName)
            .putExtra(EXTRA_ACTIVE, activo)
        sendBroadcast(i)
    }
}
