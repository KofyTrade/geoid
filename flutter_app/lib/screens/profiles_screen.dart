import 'package:flutter/material.dart';

import '../i18n.dart';
import '../models/perfil.dart';
import '../services/nativo.dart';
import '../services/registro.dart';
import '../theme.dart';

class ProfilesScreen extends StatefulWidget {
  const ProfilesScreen({super.key});

  @override
  State<ProfilesScreen> createState() => _ProfilesScreenState();
}

class _ProfilesScreenState extends State<ProfilesScreen> {
  List<Perfil> _perfiles = [];
  String? _activo;
  bool _cargando = true;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    final lista = await Almacen.lista();
    final activo = await Almacen.activo();
    if (!mounted) return;
    setState(() {
      _perfiles = lista;
      _activo = activo ?? (lista.isEmpty ? null : lista.first.nombre);
      _cargando = false;
    });
  }

  Future<void> _importar() async {
    final texto = await Nativo.elegirArchivo();
    if (texto == null || texto.trim().isEmpty) return;
    if (!_valido(texto)) {
      _avisar(t('error_config'));
      return;
    }
    await _pedirNombreYGuardar(texto);
  }

  bool _valido(String texto) {
    final minusculas = texto.toLowerCase();
    return minusculas.contains('[interface]') &&
        minusculas.contains('[peer]') &&
        minusculas.contains('privatekey') &&
        minusculas.contains('endpoint');
  }

  Future<void> _pegarTexto() async {
    final controlador = TextEditingController();
    final texto = await showDialog<String>(
      context: context,
      builder: (contexto) => AlertDialog(
        title: Text(t('pegar_texto')),
        content: SizedBox(
          width: double.maxFinite,
          height: 260,
          child: TextField(
            controller: controlador,
            maxLines: null,
            expands: true,
            style: const TextStyle(
              color: GeoidColors.texto,
              fontSize: 12,
              fontFamily: 'monospace',
            ),
            decoration: const InputDecoration(
              hintText: '[Interface]\nPrivateKey = ...\n[Peer]\nEndpoint = ...',
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(contexto),
            child: Text(t('cancelar'),
                style: const TextStyle(color: GeoidColors.textoSuave)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(contexto, controlador.text),
            child: Text(t('guardar'),
                style: const TextStyle(color: GeoidColors.acento)),
          ),
        ],
      ),
    );

    if (texto == null || texto.trim().isEmpty) return;
    if (!_valido(texto)) {
      _avisar(t('error_config'));
      return;
    }
    await _pedirNombreYGuardar(texto);
  }

  Future<void> _pedirNombreYGuardar(String conf) async {
    final sugerido = 'Perfil ${_perfiles.length + 1}';
    final controlador = TextEditingController(text: sugerido);
    final nombre = await showDialog<String>(
      context: context,
      builder: (contexto) => AlertDialog(
        title: Text(t('nuevo_perfil')),
        content: TextField(
          controller: controlador,
          autofocus: true,
          style: const TextStyle(color: GeoidColors.texto),
          decoration: InputDecoration(labelText: t('nombre')),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(contexto),
            child: Text(t('cancelar'),
                style: const TextStyle(color: GeoidColors.textoSuave)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(contexto, controlador.text.trim()),
            child: Text(t('guardar'),
                style: const TextStyle(color: GeoidColors.acento)),
          ),
        ],
      ),
    );

    if (nombre == null || nombre.isEmpty) return;

    final nuevo = Perfil(nombre, conf);
    final lista = List<Perfil>.from(_perfiles)..add(nuevo);
    await Almacen.guardarLista(lista);
    await Almacen.marcarActivo(nombre);
    Registro.anadir('${t('nuevo_perfil')}: $nombre');
    if (!mounted) return;
    setState(() {
      _perfiles = lista;
      _activo = nombre;
    });
  }

  Future<void> _renombrar(Perfil perfil) async {
    final controlador = TextEditingController(text: perfil.nombre);
    final nombre = await showDialog<String>(
      context: context,
      builder: (contexto) => AlertDialog(
        title: Text(t('renombrar')),
        content: TextField(
          controller: controlador,
          autofocus: true,
          style: const TextStyle(color: GeoidColors.texto),
          decoration: InputDecoration(labelText: t('nombre')),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(contexto),
            child: Text(t('cancelar'),
                style: const TextStyle(color: GeoidColors.textoSuave)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(contexto, controlador.text.trim()),
            child: Text(t('guardar'),
                style: const TextStyle(color: GeoidColors.acento)),
          ),
        ],
      ),
    );
    if (nombre == null || nombre.isEmpty) return;

    final anterior = perfil.nombre;
    perfil.nombre = nombre;
    await Almacen.guardarLista(_perfiles);
    if (_activo == anterior) {
      await Almacen.marcarActivo(nombre);
      _activo = nombre;
    }
    if (mounted) setState(() {});
  }

  Future<void> _eliminar(Perfil perfil) async {
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (contexto) => AlertDialog(
        title: Text(t('eliminar')),
        content: Text('${perfil.nombre}?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(contexto, false),
            child: Text(t('cancelar'),
                style: const TextStyle(color: GeoidColors.textoSuave)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(contexto, true),
            child: Text(t('eliminar'),
                style: const TextStyle(color: GeoidColors.acento)),
          ),
        ],
      ),
    );
    if (confirmar != true) return;

    final lista = List<Perfil>.from(_perfiles)..remove(perfil);
    await Almacen.guardarLista(lista);
    if (_activo == perfil.nombre) {
      final nuevo = lista.isEmpty ? null : lista.first.nombre;
      if (nuevo != null) await Almacen.marcarActivo(nuevo);
      _activo = nuevo;
    }
    if (mounted) setState(() => _perfiles = lista);
  }

  Future<void> _usar(Perfil perfil) async {
    await Almacen.marcarActivo(perfil.nombre);
    if (mounted) setState(() => _activo = perfil.nombre);
  }

  void _avisar(String texto) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(texto), behavior: SnackBarBehavior.floating),
    );
  }

  void _verConf(Perfil perfil) {
    showDialog<void>(
      context: context,
      builder: (contexto) => AlertDialog(
        title: Text(perfil.nombre),
        content: SizedBox(
          width: double.maxFinite,
          height: 300,
          child: SingleChildScrollView(
            child: Text(
              perfil.conf,
              style: const TextStyle(
                fontSize: 10,
                fontFamily: 'monospace',
                color: GeoidColors.textoSuave,
              ),
            ),
          ),
        ),
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: GeoidColors.fondo,
      appBar: AppBar(
        backgroundColor: GeoidColors.fondo,
        foregroundColor: GeoidColors.acento,
        elevation: 0,
        title: Text(
          t('perfiles'),
          style: const TextStyle(fontSize: 16, letterSpacing: 1.2),
        ),
        actions: [
          IconButton(
            tooltip: t('pegar_texto'),
            onPressed: _pegarTexto,
            icon: const Icon(Icons.content_paste, size: 20),
          ),
          const SizedBox(width: 6),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: GeoidColors.acento,
        foregroundColor: GeoidColors.fondo,
        onPressed: esAndroid ? _importar : _pegarTexto,
        icon: const Icon(Icons.add),
        label: Text(t('nuevo_perfil')),
      ),
      body: SafeArea(
        child: _cargando
            ? const Center(
                child: CircularProgressIndicator(color: GeoidColors.acento))
            : Column(
                children: [
                  if (_perfiles.isEmpty)
                    Expanded(
                      child: Center(
                        child: Text(
                          t('sin_perfiles'),
                          style: const TextStyle(
                            color: GeoidColors.textoSuave,
                            fontSize: 13,
                          ),
                        ),
                      ),
                    )
                  else
                    Expanded(
                      child: ListView.builder(
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 90),
                        itemCount: _perfiles.length,
                        itemBuilder: (contexto, i) {
                          final perfil = _perfiles[i];
                          final esActivo = perfil.nombre == _activo;
                          return Card(
                            color: esActivo
                                ? GeoidColors.panel
                                : GeoidColors.botonApagado,
                            margin: const EdgeInsets.only(bottom: 10),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(18),
                              side: BorderSide(
                                color: esActivo
                                    ? GeoidColors.acento
                                    : GeoidColors.borde,
                              ),
                            ),
                            child: ListTile(
                              onTap: () => _usar(perfil),
                              title: Text(
                                perfil.nombre,
                                style: TextStyle(
                                  color: esActivo
                                      ? GeoidColors.acento
                                      : GeoidColors.texto,
                                  fontSize: 14,
                                ),
                              ),
                              subtitle: Text(
                                perfil.resumen,
                                style: const TextStyle(
                                  color: GeoidColors.textoTenue,
                                  fontSize: 11,
                                ),
                              ),
                              trailing: PopupMenuButton<String>(
                                color: GeoidColors.panel,
                                icon: const Icon(Icons.more_vert,
                                    size: 18, color: GeoidColors.textoSuave),
                                onSelected: (accion) {
                                  switch (accion) {
                                    case 'usar':
                                      _usar(perfil);
                                      break;
                                    case 'renombrar':
                                      _renombrar(perfil);
                                      break;
                                    case 'ver':
                                      _verConf(perfil);
                                      break;
                                    case 'eliminar':
                                      _eliminar(perfil);
                                      break;
                                  }
                                },
                                itemBuilder: (_) => [
                                  PopupMenuItem(
                                    value: 'usar',
                                    child: Text(t('activar')),
                                  ),
                                  PopupMenuItem(
                                    value: 'renombrar',
                                    child: Text(t('renombrar')),
                                  ),
                                  PopupMenuItem(
                                    value: 'ver',
                                    child: Text(t('ver_conf')),
                                  ),
                                  PopupMenuItem(
                                    value: 'eliminar',
                                    child: Text(t('eliminar')),
                                  ),
                                ],
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
