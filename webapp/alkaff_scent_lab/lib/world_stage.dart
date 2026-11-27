import 'dart:math' as math;

import 'package:flutter/material.dart';

/// Dunia pabrik maklon Alkaff: plate CG + parallax ringan + UI diegetik.
///
/// Semua teks menempel pada benda fisik (papan dinding, monitor QC, kertas
/// batch). Tidak ada panel melayang dan tidak ada sosok manusia.
class WorldStage extends StatelessWidget {
  const WorldStage({
    super.key,
    required this.scene,
    required this.status,
    required this.themeName,
    required this.cta,
    required this.notes,
    required this.limitation,
    required this.error,
    required this.chatUser,
    required this.chatText,
    required this.chatTime,
    required this.products,
    required this.motion,
    required this.assetVersion,
  });

  static const List<String> _scenes = ['boot', 'scan', 'mix', 'analyze', 'result'];

  final String scene;
  final String status;
  final String themeName;
  final String cta;
  final String notes;
  final String limitation;
  final String error;
  final String chatUser;
  final String chatText;
  final String chatTime;
  final List<dynamic> products;
  final Animation<double> motion;
  final String assetVersion;

  @override
  Widget build(BuildContext context) {
    final key = _scenes.contains(scene) ? scene : 'boot';
    return AnimatedBuilder(
      animation: motion,
      builder: (context, _) {
        final t = motion.value * math.pi * 2;
        final dx = math.sin(t) * 11;
        final dy = math.cos(t * 0.7) * 5;
        final scale = 1.055 + 0.008 * math.sin(t);
        return Stack(
          children: [
            Positioned.fill(
              child: ClipRect(
                child: Transform.scale(
                  scale: scale,
                  child: Transform.translate(
                    offset: Offset(dx, dy),
                    child: Image.network(
                      'assets/assets/world/scene_$key.jpg?v=$assetVersion',
                      fit: BoxFit.cover,
                      width: double.infinity,
                      height: double.infinity,
                      gaplessPlayback: true,
                    ),
                  ),
                ),
              ),
            ),
            Positioned.fill(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      const Color(0x33070B09),
                      const Color(0x00000000),
                      const Color(0x55050907),
                    ],
                    stops: const [0, 0.45, 1],
                  ),
                ),
              ),
            ),
            _wallPlaque(),
            _qcMonitor(),
            _batchSheet(),
          ],
        );
      },
    );
  }

  /// Papan logam di dinding: identitas + status + pagar simulasi.
  Widget _wallPlaque() {
    return Positioned(
      left: 46,
      top: 40,
      child: Container(
        width: 430,
        padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 16),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(8),
          gradient: const LinearGradient(
            colors: [Color(0xFFBFC8C4), Color(0xFF77827E), Color(0xFFD6DDD9)],
            stops: [0, 0.5, 1],
          ),
          border: Border.all(color: const Color(0xFF3C4642), width: 3),
          boxShadow: const [
            BoxShadow(color: Color(0x99000000), blurRadius: 22, offset: Offset(0, 10)),
          ],
        ),
        child: Stack(
          children: [
            const Positioned(
              right: 6,
              top: 6,
              child: CircleAvatar(radius: 4, backgroundColor: Color(0xFF4A5551)),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'ALKAFF · MAKLON HALL',
                  style: TextStyle(
                    color: Color(0xFF17211D),
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 2.4,
                  ),
                ),
                const SizedBox(height: 4),
                const Text(
                  'VISUALISASI PROSES · SIMULASI',
                  style: TextStyle(
                    color: Color(0xFF3F4B46),
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.6,
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Container(
                      width: 9,
                      height: 9,
                      decoration: const BoxDecoration(
                        color: Color(0xFF2F7D5E),
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      status.isEmpty ? 'MENYIAPKAN' : status,
                      style: const TextStyle(
                        color: Color(0xFF22302A),
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.2,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  /// Monitor QC yang menempel di meja/dinding pabrik.
  Widget _qcMonitor() {
    return Positioned(
      left: 980,
      top: 350,
      child: Container(
        width: 470,
        height: 244,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(14),
          color: const Color(0xFF1A211E),
          border: Border.all(color: const Color(0xFF8C9893), width: 4),
          boxShadow: const [
            BoxShadow(color: Color(0xCC000000), blurRadius: 30, offset: Offset(0, 14)),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.forum_outlined, color: Color(0xFFD7B36B), size: 16),
                const SizedBox(width: 8),
                const Text(
                  'LIVE CHAT · SIMULASI',
                  style: TextStyle(
                    color: Color(0xFFD7B36B),
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.4,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              chatUser.isEmpty ? 'Menunggu viewer' : '@$chatUser',
              style: const TextStyle(
                color: Color(0xFFF2F7F4),
                fontSize: 18,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              chatText.isEmpty ? 'Komen viewer akan tampil di monitor ini.' : chatText,
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                color: Color(0xFFD5E4DD),
                fontSize: 13,
                height: 1.4,
              ),
            ),
            const Spacer(),
            Text(
              chatTime.isEmpty ? '—' : chatTime,
              style: const TextStyle(color: Color(0xFF7C9489), fontSize: 10),
            ),
          ],
        ),
      ),
    );
  }

  /// Kertas batch yang dijepit di stasiun; menggantikan kartu produk melayang.
  Widget _batchSheet() {
    final rows = products.isEmpty
        ? const [
            {
              'ref': '—',
              'name': 'Menunggu katalog',
              'family': 'Odoo nml',
            }
          ]
        : products.take(2).toList();
    return Positioned(
      left: 620,
      top: 648,
      child: Transform.rotate(
        angle: -0.012,
        child: Container(
          width: 380,
          height: 206,
          padding: const EdgeInsets.fromLTRB(20, 24, 20, 14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(6),
            color: const Color(0xFFEDE6D6),
            border: Border.all(color: const Color(0xFF9AA39C), width: 2),
            boxShadow: const [
              BoxShadow(color: Color(0xB3000000), blurRadius: 26, offset: Offset(0, 12)),
            ],
          ),
          child: Stack(
            children: [
              Positioned(
                left: 150,
                top: -16,
                child: Container(
                  width: 80,
                  height: 26,
                  decoration: BoxDecoration(
                    color: const Color(0xFF7B8580),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: const Color(0xFF3E4844), width: 2),
                  ),
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'BATCH SHEET · PROSES',
                    style: TextStyle(
                      color: Color(0xFF5A655F),
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 1.6,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    themeName.isEmpty ? 'Menunggu tema' : themeName,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Color(0xFF16221C),
                      fontSize: 21,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  Text(
                    notes.isEmpty ? 'notes: —' : 'notes: $notes',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Color(0xFF4B5B53), fontSize: 11),
                  ),
                  const SizedBox(height: 8),
                  for (final raw in rows)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 3),
                      child: Text(
                        '${raw['ref'] ?? ''} · ${raw['name'] ?? ''} · ${raw['family'] ?? ''}',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: Color(0xFF2A3831),
                          fontSize: 10,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  const Spacer(),
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
                        decoration: BoxDecoration(
                          color: const Color(0xFF1C2A23),
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(
                          'CTA · $cta',
                          style: const TextStyle(
                            color: Color(0xFFD7B36B),
                            fontSize: 10,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 5),
                  Text(
                    error.isNotEmpty ? 'ERROR · $error' : limitation,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: Color(0xFF6C766F), fontSize: 8, height: 1.3),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
