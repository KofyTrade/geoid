package com.geoid.vpn

import android.app.DownloadManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.net.Uri
import android.net.VpnService
import android.os.Build
import android.os.Environment
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import com.geoid.awg.Awg
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.EventChannel
import io.flutter.plugin.common.MethodChannel

/**
 * Puente entre Flutter y Android: tunel, preferencias, lista de aplicaciones,
 * selector de ficheros y descargas.
 */
class MainActivity : FlutterActivity() {

    companion object {
        private const val CANAL = "geoid/nativo"
        private const val CANAL_ESTADO = "geoid/estado"
    }

    private lateinit var canalMetodos: MethodChannel
    private var eventos: EventChannel.EventSink? = null
    private var resultadoVpn: MethodChannel.Result? = null
    private var resultadoArchivo: MethodChannel.Result? = null
    private var receptor: BroadcastReceiver? = null

    // Selector de ficheros (Activity Result API).
    private val selector = registerForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        val destino = resultadoArchivo
        resultadoArchivo = null
        if (uri == null) {
            destino?.success(null)
            return@registerForActivityResult
        }
        try {
            val texto = contentResolver.openInputStream(uri)
                ?.bufferedReader()?.use { it.readText() }
            destino?.success(texto)
        } catch (e: Exception) {
            destino?.error("archivo", e.message, null)
        }
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        canalMetodos = MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CANAL)
        canalMetodos.setMethodCallHandler { llamada, resultado ->
            try {
                when (llamada.method) {
                    "version" -> resultado.success(versionInstalada())

                    "prefsLeer" -> {
                        val nombre = llamada.argument<String>("nombre") ?: "ajustes"
                        val clave = llamada.argument<String>("clave") ?: ""
                        resultado.success(
                            getSharedPreferences(nombre, MODE_PRIVATE).getString(clave, null)
                        )
                    }

                    "prefsGuardar" -> {
                        val nombre = llamada.argument<String>("nombre") ?: "ajustes"
                        val clave = llamada.argument<String>("clave") ?: ""
                        val valor = llamada.argument<String>("valor")
                        getSharedPreferences(nombre, MODE_PRIVATE).edit()
                            .putString(clave, valor).apply()
                        resultado.success(true)
                    }

                    "listarApps" -> resultado.success(listarApps())

                    "elegirArchivo" -> {
                        resultadoArchivo = resultado
                        selector.launch("*/*")
                    }

                    "prepararVpn" -> resultado.success(prepararVpn())

                    "conectar" -> {
                        val intencion = Intent(this, AwgTunnelService::class.java)
                            .setAction(AwgTunnelService.ACTION_CONNECT)
                            .putExtra(AwgTunnelService.EXTRA_CONFIG, llamada.argument<String>("conf"))
                            .putExtra(AwgTunnelService.EXTRA_MTU, llamada.argument<Int>("mtu") ?: 0)
                            .putExtra(AwgTunnelService.EXTRA_DNS, llamada.argument<String>("dns"))
                            .putExtra(
                                AwgTunnelService.EXTRA_FILTRAR,
                                llamada.argument<Boolean>("filtrar") ?: true
                            )
                            .putStringArrayListExtra(
                                AwgTunnelService.EXTRA_APPS,
                                ArrayList(llamada.argument<List<String>>("apps").orEmpty())
                            )
                        ContextCompat.startForegroundService(this, intencion)
                        resultado.success(true)
                    }

                    "desconectar" -> {
                        val intencion = Intent(this, AwgTunnelService::class.java)
                            .setAction(AwgTunnelService.ACTION_DISCONNECT)
                        startService(intencion)
                        resultado.success(true)
                    }

                    "stats" -> resultado.success(Awg.stats())

                    "descargar" -> {
                        val url = llamada.argument<String>("url").orEmpty()
                        val nombre = llamada.argument<String>("nombre") ?: "actualizacion.apk"
                        val peticion = DownloadManager.Request(Uri.parse(url))
                            .setTitle("GeoiD-vpn")
                            .setDescription(nombre)
                            .setMimeType("application/vnd.android.package-archive")
                            .setNotificationVisibility(
                                DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED
                            )
                            .setDestinationInExternalPublicDir(
                                Environment.DIRECTORY_DOWNLOADS, nombre
                            )
                        val gestor = getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
                        gestor.enqueue(peticion)
                        resultado.success(true)
                    }

                    else -> resultado.notImplemented()
                }
            } catch (e: Exception) {
                resultado.error("nativo", e.message, null)
            }
        }

        EventChannel(flutterEngine.dartExecutor.binaryMessenger, CANAL_ESTADO)
            .setStreamHandler(object : EventChannel.StreamHandler {
                override fun onListen(argumentos: Any?, sink: EventChannel.EventSink?) {
                    eventos = sink
                    sink?.success(estado())
                }

                override fun onCancel(argumentos: Any?) {
                    eventos = null
                }
            })

        registrarReceptor()
        pedirNotificaciones()
    }

    private fun estado(): Map<String, Any?> = mapOf(
        "activo" to Estado.activo,
        "error" to Estado.error
    )

    private fun registrarReceptor() {
        if (receptor != null) return
        val r = object : BroadcastReceiver() {
            override fun onReceive(contexto: Context?, intencion: Intent?) {
                eventos?.success(estado())
            }
        }
        receptor = r
        if (Build.VERSION.SDK_INT >= 33) {
            registerReceiver(r, IntentFilter(AwgTunnelService.ACTION_STATE), RECEIVER_NOT_EXPORTED)
        } else {
            @Suppress("UnspecifiedRegisterReceiverFlag")
            registerReceiver(r, IntentFilter(AwgTunnelService.ACTION_STATE))
        }
    }

    override fun onDestroy() {
        receptor?.let {
            try {
                unregisterReceiver(it)
            } catch (e: Exception) {
            }
        }
        receptor = null
        super.onDestroy()
    }

    /** Pide permiso de VPN si hace falta. Devuelve true cuando ya esta concedido. */
    private fun prepararVpn(): Boolean {
        val intencion = VpnService.prepare(this)
        if (intencion == null) return true
        resultadoVpn = null
        startActivityForResult(intencion, 1001)
        return false
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        if (requestCode == 1001) {
            canalMetodos.invokeMethod("vpnConcedida", resultCode == RESULT_OK)
            return
        }
        super.onActivityResult(requestCode, resultCode, data)
    }

    private fun pedirNotificaciones() {
        if (Build.VERSION.SDK_INT < 33) return
        if (checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) ==
            android.content.pm.PackageManager.PERMISSION_GRANTED
        ) return
        requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS), 2001)
    }

    private fun versionInstalada(): String {
        return try {
            packageManager.getPackageInfo(packageName, 0).versionName ?: "0"
        } catch (e: Exception) {
            "0"
        }
    }

    private fun listarApps(): List<Map<String, Any?>> {
        val pm = packageManager
        val propia = packageName
        val lista = ArrayList<Map<String, Any?>>()

        val instaladas = pm.getInstalledApplications(android.content.pm.PackageManager.GET_META_DATA)
        for (app in instaladas) {
            if (app.packageName == propia) continue
            val sistema = (app.flags and android.content.pm.ApplicationInfo.FLAG_SYSTEM) != 0
            lista.add(
                mapOf(
                    "paquete" to app.packageName,
                    "nombre" to pm.getApplicationLabel(app).toString(),
                    "sistema" to sistema
                )
            )
        }
        lista.sortBy { (it["nombre"] as String).lowercase() }
        return lista
    }
}
