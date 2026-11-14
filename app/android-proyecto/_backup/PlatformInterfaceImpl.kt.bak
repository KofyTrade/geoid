package com.kofy.vlessgen

import android.content.Context
import android.net.ConnectivityManager
import android.net.LinkProperties
import android.net.Network
import android.net.NetworkCapabilities
import android.net.VpnService
import android.os.Build
import android.os.ParcelFileDescriptor
import io.nekohasekai.libbox.BridgeOptions
import io.nekohasekai.libbox.BridgeSession
import io.nekohasekai.libbox.AutoRedirectHandler
import io.nekohasekai.libbox.AutoRedirectSession
import io.nekohasekai.libbox.ConnectionOwner
import io.nekohasekai.libbox.InterfaceUpdateListener
import io.nekohasekai.libbox.Libbox
import io.nekohasekai.libbox.LocalDNSTransport
import io.nekohasekai.libbox.NeighborUpdateListener
import io.nekohasekai.libbox.NetworkInterfaceIterator
import io.nekohasekai.libbox.PlatformInterface
import io.nekohasekai.libbox.PlatformUser
import io.nekohasekai.libbox.ShellSession
import io.nekohasekai.libbox.StringIterator
import io.nekohasekai.libbox.TunOptions
import io.nekohasekai.libbox.WIFIState
import java.net.InetAddress
import java.net.InetSocketAddress

/**
 * v1.0 — Puente entre sing-box (Go) y Android.
 *
 * sing-box nos llama a [openTun] cuando necesita la interfaz de red: nosotros la
 * creamos con [VpnService.Builder] y le devolvemos el descriptor.
 *
 * El resto son funciones opcionales (shell, bridge, tailscale, notificaciones del
 * core). Las dejamos en no-op / null: sing-box funciona sin ellas.
 */
class PlatformInterfaceImpl(private val servicio: VpnService) : PlatformInterface {

    companion object {
        /** Go no acepta null en androidPackageNames: le damos un iterador vacio. */
        private val ITERADOR_VACIO: StringIterator = object : StringIterator {
            override fun hasNext(): Boolean = false
            override fun len(): Int = 0
            override fun next(): String = throw NoSuchElementException()
        }
    }

    /** Hay que mantener la referencia viva: si se recolecta, el GC cierra el fd. */
    @Volatile
    var tun: ParcelFileDescriptor? = null
        private set

    private var monitor: InterfaceUpdateListener? = null
    private var callback: ConnectivityManager.NetworkCallback? = null

    // ------------------------------------------------------------------ TUN

    override fun openTun(options: TunOptions): Int {
        val builder = servicio.Builder()
            .setSession("VlessGen")
            .setMtu(if (options.mtu in 1280..9000) options.mtu else 1500)

        val dir4 = options.inet4Address
        while (dir4.hasNext()) {
            val p = dir4.next()
            builder.addAddress(p.address(), p.prefix())
        }

        val dir6 = options.inet6Address
        while (dir6.hasNext()) {
            val p = dir6.next()
            builder.addAddress(p.address(), p.prefix())
        }

        val ruta4 = options.inet4RouteAddress
        var rutas = 0
        var hayDefault = false
        while (ruta4.hasNext()) {
            val p = ruta4.next()
            if (p.prefix() == 0) hayDefault = true
            builder.addRoute(p.address(), p.prefix())
            rutas++
        }
        android.util.Log.i("VlessGen", "openTun: mtu=${options.mtu} rutas4=$rutas default=$hayDefault")
        if (!hayDefault) {
            // El core no mando ruta por defecto: la anadimos para tunelizar todo.
            builder.addRoute("0.0.0.0", 0)
            android.util.Log.i("VlessGen", "openTun: anadida ruta 0.0.0.0/0")
        }

        val ruta6 = options.inet6RouteAddress
        while (ruta6.hasNext()) {
            val p = ruta6.next()
            builder.addRoute(p.address(), p.prefix())
        }

        val dns = options.dnsServerAddress
        while (dns.hasNext()) {
            builder.addDnsServer(dns.next())
        }

        // La lista de apps viaja dentro del JSON de sing-box y llega hasta aqui.
        val incluidas = options.includePackage
        var hayIncluidas = false
        while (incluidas.hasNext()) {
            hayIncluidas = true
            val pkg = incluidas.next()
            if (pkg != servicio.packageName) {
                try {
                    builder.addAllowedApplication(pkg)
                } catch (e: Exception) {
                    // paquete desinstalado
                }
            }
        }

        if (!hayIncluidas) {
            val excluidas = options.excludePackage
            while (excluidas.hasNext()) {
                try {
                    builder.addDisallowedApplication(excluidas.next())
                } catch (e: Exception) {
                }
            }
        }

        val descriptor = builder.establish()
            ?: throw IllegalStateException("Android denego la interfaz TUN")

        tun = descriptor
        return descriptor.fd
    }

