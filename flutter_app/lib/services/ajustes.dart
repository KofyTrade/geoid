import 'package:flutter/foundation.dart';

import '../i18n.dart';
import '../theme.dart';
import 'nativo.dart';

/// Preferencias de la app: idioma y tema.
class Ajustes {
  static const String _zona = 'ajustes';

  static final ValueNotifier<bool> oscuro = ValueNotifier(true);

  /// null = seguir el idioma del sistema.
  static String? idioma;

  static Future<void> cargar() async {
    idioma = await Nativo.leer(_zona, 'idioma');
    final tema = await Nativo.leer(_zona, 'tema');

    oscuro.value = tema != 'claro';
    GeoidColors.oscuro = oscuro.value;
    I18n.fijar(idioma);
  }

  static Future<void> ponerIdioma(String? codigo) async {
    idioma = (codigo == null || codigo.isEmpty) ? null : codigo;
    I18n.fijar(idioma);
    await Nativo.guardar(_zona, 'idioma', idioma);
  }

  static Future<void> ponerOscuro(bool valor) async {
    oscuro.value = valor;
    GeoidColors.oscuro = valor;
    await Nativo.guardar(_zona, 'tema', valor ? 'oscuro' : 'claro');
  }
}
