import 'package:flutter/material.dart';

import '../i18n.dart';
import '../services/nativo.dart';
import '../theme.dart';

/// Seleccion de aplicaciones que pasan por el tunel.
///
/// Si no hay ninguna marcada, pasan todas. Se muestran todas las aplicaciones,
/// incluidas las del sistema.
class AppsScreen extends StatefulWidget {
  AppsScreen({super.key});

  @override
  State<AppsScreen> createState() => _AppsScreenState();
}

class _AppsScreenState extends State<AppsScreen> {
  List<AppInstalada> _todas = [];
  Set<String> _marcadas = {};
  bool _cargando = true;
  String _filtro = '';

  /// false = aplicaciones instaladas · true = del sistema
  bool _verSistema = false;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    final guardado = await Nativo.leer('apps', 'seleccion') ?? '';
    final apps = await Nativo.aplicaciones();
    if (!mounted) return;
    setState(() {
      _todas = apps;
      _marcadas = guardado
          .split(',')
          .map((e) => e.trim())
          .where((e) => e.isNotEmpty)
          .toSet();
      _cargando = false;
    });
  }

  Future<void> _guardar() async {
    await Nativo.guardar('apps', 'seleccion', _marcadas.join(','));
  }

  List<AppInstalada> get _visibles {
    final texto = _filtro.toLowerCase();
    final lista = _todas.where((a) {
      if (a.sistema != _verSistema) return false;
      if (texto.isEmpty) return true;
      return a.nombre.toLowerCase().contains(texto) ||
          a.paquete.toLowerCase().contains(texto);
    }).toList();

    // Las marcadas primero.
    lista.sort((a, b) {
      final ma = _marcadas.contains(a.paquete);
      final mb = _marcadas.contains(b.paquete);
      if (ma != mb) return ma ? -1 : 1;
      return a.nombre.toLowerCase().compareTo(b.nombre.toLowerCase());
    });
    return lista;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GeoidColors.fondo,
      appBar: AppBar(
        backgroundColor: GeoidColors.fondo,
        foregroundColor: GeoidColors.acento,
        elevation: 0,
        title: Text(
          t('apps_sin_vpn'),
          style: TextStyle(fontSize: 16, letterSpacing: 1.2),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: EdgeInsets.fromLTRB(20, 6, 20, 10),
              child: TextField(
                style: TextStyle(color: GeoidColors.texto, fontSize: 14),
                decoration: InputDecoration(
                  hintText: t('buscar_apps'),
                  prefixIcon: Icon(Icons.search,
                      size: 18, color: GeoidColors.textoTenue),
                ),
                onChanged: (v) => setState(() => _filtro = v),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 10),
              child: Row(
                children: [
                  Expanded(
                    child: _grupo(
                      texto: t('apps_externas'),
                      cuantas: _todas.where((a) => !a.sistema).length,
                      color: GeoidColors.acento,
                      activo: !_verSistema,
                      alPulsar: () => setState(() => _verSistema = false),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: _grupo(
                      texto: t('apps_sistema'),
                      cuantas: _todas.where((a) => a.sistema).length,
                      color: const Color(0xFF5BA8FF),
                      activo: _verSistema,
                      alPulsar: () => setState(() => _verSistema = true),
                    ),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 8),
              child: Text(
                t('apps_sin_vpn_detalle'),
                style: TextStyle(
                  color: GeoidColors.textoTenue,
                  fontSize: 11,
                  height: 1.3,
                ),
              ),
            ),
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 20),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      _marcadas.isEmpty
                          ? t('ninguna_excluida')
                          : (_marcadas.length == 1
                              ? t('excluidas_1')
                              : t('excluidas_n')
                                  .replaceFirst('%s', '${_marcadas.length}')),
                      style: TextStyle(
                        color: GeoidColors.textoSuave,
                        fontSize: 12,
                      ),
                    ),
                  ),
                  TextButton(
                    onPressed: () {
                      setState(() {
                        if (_marcadas.isEmpty) {
                          _marcadas = _todas.map((a) => a.paquete).toSet();
                        } else {
                          _marcadas = {};
                        }
                      });
                      _guardar();
                    },
                    child: Text(
                      t('marcar_todas'),
                      style: TextStyle(
                        color: GeoidColors.acento,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            Expanded(
              child: _cargando
                  ? Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          CircularProgressIndicator(color: GeoidColors.acento),
                          SizedBox(height: 14),
                          Text(
                            'Cargando aplicaciones…',
                            style: TextStyle(
                              color: GeoidColors.textoSuave,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    )
                  : _visibles.isEmpty
                      ? Center(
                          child: Text(
                            t('sin_apps'),
                            style: TextStyle(
                              color: GeoidColors.textoSuave,
                              fontSize: 13,
                            ),
                          ),
                        )
                      : ListView.builder(
                          itemCount: _visibles.length,
                          itemBuilder: (contexto, i) {
                            final app = _visibles[i];
                            final marcada = _marcadas.contains(app.paquete);
                            return ListTile(
                              dense: true,
                              leading: CircleAvatar(
                                radius: 15,
                                backgroundColor: marcada
                                    ? GeoidColors.borde
                                    : GeoidColors.panel,
                                child: Text(
                                  app.inicial,
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: marcada
                                        ? GeoidColors.acento
                                        : GeoidColors.textoSuave,
                                  ),
                                ),
                              ),
                              title: Text(
                                app.nombre,
                                style: TextStyle(
                                  fontSize: 13,
                                  color: marcada
                                      ? GeoidColors.texto
                                      : GeoidColors.textoSuave,
                                ),
                              ),
                              subtitle: Text(
                                app.paquete,
                                style: TextStyle(
                                  fontSize: 10,
                                  color: GeoidColors.textoTenue,
                                ),
                              ),
                              trailing: SwitchTheme(
                                data: SwitchThemeData(
                                  thumbColor: WidgetStateProperty.resolveWith(
                                    (estados) =>
                                        estados.contains(WidgetState.selected)
                                            ? GeoidColors.acento
                                            : GeoidColors.textoTenue,
                                  ),
                                  trackColor: WidgetStateProperty.resolveWith(
                                    (estados) =>
                                        estados.contains(WidgetState.selected)
                                            ? GeoidColors.borde
                                            : GeoidColors.botonApagado,
                                  ),
                                ),
                                child: Switch(
                                  value: marcada,
                                  onChanged: (v) {
                                    setState(() {
                                      if (v) {
                                        _marcadas.add(app.paquete);
                                      } else {
                                        _marcadas.remove(app.paquete);
                                      }
                                    });
                                    _guardar();
                                  },
                                ),
                              ),
                            );
                          },
                        ),
            ),
          ],
        ),
      ),
    );
  }

  /// Casilla de grupo: externas o del sistema.
  Widget _grupo({
    required String texto,
    required int cuantas,
    required Color color,
    required bool activo,
    required VoidCallback alPulsar,
  }) {
    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: alPulsar,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 10),
        decoration: BoxDecoration(
          color: activo ? color.withValues(alpha: 0.18) : Colors.transparent,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: activo ? color : GeoidColors.borde,
            width: activo ? 1.4 : 1,
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              activo ? Icons.check_box : Icons.check_box_outline_blank,
              size: 16,
              color: activo ? color : GeoidColors.textoTenue,
            ),
            const SizedBox(width: 6),
            Flexible(
              child: Text(
                '$texto ($cuantas)',
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: activo ? color : GeoidColors.textoSuave,
                  fontSize: 12,
                  fontWeight: activo ? FontWeight.w600 : FontWeight.w400,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