    // ------------------------------------------------- red y utilidades

    override fun autoDetectInterfaceControl(fd: Int) {
        servicio.protect(fd)
    }

    override fun startDefaultInterfaceMonitor(listener: InterfaceUpdateListener) {
        monitor = listener
        val cm = servicio.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager

        val cb = object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) = reportar(network, listener)
            override fun onLinkPropertiesChanged(network: Network, lp: LinkProperties) =
                reportar(network, listener)
        }
        callback = cb

        try {
            cm.registerDefaultNetworkCallback(cb)
        } catch (e: Exception) {
        }

        // Reportar la red activa de inmediato: si no, sing-box arranca sin interfaz.
        try {
            cm.activeNetwork?.let { reportar(it, listener) }
        } catch (e: Exception) {
        }
    }

    /** Red real por la que salir, saltando la propia VPN. */
    private fun redSubyacente(cm: ConnectivityManager): Network? {
        val activa = cm.activeNetwork
        val caps = activa?.let { cm.getNetworkCapabilities(it) }
        if (caps != null && !caps.hasTransport(NetworkCapabilities.TRANSPORT_VPN)) return activa

        return cm.allNetworks.firstOrNull { n ->
            val c = cm.getNetworkCapabilities(n) ?: return@firstOrNull false
            c.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
                !c.hasTransport(NetworkCapabilities.TRANSPORT_VPN)
        }
    }

    private fun reportar(network: Network, listener: InterfaceUpdateListener) {
        try {
            val cm = servicio.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            var red = network
            val capsInicial = cm.getNetworkCapabilities(red)

            // Si nos llega la propia VPN, hay que reportar la red de debajo:
            // si no, sing-box intenta salir por su propio tunel y se bloquea.
            if (capsInicial != null && capsInicial.hasTransport(NetworkCapabilities.TRANSPORT_VPN)) {
                red = redSubyacente(cm) ?: return
            }

            val caps = cm.getNetworkCapabilities(red) ?: return
            val lp = cm.getLinkProperties(red) ?: return

            // Decirle a Android sobre que red va la VPN. Sin esto no la usa como
            // red por defecto y el trafico de las apps se va directo.
            try {
                servicio.setUnderlyingNetworks(arrayOf(red))
            } catch (e: Exception) {
            }
            val nombre = lp.interfaceName ?: return
            val indice = try {
                java.net.NetworkInterface.getByName(nombre)?.index ?: 0
            } catch (e: Exception) {
                0
            }
            val wifi = caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)
            val caro = !caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_METERED)
            android.util.Log.i("VlessGen", "interfaz por defecto: $nombre idx=$indice wifi=$wifi")
            listener.updateDefaultInterface(nombre, indice, wifi, caro)
        } catch (e: Exception) {
        }
    }

    override fun closeDefaultInterfaceMonitor(listener: InterfaceUpdateListener) {
        if (monitor === listener) monitor = null
        try {
            callback?.let { cb ->
                val cm = servicio.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
                cm.unregisterNetworkCallback(cb)
            }
        } catch (e: Exception) {
        }
        callback = null
    }

    override fun getInterfaces(): NetworkInterfaceIterator {
        // Go no puede enumerar interfaces por netlink (SELinux lo deniega en apps),
        // asi que se las damos ya masticadas desde Java.
        val lista = mutableListOf<io.nekohasekai.libbox.NetworkInterface>()
        try {
            val enumeracion = java.net.NetworkInterface.getNetworkInterfaces()
            while (enumeracion.hasMoreElements()) {
                val jni = enumeracion.nextElement()
                val ni = io.nekohasekai.libbox.NetworkInterface()
                ni.index = jni.index
                ni.name = jni.name
                ni.mtu = try {
                    jni.mtu
                } catch (e: Exception) {
                    1500
                }

                val direcciones = mutableListOf<String>()
                // sing-box exige CIDR ("fe80::1/64"), no direcciones sueltas.
                for (ia in jni.interfaceAddresses) {
                    val dir = ia.address ?: continue
                    val limpia = (dir.hostAddress ?: continue).substringBefore('%')
                    direcciones.add("$limpia/${ia.networkPrefixLength}")
                }
                ni.addresses = IteradorLista(direcciones)

                // Valores de net.Flag* de Go
                var flags = 0
                if (jni.isUp) flags = flags or 0x1
                if (jni.isLoopback) flags = flags or 0x4
                if (jni.isPointToPoint) flags = flags or 0x8
                if (jni.supportsMulticast()) flags = flags or 0x10
                ni.flags = flags

                val nombre = jni.name ?: ""
                ni.type = when {
                    nombre.startsWith("wlan") -> Libbox.InterfaceTypeWIFI
                    nombre.startsWith("rmnet") || nombre.startsWith("ccmni") ->
                        Libbox.InterfaceTypeCellular
                    nombre.startsWith("eth") -> Libbox.InterfaceTypeEthernet
                    else -> Libbox.InterfaceTypeOther
                }
                ni.metered = nombre.startsWith("rmnet")

                lista.add(ni)
            }
        } catch (e: Exception) {
        }
        return IteradorInterfaces(lista)
    }

    private class IteradorLista(private val items: List<String>) : StringIterator {
        private var i = 0
        override fun hasNext(): Boolean = i < items.size
        override fun len(): Int = items.size - i
        override fun next(): String = items[i++]
    }

    private class IteradorInterfaces(
        private val items: List<io.nekohasekai.libbox.NetworkInterface>
    ) : NetworkInterfaceIterator {
        private var i = 0
        override fun hasNext(): Boolean = i < items.size
        override fun next(): io.nekohasekai.libbox.NetworkInterface = items[i++]
    }

    override fun findConnectionOwner(
        ipProtocol: Int,
        sourceAddress: String?,
        sourcePort: Int,
        destinationAddress: String?,
        destinationPort: Int
    ): ConnectionOwner {
        // Devolver null aqui hace que Go reviente (nil pointer en service.go:197).
        val propietario = ConnectionOwner()
        propietario.userId = -1
        propietario.userName = ""
        propietario.processPath = ""
        propietario.setAndroidPackageNames(ITERADOR_VACIO)

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q &&
            sourceAddress != null && destinationAddress != null
        ) {
            try {
                val cm = servicio.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
                val local = InetSocketAddress(InetAddress.getByName(sourceAddress), sourcePort)
                val remoto = InetSocketAddress(InetAddress.getByName(destinationAddress), destinationPort)
                val uid = cm.getConnectionOwnerUid(ipProtocol, local, remoto)
                if (uid > 0) propietario.userId = uid
            } catch (e: Exception) {
                // sin permiso o conexion ya cerrada
            }
        }

        return propietario
    }

    override fun readWIFIState(): WIFIState? = null

    override fun registerMyInterface(name: String?) {
    }

    // ------------------------------------------- opcionales: no soportadas

    override fun usePlatformShell(): Boolean = false
    override fun usePlatformBridge(): Boolean = false
    override fun usePlatformAutoRedirect(): Boolean = false

    override fun createAutoRedirect(
        options: ByteArray?,
        handler: AutoRedirectHandler?
    ): AutoRedirectSession? = null
    override fun usePlatformAutoDetectInterfaceControl(): Boolean = true
    override fun includeAllNetworks(): Boolean = false
    override fun underNetworkExtension(): Boolean = false

    override fun localDNSTransport(): LocalDNSTransport? = null

    override fun createBridge(options: BridgeOptions?): BridgeSession? = null

    override fun lookupUser(username: String?): PlatformUser? = null

    override fun lookupSFTPServer(): String = ""

    override fun readSystemSSHHostKey(): String = ""

    override fun tailscaleHostname(): String = ""

    override fun openShellSession(
        user: PlatformUser?,
        command: String?,
        args: StringIterator?,
        env: String?,
        rows: Int,
        cols: Int
    ): ShellSession? = null

    override fun startNeighborMonitor(listener: NeighborUpdateListener?) {
    }

    override fun closeNeighborMonitor(listener: NeighborUpdateListener?) {
    }

    override fun sendNotification(notification: io.nekohasekai.libbox.Notification?) {
    }

    override fun cancelNotification(tag: String?, id: Int) {
    }

    override fun clearDNSCache() {
    }

    override fun checkPlatformShell() {
    }
}
