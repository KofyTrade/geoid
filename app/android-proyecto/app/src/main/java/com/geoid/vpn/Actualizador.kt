package com.geoid.vpn

import android.app.DownloadManager
import android.content.Context
import android.net.Uri
import android.os.Environment
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/** Una version nueva publicada en GitHub. */
data class NuevaVersion(val numero: String, val urlApk: String, val notas: String)

/**
 * Comprueba si hay una version nueva en las Releases de GitHub y la descarga.
 *
 * El repositorio es publico, asi que la API responde sin credenciales.
 */
object Actualizador {

    private const val REPO = "KofyTrade/geoid"
    private const val API = "https://api.github.com/repos/$REPO/releases/latest"

    /** Version instalada, por ejemplo "1.1". */
    fun versionInstalada(contexto: Context): String {
        return try {
            val info = contexto.packageManager.getPackageInfo(contexto.packageName, 0)
            info.versionName ?: "0"
        } catch (e: Exception) {
            "0"
        }
    }

    /** Consulta GitHub. Devuelve null si no hay red, no hay release o algo falla. */
    fun buscar(): NuevaVersion? {
        var conexion: HttpURLConnection? = null
        return try {
            conexion = URL(API).openConnection() as HttpURLConnection
            conexion.setRequestProperty("Accept", "application/vnd.github+json")
            conexion.connectTimeout = 6000
            conexion.readTimeout = 6000

            if (conexion.responseCode != HttpURLConnection.HTTP_OK) return null

            val texto = conexion.inputStream.bufferedReader().use { it.readText() }
            val json = JSONObject(texto)
            val etiqueta = json.optString("tag_name").trim().removePrefix("v").removePrefix("V")
            if (etiqueta.isEmpty()) return null

            val activos = json.optJSONArray("assets") ?: return null
            var url = ""
            for (i in 0 until activos.length()) {
                val activo = activos.getJSONObject(i)
                val nombre = activo.optString("name")
                if (nombre.endsWith(".apk", ignoreCase = true)) {
                    url = activo.optString("browser_download_url")
                    break
                }
            }
            if (url.isEmpty()) return null

            NuevaVersion(etiqueta, url, json.optString("body").orEmpty())
        } catch (e: Exception) {
            null
        } finally {
            conexion?.disconnect()
        }
    }

    /** True si [remota] es mas nueva que [actual] comparando 1.2.3. */
    fun esMasNueva(remota: String, actual: String): Boolean {
        val r = remota.split(".").mapNotNull { it.trim().toIntOrNull() }
        val a = actual.split(".").mapNotNull { it.trim().toIntOrNull() }
        if (r.isEmpty()) return false
        for (i in 0 until maxOf(r.size, a.size)) {
            val x = r.getOrElse(i) { 0 }
            val y = a.getOrElse(i) { 0 }
            if (x > y) return true
            if (x < y) return false
        }
        return false
    }

    /** Deja el APK descargandose; al terminar, la notificacion del sistema permite instalarlo. */
    fun descargar(contexto: Context, version: NuevaVersion) {
        val peticion = DownloadManager.Request(Uri.parse(version.urlApk))
            .setTitle(contexto.getString(R.string.app_name) + " " + version.numero)
            .setDescription(contexto.getString(R.string.descargando))
            .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
            .setMimeType("application/vnd.android.package-archive")
            .setDestinationInExternalPublicDir(
                Environment.DIRECTORY_DOWNLOADS,
                "GeoiD-vpn-" + version.numero + ".apk"
            )

        val gestor = contexto.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
        gestor.enqueue(peticion)
    }
}
