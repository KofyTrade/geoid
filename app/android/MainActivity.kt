package com.geoid.vpn

import android.Manifest
import android.app.AlertDialog
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.net.VpnService
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.View
import android.widget.ScrollView
import android.widget.Switch
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.google.android.material.button.MaterialButton
import com.geoid.awg.Awg
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress

class MainActivity : AppCompatActivity() {

    private lateinit var poliedro: PolyhedronView
    private lateinit var tvVpnEstado: TextView
    private lateinit var tvAppsResumen: TextView
    private lateinit var btnVpn: MaterialButton
    private lateinit var btnApps: MaterialButton
    private lateinit var btnImportarConf: MaterialButton
    private lateinit var btnRegistro: MaterialButton
    private lateinit var swAnuncios: Switch

    private lateinit var panelStats: View
    private lateinit var tvVelocidad: TextView
    private lateinit var tvPing: TextView
    private lateinit var tvServidor: TextView
    private lateinit var tvActualizacion: TextView

    private var versionNueva: NuevaVersion? = null
    private var yaComprobado = false

    private val COLOR_ACTIVO = 0xFF2EE6C5.toInt()
    private val COLOR_INACTIVO = 0xFF7FA8A4.toInt()

    private val manejador = Handler(Looper.getMainLooper())
    private var ultimoBytes = -1L
    private var ultimoInstante = 0L
    private var pingEnCurso = false

    // ------------------------------------------------------------ permiso VPN
    private val lanzadorVpn = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { resultado ->
        if (resultado.resultCode == RESULT_OK) {
            arrancar(true)
        } else {
            Toast.makeText(this, R.string.permiso_denegado, Toast.LENGTH_LONG).show()
        }
    }

    private val lanzadorNotificaciones = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { }

    private val receptor = object : BroadcastReceiver() {
        override fun onReceive(contexto: Context?, intent: Intent?) {
            val activo = intent?.getBooleanExtra(AwgTunnelService.EXTRA_ACTIVE, false) ?: false
            pintarEstadoVpn(activo)
        }
    }

