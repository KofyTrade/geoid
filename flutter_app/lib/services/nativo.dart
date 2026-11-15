import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/services.dart';

import 'tun_windows.dart';

/// Aplicacion instalada en el telefono.
class AppInstalada {
  final String paquete;
  final String nombre;
  final bool sistema;

  const AppInstalada(this.paquete, this.nombre, this.sistema);

  factory AppInstalada.desde(dynamic datos) {
    final mapa = Map<String, dynamic>.from(datos as Map);
    return AppInstalada(
      mapa['paquete'] as String? ?? '',
      mapa['nombre'] as String? ?? '',
      mapa['sistema'] as bool? ?? false,
    );
  }

  String get inicial => nombre.isEmpty ? '?' : nombre.substring(0, 1).toUpperCase();
}

bool get esAndroid => Platform.isAndroid;

/// Guardado en fichero para escritorio (Windows, Linux, macOS).
class _PrefsArchivo {
  static Map<String, Map<String, String>>? _cache;

  static Directory get _carpeta {
    final base = Platform.environment['APPDATA'] ??
        Platform.environment['XDG_CONFIG_HOME'] ??
        Platform.environment['HOME'] ??
        Directory.current.path;
    return Directory('$base${Platform.pathSeparator}GeoiD-vpn');
  }

  static File get _fichero => File(
      '${_carpeta.path}${Platform.pathSeparator}ajustes.json');

  static Map<String, Map<String, String>> _leer() {
    if (_cache != null) return _cache!;
    try {
      if (_fichero.existsSync()) {
        final datos = jsonDecode(_fichero.readAsStringSync()) as Map<String, dynamic>;
        _cache = datos.map((zona, valores) => MapEntry(
              zona,
              Map<String, String>.from(valores as Map),
            ));
      } else {
        _cache = {};
      }
    } catch (_) {
      _cache = {};
    }
    return _cache!;
  }

  static void _guardar() {
    try {
      _carpeta.createSync(recursive: true);
      _fichero.writeAsStringSync(jsonEncode(_cache));
    } catch (_) {
      // sin permisos: se pierde el cambio, no se rompe la app
    }
  }

  static String? leer(String zona, String clave) => _leer()[zona]?[clave];

  static void escribir(String zona, String clave, String? valor) {
    final datos = _leer();
    datos.putIfAbsent(zona, () => <String, String>{});
    if (valor == null) {
      datos[zona]!.remove(clave);
    } else {
      datos[zona]![clave] = valor;
    }
    _guardar();
  }
}

/// Puente con el codigo nativo. En Android habla con Kotlin; en escritorio
/// usa un fichero de ajustes y el tunel todavia no esta disponible.
class Nativo {
  static const MethodChannel _canal = MethodChannel('geoid/nativo');
  static const EventChannel _estado = EventChannel('geoid/estado');

  static String _versionEscritorio = '2.0.3';

  static Future<String> version() async {
    if (!esAndroid) return _versionEscritorio;
    final v = await _canal.invokeMethod<String>('version');
    return v ?? '0';
  }

  static Future<String?> leer(String nombre, String clave) async {
    if (!esAndroid) return _PrefsArchivo.leer(nombre, clave);
    return _canal.invokeMethod<String>('prefsLeer', {
      'nombre': nombre,
      'clave': clave,
    });
  }

  static Future<void> guardar(String nombre, String clave, String? valor) async {
    if (!esAndroid) {
      _PrefsArchivo.escribir(nombre, clave, valor);
      return;
    }
    await _canal.invokeMethod('prefsGuardar', {
      'nombre': nombre,
      'clave': clave,
      'valor': valor,
    });
  }

  static Future<List<AppInstalada>> aplicaciones() async {
    if (!esAndroid) return [];
    final lista = await _canal.invokeMethod<List<dynamic>>('listarApps');
    return (lista ?? []).map(AppInstalada.desde).toList();
  }

  static Future<String?> elegirArchivo() async {
    if (!esAndroid) return _leerConfDelPortapapeles();
    return _canal.invokeMethod<String>('elegirArchivo');
  }

  static Future<bool> prepararVpn() async {
    if (Platform.isWindows) return TunWindows.disponible;
    if (!esAndroid) return false;
    final listo = await _canal.invokeMethod<bool>('prepararVpn');
    return listo ?? false;
  }

  static Future<void> conectar({
    required String conf,
    required int mtu,
    String? dns,
    required List<String> apps,
    required bool filtrar,
  }) async {
    if (Platform.isWindows) {
      await TunWindows.conectar(conf, mtu);
      return;
    }
    if (!esAndroid) {
      throw UnsupportedError('escritorio');
    }
    await _canal.invokeMethod('conectar', {
      'conf': conf,
      'mtu': mtu,
      'dns': dns,
      'apps': apps,
      'filtrar': filtrar,
    });
  }

  static Future<void> desconectar() async {
    if (Platform.isWindows) return TunWindows.desconectar();
    if (!esAndroid) return;
    await _canal.invokeMethod('desconectar');
  }

  static Future<String> stats() async {
    if (Platform.isWindows) {
      return '\;\';
    }
    if (!esAndroid) return '';
    final crudo = await _canal.invokeMethod<String>('stats');
    return crudo ?? '';
  }

  static Future<void> descargar(String url, String nombre) async {
    if (!esAndroid) {
      // En escritorio se abre la pagina de descargas del navegador.
      if (Platform.isWindows) {
        await Process.run('cmd', ['/c', 'start', '', url], runInShell: true);
      } else if (Platform.isMacOS) {
        await Process.run('open', [url]);
      } else {
        await Process.run('xdg-open', [url]);
      }
      return;
    }
    await _canal.invokeMethod('descargar', {'url': url, 'nombre': nombre});
  }

  /// Escucha la respuesta del dialogo de permiso de VPN.
  static void alConcederVpn(void Function(bool concedido) callback) {
    if (!esAndroid) return;
    _canal.setMethodCallHandler((llamada) async {
      if (llamada.method == 'vpnConcedida') {
        callback(llamada.arguments as bool? ?? false);
      }
      return null;
    });
  }

  /// Avisos de estado del tunel: {activo: bool, error: String?}
  static Stream<Map<String, dynamic>> estado() {
    if (Platform.isWindows) return TunWindows.avisos;
    if (!esAndroid) {
      return Stream<Map<String, dynamic>>.value({'activo': false, 'error': null});
    }
    return _estado.receiveBroadcastStream().map((evento) {
      final mapa = Map<String, dynamic>.from(evento as Map);
      return mapa;
    });
  }

  /// En escritorio no hay selector de ficheros nativo: se pide pegar el texto.
  static Future<String?> _leerConfDelPortapapeles() async {
    final datos = await Clipboard.getData(Clipboard.kTextPlain);
    final texto = datos?.text ?? '';
    if (texto.toLowerCase().contains('[interface]')) return texto;
    return null;
  }
}
