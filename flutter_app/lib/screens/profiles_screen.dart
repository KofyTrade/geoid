import 'package:flutter/material.dart';

import '../i18n.dart';
import '../models/perfil.dart';
import '../services/nativo.dart';
import '../services/registro.dart';
import '../theme.dart';

class ProfilesScreen extends StatefulWidget {
  /// Si viene de abrir un .conf desde fuera, el contenido ya listo.
  final String? confInicial;

  ProfilesScreen({super.key, this.confInicial});

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

    // Si venimos de abrir un .conf, se abre el dialogo ya relleno.
    final inicial = widget.confInicial;
    if (inicial != null && inicial.trim().isNotEmpty) {
      _nuevoOEditar(contenidoInicial: inicial);
    }
  }

  /// Dialogo unico: nombre editable, texto y boton de importar archivo.
  Future<void> _nuevoOEditar({Perfil? existente, String? contenidoInicial}) async {
    final resultado = await showDialog<({String nombre, String conf})>(
      context: context,
      barrierDismissible: false,
      builder: (_) => DialogoPerfil(
        perfil: existente,
        contenidoInicial: contenidoInicial,
        sugerido: existente?.nombre ?? 'Perfil ${_perfiles.length + 1}',
      ),
    );
    if (resultado == null) return;

    final nombre = resultado.nombre.trim();
    final conf = resultado.conf;

    if (existente != null) {
      final anterior = existente.nombre;
      existente.nombre = nombre;
      existente.conf = conf;
      await Almacen.guardarLista(_perfiles);
      if (_activo == anterior) {
        await Almacen.marcarActivo(nombre);
        _activo = nombre;
      }
      Registro.anadir('${t('editar')}: $nombre');
    } else {
      final nuevo = Perfil(nombre, conf);
      final lista = List<Perfil>.from(_perfiles)..add(nuevo);
      await Almacen.guardarLista(lista);
      await Almacen.marcarActivo(nombre);
      _perfiles = lista;
      _activo = nombre;
      Registro.anadir('${t('nuevo_perfil')}: $nombre');
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
                style: TextStyle(color: GeoidColors.textoSuave)),
          ),
          TextButton(
            onPressed: () => Navigator.pop(contexto, true),
            child: Text(t('eliminar'),
                style: TextStyle(color: GeoidColors.acento)),
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

  void _verConf(Perfil perfil) {
    showDialog<void>(
      context: context,
      builder: (contexto) => AlertDialog(
        title: Text(perfil.nombre),
        content: SizedBox(
          width: double.maxFinite,
          height: 300,
          child: SingleChildScrollView(
            child: SelectableText(
              perfil.conf,
              style: TextStyle(
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
                style: TextStyle(color: GeoidColors.acento)),
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
          style: TextStyle(fontSize: 16, letterSpacing: 1.2),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: GeoidColors.acento,
        foregroundColor: GeoidColors.fondo,
        onPressed: () => _nuevoOEditar(),
        icon: Icon(Icons.add),
        label: Text(t('nuevo_perfil')),
      ),
      body: SafeArea(
        child: _cargando
            ? Center(
                child: CircularProgressIndicator(color: GeoidColors.acento))
            : _perfiles.isEmpty
                ? Center(
                    child: Text(
                      t('sin_perfiles'),
                      style: TextStyle(
                        color: GeoidColors.textoSuave,
                        fontSize: 13,
                      ),
                    ),
                  )
                : ListView.builder(
                    padding: EdgeInsets.fromLTRB(16, 8, 16, 90),
                    itemCount: _perfiles.length,
                    itemBuilder: (contexto, i) {
                      final perfil = _perfiles[i];
                      final esActivo = perfil.nombre == _activo;
                      return Card(
                        color:
                            esActivo ? GeoidColors.panel : GeoidColors.botonApagado,
                        margin: EdgeInsets.only(bottom: 10),
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
                            style: TextStyle(
                              color: GeoidColors.textoTenue,
                              fontSize: 11,
                            ),
                          ),
                          trailing: PopupMenuButton<String>(
                            color: GeoidColors.panel,
                            icon: Icon(Icons.more_vert,
                                size: 18, color: GeoidColors.textoSuave),
                            onSelected: (accion) {
                              switch (accion) {
                                case 'usar':
                                  _usar(perfil);
                                  break;
                                case 'editar':
                                  _nuevoOEditar(existente: perfil);
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
                                value: 'editar',
                                child: Text(t('editar')),
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
    );
  }
}

/// Dialogo de perfil: nombre, contenido y boton de importar desde archivo.
class DialogoPerfil extends StatefulWidget {
  final Perfil? perfil;
  final String? contenidoInicial;
  final String sugerido;

  DialogoPerfil({
    super.key,
    this.perfil,
    this.contenidoInicial,
    required this.sugerido,
  });

  @override
  State<DialogoPerfil> createState() => _DialogoPerfilState();
}

class _DialogoPerfilState extends State<DialogoPerfil> {
  late final TextEditingController _nombre =
      TextEditingController(text: widget.sugerido);
  late final TextEditingController _conf = TextEditingController(
    text: widget.perfil?.conf ?? widget.contenidoInicial ?? '',
  );
  String? _error;
  bool _importando = false;

  @override
  void dispose() {
    _nombre.dispose();
    _conf.dispose();
    super.dispose();
  }

  bool _valido(String texto) {
    final m = texto.toLowerCase();
    return m.contains('[interface]') &&
        m.contains('[peer]') &&
        m.contains('privatekey') &&
        m.contains('endpoint');
  }

  Future<void> _importar() async {
    setState(() => _importando = true);
    final texto = await Nativo.elegirArchivo();
    if (!mounted) return;
    setState(() => _importando = false);
    if (texto == null || texto.trim().isEmpty) return;
    setState(() {
      _conf.text = texto;
      _error = _valido(texto) ? null : t('error_config');
    });
  }

  void _guardar() {
    final nombre = _nombre.text.trim();
    final conf = _conf.text.trim();
    if (nombre.isEmpty) {
      setState(() => _error = t('nombre'));
      return;
    }
    if (!_valido(conf)) {
      setState(() => _error = t('error_config'));
      return;
    }
    Navigator.pop(context, (nombre: nombre, conf: conf));
  }

  @override
  Widget build(BuildContext context) {
    final editando = widget.perfil != null;
    return AlertDialog(
      title: Text(editando ? t('editar') : t('nuevo_perfil')),
      content: SizedBox(
        width: 460,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextField(
                controller: _nombre,
                autofocus: !editando,
                textCapitalization: TextCapitalization.sentences,
                style: TextStyle(color: GeoidColors.texto),
                decoration: InputDecoration(labelText: t('nombre')),
              ),
              SizedBox(height: 14),
              SizedBox(
                height: 200,
                child: TextField(
                  controller: _conf,
                  maxLines: null,
                  expands: true,
                  textAlignVertical: TextAlignVertical.top,
                  style: TextStyle(
                    color: GeoidColors.textoSuave,
                    fontSize: 11,
                    fontFamily: 'monospace',
                  ),
                  decoration: InputDecoration(
                    hintText:
                        '[Interface]\nPrivateKey = ...\n[Peer]\nEndpoint = ...',
                  ),
                  onChanged: (valor) {
                    if (_error != null) setState(() => _error = null);
                  },
                ),
              ),
              SizedBox(height: 10),
              OutlinedButton.icon(
                onPressed: _importando ? null : _importar,
                style: OutlinedButton.styleFrom(
                  foregroundColor: GeoidColors.textoBoton,
                  side: BorderSide(color: GeoidColors.borde),
                  minimumSize: Size.fromHeight(44),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(22),
                  ),
                ),
                icon: _importando
                    ? SizedBox(
                        width: 14,
                        height: 14,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: GeoidColors.acento,
                        ),
                      )
                    : Icon(Icons.folder_open, size: 16),
                label: Text(t('importar_conf'),
                    style: TextStyle(fontSize: 12)),
              ),
              if (_error != null) ...[
                SizedBox(height: 10),
                Text(
                  _error!,
                  style: TextStyle(
                    color: Color(0xFFFF8A80),
                    fontSize: 11,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: Text(t('cancelar'),
              style: TextStyle(color: GeoidColors.textoSuave)),
        ),
        TextButton(
          onPressed: _guardar,
          child: Text(t('guardar'),
              style: TextStyle(color: GeoidColors.acento)),
        ),
      ],
    );
  }
}
