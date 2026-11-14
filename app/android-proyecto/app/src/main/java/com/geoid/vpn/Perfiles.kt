package com.geoid.vpn

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID

/** Un perfil de conexion: un nombre y el contenido de su .conf. */
data class Perfil(
    val id: String,
    val nombre: String,
    val conf: String
) {
    val servidor: String
        get() = AwgConfig.parse(conf)?.ipServidor ?: ""

    val puerto: String
        get() {
            val linea = conf.lines().firstOrNull {
                it.trim().startsWith("Endpoint", ignoreCase = true)
            }
            return linea?.substringAfter(":")?.trim().orEmpty()
        }

    val valido: Boolean
        get() = AwgConfig.parse(conf) != null
}

/**
 * Guarda los perfiles en SharedPreferences como una lista JSON.
 * El perfil activo es el que usa el servicio para conectar.
 */
object Perfiles {

    private const val PREFS = "perfiles"
    private const val CLAVE_LISTA = "lista"
    private const val CLAVE_ACTIVO = "activo"

    private fun preferencias(contexto: Context) =
        contexto.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    fun listar(contexto: Context): List<Perfil> {
        val crudo = preferencias(contexto).getString(CLAVE_LISTA, null) ?: return emptyList()
        val lista = mutableListOf<Perfil>()
        try {
            val array = JSONArray(crudo)
            for (i in 0 until array.length()) {
                val o = array.getJSONObject(i)
                lista.add(
                    Perfil(
                        o.optString("id"),
                        o.optString("nombre"),
                        o.optString("conf")
                    )
                )
            }
        } catch (e: Exception) {
            return emptyList()
        }
        return lista
    }

    private fun guardarLista(contexto: Context, lista: List<Perfil>) {
        val array = JSONArray()
        for (p in lista) {
            val o = JSONObject()
            o.put("id", p.id)
            o.put("nombre", p.nombre)
            o.put("conf", p.conf)
            array.put(o)
        }
        preferencias(contexto).edit().putString(CLAVE_LISTA, array.toString()).apply()
    }

    fun activo(contexto: Context): Perfil? {
        val id = preferencias(contexto).getString(CLAVE_ACTIVO, null)
        val lista = listar(contexto)
        if (id != null) {
            lista.firstOrNull { it.id == id }?.let { return it }
        }
        return lista.firstOrNull()
    }

    fun activar(contexto: Context, id: String) {
        preferencias(contexto).edit().putString(CLAVE_ACTIVO, id).apply()
    }

    fun agregar(contexto: Context, nombre: String, conf: String): Perfil {
        val perfil = Perfil(UUID.randomUUID().toString(), nombre, conf)
        val lista = listar(contexto).toMutableList()
        lista.add(perfil)
        guardarLista(contexto, lista)
        if (lista.size == 1) activar(contexto, perfil.id)
        return perfil
    }

    fun actualizar(contexto: Context, id: String, nombre: String, conf: String) {
        val lista = listar(contexto).toMutableList()
        val pos = lista.indexOfFirst { it.id == id }
        if (pos >= 0) {
            lista[pos] = lista[pos].copy(nombre = nombre, conf = conf)
            guardarLista(contexto, lista)
        }
    }

    fun borrar(contexto: Context, id: String) {
        val lista = listar(contexto).toMutableList()
        lista.removeAll { it.id == id }
        guardarLista(contexto, lista)
        if (preferencias(contexto).getString(CLAVE_ACTIVO, null) == id) {
            lista.firstOrNull()?.let { activar(contexto, it.id) }
        }
    }

    /** Trae el .conf antiguo (unica conexion) como primer perfil. */
    fun migrar(contexto: Context) {
        if (listar(contexto).isNotEmpty()) return
        val viejo = contexto.getSharedPreferences("awg", Context.MODE_PRIVATE)
            .getString("conf", "").orEmpty()
        if (viejo.isBlank()) return
        agregar(contexto, contexto.getString(R.string.mi_servidor), viejo)
    }
}
