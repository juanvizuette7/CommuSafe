import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/constants/app_constants.dart';
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
    ),
  ];

  bool _enviando = false;

  static const List<String> _sugerencias = <String>[
    'Horarios de áreas comunes',
    '¿Cómo reporto un incidente?',
    'Normas de convivencia',
    'Contactos de la administración',
  ];

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
      );
      final respuesta = response.data?['respuesta']?.toString().trim();
      setState(() {
        _mensajes.add(
          MensajeModel(
            contenido: respuesta?.isNotEmpty == true
                ? respuesta!
                : 'No pude generar una respuesta en este momento.',
            esDelUsuario: false,
            timestamp: DateTime.now(),
          ),
        );
      });
    } on DioException catch (error) {
      final detail = error.response?.data is Map<String, dynamic>
          ? (error.response!.data as Map<String, dynamic>)['detail']?.toString()
          : null;
      setState(() {
        _mensajes.add(
          MensajeModel(
            contenido: detail?.trim().isNotEmpty == true
                ? detail!
                : 'No pude conectarme con el asistente. Intenta nuevamente en unos segundos.',
            esDelUsuario: false,
            timestamp: DateTime.now(),
          ),
        );
      });
    } catch (_) {
      setState(() {
        _mensajes.add(
          MensajeModel(
            contenido:
                'No pude procesar tu consulta. Verifica la conexión e intenta otra vez.',
            esDelUsuario: false,
            timestamp: DateTime.now(),
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

  @override
  Widget build(BuildContext context) {
    final showSuggestions = _mensajes
        .where((mensaje) => mensaje.esDelUsuario)
        .isEmpty;

    return Scaffold(
      backgroundColor: AppColors.background,
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
                  'Asistente Virtual',
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
                        suggestions: _sugerencias,
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

class _ChatBubble extends StatelessWidget {
  const _ChatBubble({required this.mensaje});

  final MensajeModel mensaje;

  @override
  Widget build(BuildContext context) {
    final isUser = mensaje.esDelUsuario;
    final time = DateFormat('hh:mm a', 'es_CO').format(mensaje.timestamp);

    return Row(
      mainAxisAlignment: isUser
          ? MainAxisAlignment.end
          : MainAxisAlignment.start,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: <Widget>[
        if (!isUser) ...<Widget>[
          const CircleAvatar(
            radius: 16,
            backgroundColor: AppColors.accent,
            child: Icon(Icons.smart_toy_rounded, color: Colors.white, size: 17),
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
                  color: isUser ? AppColors.primary : const Color(0xFFF1F5F9),
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
    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: <Widget>[
        const CircleAvatar(
          radius: 16,
          backgroundColor: AppColors.accent,
          child: Icon(Icons.smart_toy_rounded, color: Colors.white, size: 17),
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
                color: AppColors.primary,
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
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: suggestions
          .map(
            (suggestion) => ActionChip(
              label: Text(suggestion),
              avatar: const Icon(Icons.bolt_rounded, size: 16),
              onPressed: () => onSelected(suggestion),
              backgroundColor: Colors.white,
              side: const BorderSide(color: Color(0xFFE2E8F0)),
              labelStyle: const TextStyle(fontWeight: FontWeight.w700),
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
                decoration: const InputDecoration(
                  hintText: 'Escribe tu consulta...',
                  prefixIcon: Icon(Icons.chat_bubble_outline_rounded),
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
                color: canSend ? AppColors.primary : AppColors.muted,
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
