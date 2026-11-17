package com.geoid.vpn

import android.content.Context
import android.content.Intent
import androidx.core.content.ContextCompat
import org.json.JSONArray

/**
 * Conectar y desconectar la VPN sin pasar por Flutter.
 *
 * Lo usa el azulejo del panel rápido: lee el perfil activo de las mismas
 * preferencias que guarda la app y arranca el servicio con esos datos.
 */
object ControlVpn {

    private const val ZONA_PERFILES = "perfiles"
    private const val ZONA_APPS = "apps"
    private const val ZONA_AJUSTES = "ajustes"
    private const val CLAVE_ACTIVA = "vpn_activa"

    private fun prefs(context: Context) =
        context.getSharedPreferences(ZONA_AJUSTES, Context.MODE_PRIVATE)

    /** ¿Está la VPN conectada ahora mismo? */
    fun activo(context: Context): Boolean = prefs(context).getBoolean(CLAVE_ACTIVA, false)

    /** Guarda el estado y avisa al azulejo para que se repinte. */
    fun marcar(context: Context, activo: Boolean) {
        prefs(context).edit().putBoolean(CLAVE_ACTIVA, activo).apply()
        BaldosaVpn.refrescar(context)
    }

    /** Contenido del .conf del perfil activo (o el primero de la lista). */
    fun perfilActivo(context: Context): String? {
        val p = context.getSharedPreferences(ZONA_PERFILES, Context.MODE_PRIVATE)
        val crudo = p.getString("lista", null) ?: return null
        if (crudo.isEmpty()) return null
        val nombre = p.getString("activo", null)
        return try {
            val lista = JSONArray(crudo)
            var primero: String? = null
            for (i in 0 until lista.length()) {
                val item = lista.getJSONObject(i)
                val conf = item.optString("conf")
                if (conf.isEmpty()) continue
                if (nombre != null && item.optString("nombre") == nombre) return conf
                if (primero == null) primero = conf
            }
            primero
        } catch (e: Exception) {
            null
        }
    }

    fun hayPerfil(context: Context): Boolean = perfilActivo(context) != null

    /** MTU del .conf, con los mismos límites que la app. */
    private fun mtuDe(conf: String): Int {
        for (bruta in conf.lines()) {
            val linea = bruta.trim().lowercase()
            if (!linea.startsWith("mtu")) continue
            val valor = linea.substringAfterLast("=").trim().toIntOrNull() ?: continue
            if (valor in 1280..1400) return valor
        }
        return 1280
    }

    /** Arranca la VPN con el perfil activo. False si no hay ningún perfil. */
    fun conectar(context: Context): Boolean {
        val conf = perfilActivo(context) ?: return false

        val ajustes = context.getSharedPreferences(ZONA_AJUSTES, Context.MODE_PRIVATE)
        val filtrar = ajustes.getString("bloquearAnuncios", "true") != "false"

        val crudo = context.getSharedPreferences(ZONA_APPS, Context.MODE_PRIVATE)
            .getString("seleccion", "") ?: ""
        val apps = crudo.split(",").map { it.trim() }.filter { it.isNotEmpty() }

        val intencion = Intent(context, AwgTunnelService::class.java)
            .setAction(AwgTunnelService.ACTION_CONNECT)
            .putExtra(AwgTunnelService.EXTRA_CONFIG, conf)
            .putExtra(AwgTunnelService.EXTRA_MTU, mtuDe(conf))
            .putExtra(AwgTunnelService.EXTRA_FILTRAR, filtrar)
            .putStringArrayListExtra(AwgTunnelService.EXTRA_APPS, ArrayList(apps))

        return try {
            ContextCompat.startForegroundService(context, intencion)
            true
        } catch (e: Exception) {
            false
        }
    }

    fun desconectar(context: Context) {
        val intencion = Intent(context, AwgTunnelService::class.java)
            .setAction(AwgTunnelService.ACTION_DISCONNECT)
        try {
            ContextCompat.startForegroundService(context, intencion)
        } catch (e: Exception) {
            context.stopService(intencion)
        }
    }
}
