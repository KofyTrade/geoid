import 'package:flutter/material.dart';

import '../i18n.dart';
import '../services/nativo.dart';
import '../theme.dart';

/// Pantalla "Activar VPN": prueba gratis y compra, ambas en el bot de Telegram.
class SuscripcionScreen extends StatelessWidget {
  const SuscripcionScreen({super.key});

  static const String _bot = 'https://t.me/geoidvpnbot';

  Future<void> _irAlBot(BuildContext contexto, String motivo) async {
    await Nativo.abrirEnlace('$_bot?start=$motivo');
    if (!contexto.mounted) return;
    ScaffoldMessenger.of(contexto).showSnackBar(
      SnackBar(
        content: Text(t('abriendo_telegram')),
        backgroundColor: GeoidColors.panel,
        behavior: SnackBarBehavior.floating,
      ),
    );
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
          t('activar_vpn'),
          style: const TextStyle(fontSize: 16, letterSpacing: 1.2),
        ),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 20),
          children: [
            Text(
              t('activar_vpn_texto'),
              style: TextStyle(
                color: GeoidColors.textoSuave,
                fontSize: 13,
                height: 1.35,
              ),
            ),
            const SizedBox(height: 20),

            // Prueba gratuita
            _tarjeta(
              titulo: t('periodo_prueba'),
              subtitulo: t('tres_dias'),
              detalle: t('prueba_detalle'),
              icono: Icons.card_giftcard,
              destacada: true,
              alPulsar: () => _irAlBot(context, 'trial'),
            ),
            const SizedBox(height: 12),

            // Comprar
            _tarjeta(
              titulo: t('comprar_vpn'),
              subtitulo: t('planes_desde'),
              detalle: t('compra_detalle'),
              icono: Icons.workspace_premium,
              alPulsar: () => _irAlBot(context, 'buy'),
            ),
            const SizedBox(height: 12),

            // Mi acceso
            _tarjeta(
              titulo: t('mi_vpn'),
              subtitulo: t('mi_vpn_detalle'),
              icono: Icons.key,
              alPulsar: () => _irAlBot(context, 'my'),
            ),

            const SizedBox(height: 22),
            Row(
              children: [
                Icon(Icons.telegram, size: 16, color: GeoidColors.textoTenue),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '@geoidvpnbot',
                    style: TextStyle(
                      color: GeoidColors.textoTenue,
                      fontSize: 12,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _tarjeta({
    required String titulo,
    required String subtitulo,
    String? detalle,
    required IconData icono,
    bool destacada = false,
    required VoidCallback alPulsar,
  }) {
    return Material(
      color: destacada ? GeoidColors.panel : GeoidColors.botonApagado,
      borderRadius: BorderRadius.circular(18),
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: alPulsar,
        child: Container(
          padding: const EdgeInsets.fromLTRB(16, 14, 12, 14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18),
            border: Border.all(
              color: destacada ? GeoidColors.acento : GeoidColors.borde,
            ),
          ),
          child: Row(
            children: [
              Icon(icono,
                  size: 22,
                  color: destacada
                      ? GeoidColors.acento
                      : GeoidColors.textoSuave),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      titulo,
                      style: TextStyle(
                        color: destacada
                            ? GeoidColors.acento
                            : GeoidColors.texto,
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      subtitulo,
                      style: TextStyle(
                        color: GeoidColors.textoSuave,
                        fontSize: 12,
                      ),
                    ),
                    if (detalle != null) ...[
                      const SizedBox(height: 3),
                      Text(
                        detalle,
                        style: TextStyle(
                          color: GeoidColors.textoTenue,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              const Icon(Icons.chevron_right,
                  size: 20, color: GeoidColors.textoTenue),
            ],
          ),
        ),
      ),
    );
  }
}
