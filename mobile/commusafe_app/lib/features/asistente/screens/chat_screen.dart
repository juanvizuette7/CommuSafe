import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/constants/app_constants.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/services/api_service.dart';
import '../../../core/theme/app_theme.dart';
import '../models/mensaje_model.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<MensajeModel> _mensajes = <MensajeModel>[
    MensajeModel(
      contenido:
          'Hola, soy CommuBot, el asistente virtual de Remansos del Norte. ¿En qué puedo ayudarte?',
      esDelUsuario: false,
      timestamp: DateTime.now(),
      modo: 'fallback',
    ),
  ];

  bool _enviando = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final l10n = AppLocalizations.of(context);
    if (_mensajes.length == 1 && !_mensajes.first.esDelUsuario) {
      _mensajes[0] = MensajeModel(
        contenido: _welcomeText(l10n),
        esDelUsuario: false,
        timestamp: _mensajes.first.timestamp,
        modo: _mensajes.first.modo,
      );
    }
  }

  String _welcomeText(AppLocalizations l10n) {
    return l10n.tr(
      'Hola, soy CommuBot, el asistente virtual de Remansos del Norte. ¿En qué puedo ayudarte?',
      'Hi, I am CommuBot, the virtual assistant for Remansos del Norte. How can I help you?',
    );
  }

  List<String> _suggestions(AppLocalizations l10n) {
    return <String>[
      l10n.tr('Horarios de areas comunes', 'Common area schedules'),
      l10n.tr('¿Cómo reporto un incidente?', 'How do I report an incident?'),
      l10n.tr('Normas de convivencia', 'Community rules'),
      l10n.tr('Contactos de la administración', 'Administration contacts'),
    ];
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) {
        return;
      }
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent + 140,
        duration: const Duration(milliseconds: 260),
        curve: Curves.easeOutCubic,
      );
    });
  }

  List<Map<String, String>> _historialReciente() {
    return _mensajes
        .where((mensaje) => mensaje.contenido.trim().isNotEmpty)
        .toList()
        .reversed
        .take(8)
        .toList()
        .reversed
        .map(
          (mensaje) => <String, String>{
            'rol': mensaje.esDelUsuario ? 'usuario' : 'asistente',
            'contenido': mensaje.contenido,
          },
        )
        .toList();
  }

  Future<void> _sendMessage([String? forcedText]) async {
    final l10n = AppLocalizations.of(context);
    final text = (forcedText ?? _controller.text).trim();
    if (text.isEmpty || _enviando) {
      return;
    }

    final historial = _historialReciente();
    setState(() {
      _mensajes.add(
        MensajeModel(
          contenido: text,
          esDelUsuario: true,
          timestamp: DateTime.now(),
        ),
      );
      _enviando = true;
      _controller.clear();
    });
    _scrollToBottom();

    try {
      final response = await ApiService.post<Map<String, dynamic>>(
        AppConstants.chatEndpoint,
        data: <String, dynamic>{'mensaje': text, 'historial': historial},
      ).timeout(const Duration(seconds: 8));
      final respuesta = response.data?['respuesta']?.toString().trim();
      final modo = response.data?['modo']?.toString().trim() ?? 'fallback';
      setState(() {
        _mensajes.add(
          MensajeModel(
            contenido: respuesta?.isNotEmpty == true
                ? respuesta!
                : l10n.tr(
                    'No pude generar una respuesta en este momento.',
                    'I could not generate an answer right now.',
                  ),
            esDelUsuario: false,
            timestamp: DateTime.now(),
            modo: modo,
          ),
        );
      });
    } on TimeoutException {
      setState(() {
        _mensajes.add(
          MensajeModel(
            contenido:
                '${l10n.tr('El asistente tardo demasiado en responder.', 'The assistant took too long to respond.')} ${_respuestaLocal(text, l10n)}',
            esDelUsuario: false,
            timestamp: DateTime.now(),
            modo: 'fallback',
          ),
        );
      });
    } on DioException catch (error) {
      final networkError = _isNetworkError(error);
      final detail = error.response?.data is Map<String, dynamic>
          ? (error.response!.data as Map<String, dynamic>)['detail']?.toString()
          : null;
      setState(() {
        _mensajes.add(
          MensajeModel(
            contenido: networkError
                ? '${l10n.tr('No pude conectarme con el backend.', 'I could not connect to the backend.')} ${_respuestaLocal(text, l10n)}'
                : detail?.trim().isNotEmpty == true
                ? detail!
                : l10n.tr(
                    'No pude conectarme con el asistente. Intenta nuevamente en unos segundos.',
                    'I could not connect to the assistant. Try again in a few seconds.',
                  ),
            esDelUsuario: false,
            timestamp: DateTime.now(),
            modo: 'fallback',
          ),
        );
      });
    } catch (_) {
      setState(() {
        _mensajes.add(
          MensajeModel(
            contenido: l10n.tr(
              'No pude procesar tu consulta. Verifica la conexion e intenta otra vez.',
              'I could not process your question. Check the connection and try again.',
            ),
            esDelUsuario: false,
            timestamp: DateTime.now(),
            modo: 'fallback',
          ),
        );
      });
    } finally {
      if (mounted) {
        setState(() => _enviando = false);
        _scrollToBottom();
      }
    }
  }

  bool _isNetworkError(DioException error) {
    return error.response == null ||
        error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.sendTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.connectionError;
  }

  String _respuestaLocal(String mensaje, AppLocalizations l10n) {
    final texto = mensaje.toLowerCase();

    if (texto.contains('horario') ||
        texto.contains('área') ||
        texto.contains('area') ||
        texto.contains('zonas comunes')) {
      return l10n.tr(
        'Recuerda que las areas comunes funcionan de 6:00 a. m. a 10:00 p. m.',
        'Common areas are usually available from 6:00 a.m. to 10:00 p.m.',
      );
    }
    if (texto.contains('emergencia') ||
        texto.contains('urgencia') ||
        texto.contains('incendio') ||
        texto.contains('ambulancia')) {
      return l10n.tr(
        'Si hay una emergencia inminente, llama directamente a los servicios de emergencia y avisa a porteria.',
        'If there is an immediate emergency, call emergency services directly and notify the gatehouse.',
      );
    }
    if (texto.contains('como reporto') ||
        texto.contains('como puedo reportar') ||
        texto.contains('reportar un incidente') ||
        texto.contains('crear incidente') ||
        texto.contains('nuevo incidente') ||
        texto.contains('hacer un reporte')) {
      return l10n.tr(
        'Para reportar un incidente dentro de esta app: 1. Abre la pestaña Incidentes. 2. Toca Nuevo. 3. Escribe un titulo claro y elige la categoria. 4. Describe que paso y agrega la ubicacion. 5. Adjunta hasta 3 fotos si tienes evidencia. 6. Toca Reportar incidente. Luego abre el detalle para ver estado, evidencias e historial.',
        'To report an incident in this app: 1. Open the Incidents tab. 2. Tap New. 3. Enter a clear title and choose the category. 4. Describe what happened and add the location. 5. Attach up to 3 photos if you have evidence. 6. Tap Report incident. Then open the detail view to track status, evidence and history.',
      );
    }
    if (texto.contains('estado') ||
        texto.contains('seguimiento') ||
        texto.contains('historial') ||
        texto.contains('avance')) {
      return l10n.tr(
        'Para revisar el avance, entra a Incidentes y toca el reporte. Alli veras el estado actual, las evidencias y el historial de cambios con comentarios de vigilancia o administracion.',
        'To review progress, open Incidents and tap the report. You will see the current status, evidence and change history with comments from security or administration.',
      );
    }
    if (texto.contains('incidente') || texto.contains('reporte')) {
      return l10n.tr(
        'En Incidentes puedes crear reportes y consultar su seguimiento. Para reportar, toca Nuevo, completa categoria, descripcion, ubicacion y evidencias, y luego envia el caso.',
        'In Incidents you can create reports and track them. To report, tap New, complete category, description, location and evidence, then submit the case.',
      );
    }
    if (texto.contains('convivencia') ||
        texto.contains('norma') ||
        texto.contains('ruido') ||
        texto.contains('mascota')) {
      return l10n.tr(
        'Las normas basicas incluyen respetar horarios de descanso, cuidar zonas comunes y reportar situaciones de convivencia desde CommuSafe.',
        'Basic rules include respecting quiet hours, taking care of common areas and reporting coexistence issues from CommuSafe.',
      );
    }
    if (texto.contains('administración') ||
        texto.contains('administracion') ||
        texto.contains('cuota') ||
        texto.contains('pago')) {
      return l10n.tr(
        'Para valores de cuotas, cartera o tramites especificos debes contactar a la administracion del conjunto.',
        'For fees, balances or specific procedures, contact the residential administration.',
      );
    }

    return l10n.tr(
      'Verifica que el backend este encendido y vuelve a intentarlo.',
      'Check that the backend is running and try again.',
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);
    final l10n = AppLocalizations.of(context);
    final showSuggestions = _mensajes
        .where((mensaje) => mensaje.esDelUsuario)
        .isEmpty;
    final ultimoModo = _mensajes
        .where((mensaje) => !mensaje.esDelUsuario && mensaje.modo != null)
        .last
        .modo;

    return Scaffold(
      backgroundColor: theme.background,
      appBar: AppBar(
        titleSpacing: 12,
        title: Row(
          children: <Widget>[
            Container(
              height: 42,
              width: 42,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.white.withValues(alpha: 0.14),
              ),
              child: const Icon(Icons.smart_toy_rounded, color: Colors.white),
            ),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  'CommuBot',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                Text(
                  l10n.tr('Asistente Virtual', 'Virtual Assistant'),
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: Colors.white.withValues(alpha: 0.76),
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
      body: Column(
        children: <Widget>[
          _AiModeIndicator(modo: ultimoModo),
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              physics: const BouncingScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(16, 18, 16, 18),
              itemCount: _mensajes.length + (_enviando ? 1 : 0),
              itemBuilder: (BuildContext context, int index) {
                if (_enviando && index == _mensajes.length) {
                  return const _BotTypingBubble();
                }

                final mensaje = _mensajes[index];
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    _ChatBubble(mensaje: mensaje),
                    if (index == 0 && showSuggestions) ...<Widget>[
                      const SizedBox(height: 12),
                      _SuggestionChips(
                        suggestions: _suggestions(l10n),
                        onSelected: _sendMessage,
                      ),
                    ],
                    const SizedBox(height: 12),
                  ],
                );
              },
            ),
          ),
          _MessageInput(
            controller: _controller,
            enabled: !_enviando,
            onSend: () => _sendMessage(),
          ),
        ],
      ),
    );
  }
}

