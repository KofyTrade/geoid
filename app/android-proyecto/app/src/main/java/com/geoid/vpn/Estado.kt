package com.geoid.vpn

/**
 * Estado compartido entre los dos motores (sing-box y AmneziaWG) y la Activity.
 */
object Estado {
    @Volatile
    var activo: Boolean = false
}
