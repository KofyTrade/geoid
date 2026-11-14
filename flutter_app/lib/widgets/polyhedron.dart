import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';

import '../theme.dart';

/// Poliedro facetado (icosaedro) con esfera de nodos, igual que en la app Kotlin.
///
/// Apagado gira muy despacio; conectado da una vuelta cada 7 segundos.
class Polyhedron extends StatefulWidget {
  final bool conectado;

  const Polyhedron({super.key, required this.conectado});

  @override
  State<Polyhedron> createState() => _PolyhedronState();
}

class _PolyhedronState extends State<Polyhedron>
    with SingleTickerProviderStateMixin {
  late final Ticker _ticker;
  double _angulo = 0;
  Duration _ultimo = Duration.zero;

  @override
  void initState() {
    super.initState();
    _ticker = createTicker(_alLatir)..start();
  }

  void _alLatir(Duration tiempo) {
    final dt = _ultimo == Duration.zero
        ? 0.0
        : (tiempo - _ultimo).inMicroseconds / 1000000.0;
    _ultimo = tiempo;

    final velocidad = widget.conectado ? 360.0 / 7.0 : 6.0;
    setState(() {
      _angulo = (_angulo + velocidad * dt) % 360.0;
    });
  }

  @override
  void dispose() {
    _ticker.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      painter: _PintorPoliedro(
        angulo: _angulo,
        conectado: widget.conectado,
      ),
      child: const SizedBox.expand(),
    );
  }
}

class _PintorPoliedro extends CustomPainter {
  final double angulo;
  final bool conectado;

  _PintorPoliedro({required this.angulo, required this.conectado});

  static final double _phi = (1 + math.sqrt(5)) / 2;

  /// 12 vertices del icosaedro.
  static final List<List<double>> _vertices = [
    [-1, _phi, 0], [1, _phi, 0], [-1, -_phi, 0], [1, -_phi, 0],
    [0, -1, _phi], [0, 1, _phi], [0, -1, -_phi], [0, 1, -_phi],
    [_phi, 0, -1], [_phi, 0, 1], [-_phi, 0, -1], [-_phi, 0, 1],
  ];

  /// Aristas: pares de vertices a distancia 2.
  static final List<List<int>> _aristas = () {
    final lista = <List<int>>[];
    for (var i = 0; i < _vertices.length; i++) {
      for (var j = i + 1; j < _vertices.length; j++) {
        final a = _vertices[i];
        final b = _vertices[j];
        final d = math.sqrt(math.pow(a[0] - b[0], 2) +
            math.pow(a[1] - b[1], 2) +
            math.pow(a[2] - b[2], 2));
        if ((d - 2).abs() < 0.01) lista.add([i, j]);
      }
    }
    return lista;
  }();

  /// Puntos intermedios de las aristas: efecto "esfera de nodos".
  static final List<List<double>> _nodos = () {
    final lista = <List<double>>[];
    for (final a in _aristas) {
      final p = _vertices[a[0]];
      final q = _vertices[a[1]];
      for (final f in [0.3, 0.5, 0.7]) {
        lista.add([
          p[0] + (q[0] - p[0]) * f,
          p[1] + (q[1] - p[1]) * f,
          p[2] + (q[2] - p[2]) * f,
        ]);
      }
    }
    return lista;
  }();

  /// Estrellas de fondo, fijas para que no parpadeen.
  static final List<List<double>> _estrellas = () {
    final azar = math.Random(7);
    return List.generate(
      70,
      (_) => [azar.nextDouble(), azar.nextDouble(), azar.nextDouble() * 1.6 + 0.6],
    );
  }();

  @override
  void paint(Canvas canvas, Size size) {
    final centro = Offset(size.width / 2, size.height / 2);
    final escala = math.min(size.width, size.height) * 0.185;

    // Estrellas
    final pincelEstrella = Paint()..style = PaintingStyle.fill;
    for (final e in _estrellas) {
      pincelEstrella.color = const Color(0xFFC8FFF8).withValues(alpha: 0.28);
      canvas.drawCircle(
        Offset(e[0] * size.width, e[1] * size.height),
        e[2],
        pincelEstrella,
      );
    }

    final rad = angulo * math.pi / 180.0;
    final seno = math.sin(rad);
    final coseno = math.cos(rad);

    List<double> rotar(List<double> v) {
      final x = v[0] * coseno + v[2] * seno;
      final z = -v[0] * seno + v[2] * coseno;
      final y = v[1] * 0.94 - z * 0.10;
      final zz = v[1] * 0.10 + z * 0.94;
      return [x, y, zz];
    }

    Offset proyectar(List<double> v) {
      final factor = 5.0 / (5.0 + v[2]);
      return Offset(
        centro.dx + v[0] * escala * factor,
        centro.dy + v[1] * escala * factor,
      );
    }

    final rotados = _vertices.map(rotar).toList();
    final proyectados = rotados.map(proyectar).toList();

    // Aristas (halo + linea)
    final pincel = Paint()
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    for (final anchos in [
      [escala * 0.030, 26],
      [escala * 0.018, 64],
      [escala * 0.009, 235],
    ]) {
      final grosor = anchos[0];
      final alfaBase = anchos[1] as int;
      for (final a in _aristas) {
        final p = rotados[a[0]];
        final q = rotados[a[1]];
        final prof = (p[2] + q[2]) / 2;
        final cerca = ((1.7 - prof) / 3.4).clamp(0.0, 1.0);
        final alfa = (alfaBase * (0.45 + 0.55 * cerca)).toInt();
        pincel.color = conectado
            ? GeoidColors.acento.withValues(alpha: alfa / 255)
            : const Color(0xFF3C8C8C).withValues(alpha: alfa / 255 * 0.55);
        pincel.strokeWidth = math.max(1.0, grosor);
        canvas.drawLine(proyectados[a[0]], proyectados[a[1]], pincel);
      }
    }

    // Nodos intermedios
    final pincelNodo = Paint()..style = PaintingStyle.fill;
    for (final n in _nodos) {
      final r = rotar(n);
      final punto = proyectar(r);
      final cerca = ((1.7 - r[2]) / 3.4).clamp(0.0, 1.0);
      pincelNodo.color = const Color(0xFFBEFFF6)
          .withValues(alpha: (120 + 110 * cerca) / 255);
      canvas.drawCircle(punto, 1.4 + 1.8 * cerca, pincelNodo);
    }

    // Vertices
    for (var i = 0; i < proyectados.length; i++) {
      final z = rotados[i][2];
      final cerca = ((1.7 - z) / 3.4).clamp(0.0, 1.0);
      pincelNodo.color = const Color(0xFFBEFFF6)
          .withValues(alpha: (150 + 105 * cerca) / 255);
      canvas.drawCircle(proyectados[i], 2.2 + 3.0 * cerca, pincelNodo);
    }
  }

  @override
  bool shouldRepaint(covariant _PintorPoliedro anterior) =>
      anterior.angulo != angulo || anterior.conectado != conectado;
}