    /** Bucle que refresca velocidad y ping mientras hay tunel. */
    private val bucleStats = object : Runnable {
        override fun run() {
            if (!Estado.activo) return
            actualizarEstadisticas()
            manejador.postDelayed(this, 2000)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        poliedro = findViewById(R.id.poliedro)
        tvVpnEstado = findViewById(R.id.tvVpnEstado)
        tvAppsResumen = findViewById(R.id.tvAppsResumen)
        btnVpn = findViewById(R.id.btnVpn)
        btnApps = findViewById(R.id.btnApps)
        btnImportarConf = findViewById(R.id.btnImportarConf)
        btnRegistro = findViewById(R.id.btnRegistro)
        swAnuncios = findViewById(R.id.swAnuncios)

        panelStats = findViewById(R.id.panelStats)
        tvVelocidad = findViewById(R.id.tvVelocidad)
        tvPing = findViewById(R.id.tvPing)
        tvServidor = findViewById(R.id.tvServidor)
        tvActualizacion = findViewById(R.id.tvActualizacion)

        // El banner de actualizacion descarga el APK nuevo al tocarlo.
        tvActualizacion.setOnClickListener {
            val nueva = versionNueva ?: return@setOnClickListener
            Actualizador.descargar(this, nueva)
            Toast.makeText(this, R.string.descargando, Toast.LENGTH_LONG).show()
        }

        btnVpn.setOnClickListener {
            if (Estado.activo) {
                arrancar(false)
            } else {
                pedirNotificaciones()
                val permiso = VpnService.prepare(this)
                if (permiso != null) lanzadorVpn.launch(permiso) else arrancar(true)
            }
        }

        btnApps.setOnClickListener {
            startActivity(Intent(this, AppsActivity::class.java))
        }

        btnImportarConf.setOnClickListener {
            startActivity(Intent(this, PerfilesActivity::class.java))
        }
        btnRegistro.setOnClickListener { verRegistro() }

        // Bloqueador: con el interruptor encendido, la app usa el DNS del
        // servidor (dnsmasq con lista de anuncios); apagado, usa uno limpio.
        swAnuncios.isChecked = ajustes().getBoolean("bloquearAnuncios", true)
        swAnuncios.setOnCheckedChangeListener { _, marcado ->
            ajustes().edit().putBoolean("bloquearAnuncios", marcado).apply()
            if (Estado.activo) {
                Toast.makeText(this, R.string.reconectando, Toast.LENGTH_SHORT).show()
                arrancar(false)
                manejador.postDelayed({ arrancar(true) }, 700)
            }
        }

        pintarEstadoVpn(Estado.activo)

        // Si venimos de la version de un solo perfil, se convierte en el primero.
        Perfiles.migrar(this)

        buscarActualizacion()
    }

    override fun onResume() {
        super.onResume()
        actualizarResumenApps()
        pintarEstadoVpn(Estado.activo)

        val activo = Perfiles.activo(this)
        btnImportarConf.text = if (activo != null) {
            getString(R.string.perfiles_boton, activo.nombre)
        } else {
            getString(R.string.anadir_perfil)
        }
    }

    override fun onStart() {
        super.onStart()
        ContextCompat.registerReceiver(
            this, receptor,
            IntentFilter(AwgTunnelService.ACTION_STATE),
            ContextCompat.RECEIVER_NOT_EXPORTED
        )
    }

    override fun onStop() {
        super.onStop()
        try {
            unregisterReceiver(receptor)
        } catch (e: Exception) {
        }
    }

    override fun onDestroy() {
        manejador.removeCallbacksAndMessages(null)
        super.onDestroy()
    }

    private fun ajustes() = getSharedPreferences("ajustes", MODE_PRIVATE)

    // ------------------------------------------------------------------ estado
    private fun pintarEstadoVpn(activo: Boolean) {
        poliedro.conectado = activo

        if (activo) {
            tvVpnEstado.text = getString(R.string.estado_conectado)
            tvVpnEstado.setTextColor(COLOR_ACTIVO)
            btnVpn.text = getString(R.string.desconectar)
            btnVpn.backgroundTintList =
                android.content.res.ColorStateList.valueOf(0xFF13333A.toInt())
            btnVpn.setTextColor(COLOR_ACTIVO)

            panelStats.visibility = View.VISIBLE
            pintarServidor()
            ultimoBytes = -1L
            ultimoInstante = 0L
            manejador.removeCallbacks(bucleStats)
            manejador.postDelayed(bucleStats, 800)
        } else {
            tvVpnEstado.text = getString(R.string.estado_desconectado)
            tvVpnEstado.setTextColor(COLOR_INACTIVO)
            btnVpn.text = getString(R.string.conectar)
            btnVpn.backgroundTintList =
                android.content.res.ColorStateList.valueOf(COLOR_ACTIVO)
            btnVpn.setTextColor(0xFF05161A.toInt())

            panelStats.visibility = View.GONE
            tvVelocidad.text = "0 KB/s"
            tvPing.text = "-- ms"
            manejador.removeCallbacks(bucleStats)
        }
    }

    private fun etiquetaServidor(): String {
        val conf = Perfiles.activo(this)?.conf.orEmpty()
        val linea = conf.lines().firstOrNull {
            it.trim().startsWith("Endpoint", ignoreCase = true)
        }
        return linea?.substringAfter("=")?.trim().orEmpty()
    }

    /**
     * Muestra el pais del servidor (no su IP). Se consulta una vez y se guarda
     * en cache; si falla, se usa el nombre del perfil.
     */
    private fun pintarServidor() {
        val perfil = Perfiles.activo(this) ?: return
        val ip = perfil.servidor

        val guardado = getSharedPreferences("paises", MODE_PRIVATE).getString(ip, null)
        if (guardado != null) {
            tvServidor.text = guardado
            return
        }

        tvServidor.text = perfil.nombre

        Thread {
            val pais = consultarPais(ip)
            if (pais != null) {
                getSharedPreferences("paises", MODE_PRIVATE).edit().putString(ip, pais).apply()
                runOnUiThread {
                    if (Estado.activo) tvServidor.text = pais
                }
            }
        }.start()
    }

    /** Devuelve el nombre del pais ("Finlandia") a partir de su IP. */
    private fun consultarPais(ip: String): String? {
        return try {
            val conexion = java.net.URL("https://ipinfo.io/" + ip + "/country")
                .openConnection() as java.net.HttpURLConnection
            conexion.connectTimeout = 4000
            conexion.readTimeout = 4000
            val codigo = conexion.inputStream.bufferedReader().use { it.readText() }.trim()
            conexion.disconnect()
            if (codigo.length == 2) {
                java.util.Locale("", codigo).displayCountry
            } else {
                null
            }
        } catch (e: Exception) {
            null
        }
    }

    private fun actualizarResumenApps() {
        val marcadas = getSharedPreferences("apps", MODE_PRIVATE)
            .getStringSet("seleccion", emptySet()).orEmpty()
        tvAppsResumen.text = if (marcadas.isEmpty()) {
            getString(R.string.todas_las_apps)
        } else {
            resources.getQuantityString(R.plurals.apps_seleccionadas, marcadas.size, marcadas.size)
        }
    }

    // -------------------------------------------------------------- medidores
    private fun actualizarEstadisticas() {
        val crudo = try {
            Awg.stats()
        } catch (e: Exception) {
            ""
        }
        if (crudo.isNullOrEmpty()) return

        val partes = crudo.split(";")
        val rx = partes.getOrNull(0)?.toLongOrNull() ?: 0L
        val tx = partes.getOrNull(1)?.toLongOrNull() ?: 0L
        val total = rx + tx
        val ahora = System.currentTimeMillis()

        if (ultimoInstante > 0L && ultimoBytes >= 0L) {
            val segundos = (ahora - ultimoInstante) / 1000.0
            if (segundos > 0.3) {
                val delta = total - ultimoBytes
                if (delta >= 0) tvVelocidad.text = formatearVelocidad(delta / segundos)
            }
        }
        ultimoBytes = total
        ultimoInstante = ahora

        medirPing()
    }

    private fun formatearVelocidad(bytesPorSegundo: Double): String {
        return when {
            bytesPorSegundo < 1024 -> String.format("%.0f B/s", bytesPorSegundo)
            bytesPorSegundo < 1024 * 1024 -> String.format("%.0f KB/s", bytesPorSegundo / 1024)
            else -> String.format("%.1f MB/s", bytesPorSegundo / (1024 * 1024))
        }
    }

    /** Latencia real: se envia una consulta DNS de verdad y se mide la respuesta. */
    private fun medirPing() {
        if (pingEnCurso) return
        pingEnCurso = true

        val destino = puertaTunel() ?: "1.1.1.1"

        Thread {
            var ms: Int? = null
            try {
                val consulta = consultaDns("p" + (100000..999999).random() + ".com")
                DatagramSocket().use { socket ->
                    socket.soTimeout = 2500
                    val ip = InetAddress.getByName(destino)
                    val salida = DatagramPacket(consulta, consulta.size, ip, 53)
                    val bufer = ByteArray(512)
                    val entrada = DatagramPacket(bufer, bufer.size)

                    val inicio = System.nanoTime()
                    socket.send(salida)
                    socket.receive(entrada)
                    ms = ((System.nanoTime() - inicio) / 1_000_000L).toInt()
                }
            } catch (e: Exception) {
                ms = null
            }
            pingEnCurso = false
            val valor = ms
            runOnUiThread {
                tvPing.text = if (valor != null) valor.toString() + " ms" else "-- ms"
            }
        }.start()
    }

    /** Construye una consulta DNS tipo A, en binario. */
    private fun consultaDns(nombre: String): ByteArray {
        val salida = java.io.ByteArrayOutputStream()
        val identificador = (1..65535).random()
        salida.write(identificador shr 8)
        salida.write(identificador and 0xFF)
        salida.write(0x01) // recursion desired
        salida.write(0x00)
        salida.write(0x00); salida.write(0x01) // 1 pregunta
        salida.write(0x00); salida.write(0x00) // 0 respuestas
        salida.write(0x00); salida.write(0x00) // 0 autoridad
        salida.write(0x00); salida.write(0x00) // 0 adicional
        for (parte in nombre.split(".")) {
            salida.write(parte.length)
            salida.write(parte.toByteArray(Charsets.US_ASCII))
        }
        salida.write(0x00)
        salida.write(0x00); salida.write(0x01) // tipo A
        salida.write(0x00); salida.write(0x01) // clase IN
        return salida.toByteArray()
    }

    /** IP de la puerta del tunel (10.9.9.1 en un /24), a partir del .conf. */
    private fun puertaTunel(): String? {
        val conf = Perfiles.activo(this)?.conf.orEmpty()
        val ip = conf.lines()
            .firstOrNull { it.trim().startsWith("Address", ignoreCase = true) }
            ?.substringAfter("=")?.trim()?.substringBefore("/") ?: return null
        val partes = ip.split(".")
        return if (partes.size == 4) {
            partes[0] + "." + partes[1] + "." + partes[2] + ".1"
        } else {
            null
        }
    }


    /** Pregunta a GitHub si hay una version mas nueva y, si la hay, muestra el aviso. */
    private fun buscarActualizacion() {
        if (yaComprobado) return
        yaComprobado = true

        Thread {
            val nueva = Actualizador.buscar() ?: return@Thread
            val instalada = Actualizador.versionInstalada(this)
            if (!Actualizador.esMasNueva(nueva.numero, instalada)) return@Thread

            runOnUiThread {
                versionNueva = nueva
                tvActualizacion.text = getString(R.string.nueva_version, nueva.numero)
                tvActualizacion.visibility = View.VISIBLE
            }
        }.start()
    }
    // -------------------------------------------------------------- servicios
    private fun arrancar(conectar: Boolean) {
        val accion =
            if (conectar) AwgTunnelService.ACTION_CONNECT else AwgTunnelService.ACTION_DISCONNECT
        val i = Intent(this, AwgTunnelService::class.java).setAction(accion)
        if (conectar) {
            ContextCompat.startForegroundService(this, i)
        } else {
            startService(i)
        }
        pintarEstadoVpn(conectar)
    }

    private fun pedirNotificaciones() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED
            ) {
                lanzadorNotificaciones.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
    }

