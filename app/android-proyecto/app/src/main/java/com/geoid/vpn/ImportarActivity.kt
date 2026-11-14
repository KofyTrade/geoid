package com.geoid.vpn

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.provider.OpenableColumns
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.button.MaterialButton

/**
 * Se abre cuando compartes o abres un .conf desde otra app (Telegram, el
 * explorador de archivos...). Lee el texto, lo valida y crea el perfil.
 */
class ImportarActivity : AppCompatActivity() {

    private var conf: String = ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_importar)

        val tvArchivo = findViewById<TextView>(R.id.tvArchivo)
        val tvServidor = findViewById<TextView>(R.id.tvServidor)
        val etNombre = findViewById<EditText>(R.id.etNombre)

        val (texto, nombrePropuesto) = leerContenido()

        if (texto.isBlank()) {
            Toast.makeText(this, R.string.no_archivo, Toast.LENGTH_LONG).show()
            finish()
            return
        }

        val cfg = AwgConfig.parse(texto)
        if (cfg == null) {
            Toast.makeText(
                this,
                R.string.archivo_no_valido,
                Toast.LENGTH_LONG
            ).show()
            finish()
            return
        }

        conf = texto
        tvArchivo.text = nombrePropuesto
        tvServidor.text = cfg.ipServidor + " : " + puerto(cfg)
        etNombre.setText(nombrePropuesto.removeSuffix(".conf").removeSuffix(".txt"))

        findViewById<MaterialButton>(R.id.btnGuardar).setOnClickListener {
            val nombre = etNombre.text.toString().trim().ifEmpty { getString(R.string.perfil_importado) }
            Perfiles.agregar(this, nombre, conf)
            Toast.makeText(this, getString(R.string.perfil_anadido, nombre), Toast.LENGTH_SHORT).show()
            startActivity(Intent(this, PerfilesActivity::class.java))
            finish()
        }

        findViewById<MaterialButton>(R.id.btnCancelar).setOnClickListener { finish() }
    }

    private fun puerto(cfg: AwgConfig): String {
        val linea = cfg.uapi.lines().firstOrNull { it.startsWith("endpoint=") }
        return linea?.substringAfter(":")?.trim().orEmpty()
    }

    /** Devuelve el texto del .conf y un nombre propuesto a partir del archivo. */
    private fun leerContenido(): Pair<String, String> {
        val intent = intent
        var uri: Uri? = null
        var nombre = "perfil.conf"

        when (intent?.action) {
            Intent.ACTION_SEND -> {
                uri = intent.getParcelableExtra(Intent.EXTRA_STREAM)
                if (uri == null) {
                    val texto = intent.getStringExtra(Intent.EXTRA_TEXT).orEmpty()
                    return texto to "perfil.conf"
                }
            }

            else -> {
                uri = intent?.data
            }
        }

        if (uri == null) return "" to nombre

        try {
            contentResolver.query(uri, null, null, null, null)?.use { cursor ->
                val columna = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if (columna >= 0 && cursor.moveToFirst()) {
                    nombre = cursor.getString(columna) ?: nombre
                }
            }
        } catch (e: Exception) {
        }

        val texto = try {
            contentResolver.openInputStream(uri)?.bufferedReader()?.use { it.readText() }.orEmpty()
        } catch (e: Exception) {
            ""
        }

        return texto to nombre
    }
}
