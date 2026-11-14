import 'dart:convert';
import 'dart:io';

import 'nativo.dart';

/// Una version publicada en GitHub.
class NuevaVersion {
  final String numero;
  final String urlApk;

  const NuevaVersion(this.numero, this.urlApk);
}

/// Comprueba las Releases del repositorio y descarga el APK nuevo.
class Actualizador {
  static const String repo = 'KofyTrade/geoid';
  static const String _api = 'https://api.github.com/repos/$repo/releases/latest';

  static Future<String> versionInstalada() => Nativo.version();

  static Future<NuevaVersion?> buscar() async {
    final cliente = HttpClient()..connectionTimeout = const Duration(seconds: 6);
    try {
      final peticion = await cliente.getUrl(Uri.parse(_api));
      peticion.headers.set('Accept', 'application/vnd.github+json');
      final respuesta = await peticion.close().timeout(const Duration(seconds: 10));
      if (respuesta.statusCode != 200) return null;

      final texto = await respuesta.transform(utf8.decoder).join();
      final json = jsonDecode(texto) as Map<String, dynamic>;

      final etiqueta = (json['tag_name'] as String? ?? '')
          .trim()
          .replaceFirst(RegExp('^[vV]'), '');
      if (etiqueta.isEmpty) return null;

      final activos = (json['assets'] as List<dynamic>?) ?? [];
      for (final activo in activos) {
        final mapa = activo as Map<String, dynamic>;
        final nombre = (mapa['name'] as String? ?? '');
        if (nombre.toLowerCase().endsWith('.apk')) {
          final url = mapa['browser_download_url'] as String? ?? '';
          if (url.isNotEmpty) return NuevaVersion(etiqueta, url);
        }
      }
      return null;
    } catch (_) {
      return null;
    } finally {
      cliente.close(force: true);
    }
  }

  static bool masNueva(String remota, String actual) {
    List<int> numeros(String v) => v
        .split('.')
        .map((p) => int.tryParse(p.trim()) ?? 0)
        .toList();

    final r = numeros(remota);
    final a = numeros(actual);
    if (r.isEmpty) return false;
    final largo = r.length > a.length ? r.length : a.length;
    for (var i = 0; i < largo; i++) {
      final x = i < r.length ? r[i] : 0;
      final y = i < a.length ? a[i] : 0;
      if (x > y) return true;
      if (x < y) return false;
    }
    return false;
  }

  static Future<void> descargar(NuevaVersion version) {
    return Nativo.descargar(version.urlApk, 'GeoiD-vpn-${version.numero}.apk');
  }
}
