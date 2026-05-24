import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../models/conversacion_model.dart';

class ConversationSidebar extends StatelessWidget {
  const ConversationSidebar({
    super.key,
    required this.conversaciones,
    required this.activeConversationId,
    required this.isLoading,
    required this.onNewConversation,
    required this.onSelectConversation,
    required this.onDeleteConversation,
  });

  final List<ConversacionModel> conversaciones;
  final String? activeConversationId;
  final bool isLoading;
  final VoidCallback onNewConversation;
  final ValueChanged<ConversacionModel> onSelectConversation;
  final ValueChanged<ConversacionModel> onDeleteConversation;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 310,
      decoration: const BoxDecoration(
        color: Color(0xFF080D17),
        border: Border(right: BorderSide(color: Color(0xFF1E293B))),
      ),
      child: SafeArea(
        bottom: false,
        child: Column(
          children: <Widget>[
            Padding(
              padding: const EdgeInsets.fromLTRB(18, 18, 18, 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  Row(
                    children: <Widget>[
                      Container(
                        height: 42,
                        width: 42,
                        decoration: const BoxDecoration(
                          shape: BoxShape.circle,
                          gradient: LinearGradient(
                            colors: <Color>[
                              Color(0xFF0F3460),
                              Color(0xFFE94560),
                            ],
                          ),
                        ),
                        child: const Icon(
                          Icons.smart_toy_rounded,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: <Widget>[
                            Text(
                              'CommuBot',
                              style: Theme.of(context).textTheme.titleMedium
                                  ?.copyWith(
                                    color: Colors.white,
                                    fontWeight: FontWeight.w900,
                                  ),
                            ),
                            const Text(
                              'Historial conversacional',
                              style: TextStyle(
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
                  const SizedBox(height: 18),
                  ElevatedButton.icon(
                    onPressed: onNewConversation,
                    icon: const Icon(Icons.add_rounded),
                    label: const Text('Nueva conversación'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF1D4ED8),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(18),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            if (isLoading)
              const Padding(
                padding: EdgeInsets.all(20),
                child: LinearProgressIndicator(color: Color(0xFF60A5FA)),
              )
            else
              Expanded(
                child: conversaciones.isEmpty
                    ? const _EmptyConversations()
                    : ListView.separated(
                        padding: const EdgeInsets.fromLTRB(12, 4, 12, 18),
                        itemBuilder: (context, index) {
                          final conversacion = conversaciones[index];
                          return _ConversationTile(
                            conversacion: conversacion,
                            selected:
                                conversacion.id == activeConversationId,
                            onTap: () => onSelectConversation(conversacion),
                            onDelete: () => onDeleteConversation(conversacion),
                          );
                        },
                        separatorBuilder: (_, __) => const SizedBox(height: 8),
                        itemCount: conversaciones.length,
                      ),
              ),
          ],
        ),
      ),
    );
  }
}

class _ConversationTile extends StatelessWidget {
  const _ConversationTile({
    required this.conversacion,
    required this.selected,
    required this.onTap,
    required this.onDelete,
  });

  final ConversacionModel conversacion;
  final bool selected;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final date = DateFormat('d MMM · h:mm a', 'es_CO').format(
      conversacion.fechaActualizacion.toLocal(),
    );

    return Material(
      color: selected ? const Color(0xFF13233B) : Colors.transparent,
      borderRadius: BorderRadius.circular(18),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(18),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18),
            border: Border.all(
              color: selected ? const Color(0xFF2563EB) : const Color(0xFF1E293B),
            ),
          ),
          child: Row(
            children: <Widget>[
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      conversacion.titulo,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w900,
                        fontSize: 13,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      conversacion.ultimoMensaje.isEmpty
                          ? 'Sin mensajes todavía'
                          : conversacion.ultimoMensaje,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Color(0xFF94A3B8),
                        fontWeight: FontWeight.w500,
                        fontSize: 11,
                        height: 1.35,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      date,
                      style: const TextStyle(
                        color: Color(0xFF64748B),
                        fontWeight: FontWeight.w700,
                        fontSize: 10,
                      ),
                    ),
                  ],
                ),
              ),
              IconButton(
                tooltip: 'Eliminar conversación',
                onPressed: onDelete,
                icon: const Icon(Icons.delete_outline_rounded),
                color: const Color(0xFF94A3B8),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmptyConversations extends StatelessWidget {
  const _EmptyConversations();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.all(22),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: <Widget>[
          Icon(Icons.forum_outlined, color: Color(0xFF475569), size: 42),
          SizedBox(height: 12),
          Text(
            'No tienes conversaciones guardadas.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Color(0xFF94A3B8),
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }
}
