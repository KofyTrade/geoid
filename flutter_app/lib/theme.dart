import 'package:flutter/material.dart';

/// Paleta de GeoiD-vpn: verde azulado oscuro con acentos turquesa.
class GeoidColors {
  static const fondo = Color(0xFF05161A);
  static const panel = Color(0xFF0B2429);
  static const acento = Color(0xFF2EE6C5);
  static const texto = Color(0xFFE8FBF7);
  static const textoSuave = Color(0xFF7FA8A4);
  static const textoTenue = Color(0xFF4E7C79);
  static const borde = Color(0xFF1E5A58);
  static const botonApagado = Color(0xFF13333A);
  static const linea = Color(0xFF0E2A2E);
}

ThemeData temaGeoid() {
  final base = ThemeData.dark(useMaterial3: true);
  return base.copyWith(
    scaffoldBackgroundColor: GeoidColors.fondo,
    colorScheme: base.colorScheme.copyWith(
      primary: GeoidColors.acento,
      onPrimary: GeoidColors.fondo,
      secondary: GeoidColors.acento,
      surface: GeoidColors.panel,
      onSurface: GeoidColors.texto,
    ),
    dialogTheme: const DialogThemeData(
      backgroundColor: GeoidColors.panel,
      titleTextStyle: TextStyle(color: GeoidColors.texto, fontSize: 19),
      contentTextStyle: TextStyle(color: GeoidColors.textoSuave, fontSize: 14),
    ),
    textSelectionTheme: const TextSelectionThemeData(
      cursorColor: GeoidColors.acento,
      selectionColor: Color(0x552EE6C5),
      selectionHandleColor: GeoidColors.acento,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: GeoidColors.panel,
      hintStyle: const TextStyle(color: GeoidColors.textoTenue, fontSize: 14),
      contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(23),
        borderSide: const BorderSide(color: GeoidColors.borde),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(23),
        borderSide: const BorderSide(color: GeoidColors.borde),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(23),
        borderSide: const BorderSide(color: GeoidColors.acento),
      ),
    ),
  );
}
