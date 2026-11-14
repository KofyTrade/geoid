import 'package:flutter/foundation.dart';

/// Registro de lo que va pasando (para la pantalla de Log).
class Registro {
  static final ValueNotifier<List<String>> lineas = ValueNotifier<List<String>>([]);

  static void anadir(String texto) {
    final hora = DateTime.now();
    final marca = '${hora.hour.toString().padLeft(2, '0')}:'
        '${hora.minute.toString().padLeft(2, '0')}:'
        '${hora.second.toString().padLeft(2, '0')}';
    final nuevas = List<String>.from(lineas.value)..add('$marca  $texto');
    if (nuevas.length > 200) nuevas.removeRange(0, nuevas.length - 200);
    lineas.value = nuevas;
  }

  static void limpiar() => lineas.value = [];
}
