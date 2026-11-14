package com.kofy.vlessgen

/**
 * v1.0 — Genera el JSON de configuracion de sing-box.
 *
 * La lista blanca de apps va en "include_package" del inbound tun: sing-box la
 * lee y nos la pasa de vuelta en TunOptions.openTun().
 */
object SingBoxConfig {

    private fun esc(s: String): String =
        s.replace("\\", "\\\\").replace("\"", "\\\"")

    fun json(
        host: String,
        puerto: Int,
        uuid: String,
        pbk: String,
        sid: String,
        sni: String,
        apps: Set<String>,
        rutaLog: String? = null,
        bloquearAnuncios: Boolean = false,
        rutaListaAnuncios: String? = null
    ): String {
        val sb = StringBuilder()

        sb.append("{")
        sb.append("\"log\":{\"level\":\"debug\",\"timestamp\":true")
        if (rutaLog != null) {
            sb.append(",\"output\":\"").append(esc(rutaLog)).append("\"")
        }
        sb.append("},")

        // DNS en nuestro propio servidor (dnsmasq en 5353), por TCP y dentro del
        // tunel. Asi el DPI no puede envenenar las respuestas.
        sb.append("\"dns\":{")
        sb.append("\"servers\":[{\"type\":\"tcp\",\"tag\":\"remote\",\"server\":\"")
        sb.append(esc(host)).append("\",\"server_port\":5353,\"detour\":\"proxy\"}],")
        sb.append("\"final\":\"remote\"")
        sb.append("},")

        sb.append("\"inbounds\":[{")
        sb.append("\"type\":\"tun\",")
        sb.append("\"tag\":\"tun-in\",")
        sb.append("\"address\":[\"172.19.0.1/30\"],")
        sb.append("\"mtu\":1400,")
        sb.append("\"auto_route\":true,")
        sb.append("\"strict_route\":false,")
        sb.append("\"stack\":\"system\"")
        if (apps.isNotEmpty()) {
            sb.append(",\"include_package\":[")
            sb.append(apps.joinToString(",") { "\"${esc(it)}\"" })
            sb.append("]")
        }
        sb.append("}],")

        sb.append("\"outbounds\":[{")
        sb.append("\"type\":\"vless\",")
        sb.append("\"tag\":\"proxy\",")
        sb.append("\"server\":\"").append(esc(host)).append("\",")
        sb.append("\"server_port\":").append(puerto).append(",")
        sb.append("\"uuid\":\"").append(esc(uuid)).append("\",")
        sb.append("\"flow\":\"xtls-rprx-vision\",")
        sb.append("\"tls\":{")
        sb.append("\"enabled\":true,")
        sb.append("\"server_name\":\"").append(esc(sni)).append("\",")
        sb.append("\"utls\":{\"enabled\":true,\"fingerprint\":\"chrome\"},")
        sb.append("\"reality\":{")
        sb.append("\"enabled\":true,")
        sb.append("\"public_key\":\"").append(esc(pbk)).append("\",")
        sb.append("\"short_id\":\"").append(esc(sid)).append("\"")
        sb.append("}")
        sb.append("}")
        sb.append("},{\"type\":\"direct\",\"tag\":\"direct\"}],")

        sb.append("\"route\":{")

        val conBloqueo = bloquearAnuncios && rutaListaAnuncios != null
        if (conBloqueo) {
            sb.append("\"rule_set\":[{")
            sb.append("\"type\":\"local\",\"tag\":\"ads\",\"format\":\"source\",\"path\":\"")
            sb.append(esc(rutaListaAnuncios!!))
            sb.append("\"}],")
        }

        // Desde 1.11 el DNS del tun ya no se intercepta solo: hay que declararlo.
        sb.append("\"rules\":[{\"port\":53,\"action\":\"hijack-dns\"}")
        // El UDP no vuelve por el tunel (Vision no lo transporta bien). Al rechazar
        // QUIC, las apps caen a TCP y el video/imagenes si cargan.
        sb.append(",{\"network\":\"udp\",\"port\":443,\"action\":\"reject\"}")
        if (conBloqueo) {
            sb.append(",{\"rule_set\":\"ads\",\"action\":\"reject\"}")
        }
        sb.append("],")

        sb.append("\"final\":\"proxy\",")
        // Con la lista de interfaces y el monitor funcionando, sing-box sale por
        // wlan0 protegido con VpnService.protect(fd).
        sb.append("\"auto_detect_interface\":true")
        sb.append("}")

        sb.append("}")
        return sb.toString()
    }
}
