import 'package:flutter/material.dart';

import 'reward_bottle.dart';

/// Presenter robot mekanis di atas meja QC.
///
/// Ini mesin, bukan sosok manusia. Mulut, kedip, dan lengan digerakkan dari
/// status bicara theater; tidak ada teks melayang dan tidak ada klaim produk.
class RobotPresenter extends StatelessWidget {
  const RobotPresenter({
    super.key,
    required this.mouth,
    required this.action,
    required this.speaking,
    required this.blink,
    this.bottleType = '',
    this.bottleTier = '',
    this.bottlePhoto = '',
    this.bottleName = '',
    this.assetVersion = '1',
  });

  /// 0 = tertutup, 1 = terbuka penuh.
  final double mouth;
  /// idle | scan | mix | qc | pour | point
  final String action;
  final bool speaking;
  final bool blink;
  final String bottleType;
  final String bottleTier;
  final String bottlePhoto;
  final String bottleName;
  final String assetVersion;

  @override
  Widget build(BuildContext context) {
    return Positioned(
      right: 92,
      bottom: 118,
      child: IgnorePointer(
        child: Stack(
          children: [
            CustomPaint(
              size: const Size(360, 300),
              painter: _RobotPainter(
                mouth: mouth,
                action: action,
                speaking: speaking,
                blink: blink,
              ),
            ),
            if (bottleType == 'rollon' ||
                bottleType == 'spray' ||
                bottleType == 'usap')
              Positioned(
                right: bottleType == 'spray' ? -4.0 : (bottleType == 'usap' ? 8.0 : 14.0),
                bottom: bottleType == 'spray' ? 70.0 : (bottleType == 'usap' ? 112.0 : 96.0),
                child: RewardBottle(
                  type: bottleType,
                  tier: bottleTier,
                  photoUrl: bottlePhoto,
                  name: bottleName,
                  assetVersion: assetVersion,
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _RobotPainter extends CustomPainter {
  const _RobotPainter({
    required this.mouth,
    required this.action,
    required this.speaking,
    required this.blink,
  });

  final double mouth;
  final String action;
  final bool speaking;
  final bool blink;

  static const _metal = Color(0xFF9DAAA4);
  static const _metalDark = Color(0xFF3B4642);
  static const _amber = Color(0xFFD8A24D);
  static const _green = Color(0xFF8FD8B4);

  @override
  void paint(Canvas canvas, Size size) {
    final m = mouth.clamp(0.0, 1.0);
    final steel = Paint()
      ..shader = const LinearGradient(
        colors: [Color(0xFFD3DCD7), _metal, Color(0xFF66736D)],
        stops: [0, 0.45, 1],
      ).createShader(const Rect.fromLTWH(110, 90, 140, 110));

    _shadow(canvas);
    _arms(canvas, m);
    _pedestal(canvas, steel);
    _chest(canvas, steel);
    _head(canvas, steel, m);
    _antenna(canvas);
  }

  void _shadow(Canvas canvas) {
    canvas.drawOval(
      Rect.fromCenter(center: const Offset(180, 286), width: 190, height: 24),
      Paint()..color = const Color(0x88070504),
    );
  }

  void _pedestal(Canvas canvas, Paint steel) {
    final base = Paint()..color = const Color(0xFF202824);
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(108, 256, 144, 32),
        const Radius.circular(10),
      ),
      base,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(118, 250, 124, 12),
        const Radius.circular(6),
      ),
      steel,
    );
    final neck = Paint()..color = _metalDark;
    canvas.drawRect(const Rect.fromLTWH(166, 214, 28, 44), neck);
    canvas.drawLine(
      const Offset(170, 222),
      const Offset(190, 222),
      Paint()
        ..color = const Color(0x66D8E4DD)
        ..strokeWidth = 2,
    );
  }

  void _chest(Canvas canvas, Paint steel) {
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(126, 190, 108, 62),
        const Radius.circular(12),
      ),
      steel,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(136, 200, 88, 40),
        const Radius.circular(8),
      ),
      Paint()..color = const Color(0xFF1C2722),
    );
    canvas.drawCircle(
      const Offset(155, 220),
      8,
      Paint()
        ..color = speaking ? _amber : const Color(0xFF4E5D56)
        ..strokeWidth = 2
        ..style = PaintingStyle.stroke,
    );
    canvas.drawCircle(
      const Offset(155, 220),
      3,
      Paint()..color = speaking ? const Color(0xFFF4C979) : const Color(0xFF6C7C74),
    );
    for (var i = 0; i < 4; i++) {
      canvas.drawLine(
        Offset(176 + i * 10, 212),
        Offset(176 + i * 10, 229),
        Paint()
          ..color = i < (speaking ? 4 : 1) ? _green : const Color(0xFF3D4B45)
          ..strokeWidth = 3
          ..strokeCap = StrokeCap.round,
      );
    }
    canvas.drawCircle(
      const Offset(116, 198),
      3,
      Paint()..color = const Color(0xFF2A332F),
    );
    canvas.drawCircle(
      const Offset(244, 198),
      3,
      Paint()..color = const Color(0xFF2A332F),
    );
  }

  void _head(Canvas canvas, Paint steel, double m) {
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(106, 78, 148, 112),
        const Radius.circular(26),
      ),
      steel,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        const Rect.fromLTWH(114, 86, 132, 86),
        const Radius.circular(20),
      ),
      Paint()..color = const Color(0xFF24302B),
    );

