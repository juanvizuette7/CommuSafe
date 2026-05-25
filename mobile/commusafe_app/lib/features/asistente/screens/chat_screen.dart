import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/conversacion_model.dart';
import '../providers/asistente_provider.dart';
import '../widgets/assistant_empty_state.dart';
import '../widgets/chat_input_bar.dart';
import '../widgets/chat_message_bubble.dart';
import '../widgets/conversation_sidebar.dart';
import '../widgets/typing_indicator.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  bool _loaded = false;
  int _lastMessageCount = 0;
  bool _lastSending = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_loaded) {
      return;
    }
    _loaded = true;
    Future<void>.microtask(
      context.read<AsistenteProvider>().cargarConversaciones,
    );
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
        duration: const Duration(milliseconds: 320),
        curve: Curves.easeOutCubic,
      );
    });
  }

  Future<void> _confirmDelete(
    BuildContext context,
    ConversacionModel conversacion,
  ) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          backgroundColor: const Color(0xFF0F172A),
          title: const Text(
            'Eliminar conversación',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900),
          ),
          content: Text(
            'Se eliminará definitivamente "${conversacion.titulo}" y todos sus mensajes.',
            style: const TextStyle(color: Color(0xFFCBD5E1)),
          ),
          actions: <Widget>[
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(false),
              child: const Text('Cancelar'),
            ),
            FilledButton(
              style: FilledButton.styleFrom(
                backgroundColor: const Color(0xFFE94560),
              ),
              onPressed: () => Navigator.of(dialogContext).pop(true),
              child: const Text('Eliminar'),
            ),
          ],
        );
      },
    );

    if (confirmed == true && context.mounted) {
      await context.read<AsistenteProvider>().eliminarConversacion(
        conversacion.id,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AsistenteProvider>(
      builder: (context, provider, _) {
        if (_lastMessageCount != provider.mensajes.length ||
            _lastSending != provider.isSending) {
          _lastMessageCount = provider.mensajes.length;
          _lastSending = provider.isSending;
          _scrollToBottom();
        }

        final isWide = MediaQuery.sizeOf(context).width >= 860;
        final sidebar = ConversationSidebar(
          conversaciones: provider.conversaciones,
          activeConversationId: provider.conversacionActiva?.id,
          isLoading: provider.isLoadingConversations,
          onNewConversation: () {
            provider.nuevaConversacion();
            if (!isWide) {
              Navigator.of(context).maybePop();
            }
          },
          onSelectConversation: (conversation) async {
            await provider.seleccionarConversacion(conversation);
            if (!isWide && context.mounted) {
              Navigator.of(context).maybePop();
            }
          },
          onDeleteConversation: (conversation) =>
              _confirmDelete(context, conversation),
        );

        return Scaffold(
          backgroundColor: const Color(0xFF050812),
          drawer: isWide ? null : Drawer(width: 320, child: sidebar),
          appBar: AppBar(
            backgroundColor: const Color(0xFF050812),
            foregroundColor: Colors.white,
            leading: isWide
                ? null
                : Builder(
                    builder: (context) {
                      return IconButton(
                        icon: const Icon(Icons.menu_rounded),
                        onPressed: () => Scaffold.of(context).openDrawer(),
                      );
                    },
                  ),
            title: Row(
              children: <Widget>[
                Container(
                  height: 38,
                  width: 38,
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: LinearGradient(
                      colors: <Color>[Color(0xFF0F3460), Color(0xFFE94560)],
                    ),
                  ),
                  child: const Icon(Icons.smart_toy_rounded, size: 20),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        provider.conversacionActiva?.titulo ?? 'CommuBot',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontWeight: FontWeight.w900,
                          color: Colors.white,
                        ),
                      ),
                      Text(
                        provider.ultimoModo == 'error'
                            ? 'IA temporalmente no disponible'
                            : 'CommuBot IA · memoria persistente',
                        style: const TextStyle(
                          color: Color(0xFF94A3B8),
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            actions: <Widget>[
              IconButton(
                tooltip: 'Nueva conversación',
                onPressed: provider.nuevaConversacion,
                icon: const Icon(Icons.add_comment_rounded),
              ),
            ],
          ),
          body: Row(
            children: <Widget>[
              if (isWide) sidebar,
              Expanded(
                child: _ChatWorkspace(
                  controller: _controller,
                  scrollController: _scrollController,
                  provider: provider,
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _ChatWorkspace extends StatelessWidget {
  const _ChatWorkspace({
    required this.controller,
    required this.scrollController,
    required this.provider,
  });

  final TextEditingController controller;
  final ScrollController scrollController;
  final AsistenteProvider provider;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: RadialGradient(
          center: Alignment.topRight,
          radius: 1.2,
          colors: <Color>[Color(0xFF101A2D), Color(0xFF050812)],
        ),
      ),
      child: Column(
        children: <Widget>[
          if (provider.errorMessage != null)
            _ErrorBanner(
              message: provider.errorMessage!,
              onRetry: provider.cargarConversaciones,
            ),
          Expanded(
            child: AnimatedSwitcher(
              duration: const Duration(milliseconds: 240),
              child: provider.isLoadingMessages
                  ? const Center(
                      child: CircularProgressIndicator(
                        color: Color(0xFF60A5FA),
                      ),
                    )
                  : provider.mensajes.isEmpty
                  ? AssistantEmptyState(
                      onSuggestionSelected: provider.enviarMensaje,
                    )
                  : ListView.builder(
                      key: ValueKey<int>(provider.mensajes.length),
                      controller: scrollController,
                      physics: const BouncingScrollPhysics(),
                      padding: const EdgeInsets.fromLTRB(18, 20, 18, 28),
                      itemCount:
                          provider.mensajes.length +
                          (provider.isSending ? 1 : 0),
                      itemBuilder: (context, index) {
                        if (provider.isSending &&
                            index == provider.mensajes.length) {
                          return const Padding(
                            padding: EdgeInsets.only(top: 6),
                            child: TypingIndicator(),
                          );
                        }
                        return ChatMessageBubble(
                          mensaje: provider.mensajes[index],
                        );
                      },
                    ),
            ),
          ),
          ChatInputBar(
            controller: controller,
            enabled: !provider.isSending,
            onSend: provider.enviarMensaje,
          ),
        ],
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 12, 16, 0),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFE94560).withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: const Color(0xFFE94560).withValues(alpha: 0.35),
        ),
      ),
      child: Row(
        children: <Widget>[
          const Icon(Icons.error_outline_rounded, color: Color(0xFFE94560)),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(
                color: Color(0xFFFFCDD2),
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          TextButton(onPressed: onRetry, child: const Text('Reintentar')),
        ],
      ),
    );
  }
}
