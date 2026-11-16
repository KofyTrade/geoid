import 'package:flutter/material.dart';

import '../i18n.dart';
import '../services/nativo.dart';
import '../services/registro.dart';
import '../theme.dart';

/// Registro de eventos de la sesion.
class LogScreen extends StatelessWidget {
  LogScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GeoidColors.fondo,
      appBar: AppBar(
        backgroundColor: GeoidColors.fondo,
        foregroundColor: GeoidColors.acento,
        elevation: 0,
        title: Text(
          t('registro'),
          style: TextStyle(fontSize: 16, letterSpacing: 1.2),
        ),
        actions: [
          Center(
            child: FutureBuilder<String>(
              future: Nativo.version(),
              builder: (contexto, instantanea) => Padding(
                padding: EdgeInsets.only(right: 6),
                child: Text(
                  'v${instantanea.data ?? ''}',
                  style: TextStyle(
                    color: GeoidColors.textoTenue,
                    fontSize: 11,
                  ),
                ),
              ),
            ),
          ),
          IconButton(
            tooltip: t('limpiar'),
            onPressed: Registro.limpiar,
            icon: Icon(Icons.delete_outline, size: 20),
          ),
        ],
      ),
      body: SafeArea(
        child: ValueListenableBuilder<List<String>>(
          valueListenable: Registro.lineas,
          builder: (contexto, lineas, _) {
            if (lineas.isEmpty) {
              return Center(
                child: Text(
                  t('registro_vacio'),
                  style: TextStyle(
                    color: GeoidColors.textoSuave,
                    fontSize: 13,
                  ),
                ),
              );
            }
            return ListView.builder(
              padding: EdgeInsets.all(16),
              itemCount: lineas.length,
              itemBuilder: (contexto, i) => Padding(
                padding: EdgeInsets.only(bottom: 6),
                child: Text(
                  lineas[i],
                  style: TextStyle(
                    color: GeoidColors.textoSuave,
                    fontSize: 11,
                    fontFamily: 'monospace',
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