class _AiModeIndicator extends StatelessWidget {
  const _AiModeIndicator({required this.modo});

  final String? modo;

  @override
  Widget build(BuildContext context) {
    final iaReal = modo == 'ia';
    final l10n = AppLocalizations.of(context);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 6),
      color: iaReal
          ? AppColors.success.withValues(alpha: 0.08)
          : AppColors.muted.withValues(alpha: 0.45),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: <Widget>[
          Container(
            height: 8,
            width: 8,
            decoration: BoxDecoration(
              color: iaReal ? AppColors.success : AppColors.textSecondary,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 8),
          Text(
            iaReal
                ? l10n.tr('Modo IA real', 'Real AI mode')
                : l10n.tr('Modo respuesta local', 'Local answer mode'),
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: iaReal ? AppColors.success : AppColors.textSecondary,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}

class _ChatBubble extends StatelessWidget {
  const _ChatBubble({required this.mensaje});

  final MensajeModel mensaje;

  @override
  Widget build(BuildContext context) {
    final isUser = mensaje.esDelUsuario;
    final theme = CommuSafeThemeExtension.of(context);
    final l10n = AppLocalizations.of(context);
    final time = DateFormat(
      'hh:mm a',
      l10n.isEnglish ? 'en_US' : 'es_CO',
    ).format(mensaje.timestamp);

    return Row(
      mainAxisAlignment: isUser
          ? MainAxisAlignment.end
          : MainAxisAlignment.start,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: <Widget>[
        if (!isUser) ...<Widget>[
          CircleAvatar(
            radius: 16,
            backgroundColor: theme.accent,
            child: const Icon(
              Icons.smart_toy_rounded,
              color: Colors.white,
              size: 17,
            ),
          ),
          const SizedBox(width: 8),
        ],
        Flexible(
          child: Column(
            crossAxisAlignment: isUser
                ? CrossAxisAlignment.end
                : CrossAxisAlignment.start,
            children: <Widget>[
              Container(
                constraints: const BoxConstraints(maxWidth: 310),
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 13,
                ),
                decoration: BoxDecoration(
                  color: isUser ? theme.primary : const Color(0xFFF1F5F9),
                  borderRadius: BorderRadius.only(
                    topLeft: const Radius.circular(18),
                    topRight: const Radius.circular(18),
                    bottomLeft: Radius.circular(isUser ? 18 : 4),
                    bottomRight: Radius.circular(isUser ? 4 : 18),
                  ),
                  boxShadow: <BoxShadow>[
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.05),
                      blurRadius: 16,
                      offset: const Offset(0, 8),
                    ),
                  ],
                ),
                child: Text(
                  mensaje.contenido,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: isUser ? Colors.white : AppColors.textPrimary,
                    height: 1.45,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
              const SizedBox(height: 4),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 4),
                child: Text(
                  time,
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: AppColors.textSecondary,
                    fontSize: 10,
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _BotTypingBubble extends StatefulWidget {
  const _BotTypingBubble();

  @override
  State<_BotTypingBubble> createState() => _BotTypingBubbleState();
}

class _BotTypingBubbleState extends State<_BotTypingBubble> {
  Timer? _timer;
  int _dots = 1;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(milliseconds: 420), (_) {
      if (!mounted) {
        return;
      }
      setState(() => _dots = _dots == 3 ? 1 : _dots + 1);
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);

    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: <Widget>[
        CircleAvatar(
          radius: 16,
          backgroundColor: theme.accent,
          child: const Icon(
            Icons.smart_toy_rounded,
            color: Colors.white,
            size: 17,
          ),
        ),
        const SizedBox(width: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
          decoration: BoxDecoration(
            color: const Color(0xFFF1F5F9),
            borderRadius: BorderRadius.circular(
              18,
            ).copyWith(bottomLeft: const Radius.circular(4)),
          ),
          child: AnimatedSwitcher(
            duration: const Duration(milliseconds: 180),
            child: Text(
              '.' * _dots,
              key: ValueKey<int>(_dots),
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: theme.primary,
                fontWeight: FontWeight.w900,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _SuggestionChips extends StatelessWidget {
  const _SuggestionChips({required this.suggestions, required this.onSelected});

  final List<String> suggestions;
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: suggestions
          .map(
            (suggestion) => ActionChip(
              label: Text(suggestion),
              avatar: Icon(Icons.bolt_rounded, size: 16, color: theme.accent),
              onPressed: () => onSelected(suggestion),
              backgroundColor: Colors.white,
              side: BorderSide(color: theme.primary.withValues(alpha: 0.14)),
              labelStyle: TextStyle(
                color: theme.primary,
                fontWeight: FontWeight.w700,
              ),
            ),
          )
          .toList(),
    );
  }
}

class _MessageInput extends StatefulWidget {
  const _MessageInput({
    required this.controller,
    required this.enabled,
    required this.onSend,
  });

  final TextEditingController controller;
  final bool enabled;
  final VoidCallback onSend;

  @override
  State<_MessageInput> createState() => _MessageInputState();
}

class _MessageInputState extends State<_MessageInput> {
  bool _hasText = false;

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_syncTextState);
  }

  @override
  void didUpdateWidget(covariant _MessageInput oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.controller != widget.controller) {
      oldWidget.controller.removeListener(_syncTextState);
      widget.controller.addListener(_syncTextState);
      _syncTextState();
    }
  }

  @override
  void dispose() {
    widget.controller.removeListener(_syncTextState);
    super.dispose();
  }

  void _syncTextState() {
    final hasText = widget.controller.text.trim().isNotEmpty;
    if (hasText != _hasText) {
      setState(() => _hasText = hasText);
    }
  }

  @override
  Widget build(BuildContext context) {
    final canSend = widget.enabled && _hasText;
    final theme = CommuSafeThemeExtension.of(context);
    final l10n = AppLocalizations.of(context);

    return SafeArea(
      top: false,
      child: Container(
        padding: const EdgeInsets.fromLTRB(14, 10, 14, 14),
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: <BoxShadow>[
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.06),
              blurRadius: 20,
              offset: const Offset(0, -8),
            ),
          ],
        ),
        child: Row(
          children: <Widget>[
            Expanded(
              child: TextField(
                controller: widget.controller,
                enabled: widget.enabled,
                minLines: 1,
                maxLines: 4,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) {
                  if (canSend) {
                    widget.onSend();
                  }
                },
                decoration: InputDecoration(
                  hintText: l10n.tr(
                    'Escribe tu consulta...',
                    'Write your question...',
                  ),
                  prefixIcon: const Icon(Icons.chat_bubble_outline_rounded),
                ),
              ),
            ),
            const SizedBox(width: 10),
            AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              height: 52,
              width: 52,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: canSend ? theme.primary : AppColors.muted,
              ),
              child: IconButton(
                onPressed: canSend ? widget.onSend : null,
                icon: const Icon(Icons.arrow_upward_rounded),
                color: canSend ? Colors.white : AppColors.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
