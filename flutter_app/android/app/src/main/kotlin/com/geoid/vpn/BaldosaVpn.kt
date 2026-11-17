package com.geoid.vpn

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.graphics.drawable.Icon
import android.net.VpnService
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService

/**
 * Azulejo del panel rápido: conectar y desconectar la VPN desde arriba.
 *
 * Si aún no hay permiso de VPN o no hay ningún perfil creado, abre la app
 * para resolverlo; en el resto de casos conecta o desconecta al instante.
 */
class BaldosaVpn : TileService() {

    override fun onStartListening() {
        super.onStartListening()
        pintar()
    }

    override fun onClick() {
        super.onClick()

        if (ControlVpn.activo(this)) {
            ControlVpn.desconectar(this)
            pintar()
            return
        }

        // Falta el permiso de VPN o no hay perfil: hay que abrir la app.
        val permiso = try {
            VpnService.prepare(this)
        } catch (e: Exception) {
            null
        }
        if (permiso != null || !ControlVpn.hayPerfil(this)) {
            val abrir = Intent(this, MainActivity::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            @Suppress("DEPRECATION")
            startActivityAndCollapse(abrir)
            return
        }

        ControlVpn.conectar(this)
        pintar()
    }

    private fun pintar() {
        val azulejo = qsTile ?: return
        val conectada = ControlVpn.activo(this)
        azulejo.state = if (conectada) Tile.STATE_ACTIVE else Tile.STATE_INACTIVE
        azulejo.label = getString(R.string.app_name)
        try {
            azulejo.icon = Icon.createWithResource(this, R.mipmap.ic_launcher)
        } catch (e: Exception) {
            // si el icono falla, se queda el que ponga el sistema
        }
        azulejo.updateTile()
    }

    companion object {
        /** Pide al sistema que vuelva a dibujar el azulejo. */
        fun refrescar(context: Context) {
            try {
                requestListeningState(
                    context,
                    ComponentName(context, BaldosaVpn::class.java)
                )
            } catch (e: Exception) {
                // sin azulejo colocado no hay nada que refrescar
            }
        }
    }
}
