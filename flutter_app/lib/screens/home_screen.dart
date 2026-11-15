import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../i18n.dart';
import '../models/perfil.dart';
import '../services/actualizador.dart';
import '../services/nativo.dart';
import '../services/registro.dart';
import '../services/tun_windows.dart';
import '../theme.dart';
import '../widgets/polyhedron.dart';
import 'apps_screen.dart';
import 'log_screen.dart';
import 'profiles_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _conectado = false;
  bool _conectando = false;
  bool _bloquearAnuncios = true;

  Perfil? _perfil;
  NuevaVersion? _actualizacion;
  String _velocidad = '0 KB/s';
  String _ping = '-- ms';

  StreamSubscription<Map<String, dynamic>>? _suscripcion;
  Timer? _bucleStats;

  int _ultimoTotal = -1;
  int _ciclos = 0;
  bool _midiendo = false;
  RawDatagramSocket? _socketPing;
  Completer<int?>? _esperaPing;
  DateTime _inicioPing = DateTime.now();

  /// Consulta DNS fija (example.com A): solo interesa el tiempo de ida y vuelta.
  static const List<int> _consultaDns = [
    0x12, 0x34, 0x01, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x07, 0x65, 0x78, 0x61, 0x6d, 0x70, 0x6c, 0x65, 0x03, 0x63, 0x6f, 0x6d,
    0x00, 0x00, 0x01, 0x00, 0x01,
  ];
  int _ultimoInstante = 0;

  @override
  void initState() {
    super.initState();
    I18n.iniciar();
    _cargarAjustes();
    _escucharEstado();
    _buscarActualizacion();

    Nativo.alConcederVpn((concedido) {
      if (concedido) {
        _conectarAhora();
      } else {
        Registro.anadir(t('error_vpn'));
        _error(t('error_vpn'));
      }
    });
  }

  Future<void> _cargarAjustes() async {
    final filtrar = await Nativo.leer('ajustes', 'bloquearAnuncios');
    final perfil = await Almacen.activoPerfil();
    if (!mounted) return;
    setState(() {
      _bloquearAnuncios = filtrar == null ? true : filtrar == 'true';
      _perfil = perfil;
    });
  }

  void _escucharEstado() {
    _suscripcion?.cancel();
    _suscripcion = Nativo.estado().listen((datos) {
      final activo = datos['activo'] as bool? ?? false;
      final error = datos['error'] as String?;
      if (!mounted) return;

      if (error != null && error.isNotEmpty) {
        _error(t('error_tunel') + ': $error');
      }

      setState(() {
        _conectado = activo;
        _conectando = false;
      });

      if (activo) {
        Registro.anadir('${t('conectado')} · ${_perfil?.nombre ?? ''}');
        _arrancarStats();
        _buscarActualizacion(otraVez: true);
      } else {
        _pararStats();
      }
    });
  }

  void _error(String texto) {
    Registro.anadir(texto);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(texto),
        backgroundColor: GeoidColors.panel,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  Future<void> _pulsarBoton() async {
    if (_conectando) return;

    if (!esAndroid && !(Platform.isWindows && TunWindows.disponible)) {
      _dialogoEscritorio();
      return;
    }
    if (_conectado) {
      await Nativo.desconectar();
      return;
    }

    final perfil = await Almacen.activoPerfil();
    if (perfil == null) {
      _error(t('sin_perfiles'));
      _abrirPerfiles();
      return;
    }
    _perfil = perfil;

    setState(() => _conectando = true);
    Registro.anadir(t('conectando'));

    final listo = await Nativo.prepararVpn();
    if (listo) {
      await _conectarAhora();
    }
  }


    /// En escritorio no hay seleccion por aplicacion: el tunel es del sistema.
    void _dialogoSoloAndroid() {
      showDialog<void>(
        context: context,
        builder: (contexto) => AlertDialog(
          title: Text(t('apps_titulo')),
          content: Text(t('apps_texto')),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(contexto),
              child: Text(t('cancelar'),
                  style: const TextStyle(color: GeoidColors.acento)),
            ),
          ],
        ),
      );
    }

    /// Aviso en escritorio: el tunel todavia no esta disponible.
    void _dialogoEscritorio() {
      showDialog<void>(
        context: context,
        builder: (contexto) => AlertDialog(
          title: Text(t('escritorio_titulo')),
          content: Text(t('escritorio_texto')),
          actions: [
            TextButton(
              onPressed: () async {
                final perfil = _perfil ?? await Almacen.activoPerfil();
                if (perfil != null) {
                  await Clipboard.setData(ClipboardData(text: perfil.conf));
                }
                if (contexto.mounted) Navigator.pop(contexto);
                _error(t('copiado'));
              },
              child: Text(t('copiar_conf'),
                  style: const TextStyle(color: GeoidColors.acento)),
            ),
            TextButton(
              onPressed: () => Navigator.pop(contexto),
              child: Text(t('cancelar'),
                  style: const TextStyle(color: GeoidColors.textoSuave)),
            ),
          ],
        ),
      );
    }
  Future<void> _conectarAhora() async {
    final perfil = _perfil ?? await Almacen.activoPerfil();
    if (perfil == null) {
      _error(t('sin_perfiles'));
      setState(() => _conectando = false);
      return;
    }

    final seleccion = await Nativo.leer('apps', 'seleccion') ?? '';
    final apps = seleccion
        .split(',')
        .map((e) => e.trim())
        .where((e) => e.isNotEmpty)
        .toList();

    try {
      await Nativo.conectar(
        conf: perfil.conf,
        mtu: perfil.mtu,
        dns: null,
        apps: apps,
        filtrar: _bloquearAnuncios,
      );
    } catch (e) {
      setState(() => _conectando = false);
      _error(t('error_config'));
    }
  }

  void _arrancarStats() {
    _pararStats();
    _ultimoTotal = -1;
    _ultimoInstante = 0;
    _crearSocketPing();
    _bucleStats = Timer.periodic(const Duration(seconds: 2), (_) {
      if (_midiendo) return; // evita solaparse si una medida tarda
      _midiendo = true;
      _medir().whenComplete(() => _midiendo = false);
    });
  }

  void _pararStats() {
    _bucleStats?.cancel();
    _bucleStats = null;
    _cerrarSocketPing();
    if (mounted) {
      setState(() {
        _velocidad = '0 KB/s';
        _ping = '-- ms';
      });
    }
  }

  /// Un solo socket para todas las medidas de latencia (antes se abria uno
  /// nuevo cada 2 segundos).
  Future<void> _crearSocketPing() async {
    if (_socketPing != null) return;
    try {
      final socket = await RawDatagramSocket.bind(InternetAddress.anyIPv4, 0);
      socket.listen((evento) {
        if (evento != RawSocketEvent.read) return;
        final datagrama = socket.receive();
        final espera = _esperaPing;
        if (datagrama != null && espera != null && !espera.isCompleted) {
          espera.complete(
            DateTime.now().difference(_inicioPing).inMilliseconds,
          );
        }
      });
      _socketPing = socket;
    } catch (_) {
      _socketPing = null;
    }
  }

  void _cerrarSocketPing() {
    _socketPing?.close();
    _socketPing = null;
    _esperaPing = null;
  }

  Future<void> _medir() async {
    if (!_conectado) return;
    String crudo;
    try {
      crudo = await Nativo.stats();
    } catch (_) {
      return;
    }
    final partes = crudo.split(';');
    if (partes.length < 2) return;
    final rx = int.tryParse(partes[0].trim()) ?? 0;
    final tx = int.tryParse(partes[1].trim()) ?? 0;
    final total = rx + tx;
    final ahora = DateTime.now().millisecondsSinceEpoch;

    var texto = _velocidad;
    if (_ultimoInstante > 0 && _ultimoTotal >= 0) {
      final segundos = (ahora - _ultimoInstante) / 1000.0;
      if (segundos > 0.3 && total >= _ultimoTotal) {
        texto = _formatear((total - _ultimoTotal) / segundos);
      }
    }
    _ultimoTotal = total;
    _ultimoInstante = ahora;

    // La latencia se mide cada 6 segundos: menos red, mismo resultado util.
    _ciclos++;
    int? ping;
    if (_ciclos % 3 == 0) ping = await _medirPing();

    if (!mounted) return;
    setState(() {
      _velocidad = texto;
      if (ping != null) _ping = '$ping ms';
    });
  }

  String _formatear(double bps) {
    if (bps < 1024) return '${bps.toStringAsFixed(0)} B/s';
    if (bps < 1024 * 1024) return '${(bps / 1024).toStringAsFixed(0)} KB/s';
    return '${(bps / (1024 * 1024)).toStringAsFixed(1)} MB/s';
  }

  /// Latencia real: consulta DNS al servidor del tunel y mide la respuesta.
  Future<int?> _medirPing() async {
    final socket = _socketPing;
    final puerta = _puertaTunel();
    if (socket == null || puerta == null) return null;

    final espera = Completer<int?>();
    _esperaPing = espera;
    _inicioPing = DateTime.now();

    try {
      socket.send(_consultaDns, puerta, 53);
      return await espera.future
          .timeout(const Duration(milliseconds: 1500), onTimeout: () => null);
    } catch (_) {
      return null;
    } finally {
      if (identical(_esperaPing, espera)) _esperaPing = null;
    }
  }
  InternetAddress? _puertaTunel() {
    final conf = _perfil?.conf ?? '';
    for (final bruta in conf.split('\n')) {
      final linea = bruta.trim();
      if (linea.toLowerCase().startsWith('address')) {
        final ip = linea.split('=').last.split(',').first.trim();
        final partes = ip.split('/').first.split('.');
        if (partes.length == 4) {
          return InternetAddress.tryParse('${partes[0]}.${partes[1]}.${partes[2]}.1');
        }
      }
    }
    return null;
  }

  Future<void> _buscarActualizacion({bool otraVez = false}) async {
    final nueva = await Actualizador.buscar();
    if (nueva == null) return;
    final actual = await Actualizador.versionInstalada();
    // Si el binario no lleva la version incrustada, no se avisa: mejor no
    // molestar con un aviso que podria ser falso.
    if (actual.isEmpty || actual == '0.0.0') return;
    if (!Actualizador.masNueva(nueva.numero, actual)) return;
    if (!mounted) return;
    setState(() => _actualizacion = nueva);
  }

  @override
  void dispose() {
    _suscripcion?.cancel();
    _bucleStats?.cancel();
    super.dispose();
  }

  Future<void> _abrirAplicaciones() async {
    if (!esAndroid) {
      _dialogoSoloAndroid();
      return;
    }
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const AppsScreen()),
    );
    // Al volver, se refresca el contador de la pantalla principal.
    await _actualizarResumenApps();
  }

  Future<void> _abrirPerfiles() async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const ProfilesScreen()),
    );
    final perfil = await Almacen.activoPerfil();
    if (mounted) setState(() => _perfil = perfil);
  }

  void _abrirRegistro() {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const LogScreen()),
    );
  }

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
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.baseline,
                        textBaseline: TextBaseline.alphabetic,
                        children: [
                          const Text(
                            'GEOID-VPN',
                            style: TextStyle(
                              color: Color(0xFF5FD9C8),
                              fontSize: 12,
                              letterSpacing: 3.6,
                              fontWeight: FontWeight.w300,
                            ),
                          ),
                          const SizedBox(width: 8),
                          FutureBuilder<String>(
                            future: Nativo.version(),
                            builder: (contexto, instantanea) {
                              final v = instantanea.data;
                              if (v == null || v.isEmpty) {
                                return const SizedBox.shrink();
                              }
                              return Text(
                                'v$v',
                                style: const TextStyle(
                                  color: GeoidColors.textoTenue,
                                  fontSize: 9,
                                ),
                              );
                            },
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Text(
                        _conectando
                            ? t('conectando').toUpperCase()
                            : (_conectado ? t('conectado') : t('desconectado')),
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
                  if (_conectado)
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          _velocidad,
                          style: const TextStyle(
                            color: GeoidColors.acento,
                            fontSize: 13,
                            fontFamily: 'monospace',
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          _ping,
                          style: const TextStyle(
                            color: GeoidColors.textoSuave,
                            fontSize: 11,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          'Finland',
                          style: TextStyle(
                            color: GeoidColors.textoTenue,
                            fontSize: 10,
                          ),
                        ),
                      ],
                    ),
                ],
              ),

              if (_actualizacion != null) ...[
                const SizedBox(height: 10),
                _bannerActualizacion(),
              ],

              Expanded(child: Polyhedron(conectado: _conectado)),

              _botonPrincipal(),
              const SizedBox(height: 12),

              Row(
                children: [
                  Expanded(
                    child: _botonSecundario(
                      t('apps'),
                      _abrirAplicaciones,
                      resumen: _resumenApps(),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(child: _botonSecundario(t('registro'), _abrirRegistro)),
                ],
              ),
              const SizedBox(height: 14),

              Row(
                children: [
                  Expanded(
                    child: Text(
                      _resumenApps(),
                      style: const TextStyle(
                        color: GeoidColors.textoSuave,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ),

              Row(
                children: [
                  Expanded(
                    child: Text(
                      t('bloquear_anuncios'),
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
                      onChanged: (v) async {
                        setState(() => _bloquearAnuncios = v);
                        await Nativo.guardar('ajustes', 'bloquearAnuncios', '$v');
                        if (_conectado) {
                          await Nativo.desconectar();
                          await _conectarAhora();
                        }
                      },
                    ),
                  ),
                ],
              ),

              TextButton(
                onPressed: _abrirPerfiles,
                child: Text(
                  '${t('perfiles')}: ${_perfil?.nombre ?? t('sin_perfiles')}',
                  style: const TextStyle(color: GeoidColors.acento, fontSize: 12),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _resumenApps() {
    // Se lee de forma sincrona de la cache del canal; si no, texto por defecto.
    return _appsResumen;
  }

  String _appsResumen = '';

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _actualizarResumenApps();
  }

  Future<void> _actualizarResumenApps() async {
    final seleccion = await Nativo.leer('apps', 'seleccion') ?? '';
    final cuantas = seleccion
        .split(',')
        .map((e) => e.trim())
        .where((e) => e.isNotEmpty)
        .length;
    if (!mounted) return;
    setState(() {
      if (!esAndroid) {
        _appsResumen = t('todo_sistema');
      } else if (cuantas == 0) {
        _appsResumen = t('todas_apps');
      } else {
        _appsResumen = cuantas == 1
            ? t('apps_1')
            : t('apps_n').replaceFirst('%s', '$cuantas');
      }
    });
  }

  Widget _bannerActualizacion() {
    return InkWell(
      borderRadius: BorderRadius.circular(20),
      onTap: () async {
        final version = _actualizacion;
        if (version == null) return;
        await Actualizador.descargar(version);
        _error(t('descargando'));
        // Ya se ha descargado: el aviso no vuelve a molestar.
        if (mounted) setState(() => _actualizacion = null);
      },
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 11, horizontal: 14),
        decoration: BoxDecoration(
          color: GeoidColors.panel,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: GeoidColors.borde),
        ),
        child: Text(
          t('nueva_version').replaceFirst('%s', _actualizacion!.numero),
          textAlign: TextAlign.center,
          style: const TextStyle(color: GeoidColors.acento, fontSize: 12),
        ),
      ),
    );
  }

  Widget _botonPrincipal() {
    return SizedBox(
      height: 60,
      child: FilledButton(
        onPressed: _pulsarBoton,
        style: FilledButton.styleFrom(
          backgroundColor:
              _conectado ? GeoidColors.botonApagado : GeoidColors.acento,
          foregroundColor:
              _conectado ? GeoidColors.acento : GeoidColors.fondo,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
        ),
        child: Text(
          _conectando
              ? '…'
              : (_conectado ? t('desconectar') : t('conectar')),
          style: const TextStyle(fontSize: 16),
        ),
      ),
    );
  }

  Widget _botonSecundario(String texto, VoidCallback alPulsar, {String? resumen}) {
    return SizedBox(
      height: 48,
      child: OutlinedButton(
        onPressed: alPulsar,
        style: OutlinedButton.styleFrom(
          foregroundColor: const Color(0xFF9BE8DC),
          side: const BorderSide(color: GeoidColors.borde),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        ),
        child: Text(texto, style: const TextStyle(fontSize: 13)),
      ),
    );
  }
}
