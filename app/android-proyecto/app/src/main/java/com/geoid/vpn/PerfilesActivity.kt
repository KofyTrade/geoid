package com.geoid.vpn

import android.app.AlertDialog
import android.net.Uri
import android.os.Bundle
import android.provider.OpenableColumns
import android.text.InputType
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.BaseAdapter
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ListView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.button.MaterialButton

/**
 * Lista de perfiles de conexion.
 *
 * - Un toque: usa ese perfil.
 * - Pulsacion larga: renombrar, editar la configuracion o borrar.
 * - Boton inferior: crear uno nuevo pegando el .conf.
 */
class PerfilesActivity : AppCompatActivity() {

    private lateinit var lista: ListView
    private lateinit var tvAyuda: TextView
    private lateinit var adaptador: Adaptador

    private var perfiles: List<Perfil> = emptyList()

    // Campos del dialogo abierto, para rellenarlos cuando se elige un archivo.
    private var campoNombreActual: EditText? = null
    private var campoConfActual: EditText? = null

    private val selectorArchivo = registerForActivityResult(
        ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        if (uri == null) return@registerForActivityResult
        try {
            val texto = contentResolver.openInputStream(uri)
                ?.bufferedReader()
                ?.use { it.readText() }
                .orEmpty()

            if (texto.isBlank()) {
                Toast.makeText(this, R.string.archivo_vacio, Toast.LENGTH_SHORT).show()
                return@registerForActivityResult
            }

            if (AwgConfig.parse(texto) == null) {
                Toast.makeText(
                    this,
                    R.string.archivo_no_valido,
                    Toast.LENGTH_LONG
                ).show()
                return@registerForActivityResult
            }

            campoConfActual?.setText(texto)
            if (campoNombreActual?.text.isNullOrBlank()) {
                campoNombreActual?.setText(nombreDelArchivo(uri))
            }
            Toast.makeText(this, R.string.conf_cargada, Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            Toast.makeText(this, getString(R.string.error_leer_archivo, e.message ?: ""), Toast.LENGTH_LONG).show()
        }
    }

    /** Nombre del archivo sin la extension, para proponerlo como nombre del perfil. */
    private fun nombreDelArchivo(uri: Uri): String {
        var nombre = getString(R.string.nuevo_perfil)
        try {
            contentResolver.query(uri, null, null, null, null)?.use { cursor ->
                val columna = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if (columna >= 0 && cursor.moveToFirst()) {
                    nombre = cursor.getString(columna) ?: nombre
                }
            }
        } catch (e: Exception) {
        }
        return nombre.removeSuffix(".conf").removeSuffix(".txt")
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_perfiles)

        lista = findViewById(R.id.lvPerfiles)
        tvAyuda = findViewById(R.id.tvAyuda)

        findViewById<TextView>(R.id.btnVolver).setOnClickListener { finish() }
        findViewById<MaterialButton>(R.id.btnNuevo).setOnClickListener { dialogoPerfil(null) }

        Perfiles.migrar(this)

        adaptador = Adaptador()
        lista.adapter = adaptador

        lista.setOnItemClickListener { _, _, posicion, _ ->
            activar(perfiles[posicion])
        }

        lista.setOnItemLongClickListener { _, _, posicion, _ ->
            menuPerfil(perfiles[posicion])
            true
        }
    }

    override fun onResume() {
        super.onResume()
        recargar()
    }

    private fun recargar() {
        perfiles = Perfiles.listar(this)
        adaptador.notifyDataSetChanged()
        val activo = Perfiles.activo(this)
        tvAyuda.text = if (perfiles.isEmpty()) {
            getString(R.string.perfiles_vacio)
        } else if (activo != null) {
            getString(R.string.perfiles_en_uso, activo.nombre)
        } else {
            getString(R.string.perfiles_toca)
        }
    }

    private fun activar(perfil: Perfil) {
        Perfiles.activar(this, perfil.id)
        recargar()
        Toast.makeText(this, getString(R.string.usando_perfil, perfil.nombre), Toast.LENGTH_SHORT).show()
    }

    private fun menuPerfil(perfil: Perfil) {
        AlertDialog.Builder(this)
            .setTitle(perfil.nombre)
            .setItems(arrayOf(getString(R.string.renombrar), getString(R.string.editar_configuracion), getString(R.string.borrar))) { _, opcion ->
                when (opcion) {
                    0 -> dialogoRenombrar(perfil)
                    1 -> dialogoPerfil(perfil)
                    2 -> confirmarBorrado(perfil)
                }
            }
            .show()
    }

