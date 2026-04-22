import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/theme/app_theme.dart';
import '../../../shared/widgets/section_card.dart';

class EmergenciasScreen extends StatelessWidget {
  const EmergenciasScreen({super.key});

  static const List<_EmergencyContact> _contacts = <_EmergencyContact>[
    _EmergencyContact('Portería principal', '6015551001', Icons.shield_rounded),
    _EmergencyContact('Administración', '6015551002', Icons.apartment_rounded),
    _EmergencyContact('Línea de emergencias', '123', Icons.local_hospital_rounded),
    _EmergencyContact('Policía', '112', Icons.local_police_rounded),
  ];

  Future<void> _call(String phone) async {
    final uri = Uri(scheme: 'tel', path: phone);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: <Widget>[
        SectionCard(
          title: 'Contactos de emergencia',
          subtitle: 'Accesos directos para actuar con rapidez desde la app.',
          child: Column(
            children: _contacts
                .map(
                  (contact) => Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: ListTile(
                      tileColor: const Color(0xFFF8FAFC),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                      leading: CircleAvatar(
                        backgroundColor: AppColors.danger.withValues(alpha: 0.14),
                        child: Icon(contact.icon, color: AppColors.danger),
                      ),
                      title: Text(contact.title),
                      subtitle: Text(contact.phone),
                      trailing: IconButton(
                        onPressed: () => _call(contact.phone),
                        icon: const Icon(Icons.call_rounded),
                        color: AppColors.primary,
                      ),
                    ),
                  ),
                )
                .toList(),
          ),
        ),
      ],
    );
  }
}

class _EmergencyContact {
  const _EmergencyContact(this.title, this.phone, this.icon);

  final String title;
  final String phone;
  final IconData icon;
}
