import 'package:flutter/material.dart';

import '../theme.dart';
import '../widgets/polyhedron.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _conectado = false;
  bool _bloquearAnuncios = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GeoidColors.fondo,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 22, 24, 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Cabecera
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _marca('GEOID-VPN'),
                      const SizedBox(height: 12),
                      Text(
                        _conectado ? 'CONNECTED' : 'DISCONNECTED',
                        style: TextStyle(
                          color: _conectado
                              ? GeoidColors.acento
                              : GeoidColors.textoSuave,
                          fontSize: 13,
                          letterSpacing: 2.6,
                          fontWeight: FontWeight.w300,
                        ),
                      ),
                    ],
                  ),
                  const Spacer(),
                  if (_conectado) _panelDatos(),
                ],
              ),

              // Poliedro
              Expanded(child: Polyhedron(conectado: _conectado)),

              // Boton principal
              _botonPrincipal(),
              const SizedBox(height: 12),

              // Aplicaciones / Registro
              Row(
                children: [
                  Expanded(
                    child: _botonSecundario('Apps', () {}),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _botonSecundario('Log', () {}),
                  ),
                ],
              ),
              const SizedBox(height: 14),

              Text(
                'All apps',
                style: TextStyle(color: GeoidColors.textoSuave, fontSize: 12),
              ),
              const SizedBox(height: 6),

              // Bloquear anuncios
              Row(
                children: [
                  Expanded(
                    child: Text(
                      'Block ads',
                      style: const TextStyle(
                        color: GeoidColors.texto,
                        fontSize: 13,
                      ),
                    ),
                  ),
                  SwitchTheme(
                    data: SwitchThemeData(
                      thumbColor: WidgetStateProperty.resolveWith(
                        (estados) => estados.contains(WidgetState.selected)
                            ? GeoidColors.acento
                            : GeoidColors.textoTenue,
                      ),
                      trackColor: WidgetStateProperty.resolveWith(
                        (estados) => estados.contains(WidgetState.selected)
                            ? GeoidColors.borde
                            : GeoidColors.botonApagado,
                      ),
                    ),
                    child: Switch(
                      value: _bloquearAnuncios,
                      onChanged: (v) => setState(() => _bloquearAnuncios = v),
                    ),
                  ),
                ],
              ),

              // Perfiles
              TextButton(
                onPressed: () {},
                child: Text(
                  'Profiles: Mi servidor',
                  style: TextStyle(color: GeoidColors.acento, fontSize: 12),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _marca(String texto) {
    return Text(
      texto,
      style: const TextStyle(
        color: Color(0xFF5FD9C8),
        fontSize: 12,
        letterSpacing: 3.6,
        fontWeight: FontWeight.w300,
      ),
    );
  }

  Widget _panelDatos() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        const Text(
          '0 KB/s',
          style: TextStyle(
            color: GeoidColors.acento,
            fontSize: 13,
            fontFamily: 'monospace',
          ),
        ),
        const SizedBox(height: 2),
        Text(
          '-- ms',
          style: TextStyle(color: GeoidColors.textoSuave, fontSize: 11),
        ),
        const SizedBox(height: 2),
        Text(
          'Finland',
          style: TextStyle(color: GeoidColors.textoTenue, fontSize: 10),
        ),
      ],
    );
  }

  Widget _botonPrincipal() {
    return SizedBox(
      height: 60,
      child: FilledButton(
        onPressed: () => setState(() => _conectado = !_conectado),
        style: FilledButton.styleFrom(
          backgroundColor: _conectado
              ? GeoidColors.botonApagado
              : GeoidColors.acento,
          foregroundColor: _conectado
              ? GeoidColors.acento
              : GeoidColors.fondo,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(30),
          ),
        ),
        child: Text(
          _conectado ? 'Disconnect' : 'Connect',
          style: const TextStyle(fontSize: 16),
        ),
      ),
    );
  }

  Widget _botonSecundario(String texto, VoidCallback alPulsar) {
    return SizedBox(
      height: 48,
      child: OutlinedButton(
        onPressed: alPulsar,
        style: OutlinedButton.styleFrom(
          foregroundColor: const Color(0xFF9BE8DC),
          side: const BorderSide(color: GeoidColors.borde),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24),
          ),
        ),
        child: Text(texto, style: const TextStyle(fontSize: 13)),
      ),
    );
  }
}
