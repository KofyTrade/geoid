package com.geoid.vpn

/** Estado compartido del tunel. */
object Estado {
    @Volatile
    var activo: Boolean = false

    @Volatile
    var error: String? = null
}
