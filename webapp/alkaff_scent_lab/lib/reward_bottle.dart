import 'package:flutter/material.dart';

/// Botol hadiah yang menempel di tangan robot.
///
/// Visual ini bukan foto produk: bila admin belum mengisi `photoUrl` di
/// allowlist, label memakai monogram ALK. Nama penonton hanya dipakai untuk
/// tier `signature` (5 poin), dan tetap berada di dalam label botol.
class RewardBottle extends StatelessWidget {
  const RewardBottle({
    super.key,
    required this.type,
    required this.tier,
    required this.photoUrl,
    required this.name,
    required this.assetVersion,
  });

  /// rollon | spray | usap
  final String type;
  /// basic | signature
  final String tier;
  final String photoUrl;
  final String name;
  final String assetVersion;

  bool get _signature => tier == 'signature';
  bool get _usap => type == 'usap';
  bool get _spray => type == 'spray';

  Size get _size {
    if (_usap) return const Size(132, 108);
    if (_spray) return const Size(156, 208);
    return const Size(112, 156);
  }

  @override
  Widget build(BuildContext context) {
    final size = _size;
    final labelTop = _usap ? 34.0 : (_spray ? 96.0 : 78.0);
    final labelWidth = _usap ? 104.0 : (_spray ? 116.0 : 84.0);
    final labelHeight = _usap ? 54.0 : (_spray ? 76.0 : 54.0);
    final photoSize = _signature ? 48.0 : 28.0;

    return SizedBox(
      width: size.width,
      height: size.height,
      child: Stack(
        children: [
          Positioned.fill(
            child: CustomPaint(
              painter: _BottlePainter(type: type, signature: _signature),
            ),
          ),
          Positioned(
            left: (size.width - labelWidth) / 2,
            top: labelTop,
            width: labelWidth,
            height: labelHeight,
            child: _Label(
              photoUrl: photoUrl,
              photoSize: photoSize,
              name: _signature ? name : '',
              type: type,
              assetVersion: assetVersion,
            ),
          ),
        ],
      ),
    );
  }
}

class _Label extends StatelessWidget {
  const _Label({
    required this.photoUrl,
    required this.photoSize,
    required this.name,
    required this.type,
    required this.assetVersion,
  });

  final String photoUrl;
  final double photoSize;
  final String name;
  final String type;
  final String assetVersion;

  @override
  Widget build(BuildContext context) {
    final hasPhoto = photoUrl.isNotEmpty;
    final cleanName = name.trim();
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 3),
      decoration: BoxDecoration(
        color: const Color(0xFFF4E8C8),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: const Color(0xFF7A5B2A), width: 1),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        mainAxisSize: MainAxisSize.min,
        children: [
          if (hasPhoto)
            ClipRRect(
              borderRadius: BorderRadius.circular(2),
              child: Image.network(
                photoUrl.contains('?') ? '$photoUrl&v=$assetVersion' : '$photoUrl?v=$assetVersion',
                width: photoSize,
                height: photoSize,
                fit: BoxFit.cover,
                filterQuality: FilterQuality.none,
                errorBuilder: (_, __, ___) => const _Monogram(),
              ),
            )
          else
            const _Monogram(size: 24),
          if (cleanName.isNotEmpty) ...[
            const SizedBox(height: 2),
            Text(
              cleanName,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: Color(0xFF1B2A22),
                fontSize: 9,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
          Text(
            type == 'rollon' ? 'ROLL-ON' : type.toUpperCase(),
            maxLines: 1,
            style: const TextStyle(
              color: Color(0xFF5B4726),
              fontSize: 7,
              letterSpacing: 1,
            ),
          ),
        ],
      ),
    );
  }
}

class _Monogram extends StatelessWidget {
  const _Monogram({this.size = 24});

  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: const Color(0xFF0C2F21),
        borderRadius: BorderRadius.circular(2),
      ),
      child: const Text(
        'ALK',
        style: TextStyle(
          color: Color(0xFFD8A24D),
          fontSize: 8,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}

class _BottlePainter extends CustomPainter {
  const _BottlePainter({required this.type, required this.signature});

  final String type;
  final bool signature;

  static const _glass = Color(0xCC0C2F21);
  static const _glassLight = Color(0xCC1D6B4F);
  static const _gold = Color(0xFFD8A24D);
  static const _metal = Color(0xFFB9C4BF);

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;
    final glass = Paint()
      ..shader = LinearGradient(
        colors: [_glassLight, _glass],
        stops: const [0, 1],
      ).createShader(Rect.fromLTWH(0, 0, w, h));
    final edge = Paint()
      ..color = const Color(0x88D8E4DD)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;

    if (type == 'usap') {
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(8, 14, w - 16, h - 30),
          const Radius.circular(10),
        ),
        Paint()..color = const Color(0xFF123E2E),
      );
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(12, 18, w - 24, h - 38),
          const Radius.circular(8),
        ),
        glass,
      );
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(8, 14, w - 16, h - 30),
          const Radius.circular(10),
        ),
        edge,
      );
      canvas.drawLine(
        Offset(w * 0.34, 14),
        Offset(w * 0.66, 14),
        Paint()
          ..color = _gold
          ..strokeWidth = 3,
      );
      return;
    }

    if (type == 'spray') {
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(w * 0.28, 8, w * 0.44, 34),
          const Radius.circular(6),
        ),
        Paint()..color = signature ? _gold : _metal,
      );
      canvas.drawRect(
        Rect.fromLTWH(w * 0.44, 42, w * 0.12, 12),
        Paint()..color = const Color(0xFF6E7B75),
      );
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(14, 54, w - 28, h - 66),
          const Radius.circular(16),
        ),
        glass,
      );
      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromLTWH(14, 54, w - 28, h - 66),
          const Radius.circular(16),
        ),
        edge,
      );
      if (signature) {
        canvas.drawLine(
          Offset(w * 0.30, h - 8),
          Offset(w * 0.70, h - 8),
          Paint()
            ..color = _gold
            ..strokeWidth = 3
            ..strokeCap = StrokeCap.round,
        );
      }
      return;
    }

    // roll-on: badan kecil dan bola logam di atasnya.
    canvas.drawCircle(
      Offset(w / 2, 18),
      12,
      Paint()..color = _metal,
    );
    canvas.drawRect(
      Rect.fromLTWH(w * 0.38, 30, w * 0.24, 14),
      Paint()..color = const Color(0xFF5C6D65),
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(18, 44, w - 36, h - 56),
        const Radius.circular(12),
      ),
      glass,
    );
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(18, 44, w - 36, h - 56),
        const Radius.circular(12),
      ),
      edge,
    );
  }

  @override
  bool shouldRepaint(covariant _BottlePainter oldDelegate) {
    return oldDelegate.type != type || oldDelegate.signature != signature;
  }
}
