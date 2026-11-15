//go:build windows

// geoid-tun: crea el adaptador de red virtual (Wintun), lo configura y levanta
// AmneziaWG dentro del mismo proceso.
//
// Uso:  geoid-tun.exe <ruta-al-.conf> [mtu]
//
// Escribe en la salida estandar:
//   LISTO            cuando el tunel esta funcionando
//   STATS rx tx      cada 2 segundos
//   ERROR <texto>    si algo falla
//
// Se cierra cuando se cierra su entrada estandar (la app lo hace al desconectar).
package main

import (
	"bufio"
	"encoding/base64"
	"encoding/hex"
	"fmt"
	"io"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"syscall"
	"time"

	"github.com/amnezia-vpn/amneziawg-go/v3/conn"
	"github.com/amnezia-vpn/amneziawg-go/v3/device"
	"github.com/amnezia-vpn/amneziawg-go/v3/tun"
)

const nombreInterfaz = "geoid"

var archivoLog = "geoid-tun.log"

func anotar(formato string, args ...any) {
	linea := fmt.Sprintf("%s  %s\n", time.Now().Format("2006-01-02 15:04:05"),
		fmt.Sprintf(formato, args...))
	os.Stderr.WriteString(linea)
	if f, err := os.OpenFile(archivoLog, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644); err == nil {
		f.WriteString(linea)
		f.Close()
	}
}

type config struct {
	direccion string
	dns       string
	mtu       int
	endpoint  string
	uapi      string
}

func aHex(b64 string) string {
	datos, err := base64.StdEncoding.DecodeString(strings.TrimSpace(b64))
	if err != nil {
		return ""
	}
	return hex.EncodeToString(datos)
}

var directas = map[string]bool{
	"jc": true, "jmin": true, "jmax": true,
	"s1": true, "s2": true, "s3": true, "s4": true,
	"h1": true, "h2": true, "h3": true, "h4": true,
	"i1": true, "i2": true, "i3": true, "i4": true, "i5": true,
	"randomtrailers": true, "disablecookies": true,
}

func analizar(texto string) (*config, error) {
	privada, publica, precompartida := "", "", ""
	endpoint, allowed, keepalive := "", "", ""
	direccion, dns, cabecera := "", "", ""
	mtu := 1420
	enPeer := false
	dispositivo := make([][2]string, 0, 8)

	for _, bruta := range strings.Split(texto, "\n") {
		linea := strings.TrimSpace(bruta)
		if linea == "" || strings.HasPrefix(linea, "#") {
			continue
		}
		if strings.HasPrefix(linea, "[") {
			enPeer = strings.EqualFold(linea, "[Peer]")
			continue
		}
		pos := strings.Index(linea, "=")
		if pos < 0 {
			continue
		}
		clave := strings.ToLower(strings.ReplaceAll(strings.TrimSpace(linea[:pos]), "_", ""))
		valor := strings.TrimSpace(linea[pos+1:])

		switch {
		case clave == "privatekey":
			privada = valor
		case clave == "address":
			direccion = valor
		case clave == "dns":
			dns = valor
		case clave == "mtu":
			if n, err := strconv.Atoi(valor); err == nil {
				mtu = n
			}
		case clave == "publickey" && enPeer:
			publica = valor
		case clave == "presharedkey" && enPeer:
			precompartida = valor
		case clave == "endpoint" && enPeer:
			endpoint = valor
		case clave == "allowedips" && enPeer:
			allowed = valor
		case clave == "persistentkeepalive" && enPeer:
			keepalive = valor
		case clave == "headerprotectionkey":
			cabecera = valor
		case directas[clave]:
			dispositivo = append(dispositivo, [2]string{clave, valor})
		case clave == "contentpaddingaddition":
			dispositivo = append(dispositivo, [2]string{"content_padding_addition", valor})
		}
	}

	if privada == "" || publica == "" || endpoint == "" {
		return nil, fmt.Errorf("configuracion incompleta (falta clave o endpoint)")
	}

	var uapi strings.Builder
	uapi.WriteString("private_key=" + aHex(privada) + "\n")
	uapi.WriteString("listen_port=0\n")
	for _, par := range dispositivo {
		uapi.WriteString(par[0] + "=" + par[1] + "\n")
	}
	if cabecera != "" {
		uapi.WriteString("header_protection_key=" + aHex(cabecera) + "\n")
	}
	uapi.WriteString("public_key=" + aHex(publica) + "\n")
	if precompartida != "" {
		uapi.WriteString("preshared_key=" + aHex(precompartida) + "\n")
	}
	uapi.WriteString("endpoint=" + endpoint + "\n")
	for _, a := range strings.Split(allowed, ",") {
		if limpio := strings.TrimSpace(a); limpio != "" {
			uapi.WriteString("allowed_ip=" + limpio + "\n")
		}
	}
	if keepalive != "" {
		uapi.WriteString("persistent_keepalive_interval=" + keepalive + "\n")
	}
	uapi.WriteString("\n") // linea en blanco: fin de la operacion

	primera := strings.TrimSpace(strings.Split(direccion, ",")[0])
	primera = strings.TrimSpace(strings.Split(primera, "/")[0])
	if primera == "" {
		return nil, fmt.Errorf("la configuracion no tiene direccion")
	}
	primerDns := strings.TrimSpace(strings.Split(dns, ",")[0])

	return &config{
		direccion: primera,
		dns:       primerDns,
		mtu:       mtu,
		endpoint:  strings.TrimSpace(strings.Split(endpoint, ":")[0]),
		uapi:      uapi.String(),
	}, nil
}