    // ------------------------------------------------------------ configuracion
    private fun verRegistro() {
        val perfil = Perfiles.activo(this)
        val conf = perfil?.conf.orEmpty()
        val cfg = AwgConfig.parse(conf)
        val crudo = try {
            Awg.stats()
        } catch (e: Exception) {
            ""
        }

        val conectadoTxt = getString(R.string.estado_conectado)
        val desconectadoTxt = getString(R.string.estado_desconectado)
        val siTxt = getString(R.string.si)
        val noTxt = getString(R.string.no)

        val texto = buildString {
            appendLine(
                getString(
                    R.string.diagnostico_estado,
                    if (Estado.activo) conectadoTxt else desconectadoTxt
                )
            )
            appendLine(
                getString(
                    R.string.diagnostico_servidor,
                    cfg?.ipServidor ?: getString(R.string.sin_configuracion)
                )
            )
            appendLine(getString(R.string.diagnostico_mtu, (cfg?.mtu ?: 0).toString()))
            appendLine(
                getString(R.string.diagnostico_dns, cfg?.dns?.joinToString(", ") ?: "-")
            )
            appendLine(
                getString(
                    R.string.diagnostico_anuncios,
                    if (ajustes().getBoolean("bloquearAnuncios", true)) siTxt else noTxt
                )
            )
            appendLine()
            if (crudo.isNullOrEmpty()) {
                appendLine(getString(R.string.diagnostico_sin_datos))
            } else {
                val p = crudo.split(";")
                appendLine(getString(R.string.diagnostico_recibido, p.getOrNull(0) ?: "?"))
                appendLine(getString(R.string.diagnostico_enviado, p.getOrNull(1) ?: "?"))
                appendLine(getString(R.string.diagnostico_handshake, p.getOrNull(2) ?: "?"))
            }
        }

        val vista = ScrollView(this).apply {
            addView(
                TextView(this@MainActivity).apply {
                    text = texto
                    textSize = 12f
                    setTextIsSelectable(true)
                    setPadding(24, 24, 24, 24)
                }
            )
        }

        AlertDialog.Builder(this)
            .setTitle(R.string.diagnostico)
            .setView(vista)
            .setPositiveButton(R.string.compartir) { _, _ ->
                val i = Intent(Intent.ACTION_SEND).apply {
                    type = "text/plain"
                    putExtra(Intent.EXTRA_TEXT, texto)
                }
                startActivity(Intent.createChooser(i, getString(R.string.enviar)))
            }
            .setNegativeButton(R.string.cerrar, null)
            .show()
    }
}
