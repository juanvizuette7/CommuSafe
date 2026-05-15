import 'dart:io';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/localization/app_localizations.dart';
import '../../../core/theme/app_theme.dart';
import '../providers/incidente_provider.dart';

class CrearIncidenteScreen extends StatefulWidget {
  const CrearIncidenteScreen({super.key});

  @override
  State<CrearIncidenteScreen> createState() => _CrearIncidenteScreenState();
}

class _CrearIncidenteScreenState extends State<CrearIncidenteScreen> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  final TextEditingController _tituloController = TextEditingController();
  final TextEditingController _descripcionController = TextEditingController();
  final TextEditingController _ubicacionController = TextEditingController();
  final ImagePicker _imagePicker = ImagePicker();

  final List<XFile> _imagenes = <XFile>[];
  String _categoriaSeleccionada = 'SEGURIDAD';

  static const List<Map<String, String>> _categorias = <Map<String, String>>[
    <String, String>{'value': 'SEGURIDAD', 'label': 'Seguridad'},
    <String, String>{'value': 'CONVIVENCIA', 'label': 'Convivencia'},
    <String, String>{'value': 'INFRAESTRUCTURA', 'label': 'Infraestructura'},
    <String, String>{'value': 'EMERGENCIA', 'label': 'Emergencia'},
  ];

  @override
  void dispose() {
    _tituloController.dispose();
    _descripcionController.dispose();
    _ubicacionController.dispose();
    super.dispose();
  }

  Future<void> _seleccionarFuente() async {
    await showModalBottomSheet<void>(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (BuildContext context) {
        final l10n = AppLocalizations.of(context);
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Container(
                  width: 48,
                  height: 4,
                  decoration: BoxDecoration(
                    color: AppColors.muted,
                    borderRadius: BorderRadius.circular(999),
                  ),
                ),
                const SizedBox(height: 18),
                Text(
                  l10n.tr(
                    'Agregar evidencia fotografica',
                    'Add photo evidence',
                  ),
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 18),
                ListTile(
                  leading: const CircleAvatar(
                    backgroundColor: Color(0xFFE2E8F0),
                    child: Icon(Icons.photo_camera_rounded),
                  ),
                  title: Text(l10n.tr('Tomar foto', 'Take photo')),
                  subtitle: Text(
                    l10n.tr(
                      'Usar la camara del dispositivo',
                      'Use the device camera',
                    ),
                  ),
                  onTap: () async {
                    Navigator.of(context).pop();
                    await _tomarFoto();
                  },
                ),
                ListTile(
                  leading: const CircleAvatar(
                    backgroundColor: Color(0xFFE2E8F0),
                    child: Icon(Icons.photo_library_rounded),
                  ),
                  title: Text(
                    l10n.tr('Elegir de la galeria', 'Choose from gallery'),
                  ),
                  subtitle: Text(
                    l10n.tr(
                      'Selecciona hasta 3 imagenes',
                      'Select up to 3 images',
                    ),
                  ),
                  onTap: () async {
                    Navigator.of(context).pop();
                    await _seleccionarGaleria();
                  },
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Future<void> _tomarFoto() async {
    final image = await _imagePicker.pickImage(
      source: ImageSource.camera,
      imageQuality: 85,
      maxWidth: 1800,
    );
    if (image == null) {
      return;
    }
    _agregarImagenes(<XFile>[image]);
  }

  Future<void> _seleccionarGaleria() async {
    final images = await _imagePicker.pickMultiImage(
      imageQuality: 85,
      maxWidth: 1800,
    );
    if (images.isEmpty) {
      return;
    }
    _agregarImagenes(images);
  }

  void _agregarImagenes(List<XFile> images) {
    final remaining = 3 - _imagenes.length;
    final l10n = AppLocalizations.of(context);
    if (remaining <= 0) {
      _showSnack(
        l10n.tr(
          'Solo puedes adjuntar maximo 3 evidencias.',
          'You can attach up to 3 evidence files.',
        ),
      );
      return;
    }

    setState(() {
      _imagenes.addAll(images.take(remaining));
    });

    if (images.length > remaining) {
      _showSnack(
        l10n.tr(
          'Solo se agregaron $remaining imagenes.',
          'Only $remaining images were added.',
        ),
      );
    }
  }

  void _showSnack(String message, {Color? color}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: color ?? CommuSafeThemeExtension.of(context).primary,
      ),
    );
  }

  Future<void> _callEmergencyLine() async {
    await launchUrl(Uri(scheme: 'tel', path: '112'));
  }

  Future<void> _submit() async {
    final form = _formKey.currentState;
    if (form == null || !form.validate()) {
      return;
    }

    final provider = context.read<IncidenteProvider>();
    final incidente = await provider.crearIncidente(
      titulo: _tituloController.text,
      descripcion: _descripcionController.text,
      categoria: _categoriaSeleccionada,
      ubicacionReferencia: _ubicacionController.text,
      imagenes: _imagenes,
    );

    if (!mounted) {
      return;
    }

    if (incidente == null) {
      final l10n = AppLocalizations.of(context);
      _showSnack(
        provider.errorMessage ??
            l10n.tr(
              'No fue posible reportar el incidente.',
              'The incident could not be reported.',
            ),
        color: AppColors.danger,
      );
      return;
    }

    _showSnack(
      AppLocalizations.of(context).tr(
        'Incidente reportado correctamente.',
        'Incident reported successfully.',
      ),
      color: AppColors.success,
    );
    context.pop(true);
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<IncidenteProvider>();
    final theme = CommuSafeThemeExtension.of(context);
    final l10n = AppLocalizations.of(context);

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Text(l10n.tr('Reportar incidente', 'Report incident')),
        leading: IconButton(
          icon: const Icon(Icons.close_rounded),
          onPressed: () => context.pop(),
        ),
      ),
      body: SafeArea(
        top: false,
        child: Form(
          key: _formKey,
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
            children: <Widget>[
              _FormCard(
                title: l10n.tr('Informacion principal', 'Main information'),
                subtitle: l10n.tr(
                  'Describe claramente el incidente que estas reportando.',
                  'Clearly describe the incident you are reporting.',
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    TextFormField(
                      controller: _tituloController,
                      decoration: InputDecoration(
                        labelText: l10n.tr('Titulo', 'Title'),
                        hintText: l10n.tr(
                          'Ej. Ruido excesivo en torre B',
                          'Ex. Excessive noise in tower B',
                        ),
                      ),
                      validator: (String? value) {
                        if ((value ?? '').trim().isEmpty) {
                          return l10n.tr(
                            'Ingresa un titulo para el incidente.',
                            'Enter a title for the incident.',
                          );
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 20),
                    Text(
                      l10n.tr('Categoria', 'Category'),
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      height: 46,
                      child: ListView.separated(
                        scrollDirection: Axis.horizontal,
                        itemCount: _categorias.length,
                        separatorBuilder: (_, __) => const SizedBox(width: 10),
                        itemBuilder: (BuildContext context, int index) {
                          final categoria = _categorias[index];
                          final isSelected =
                              _categoriaSeleccionada == categoria['value'];
                          return ChoiceChip(
                            label: Text(
                              _categoryLabel(categoria['value'] ?? '', l10n),
                            ),
                            selected: isSelected,
                            onSelected: (_) {
                              setState(() {
                                _categoriaSeleccionada =
                                    categoria['value'] ?? 'SEGURIDAD';
                              });
                            },
                            selectedColor: theme.primary,
                            backgroundColor: const Color(0xFFF1F5F9),
                            side: BorderSide(
                              color: isSelected
                                  ? theme.primary
                                  : const Color(0xFFE2E8F0),
                            ),
                            labelStyle: TextStyle(
                              color: isSelected
                                  ? Colors.white
                                  : AppColors.textSecondary,
                              fontWeight: FontWeight.w700,
                            ),
                          );
                        },
                      ),
                    ),
                    const SizedBox(height: 20),
                    AnimatedSwitcher(
                      duration: const Duration(milliseconds: 250),
                      child: _categoriaSeleccionada == 'EMERGENCIA'
                          ? Container(
                              key: const ValueKey<String>('emergency-banner'),
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: AppColors.danger.withValues(alpha: 0.12),
                                borderRadius: BorderRadius.circular(18),
                                border: Border.all(
                                  color: AppColors.danger.withValues(
                                    alpha: 0.24,
                                  ),
                                ),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: <Widget>[
                                  Row(
                                    children: <Widget>[
                                      const Icon(
                                        Icons.warning_amber_rounded,
                                        color: AppColors.danger,
                                      ),
                                      const SizedBox(width: 8),
                                      Expanded(
                                        child: Text(
                                          l10n.tr(
                                            'ATENCION: Estas reportando una emergencia.',
                                            'ATTENTION: You are reporting an emergency.',
                                          ),
                                          style: Theme.of(context)
                                              .textTheme
                                              .titleSmall
                                              ?.copyWith(
                                                color: AppColors.danger,
                                                fontWeight: FontWeight.w800,
                                              ),
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 10),
                                  Text(
                                    l10n.tr(
                                      'Si hay riesgo de vida, llama al 112 directamente.',
                                      'If there is a life-threatening risk, call 112 directly.',
                                    ),
                                    style: Theme.of(context)
                                        .textTheme
                                        .bodyMedium
                                        ?.copyWith(
                                          color: AppColors.textPrimary,
                                          height: 1.45,
                                        ),
                                  ),
                                  const SizedBox(height: 12),
                                  OutlinedButton.icon(
                                    onPressed: _callEmergencyLine,
                                    style: OutlinedButton.styleFrom(
                                      foregroundColor: AppColors.danger,
                                      side: const BorderSide(
                                        color: AppColors.danger,
                                      ),
                                    ),
                                    icon: const Icon(Icons.call_rounded),
                                    label: Text(
                                      l10n.tr('Llamar al 112', 'Call 112'),
                                    ),
                                  ),
                                ],
                              ),
                            )
                          : const SizedBox.shrink(),
                    ),
                    const SizedBox(height: 20),
                    TextFormField(
                      controller: _descripcionController,
                      minLines: 4,
                      maxLines: 6,
                      maxLength: 500,
                      decoration: InputDecoration(
                        labelText: l10n.tr('Descripcion', 'Description'),
                        hintText: l10n.tr(
                          'Describe lo sucedido con el mayor detalle posible.',
                          'Describe what happened with as much detail as possible.',
                        ),
                        alignLabelWithHint: true,
                      ),
                      validator: (String? value) {
                        if ((value ?? '').trim().isEmpty) {
                          return l10n.tr(
                            'Ingresa una descripcion del incidente.',
                            'Enter an incident description.',
                          );
                        }
                        if ((value ?? '').trim().length < 10) {
                          return l10n.tr(
                            'La descripcion debe tener al menos 10 caracteres.',
                            'The description must have at least 10 characters.',
                          );
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _ubicacionController,
                      decoration: InputDecoration(
                        labelText: l10n.tr(
                          'Ubicacion de referencia',
                          'Reference location',
                        ),
                        hintText: l10n.tr(
                          'Ej. Porteria principal, Torre A piso 2',
                          'Ex. Main gate, Tower A floor 2',
                        ),
                        prefixIcon: const Icon(Icons.place_outlined),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),
              _FormCard(
                title: l10n.tr('Evidencias fotograficas', 'Photo evidence'),
                subtitle: l10n.tr(
                  'Adjunta hasta 3 imagenes para respaldar el reporte.',
                  'Attach up to 3 images to support the report.',
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    SizedBox(
                      height: 108,
                      child: ListView.separated(
                        scrollDirection: Axis.horizontal,
                        itemCount: _imagenes.length + 1,
                        separatorBuilder: (_, __) => const SizedBox(width: 12),
                        itemBuilder: (BuildContext context, int index) {
                          if (index == _imagenes.length) {
                            final canAdd = _imagenes.length < 3;
                            return InkWell(
                              onTap: canAdd ? _seleccionarFuente : null,
                              borderRadius: BorderRadius.circular(18),
                              child: Ink(
                                width: 96,
                                decoration: BoxDecoration(
                                  color: const Color(0xFFF8FAFC),
                                  borderRadius: BorderRadius.circular(18),
                                  border: Border.all(
                                    color: canAdd
                                        ? theme.primary.withValues(alpha: 0.2)
                                        : const Color(0xFFE2E8F0),
                                  ),
                                ),
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: <Widget>[
                                    Icon(
                                      Icons.add_a_photo_outlined,
                                      color: canAdd
                                          ? theme.primary
                                          : AppColors.textSecondary,
                                    ),
                                    const SizedBox(height: 10),
                                    Text(
                                      canAdd
                                          ? l10n.tr('Agregar', 'Add')
                                          : l10n.tr('Limite', 'Limit'),
                                      style: Theme.of(context)
                                          .textTheme
                                          .bodySmall
                                          ?.copyWith(
                                            color: canAdd
                                                ? theme.primary
                                                : AppColors.textSecondary,
                                            fontWeight: FontWeight.w700,
                                          ),
                                    ),
                                  ],
                                ),
                              ),
                            );
                          }

                          final image = _imagenes[index];
                          return Stack(
                            children: <Widget>[
                              ClipRRect(
                                borderRadius: BorderRadius.circular(18),
                                child: Image.file(
                                  File(image.path),
                                  width: 108,
                                  height: 108,
                                  fit: BoxFit.cover,
                                ),
                              ),
                              Positioned(
                                top: 8,
                                right: 8,
                                child: InkWell(
                                  onTap: () {
                                    setState(() {
                                      _imagenes.removeAt(index);
                                    });
                                  },
                                  borderRadius: BorderRadius.circular(999),
                                  child: Ink(
                                    padding: const EdgeInsets.all(6),
                                    decoration: const BoxDecoration(
                                      shape: BoxShape.circle,
                                      color: Colors.black54,
                                    ),
                                    child: const Icon(
                                      Icons.close_rounded,
                                      color: Colors.white,
                                      size: 16,
                                    ),
                                  ),
                                ),
                              ),
                            ],
                          );
                        },
                      ),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      l10n.tr(
                        'Seleccionadas: ${_imagenes.length}/3',
                        'Selected: ${_imagenes.length}/3',
                      ),
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppColors.textSecondary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: provider.isCreating ? null : _submit,
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size.fromHeight(56),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                  child: provider.isCreating
                      ? const SizedBox(
                          height: 22,
                          width: 22,
                          child: CircularProgressIndicator(
                            strokeWidth: 2.4,
                            color: Colors.white,
                          ),
                        )
                      : Text(l10n.tr('Reportar incidente', 'Report incident')),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

String _categoryLabel(String value, AppLocalizations l10n) {
  switch (value) {
    case 'SEGURIDAD':
      return l10n.tr('Seguridad', 'Security');
    case 'CONVIVENCIA':
      return l10n.tr('Convivencia', 'Community');
    case 'INFRAESTRUCTURA':
      return l10n.tr('Infraestructura', 'Infrastructure');
    case 'EMERGENCIA':
      return l10n.tr('Emergencia', 'Emergency');
    default:
      return value;
  }
}

class _FormCard extends StatelessWidget {
  const _FormCard({
    required this.title,
    required this.subtitle,
    required this.child,
  });

  final String title;
  final String subtitle;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: theme.surface,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: theme.primary.withValues(alpha: 0.08)),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: theme.primary.withValues(alpha: 0.07),
            blurRadius: 22,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            title,
            style: Theme.of(
              context,
            ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 6),
          Text(
            subtitle,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: AppColors.textSecondary,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 20),
          child,
        ],
      ),
    );
  }
}