func ejecutar(nombre string, argumentos ...string) (string, error) {
	cmd := exec.Command(nombre, argumentos...)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	salida, err := cmd.CombinedOutput()
	texto := strings.TrimSpace(string(salida))
	if err != nil {
		anotar("%s %s -> %v (%s)", nombre, strings.Join(argumentos, " "), err, texto)
	}
	return texto, err
}

func netsh(argumentos ...string) {
	ejecutar("netsh", argumentos...)
}

// puertaFisica devuelve la pasarela y el indice de la interfaz por la que sale
// el trafico normal, para que el handshake no entre en el propio tunel.
func puertaFisica() (string, string) {
	orden := "(Get-NetRoute -DestinationPrefix '0.0.0.0/0' | " +
		"Where-Object { $_.NextHop -ne '0.0.0.0' } | " +
		"Sort-Object RouteMetric | Select-Object -First 1 | " +
		"ForEach-Object { $_.NextHop + '|' + $_.ifIndex })"
	texto, err := ejecutar("powershell",
		"-NoProfile", "-NonInteractive", "-Command", orden)
	if err != nil || texto == "" {
		return "", ""
	}
	partes := strings.Split(strings.TrimSpace(texto), "|")
	if len(partes) != 2 {
		return "", ""
	}
	return strings.TrimSpace(partes[0]), strings.TrimSpace(partes[1])
}

func main() {
	anotar("arrancando geoid-tun")

	if len(os.Args) < 2 {
		fmt.Println("ERROR uso: geoid-tun.exe <conf> [mtu]")
		return
	}
	contenido, err := os.ReadFile(os.Args[1])
	if err != nil {
		fmt.Println("ERROR no se pudo leer la configuracion: " + err.Error())
		return
	}
	cfg, err := analizar(string(contenido))
	if err != nil {
		fmt.Println("ERROR " + err.Error())
		return
	}
	if len(os.Args) > 2 {
		if n, e := strconv.Atoi(os.Args[2]); e == nil && n > 0 {
			cfg.mtu = n
		}
	}

	dispositivo, err := tun.CreateTUN(nombreInterfaz, cfg.mtu)
	if err != nil {
		fmt.Println("ERROR creando el adaptador (hacen falta permisos de administrador): " + err.Error())
		return
	}
	anotar("adaptador %s creado (mtu %d)", nombreInterfaz, cfg.mtu)

	// 1) excepcion para el servidor: sale por la red fisica
	if cfg.endpoint != "" {
		if gw, indice := puertaFisica(); gw != "" && indice != "" {
			netsh("interface", "ipv4", "add", "route",
				cfg.endpoint+"/32", "interface="+indice, "nexthop="+gw,
				"metric=1", "store=active")
			anotar("ruta del servidor %s via %s (interfaz %s)", cfg.endpoint, gw, indice)
		}
	}

	// 2) direccion, ruta por defecto y DNS
	netsh("interface", "ipv4", "set", "address", "name="+nombreInterfaz,
		"source=static", "address="+cfg.direccion, "mask=255.255.255.255", "gateway=none")
	netsh("interface", "ipv4", "add", "route", "prefix=0.0.0.0/0",
		"interface="+nombreInterfaz, "nexthop=0.0.0.0", "metric=1", "store=active")
	if cfg.dns != "" {
		netsh("interface", "ipv4", "set", "dnsservers", "name="+nombreInterfaz,
			"source=static", "address="+cfg.dns, "register=primary", "validate=no")
	}
	anotar("red configurada: %s dns %s", cfg.direccion, cfg.dns)

	// 3) motor
	dev := device.NewDevice(dispositivo, conn.NewDefaultBind(),
		device.NewLogger(device.LogLevelError, "geoid: "))
	if err := dev.IpcSet(cfg.uapi); err != nil {
		fmt.Println("ERROR configurando el motor: " + err.Error())
		dev.Close()
		return
	}
	if err := dev.Up(); err != nil {
		fmt.Println("ERROR levantando el motor: " + err.Error())
		dev.Close()
		return
	}
	anotar("motor en marcha")
	fmt.Println("LISTO")

	terminado := make(chan struct{})
	go func() {
		io.Copy(io.Discard, os.Stdin)
		close(terminado)
	}()

	go func() {
		for {
			select {
			case <-terminado:
				return
			case <-time.After(2 * time.Second):
				estado, err := dev.IpcGet()
				if err != nil {
					continue
				}
				var rx, tx string
				sc := bufio.NewScanner(strings.NewReader(estado))
				for sc.Scan() {
					linea := sc.Text()
					if strings.HasPrefix(linea, "rx_bytes=") {
						rx = strings.TrimPrefix(linea, "rx_bytes=")
					}
					if strings.HasPrefix(linea, "tx_bytes=") {
						tx = strings.TrimPrefix(linea, "tx_bytes=")
					}
				}
				if rx == "" {
					rx = "0"
				}
				if tx == "" {
					tx = "0"
				}
				fmt.Printf("STATS %s %s\n", rx, tx)
			}
		}
	}()

	<-terminado
	anotar("cerrando")
	dev.Close()
	fmt.Println("CERRADO")
}
