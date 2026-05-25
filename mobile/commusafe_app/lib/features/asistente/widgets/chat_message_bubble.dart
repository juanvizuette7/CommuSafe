import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/theme/app_theme.dart';
import '../models/mensaje_model.dart';

class ChatMessageBubble extends StatelessWidget {
  const ChatMessageBubble({super.key, required this.mensaje});

  final MensajeModel mensaje;

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);
    final isUser = mensaje.esDelUsuario;
    final time = DateFormat('hh:mm a', 'es_CO').format(mensaje.fechaCreacion);
    final bubbleText = _limpiarTextoVisual(mensaje.contenido);

    return TweenAnimationBuilder<double>(
      duration: const Duration(milliseconds: 260),
      tween: Tween<double>(begin: 0, end: 1),
      curve: Curves.easeOutCubic,
      builder: (context, value, child) {
        return Opacity(
          opacity: value,
          child: Transform.translate(
            offset: Offset(0, 14 * (1 - value)),
            child: child,
          ),
        );
      },
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 7),
        child: Row(
          mainAxisAlignment: isUser
              ? MainAxisAlignment.end
              : MainAxisAlignment.start,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: <Widget>[
            if (!isUser) ...<Widget>[
              const _AssistantAvatar(),
              const SizedBox(width: 10),
            ],
            Flexible(
              child: Column(
                crossAxisAlignment: isUser
                    ? CrossAxisAlignment.end
                    : CrossAxisAlignment.start,
                children: <Widget>[
                  Container(
                    constraints: const BoxConstraints(maxWidth: 680),
                    padding: const EdgeInsets.symmetric(
                      horizontal: 17,
                      vertical: 14,
                    ),
                    decoration: BoxDecoration(
                      gradient: isUser
                          ? LinearGradient(
                              colors: <Color>[
                                theme.primary,
                                Color.lerp(theme.primary, theme.accent, 0.38)!,
                              ],
                            )
                          : null,
                      color: isUser
                          ? null
                          : Color.lerp(
                              const Color(0xFF111827),
                              theme.secondary,
                              0.20,
                            ),
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(22),
                        topRight: const Radius.circular(22),
                        bottomLeft: Radius.circular(isUser ? 22 : 6),
                        bottomRight: Radius.circular(isUser ? 6 : 22),
                      ),
                      border: Border.all(
                        color: isUser
                            ? theme.accent.withValues(alpha: 0.42)
                            : theme.primary.withValues(alpha: 0.20),
                      ),
                      boxShadow: <BoxShadow>[
                        BoxShadow(
                          color: (isUser ? theme.primary : Colors.black)
                              .withValues(alpha: isUser ? 0.18 : 0.24),
                          blurRadius: 22,
                          offset: const Offset(0, 12),
                        ),
                      ],
                    ),
                    child: SelectableText(
                      bubbleText,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Colors.white.withValues(
                          alpha: isUser ? 1 : 0.92,
                        ),
                        height: 1.55,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  const SizedBox(height: 5),
                  Text(
                    time,
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                      color: Colors.white.withValues(alpha: 0.42),
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AssistantAvatar extends StatelessWidget {
  const _AssistantAvatar();

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);
    return Container(
      height: 34,
      width: 34,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: LinearGradient(colors: <Color>[theme.primary, theme.accent]),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: theme.accent.withValues(alpha: 0.26),
            blurRadius: 14,
            offset: const Offset(0, 7),
          ),
        ],
      ),
      child: const Icon(Icons.smart_toy_rounded, size: 18, color: Colors.white),
    );
  }
}

String _limpiarTextoVisual(String texto) {
  return texto
      .replaceAll(RegExp(r'[*_]{2,}'), '')
      .replaceAll(RegExp(r'^\s*#{1,6}\s*', multiLine: true), '')
      .replaceAll(RegExp(r'\n{3,}'), '\n\n')
      .trim();
}
