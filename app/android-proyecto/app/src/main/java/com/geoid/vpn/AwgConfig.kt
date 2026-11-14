package com.geoid.vpn

import android.util.Base64

/**
 * Parser de ficheros de configuracion de AmneziaWG (.conf).
 *
 * De un mismo texto saca dos cosas:
 *  1. Lo que necesita el VpnService: direcciones, DNS y MTU.
 *  2. La configuracion UAPI (formato "wg setconf") para el motor Go.
 *
 * Soporta AmneziaWG 2.x (Jc/Jmin/Jmax, S1-S4, H1-H4) y 3.x (I1-I5,
 * HeaderProtectionKey, ContentPaddingAddition, RandomTrailers, DisableCookies).
 * Sin los parametros 3.x el servidor descarta el handshake.
 */
data class AwgConfig(
    val direcciones: List<String>,
    val dns: List<String>,
    val mtu: Int,
    val uapi: String,
    val ipServidor: String
) {
    companion object {

        /** Claves que se copian tal cual a la UAPI (mismo nombre, en minusculas). */
        private val DIRECTAS = setOf(
            "jc", "jmin", "jmax",
            "s1", "s2", "s3", "s4",
            "h1", "h2", "h3", "h4",
            "i1", "i2", "i3", "i4", "i5",
            "random_trailers", "disable_cookies"
        )

        /** Claves del .conf que en la UAPI se llaman distinto. */
        private val RENOMBRADAS = mapOf(
            "contentpaddingaddition" to "content_padding_addition"
        )

        /** base64 (formato .conf) -> hexadecimal (formato UAPI). */
        private fun aHex(b64: String): String {
            return try {
                val bytes = Base64.decode(b64, Base64.DEFAULT)
                bytes.joinToString("") { "%02x".format(it) }
            } catch (e: Exception) {
                ""
            }
        }

        fun parse(texto: String): AwgConfig? {
            var privada = ""
            var publica = ""
            var precompartida = ""
            var endpoint = ""
            var allowed = ""
            var keepalive = ""
            var address = ""
            var dns = ""
            var mtu = 1420
            var enPeer = false
            var claveCabecera = ""
            val dispositivo = mutableListOf<Pair<String, String>>()

            for (bruta in texto.lines()) {
                val linea = bruta.trim()
                if (linea.isEmpty() || linea.startsWith("#")) continue
                if (linea.startsWith("[")) {
                    enPeer = linea.equals("[Peer]", ignoreCase = true)
                    continue
                }
                val pos = linea.indexOf('=')
                if (pos < 0) continue
                val clave = linea.substring(0, pos).trim().lowercase().replace("_", "")
                val valor = linea.substring(pos + 1).trim()

                when {
                    clave == "privatekey" -> privada = valor
                    clave == "address" -> address = valor
                    clave == "dns" -> dns = valor
                    clave == "mtu" -> mtu = valor.toIntOrNull() ?: mtu

                    clave == "publickey" && enPeer -> publica = valor
                    clave == "presharedkey" && enPeer -> precompartida = valor
                    clave == "endpoint" && enPeer -> endpoint = valor
                    clave == "allowedips" && enPeer -> allowed = valor
                    clave == "persistentkeepalive" && enPeer -> keepalive = valor

                    clave == "headerprotectionkey" -> claveCabecera = valor

                    DIRECTAS.contains(clave) -> dispositivo.add(clave to valor)

                    RENOMBRADAS.containsKey(clave) ->
                        dispositivo.add(RENOMBRADAS.getValue(clave) to valor)
                }
            }

            if (privada.isEmpty() || publica.isEmpty() || endpoint.isEmpty()) return null

            val uapi = buildString {
                append("private_key=").append(aHex(privada)).append('\n')
                append("listen_port=0\n")
                for ((c, v) in dispositivo) append(c).append('=').append(v).append('\n')
                if (claveCabecera.isNotEmpty()) {
                    append("header_protection_key=").append(aHex(claveCabecera)).append('\n')
                }
                append("public_key=").append(aHex(publica)).append('\n')
                if (precompartida.isNotEmpty()) {
                    append("preshared_key=").append(aHex(precompartida)).append('\n')
                }
                append("endpoint=").append(endpoint).append('\n')
                for (a in allowed.split(",")) {
                    val limpio = a.trim()
                    if (limpio.isNotEmpty()) append("allowed_ip=").append(limpio).append('\n')
                }
                if (keepalive.isNotEmpty()) {
                    append("persistent_keepalive_interval=").append(keepalive).append('\n')
                }
            }

            val direcciones = address.split(",").map { it.trim() }.filter { it.isNotEmpty() }
            val servidores = dns.split(",").map { it.trim() }.filter { it.isNotEmpty() }

            return AwgConfig(direcciones, servidores, mtu, uapi, endpoint.substringBefore(":"))
        }
    }
}