    // Panel atas: dua baut dan garis ventilasi.
    final bolt = Paint()..color = const Color(0xFF66736D);
    canvas.drawCircle(const Offset(124, 98), 3, bolt);
    canvas.drawCircle(const Offset(236, 98), 3, bolt);
    for (var i = 0; i < 3; i++) {
      canvas.drawLine(
        Offset(164 + i * 12, 94),
        Offset(164 + i * 12, 102),
        Paint()
          ..color = const Color(0xFF4B5A53)
          ..strokeWidth = 2,
      );
    }

    _eyes(canvas);
    _jaw(canvas, m);
  }

  void _eyes(Canvas canvas) {
    for (final x in [148.0, 212.0]) {
      if (blink) {
        canvas.drawLine(
          Offset(x - 11, 130),
          Offset(x + 11, 130),
          Paint()
            ..color = _amber
            ..strokeWidth = 4
            ..strokeCap = StrokeCap.round,
        );
      } else {
        canvas.drawCircle(
          Offset(x, 130),
          11,
          Paint()..color = const Color(0x5548322C),
        );
        canvas.drawCircle(
          Offset(x, 130),
          7,
          Paint()..color = speaking ? const Color(0xFFF3C77D) : _amber,
        );
        canvas.drawCircle(
          Offset(x - 2, 128),
          2,
          Paint()..color = const Color(0xFFFFF3D8),
        );
      }
    }
  }

  void _jaw(Canvas canvas, double m) {
    final drop = m * 16;
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(144, 156 + drop, 72, 26),
        const Radius.circular(8),
      ),
      Paint()..color = const Color(0xFF8E9B95),
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(150, 159 + drop, 60, 18),
        const Radius.circular(6),
      ),
      Paint()..color = const Color(0xFF120D08),
    );
    if (m > 0.08) {
      for (var i = 0; i < 3; i++) {
        canvas.drawLine(
          Offset(158 + i * 22, 164 + drop),
          Offset(172 + i * 22, 164 + drop),
          Paint()
            ..color = const Color(0xCCE0B679)
            ..strokeWidth = 2
            ..strokeCap = StrokeCap.round,
        );
      }
    }
    canvas.drawLine(
      const Offset(146, 152),
      const Offset(214, 152),
      Paint()
        ..color = const Color(0x88D8E4DD)
        ..strokeWidth = 2,
    );
  }

  void _antenna(Canvas canvas) {
    canvas.drawLine(
      const Offset(180, 78),
      const Offset(180, 54),
      Paint()
        ..color = _metalDark
        ..strokeWidth = 5
        ..strokeCap = StrokeCap.round,
    );
    canvas.drawCircle(
      const Offset(180, 48),
      8,
      Paint()..color = const Color(0x5548322C),
    );
    canvas.drawCircle(
      const Offset(180, 48),
      4.5,
      Paint()..color = speaking ? const Color(0xFFF3C77D) : _green,
    );
  }

  void _arms(Canvas canvas, double m) {
    final left = _jointColor();
    final right = _jointColor();
    Offset l1, l2, r1, r2;

    switch (action) {
      case 'point':
        l1 = const Offset(104, 210);
        l2 = const Offset(66, 238);
        r1 = const Offset(256, 208);
        r2 = const Offset(336, 176);
        break;
      case 'pour':
        l1 = const Offset(104, 212);
        l2 = const Offset(72, 244);
        r1 = const Offset(256, 206);
        r2 = const Offset(318, 140);
        break;
      case 'scan':
        l1 = const Offset(104, 212);
        l2 = const Offset(78, 224);
        r1 = const Offset(256, 208);
        r2 = const Offset(322, 190);
        break;
      case 'mix':
        l1 = const Offset(104, 206);
        l2 = const Offset(48, 172);
        r1 = const Offset(256, 206);
        r2 = const Offset(312, 172);
        break;
      case 'qc':
        l1 = const Offset(104, 212);
        l2 = const Offset(70, 232);
        r1 = const Offset(256, 208);
        r2 = const Offset(308, 224);
        break;
      default:
        l1 = const Offset(104, 214);
        l2 = const Offset(74, 248);
        r1 = const Offset(256, 214);
        r2 = const Offset(286, 248);
    }

    final sway = m * 6;
    _arm(canvas, const Offset(122, 198), l1, l2 + Offset(0, sway), left);
    _arm(canvas, const Offset(238, 198), r1, r2 - Offset(0, sway), right);

    if (action == 'scan') {
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          const Rect.fromLTWH(316, 182, 24, 16),
          const Radius.circular(4),
        ),
        Paint()..color = const Color(0xFF2B3B34),
      );
      canvas.drawLine(
        const Offset(320, 190),
        const Offset(336, 190),
        Paint()
          ..color = _green
          ..strokeWidth = 3
          ..strokeCap = StrokeCap.round,
      );
    }
    if (action == 'pour') {
      canvas.drawCircle(
        const Offset(322, 156),
        3,
        Paint()..color = const Color(0xFFD89A44),
      );
      canvas.drawCircle(
        const Offset(324, 168),
        2,
        Paint()..color = const Color(0xFFC98C3A),
      );
    }
  }

  Paint _jointColor() => Paint()
    ..color = _metalDark
    ..strokeWidth = 13
    ..strokeCap = StrokeCap.round
    ..strokeJoin = StrokeJoin.round;

  void _arm(Canvas canvas, Offset shoulder, Offset elbow, Offset hand, Paint paint) {
    canvas.drawLine(shoulder, elbow, paint);
    canvas.drawLine(elbow, hand, paint);
    canvas.drawCircle(
      elbow,
      7,
      Paint()..color = const Color(0xFF6E7C75),
    );
    canvas.drawCircle(
      hand,
      6,
      Paint()..color = _metal,
    );
    canvas.drawCircle(
      hand,
      3,
      Paint()..color = const Color(0xFF3A453F),
    );
  }

  @override
  bool shouldRepaint(covariant _RobotPainter oldDelegate) {
    return oldDelegate.mouth != mouth ||
        oldDelegate.action != action ||
        oldDelegate.speaking != speaking ||
        oldDelegate.blink != blink;
  }
}
