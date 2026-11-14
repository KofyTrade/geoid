import 'package:flutter/services.dart';

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

/// Puente con el codigo nativo de Android.
class Nativo {
  static const MethodChannel _canal = MethodChannel('geoid/nativo');
  static const EventChannel _estado = EventChannel('geoid/estado');

  static Future<String> version() async {
    final v = await _canal.invokeMethod<String>('version');
    return v ?? '0';
  }

  static Future<String?> leer(String nombre, String clave) {
    return _canal.invokeMethod<String>('prefsLeer', {
      'nombre': nombre,
      'clave': clave,
    });
  }

  static Future<void> guardar(String nombre, String clave, String? valor) {
    return _canal.invokeMethod('prefsGuardar', {
      'nombre': nombre,
      'clave': clave,
      'valor': valor,
    });
  }

  static Future<List<AppInstalada>> aplicaciones() async {
    final lista = await _canal.invokeMethod<List<dynamic>>('listarApps');
    return (lista ?? []).map(AppInstalada.desde).toList();
  }

  static Future<String?> elegirArchivo() {
    return _canal.invokeMethod<String>('elegirArchivo');
  }

  static Future<bool> prepararVpn() async {
    final listo = await _canal.invokeMethod<bool>('prepararVpn');
    return listo ?? false;
  }

  static Future<void> conectar({
    required String conf,
    required int mtu,
    String? dns,
    required List<String> apps,
    required bool filtrar,
  }) {
    return _canal.invokeMethod('conectar', {
      'conf': conf,
      'mtu': mtu,
      'dns': dns,
      'apps': apps,
      'filtrar': filtrar,
    });
  }

  static Future<void> desconectar() {
    return _canal.invokeMethod('desconectar');
  }

  static Future<String> stats() async {
    final crudo = await _canal.invokeMethod<String>('stats');
    return crudo ?? '';
  }

  static Future<void> descargar(String url, String nombre) {
    return _canal.invokeMethod('descargar', {'url': url, 'nombre': nombre});
  }

  /// Escucha la respuesta del dialogo de permiso de VPN.
  static void alConcederVpn(void Function(bool concedido) callback) {
    _canal.setMethodCallHandler((llamada) async {
      if (llamada.method == 'vpnConcedida') {
        callback(llamada.arguments as bool? ?? false);
      }
      return null;
    });
  }

  /// Avisos de estado del tunel: {activo: bool, error: String?}
  static Stream<Map<String, dynamic>> estado() {
    return _estado.receiveBroadcastStream().map((evento) {
      final mapa = Map<String, dynamic>.from(evento as Map);
      return mapa;
    });
  }
}
