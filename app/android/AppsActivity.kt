package com.geoid.vpn

import android.content.Intent
import android.graphics.Color
import android.graphics.drawable.Drawable
import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.BaseAdapter
import android.widget.EditText
import android.widget.ImageView
import android.widget.ListView
import android.widget.Switch
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/**
 * Selector de aplicaciones, con el mismo estilo que la pantalla principal.
 *
 * - Interruptor por aplicacion (se pulsa la fila entera).
 * - Las seleccionadas suben al principio de la lista.
 * - Sin seleccion, pasan TODAS las apps por la VPN (comportamiento por defecto).
 */
class AppsActivity : AppCompatActivity() {

    private data class App(val paquete: String, val nombre: String, val icono: Drawable)

    private val seleccion = mutableSetOf<String>()
    private var todas: List<App> = emptyList()
    private var visibles: List<App> = emptyList()
    private var busqueda: String = ""

    private lateinit var adaptador: Adaptador
    private lateinit var tvResumen: TextView
    private lateinit var swTodas: Switch
    private lateinit var pbCargando: android.widget.ProgressBar
    private var actualizandoSwitch = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_apps)

        tvResumen = findViewById(R.id.tvResumen)
        val lista = findViewById<ListView>(R.id.lvApps)
        val buscar = findViewById<EditText>(R.id.etBuscar)
        swTodas = findViewById(R.id.swTodas)
        pbCargando = findViewById(R.id.pbCargando)

        findViewById<TextView>(R.id.btnVolver).setOnClickListener { finish() }

        getSharedPreferences("apps", MODE_PRIVATE)
            .getStringSet("seleccion", emptySet())
            ?.let { seleccion.addAll(it) }

        adaptador = Adaptador()
        lista.adapter = adaptador

        // Cargar la lista de apps (con sus iconos) tarda: va en segundo plano
        // para que la pantalla no se quede congelada al abrirse.
        Thread {
            val cargadas = cargarApps()
            runOnUiThread {
                todas = cargadas
                pbCargando.visibility = View.GONE
                lista.visibility = View.VISIBLE
                recalcular()
            }
        }.start()

        swTodas.setOnCheckedChangeListener { _, marcado ->
            if (actualizandoSwitch) return@setOnCheckedChangeListener
            if (marcado) {
                seleccion.addAll(todas.map { it.paquete })
            } else {
                seleccion.clear()
            }
            guardar()
            recalcular()
        }

        // Se pulsa la fila entera: mas comodo que apuntar al interruptor.
        lista.setOnItemClickListener { _, _, posicion, _ ->
            val app = visibles[posicion]
            if (!seleccion.add(app.paquete)) seleccion.remove(app.paquete)
            guardar()
            recalcular()
        }

        buscar.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            override fun afterTextChanged(s: Editable?) {
                busqueda = s?.toString()?.trim()?.lowercase().orEmpty()
                recalcular()
            }
        })
    }

    override fun onPause() {
        super.onPause()
        guardar()
    }

    private fun guardar() {
        getSharedPreferences("apps", MODE_PRIVATE)
            .edit()
            .putStringSet("seleccion", seleccion)
            .apply()
    }

    /** Rehace la lista visible: filtra por busqueda y pone las elegidas arriba. */
    private fun recalcular() {
        val filtradas = if (busqueda.isEmpty()) {
            todas
        } else {
            todas.filter {
                it.nombre.lowercase().contains(busqueda) ||
                    it.paquete.lowercase().contains(busqueda)
            }
        }

        visibles = filtradas.sortedWith(
            compareByDescending<App> { seleccion.contains(it.paquete) }
                .thenBy { it.nombre.lowercase() }
        )

        adaptador.notifyDataSetChanged()
        pintarResumen()

        // Refleja el estado del interruptor "seleccionar todas" sin disparar su listener.
        actualizandoSwitch = true
        swTodas.isChecked = todas.isNotEmpty() && todas.all { seleccion.contains(it.paquete) }
        actualizandoSwitch = false
    }

    private fun cargarApps(): List<App> {
        val intento = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
        val resueltos = packageManager.queryIntentActivities(intento, 0)
        val vistos = mutableSetOf<String>()
        val lista = mutableListOf<App>()

        for (r in resueltos) {
            val pkg = r.activityInfo.packageName
            if (pkg == packageName) continue
            if (!vistos.add(pkg)) continue
            lista.add(App(pkg, r.loadLabel(packageManager).toString(), r.loadIcon(packageManager)))
        }
        return lista
    }

    private fun pintarResumen() {
        tvResumen.text = if (seleccion.isEmpty()) {
            getString(R.string.apps_todas_usan)
        } else {
            resources.getQuantityString(R.plurals.apps_resumen, seleccion.size, seleccion.size)
        }
    }

    private inner class Adaptador : BaseAdapter() {
        override fun getCount(): Int = visibles.size
        override fun getItem(position: Int): Any = visibles[position]
        override fun getItemId(position: Int): Long = position.toLong()

        override fun getView(position: Int, convertView: View?, parent: ViewGroup?): View {
            val vista = convertView ?: LayoutInflater.from(this@AppsActivity)
                .inflate(R.layout.item_app, parent, false)

            val app = visibles[position]
            val marcada = seleccion.contains(app.paquete)

            vista.findViewById<ImageView>(R.id.ivIcono).setImageDrawable(app.icono)
            vista.findViewById<TextView>(R.id.tvNombre).text = app.nombre
            vista.findViewById<TextView>(R.id.tvPaquete).text = app.paquete
            vista.findViewById<Switch>(R.id.swSeleccion).isChecked = marcada

            // Fondo un poco mas claro en las seleccionadas: se ven de un vistazo.
            vista.setBackgroundColor(if (marcada) 0xFF0B2429.toInt() else Color.TRANSPARENT)

            return vista
        }
    }
}
