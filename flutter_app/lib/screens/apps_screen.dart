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
          t('apps'),
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
              padding: EdgeInsets.symmetric(horizontal: 20),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      _marcadas.isEmpty
                          ? t('sin_seleccion')
                          : (_marcadas.length == 1
                              ? t('apps_1')
                              : t('apps_n')
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
                      t('seleccionar_todas'),
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
}
