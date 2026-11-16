import 'dart:async';
import 'dart:convert';
import 'dart:io';

/// Tunel de Windows: lanza `geoid-tun.exe` (AmneziaWG + Wintun) y escucha lo
/// que escribe en la salida estandar.
///
/// LISTO            -> conectado
/// STATS rx tx      -> contadores
/// ERROR <texto>    -> fallo
class TunWindows {
  static Process? _proceso;
  static StreamSubscription<String>? _lineas;
  static final StreamController<Map<String, dynamic>> _avisos =
      StreamController<Map<String, dynamic>>.broadcast();

  static int rxBytes = 0;
  static int txBytes = 0;

  static Stream<Map<String, dynamic>> get avisos => _avisos.stream;

  static Directory get _carpetaExe =>
      File(Platform.resolvedExecutable).parent;

  static String get _rutaAyudante =>
      '${_carpetaExe.path}${Platform.pathSeparator}geoid-tun.exe';

  static bool get disponible => File(_rutaAyudante).existsSync();

  static Future<void> conectar(String conf, int mtu) async {
    await desconectar();

    if (!disponible) {
      _avisos.add({
        'activo': false,
        'error': 'falta geoid-tun.exe junto a la aplicación',
      });
      return;
    }

    final carpeta = await Directory.systemTemp.createTemp('geoid');
    final archivo = File('${carpeta.path}${Platform.pathSeparator}geoid.conf');
    await archivo.writeAsString(conf);

    try {
      final proceso = await Process.start(
        _rutaAyudante,
        [archivo.path, '$mtu'],
        workingDirectory: _carpetaExe.path,
        runInShell: false,
      );
      _proceso = proceso;
      rxBytes = 0;
      txBytes = 0;

      _lineas = proceso.stdout
          .transform(utf8.decoder)
          .transform(LineSplitter())
          .listen(_procesarLinea);

      proceso.stderr
          .transform(utf8.decoder)
          .transform(LineSplitter())
          .listen((linea) {
        if (linea.trim().isNotEmpty) {
          // Solo informativo; el detalle queda en geoid-tun.log
        }
      });

      proceso.exitCode.then((codigo) {
        if (_proceso == proceso) {
          _proceso = null;
          _avisos.add({
            'activo': false,
            'error': codigo == 0 ? null : 'el motor terminó con código $codigo',
          });
        }
      });
    } catch (e) {
      _avisos.add({'activo': false, 'error': '$e'});
    }
  }

  static void _procesarLinea(String linea) {
    final texto = linea.trim();
    if (texto == 'LISTO') {
      _avisos.add({'activo': true, 'error': null});
      return;
    }
    if (texto.startsWith('ERROR')) {
      _avisos.add({'activo': false, 'error': texto});
      return;
    }
    if (texto.startsWith('STATS')) {
      final partes = texto.split(' ');
      if (partes.length >= 3) {
        rxBytes = int.tryParse(partes[1]) ?? rxBytes;
        txBytes = int.tryParse(partes[2]) ?? txBytes;
      }
    }
  }

  static Future<void> desconectar() async {
    final proceso = _proceso;
    _proceso = null;
    await _lineas?.cancel();
    _lineas = null;
    if (proceso == null) return;
    try {
      await proceso.stdin.close();
    } catch (_) {}
    try {
      await proceso.exitCode.timeout(Duration(seconds: 4));
    } catch (_) {
      proceso.kill();
    }
    _avisos.add({'activo': false, 'error': null});
  }
}
