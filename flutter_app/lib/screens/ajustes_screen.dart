import 'dart:io';

import 'package:flutter/material.dart';

import '../i18n.dart';
import '../services/ajustes.dart';
import '../services/nativo.dart';
import '../theme.dart';

/// Ajustes de la app: idioma, tema y "Acerca de".
class AjustesScreen extends StatefulWidget {
  AjustesScreen({super.key});

  @override
  State<AjustesScreen> createState() => _AjustesScreenState();
}

class _AjustesScreenState extends State<AjustesScreen> {
  String _version = '';

  static const String _sistema = '__sistema__';

  static const Map<String, String> _nombres = {
    'es': 'Español',
    'en': 'English',
    'ru': 'Русский',
    'fr': 'Français',
    'de': 'Deutsch',
    'it': 'Italiano',
    'ja': '日本語',
    'ko': '한국어',
  };

  @override
  void initState() {
    super.initState();
    Nativo.version().then((v) {
      if (mounted) setState(() => _version = v);
    });
  }

  @override
  Widget build(BuildContext context) {
    final esEscritorio = Platform.isWindows || Platform.isMacOS || Platform.isLinux;

    return Scaffold(
      backgroundColor: GeoidColors.fondo,
      appBar: AppBar(
        backgroundColor: GeoidColors.fondo,
        foregroundColor: GeoidColors.acento,
        elevation: 0,
        title: Text(
          t('configuracion'),
          style: TextStyle(fontSize: 16, letterSpacing: 1.2),
        ),
      ),
      body: ListView(
        padding: EdgeInsets.symmetric(horizontal: 20, vertical: 8),
        children: [
          _fila(
            icono: Icons.translate,
            titulo: t('idioma'),
            valor: _nombreIdioma(I18n.idioma),
            alPulsar: _elegirIdioma,
          ),
          _fila(
            icono: Ajustes.oscuro.value ? Icons.dark_mode : Icons.light_mode,
            titulo: t('tema'),
            valor: Ajustes.oscuro.value ? t('tema_oscuro') : t('tema_claro'),
            alPulsar: _elegirTema,
          ),
          _fila(
            icono: Icons.info_outline,
            titulo: t('acerca_de'),
            valor: _version.isEmpty ? 'GeoiD-vpn' : 'GeoiD-vpn v$_version',
            alPulsar: _acercaDe,
          ),
          if (esEscritorio)
            _fila(
              icono: Icons.close,
              titulo: t('cerrar_app'),
              alPulsar: () => exit(0),
            ),
          SizedBox(height: 18),
          Row(
            children: [
              Icon(Icons.telegram, size: 15, color: GeoidColors.textoTenue),
              SizedBox(width: 8),
              Text(
                '@geoidvpn_bot',
                style: TextStyle(color: GeoidColors.textoTenue, fontSize: 12),
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _nombreIdioma(String codigo) {
    return _nombres[codigo] ?? codigo.toUpperCase();
  }

  Future<void> _elegirIdioma() async {
    final elegido = await showModalBottomSheet<String>(
      context: context,
      backgroundColor: GeoidColors.panel,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(22)),
      ),
      builder: (hoja) {
        return SafeArea(
          child: ListView(
            shrinkWrap: true,
            children: [
              _tituloHoja(t('idioma')),
              _opcion(
                hoja,
                valor: _sistema,
                texto: t('idioma_sistema'),
                activo: Ajustes.idioma == null,
              ),
              for (final codigo in I18n.soportados)
                _opcion(
                  hoja,
                  valor: codigo,
                  texto: _nombres[codigo] ?? codigo,
                  activo: Ajustes.idioma == codigo,
                ),
              SizedBox(height: 10),
            ],
          ),
        );
      },
    );

    if (elegido == null) return;
    await Ajustes.ponerIdioma(elegido == _sistema ? null : elegido);
    if (mounted) setState(() {});
  }

  Future<void> _elegirTema() async {
    final elegido = await showModalBottomSheet<String>(
      context: context,
      backgroundColor: GeoidColors.panel,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(22)),
      ),
      builder: (hoja) {
        return SafeArea(
          child: ListView(
            shrinkWrap: true,
            children: [
              _tituloHoja(t('tema')),
              _opcion(
                hoja,
                valor: 'oscuro',
                texto: t('tema_oscuro'),
                activo: Ajustes.oscuro.value,
              ),
              _opcion(
                hoja,
                valor: 'claro',
                texto: t('tema_claro'),
                activo: !Ajustes.oscuro.value,
              ),
              SizedBox(height: 10),
            ],
          ),
        );
      },
    );

    if (elegido == null) return;
    await Ajustes.ponerOscuro(elegido == 'oscuro');
    if (mounted) setState(() {});
  }

  Widget _tituloHoja(String texto) {
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 20, 20, 8),
      child: Text(
        texto,
        style: TextStyle(
          color: GeoidColors.texto,
          fontSize: 15,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  Widget _opcion(
    BuildContext hoja, {
    required String valor,
    required String texto,
    required bool activo,
  }) {
    return ListTile(
      onTap: () => Navigator.of(hoja).pop(valor),
      title: Text(
        texto,
        style: TextStyle(
          color: activo ? GeoidColors.acento : GeoidColors.texto,
          fontSize: 14,
        ),
      ),
      trailing:
          activo ? Icon(Icons.check, color: GeoidColors.acento, size: 18) : null,
    );
  }

  void _acercaDe() {
    showDialog<void>(
      context: context,
      builder: (dialogo) => AlertDialog(
        backgroundColor: GeoidColors.panel,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(22),
          side: BorderSide(color: GeoidColors.borde),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 74,
              height: 74,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: GeoidColors.botonApagado,
                border: Border.all(color: GeoidColors.acento, width: 1.4),
              ),
              child: Icon(Icons.hub, color: GeoidColors.acento, size: 36),
            ),
            SizedBox(height: 14),
            Text(
              'GeoiD-vpn',
              style: TextStyle(
                color: GeoidColors.marca,
                fontSize: 18,
                letterSpacing: 1.6,
              ),
            ),
            SizedBox(height: 4),
            Text(
              _version.isEmpty ? '' : 'v$_version',
              style: TextStyle(color: GeoidColors.textoTenue, fontSize: 12),
            ),
            SizedBox(height: 16),
            Text(
              t('acerca_texto'),
              textAlign: TextAlign.center,
              style: TextStyle(
                color: GeoidColors.textoSuave,
                fontSize: 12,
                height: 1.35,
              ),
            ),
            SizedBox(height: 14),
            Text(
              '@geoidvpn_bot',
              style: TextStyle(color: GeoidColors.marca, fontSize: 12),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogo).pop(),
            child: Text(
              t('cerrar'),
              style: TextStyle(color: GeoidColors.acento),
            ),
          ),
        ],
      ),
    );
  }

  Widget _fila({
    required IconData icono,
    required String titulo,
    String? valor,
    VoidCallback? alPulsar,
  }) {
    return InkWell(
      onTap: alPulsar,
      child: Container(
        padding: EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          border: Border(bottom: BorderSide(color: GeoidColors.linea)),
        ),
        child: Row(
          children: [
            Icon(icono, size: 20, color: GeoidColors.textoSuave),
            SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    titulo,
                    style: TextStyle(color: GeoidColors.texto, fontSize: 14),
                  ),
                  if (valor != null && valor.isNotEmpty) ...[
                    SizedBox(height: 2),
                    Text(
                      valor,
                      style: TextStyle(
                        color: GeoidColors.textoSuave,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            Icon(Icons.chevron_right,
                size: 20, color: GeoidColors.textoTenue),
          ],
        ),
      ),
    );
  }
}