    /** Campo de texto con el estilo de la app (fondo redondeado, sin subrayado). */
    private fun campo(ayuda: String, valor: String, multilinea: Boolean = false): EditText {
        return EditText(this).apply {
            hint = ayuda
            setText(valor)
            background = androidx.core.content.ContextCompat
                .getDrawable(this@PerfilesActivity, R.drawable.bg_busqueda)
            setPadding(34, 26, 34, 26)
            setTextColor(0xFFE8FBF7.toInt())
            setHintTextColor(0xFF4E7C79.toInt())
            if (multilinea) {
                minLines = 6
                gravity = android.view.Gravity.TOP
                inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_MULTI_LINE
            } else {
                inputType = InputType.TYPE_CLASS_TEXT
            }
        }
    }

    private fun caja(vararg vistas: android.view.View): LinearLayout {
        return LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 32, 48, 8)
            for (v in vistas) {
                val parametros = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                )
                parametros.bottomMargin = 20
                addView(v, parametros)
            }
        }
    }

    private fun dialogoRenombrar(perfil: Perfil) {
        val entrada = campo(getString(R.string.nombre_perfil), perfil.nombre)
        entrada.setSelection(perfil.nombre.length)

        AlertDialog.Builder(this)
            .setTitle(R.string.renombrar_perfil)
            .setView(caja(entrada))
            .setPositiveButton(R.string.guardar) { _, _ ->
                val nombre = entrada.text.toString().trim()
                if (nombre.isEmpty()) {
                    Toast.makeText(this, R.string.nombre_vacio, Toast.LENGTH_SHORT).show()
                } else {
                    Perfiles.actualizar(this, perfil.id, nombre, perfil.conf)
                    recargar()
                }
            }
            .setNegativeButton(R.string.cancelar, null)
            .show()
    }

    private fun dialogoPerfil(original: Perfil?) {
        val esNuevo = original == null

        val etNombre = campo(getString(R.string.nombre_ejemplo), original?.nombre ?: "")
        val etConf = campo(getString(R.string.pega_conf), original?.conf ?: "", multilinea = true)
        etConf.setTextIsSelectable(true)

        campoNombreActual = etNombre
        campoConfActual = etConf

        // Boton para traer el .conf desde el almacenamiento del movil.
        val btnArchivo = MaterialButton(this).apply {
            text = getString(R.string.elegir_archivo)
            textSize = 13f
            setTextColor(0xFF05161A.toInt())
            backgroundTintList =
                android.content.res.ColorStateList.valueOf(0xFF2EE6C5.toInt())
            setOnClickListener { selectorArchivo.launch("*/*") }
        }

        AlertDialog.Builder(this)
            .setTitle(if (esNuevo) R.string.nuevo_perfil else R.string.editar_configuracion)
            .setView(caja(btnArchivo, etNombre, etConf))
            .setPositiveButton(R.string.guardar) { _, _ ->
                val nombre = etNombre.text.toString().trim().ifEmpty {
                    getString(R.string.perfil_n, perfiles.size + 1)
                }
                val conf = etConf.text.toString()

                if (AwgConfig.parse(conf) == null) {
                    Toast.makeText(
                        this,
                        R.string.datos_incompletos,
                        Toast.LENGTH_LONG
                    ).show()
                    return@setPositiveButton
                }

                if (esNuevo) {
                    Perfiles.agregar(this, nombre, conf)
                } else {
                    Perfiles.actualizar(this, original!!.id, nombre, conf)
                }
                recargar()
            }
            .setNegativeButton(R.string.cancelar, null)
            .show()
    }

    private fun confirmarBorrado(perfil: Perfil) {
        AlertDialog.Builder(this)
            .setTitle(R.string.borrar_perfil_titulo)
            .setMessage(perfil.nombre + "\n" + perfil.servidor)
            .setPositiveButton(R.string.borrar) { _, _ ->
                Perfiles.borrar(this, perfil.id)
                recargar()
                Toast.makeText(this, R.string.perfil_borrado, Toast.LENGTH_SHORT).show()
            }
            .setNegativeButton(R.string.cancelar, null)
            .show()
    }

    private inner class Adaptador : BaseAdapter() {
        override fun getCount(): Int = perfiles.size
        override fun getItem(position: Int): Any = perfiles[position]
        override fun getItemId(position: Int): Long = position.toLong()

        override fun getView(position: Int, convertView: View?, parent: ViewGroup?): View {
            val vista = convertView ?: LayoutInflater.from(this@PerfilesActivity)
                .inflate(R.layout.item_perfil, parent, false)

            val perfil = perfiles[position]
            val activo = Perfiles.activo(this@PerfilesActivity)?.id == perfil.id

            vista.findViewById<TextView>(R.id.tvNombre).text = perfil.nombre
            vista.findViewById<TextView>(R.id.tvServidor).text =
                perfil.servidor + " : " + perfil.puerto
            vista.findViewById<TextView>(R.id.tvActivo).visibility =
                if (activo) View.VISIBLE else View.GONE

            vista.setBackgroundColor(if (activo) 0xFF0B2429.toInt() else 0x00000000)
            return vista
        }
    }
}
