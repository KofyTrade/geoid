import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:tray_manager/legacy.dart';
import 'package:window_manager/legacy.dart';

/// Bandeja del sistema en Windows: minimizar y cerrar ocultan la ventana en
/// lugar de terminar la app. El tunel sigue funcionando mientras esta oculta.
class Bandeja with TrayListener, WindowListener {
  static final Bandeja _yo = Bandeja._();

  Bandeja._();

  bool _listo = false;

  static Future<void> iniciar() async {
    if (!Platform.isWindows) return;
    await _yo._preparar();
  }

  Future<void> _preparar() async {
    if (_listo) return;
    try {
      // Primero la bandeja: si fallara, cerrar la ventana debe seguir cerrando.
      await windowManager.ensureInitialized();

      await trayManager.setIcon(await _copiarIcono());
      await trayManager.setToolTip('GeoiD-vpn');
      await trayManager.setContextMenu(
        Menu(
          items: [
            MenuItem(key: 'mostrar', label: 'Mostrar GeoiD-vpn'),
            MenuItem.separator(),
            MenuItem(key: 'salir', label: 'Salir'),
          ],
        ),
      );
      trayManager.addListener(this);

      await windowManager.setPreventClose(true);
      windowManager.addListener(this);
      _listo = true;
    } catch (e) {
      debugPrint('bandeja: $e');
    }
  }

  /// El icono tiene que estar en disco para la bandeja.
  Future<String> _copiarIcono() async {
    final base = Platform.environment['APPDATA'] ?? Directory.systemTemp.path;
    final carpeta = Directory('$base${Platform.pathSeparator}GeoiD-vpn');
    if (!carpeta.existsSync()) carpeta.createSync(recursive: true);
    final destino =
        File('${carpeta.path}${Platform.pathSeparator}icono.ico');

    final datos = await rootBundle.load('assets/icono.ico');
    final bytes = datos.buffer.asUint8List(datos.offsetInBytes, datos.lengthInBytes);
    if (!destino.existsSync() || destino.lengthSync() != bytes.length) {
      await destino.writeAsBytes(bytes, flush: true);
    }
    return destino.path;
  }

  Future<void> _mostrar() async {
    try {
      await windowManager.restore();
    } catch (_) {
      // la ventana podria no estar minimizada
    }
    await windowManager.show();
    await windowManager.focus();
  }

  // ---- ventana ----

  @override
  void onWindowClose() {
    windowManager.hide();
  }

  @override
  void onWindowMinimize() {
    // Se espera a que Windows termine la animacion y luego se oculta.
    Future.delayed(Duration(milliseconds: 120), () {
      windowManager.hide();
    });
  }

  // ---- bandeja ----

  @override
  void onTrayIconMouseDown() {
    _mostrar();
  }

  @override
  void onTrayIconRightMouseDown() {
    trayManager.popUpContextMenu();
  }

  @override
  void onTrayMenuItemClick(MenuItem menuItem) {
    switch (menuItem.key) {
      case 'mostrar':
        _mostrar();
        break;
      case 'salir':
        _salir();
        break;
    }
  }

  Future<void> _salir() async {
    await windowManager.setPreventClose(false);
    await windowManager.destroy();
  }
}
