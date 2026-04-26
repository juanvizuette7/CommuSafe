import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/theme/app_theme.dart';

class ContactosEmergenciaScreen extends StatelessWidget {
  const ContactosEmergenciaScreen({super.key});

  static const List<_EmergencyContact> _contacts = <_EmergencyContact>[
    _EmergencyContact(
      title: 'Policía Nacional',
      phone: '112',
      icon: Icons.local_police_rounded,
      color: Color(0xFF991B1B),
    ),
    _EmergencyContact(
      title: 'Bomberos',
      phone: '119',
      icon: Icons.local_fire_department_rounded,
      color: Color(0xFFF97316),
    ),
    _EmergencyContact(
      title: 'Ambulancia',
      phone: '132',
      icon: Icons.emergency_rounded,
      color: Color(0xFFE11D48),
    ),
    _EmergencyContact(
      title: 'Hospital',
      phone: '6015551003',
      icon: Icons.local_hospital_rounded,
      color: Color(0xFF7C3AED),
    ),
    _EmergencyContact(
      title: 'Administración',
      phone: '6015551002',
      icon: Icons.apartment_rounded,
      color: Color(0xFF2563EB),
    ),
    _EmergencyContact(
      title: 'Portería',
      phone: '6015551001',
      icon: Icons.shield_rounded,
      color: Color(0xFF065F46),
    ),
  ];

  Future<void> _call(BuildContext context, String phone) async {
    final uri = Uri(scheme: 'tel', path: phone);
    final launched = await launchUrl(uri);
    if (!launched && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No fue posible iniciar la llamada.'),
          backgroundColor: AppColors.danger,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Contactos de emergencia')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(18, 18, 18, 28),
        children: <Widget>[
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFFFEF3C7),
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: const Color(0xFFF59E0B)),
            ),
            child: Row(
              children: <Widget>[
                Container(
                  height: 42,
                  width: 42,
                  decoration: const BoxDecoration(
                    color: Color(0xFFF59E0B),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.warning_amber_rounded,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'En caso de emergencia inminente, llama directamente a los servicios.',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: const Color(0xFF78350F),
                      fontWeight: FontWeight.w800,
                      height: 1.35,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 18),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: _contacts.length,
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              childAspectRatio: 0.92,
            ),
            itemBuilder: (BuildContext context, int index) {
              final contact = _contacts[index];
              return _EmergencyCard(
                contact: contact,
                onTap: () => _call(context, contact.phone),
              );
            },
          ),
        ],
      ),
    );
  }
}

class _EmergencyCard extends StatelessWidget {
  const _EmergencyCard({required this.contact, required this.onTap});

  final _EmergencyContact contact;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: contact.color,
      borderRadius: BorderRadius.circular(22),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(22),
        child: Ink(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(22),
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: <Color>[
                contact.color,
                Color.lerp(contact.color, Colors.black, 0.24)!,
              ],
            ),
            boxShadow: <BoxShadow>[
              BoxShadow(
                color: contact.color.withValues(alpha: 0.25),
                blurRadius: 20,
                offset: const Offset(0, 12),
              ),
            ],
          ),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Container(
                  height: 52,
                  width: 52,
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.18),
                    borderRadius: BorderRadius.circular(18),
                  ),
                  child: Icon(contact.icon, color: Colors.white, size: 30),
                ),
                const Spacer(),
                Text(
                  contact.title,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.w900,
                    height: 1.15,
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  children: <Widget>[
                    const Icon(
                      Icons.call_rounded,
                      color: Colors.white,
                      size: 17,
                    ),
                    const SizedBox(width: 6),
                    Flexible(
                      child: Text(
                        contact.phone,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Colors.white.withValues(alpha: 0.90),
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _EmergencyContact {
  const _EmergencyContact({
    required this.title,
    required this.phone,
    required this.icon,
    required this.color,
  });

  final String title;
  final String phone;
  final IconData icon;
  final Color color;
}
