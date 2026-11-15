import 'package:flutter/material.dart';

import 'i18n.dart';
import 'screens/home_screen.dart';
import 'services/bandeja.dart';
import 'theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  I18n.iniciar();
  // En Windows: minimizar y cerrar llevan la app a la bandeja del sistema.
  Bandeja.iniciar();
  runApp(const GeoidApp());
}

class GeoidApp extends StatelessWidget {
  const GeoidApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: I18n.aviso,
      builder: (contexto, idioma, _) {
        return MaterialApp(
          title: 'GeoiD-vpn',
          debugShowCheckedModeBanner: false,
          theme: temaGeoid(),
          home: const HomeScreen(),
        );
      },
    );
  }
}
