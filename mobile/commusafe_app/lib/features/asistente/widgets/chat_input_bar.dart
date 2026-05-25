import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';

class ChatInputBar extends StatefulWidget {
  const ChatInputBar({
    super.key,
    required this.controller,
    required this.enabled,
    required this.onSend,
  });

  final TextEditingController controller;
  final bool enabled;
  final ValueChanged<String> onSend;

  @override
  State<ChatInputBar> createState() => _ChatInputBarState();
}

class _ChatInputBarState extends State<ChatInputBar> {
  bool _hasText = false;

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_sync);
  }

  @override
  void didUpdateWidget(covariant ChatInputBar oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.controller != widget.controller) {
      oldWidget.controller.removeListener(_sync);
      widget.controller.addListener(_sync);
      _sync();
    }
  }

  @override
  void dispose() {
    widget.controller.removeListener(_sync);
    super.dispose();
  }

  void _sync() {
    final hasText = widget.controller.text.trim().isNotEmpty;
    if (hasText != _hasText) {
      setState(() => _hasText = hasText);
    }
  }

  void _submit() {
    final text = widget.controller.text.trim();
    if (!widget.enabled || text.isEmpty) {
      return;
    }
    widget.controller.clear();
    widget.onSend(text);
  }

  @override
  Widget build(BuildContext context) {
    final theme = CommuSafeThemeExtension.of(context);
    final canSend = widget.enabled && _hasText;
    final panelColor = Color.lerp(
      const Color(0xFF070B13),
      theme.primary,
      0.10,
    )!;
    final inputColor = Color.lerp(
      const Color(0xFF101827),
      theme.secondary,
      0.18,
    )!;

    return SafeArea(
      top: false,
      child: Container(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
        decoration: BoxDecoration(
          color: panelColor.withValues(alpha: 0.98),
          border: Border(
            top: BorderSide(color: theme.accent.withValues(alpha: 0.24)),
          ),
          boxShadow: <BoxShadow>[
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.35),
              blurRadius: 26,
              offset: const Offset(0, -12),
            ),
          ],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: <Widget>[
            Expanded(
              child: TextField(
                controller: widget.controller,
                enabled: widget.enabled,
                minLines: 1,
                maxLines: 5,
                textInputAction: TextInputAction.newline,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                ),
                decoration: InputDecoration(
                  hintText: 'Pregunta sobre Remansos del Norte o CommuSafe...',
                  hintStyle: TextStyle(
                    color: Colors.white.withValues(alpha: 0.42),
                  ),
                  filled: true,
                  fillColor: inputColor,
                  prefixIcon: Icon(
                    Icons.auto_awesome_rounded,
                    color: theme.accent,
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(22),
                    borderSide: BorderSide(
                      color: theme.primary.withValues(alpha: 0.26),
                    ),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(22),
                    borderSide: BorderSide(color: theme.accent, width: 1.6),
                  ),
                  disabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(22),
                    borderSide: BorderSide(
                      color: theme.primary.withValues(alpha: 0.16),
                    ),
                  ),
                ),
                onSubmitted: (_) {
                  if (canSend) {
                    _submit();
                  }
                },
              ),
            ),
            const SizedBox(width: 10),
            AnimatedScale(
              duration: const Duration(milliseconds: 180),
              scale: canSend ? 1 : 0.92,
              child: Container(
                height: 54,
                width: 54,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: canSend
                      ? LinearGradient(
                          colors: <Color>[theme.accent, theme.primary],
                        )
                      : null,
                  color: canSend ? null : Colors.white.withValues(alpha: 0.10),
                  boxShadow: canSend
                      ? <BoxShadow>[
                          BoxShadow(
                            color: theme.accent.withValues(alpha: 0.26),
                            blurRadius: 18,
                            offset: const Offset(0, 9),
                          ),
                        ]
                      : null,
                ),
                child: IconButton(
                  onPressed: canSend ? _submit : null,
                  icon: const Icon(Icons.arrow_upward_rounded),
                  color: canSend ? Colors.white : Colors.white38,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
