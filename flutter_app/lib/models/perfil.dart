import 'dart:convert';

import '../services/nativo.dart';

/// Un perfil: nombre visible + contenido del .conf.
class Perfil {
  String nombre;
  String conf;

  Perfil(this.nombre, this.conf);

  Map<String, dynamic> aJson() => {'nombre': nombre, 'conf': conf};

  factory Perfil.desdeJson(Map<String, dynamic> json) => Perfil(
        json['nombre'] as String? ?? 'Perfil',
        json['conf'] as String? ?? '',
      );

  /// IP y puerto del servidor, para mostrarlos en la lista.
  String get resumen {
    for (final bruta in conf.split('\n')) {
      final linea = bruta.trim();
      if (linea.toLowerCase().startsWith('endpoint')) {
        return linea.split('=').last.trim();
      }
    }
    return '';
  }
}

/// Guardado de perfiles en las preferencias de Android (via canal nativo).
class Almacen {
  static const String _zona = 'perfiles';

  static Future<List<Perfil>> lista() async {
    final crudo = await Nativo.leer(_zona, 'lista');
    if (crudo == null || crudo.isEmpty) return [];
    try {
      final datos = jsonDecode(crudo) as List<dynamic>;
      return datos
          .map((e) => Perfil.desdeJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (_) {
      return [];
    }
  }

  static Future<void> guardarLista(List<Perfil> perfiles) {
    return Nativo.guardar(
      _zona,
      'lista',
      jsonEncode(perfiles.map((p) => p.aJson()).toList()),
    );
  }

  static Future<String?> activo() => Nativo.leer(_zona, 'activo');

  static Future<void> marcarActivo(String nombre) =>
      Nativo.guardar(_zona, 'activo', nombre);

  /// Devuelve el perfil activo, o el primero si no hay marcado.
  static Future<Perfil?> activoPerfil() async {
    final todos = await lista();
    if (todos.isEmpty) return null;
    final nombre = await activo();
    if (nombre == null) return todos.first;
    for (final p in todos) {
      if (p.nombre == nombre) return p;
    }
    return todos.first;
  }
}
