import 'package:flutter/material.dart';

import 'i18n.dart';
import 'screens/home_screen.dart';
import 'services/ajustes.dart';
import 'services/bandeja.dart';
import 'theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  I18n.iniciar();
  // Idioma y tema guardados por el usuario.
  await Ajustes.cargar();
  // En Windows: minimizar y cerrar llevan la app a la bandeja del sistema.
  Bandeja.iniciar();
  runApp(GeoidApp());
}

class GeoidApp extends StatelessWidget {
  GeoidApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: I18n.aviso,
      builder: (contexto, idioma, _) {
        return ValueListenableBuilder<bool>(
          valueListenable: Ajustes.oscuro,
          builder: (contexto, esOscuro, _) {
            return MaterialApp(
              title: 'GeoiD-vpn',
              debugShowCheckedModeBanner: false,
              theme: temaGeoid(oscuro: esOscuro),
              home: HomeScreen(),
            );
          },
        );
      },
    );
  }
}
