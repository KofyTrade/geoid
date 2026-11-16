import 'package:flutter/material.dart';

/// Paleta activa. El tema claro/oscuro cambia estos valores y toda la
/// interfaz los sigue.
class GeoidColors {
  static bool oscuro = true;

  static const Color _acento = Color(0xFF2EE6C5);

  // --- oscuro (el de siempre) ---
  static const Color _fondoOscuro = Color(0xFF05161A);
  static const Color _panelOscuro = Color(0xFF0B2429);
  static const Color _botonOscuro = Color(0xFF13333A);
  static const Color _textoOscuro = Color(0xFFE8FBF7);
  static const Color _textoSuaveOscuro = Color(0xFF7FA8A4);
  static const Color _textoTenueOscuro = Color(0xFF4E7C79);
  static const Color _bordeOscuro = Color(0xFF1E5A58);

  // --- claro ---
  static const Color _fondoClaro = Color(0xFFF2FAF8);
  static const Color _panelClaro = Color(0xFFFFFFFF);
  static const Color _botonClaro = Color(0xFFE3F4F0);
  static const Color _textoClaro = Color(0xFF08282C);
  static const Color _textoSuaveClaro = Color(0xFF3F6F6B);
  static const Color _textoTenueClaro = Color(0xFF6E9A95);
  static const Color _bordeClaro = Color(0xFFAED9D2);

  static Color get fondo => oscuro ? _fondoOscuro : _fondoClaro;
  static Color get panel => oscuro ? _panelOscuro : _panelClaro;
  static Color get botonApagado => oscuro ? _botonOscuro : _botonClaro;
  static Color get texto => oscuro ? _textoOscuro : _textoClaro;
  static Color get textoSuave => oscuro ? _textoSuaveOscuro : _textoSuaveClaro;
  static Color get textoTenue => oscuro ? _textoTenueOscuro : _textoTenueClaro;
  static Color get borde => oscuro ? _bordeOscuro : _bordeClaro;
  static Color get acento => _acento;
  static Color get linea => oscuro ? const Color(0xFF0E2A2E) : const Color(0xFFDCEEEA);

  /// Marca (siempre turquesa, legible en los dos temas).
  static Color get marca => oscuro ? const Color(0xFF5FD9C8) : const Color(0xFF0E8C7F);

  /// Texto de los botones secundarios.
  static Color get textoBoton =>
      oscuro ? const Color(0xFF9BE8DC) : const Color(0xFF0C6F66);
}

ThemeData temaGeoid({bool? oscuro}) {
  final esOscuro = oscuro ?? GeoidColors.oscuro;
  final base = esOscuro ? ThemeData.dark(useMaterial3: true) : ThemeData.light(useMaterial3: true);

  return base.copyWith(
    scaffoldBackgroundColor: GeoidColors.fondo,
    colorScheme: base.colorScheme.copyWith(
      primary: GeoidColors.acento,
      onPrimary: esOscuro ? GeoidColors.fondo : Colors.white,
      secondary: GeoidColors.acento,
      surface: GeoidColors.panel,
      onSurface: GeoidColors.texto,
      brightness: esOscuro ? Brightness.dark : Brightness.light,
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: GeoidColors.panel,
      titleTextStyle: TextStyle(color: GeoidColors.texto, fontSize: 19),
      contentTextStyle: TextStyle(color: GeoidColors.textoSuave, fontSize: 14),
    ),
    textSelectionTheme: TextSelectionThemeData(
      cursorColor: GeoidColors.acento,
      selectionColor: GeoidColors.acento.withValues(alpha: 0.35),
      selectionHandleColor: GeoidColors.acento,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: GeoidColors.panel,
      hintStyle: TextStyle(color: GeoidColors.textoTenue, fontSize: 14),
      contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(23),
        borderSide: BorderSide(color: GeoidColors.borde),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(23),
        borderSide: BorderSide(color: GeoidColors.borde),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(23),
        borderSide: BorderSide(color: GeoidColors.acento),
      ),
    ),
  );
}
