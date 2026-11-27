import 'dart:async';
import 'dart:convert';
import 'dart:html' as html;
import 'dart:math' as math;

import 'package:flutter/material.dart';

void main() => runApp(const AlkaffApp());

/// API dibaca langsung dari instance Odoo `nml` yang sudah dipublish.
/// Bisa dioverride lewat query string untuk pengujian lokal:
/// ?api=http://127.0.0.1:8071/alkaff/api
const String _defaultApiBase = 'https://nml.lokal.or.id/alkaff/api';
const Size _stageSize = Size(1600, 900);

class AlkaffApp extends StatelessWidget {
  const AlkaffApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Alkaff Scent Lab',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1D8F6C),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: const LabScreen(),
    );
  }
}

class LabScreen extends StatefulWidget {
  const LabScreen({super.key});

  @override
  State<LabScreen> createState() => _LabScreenState();
}

class _LabScreenState extends State<LabScreen> with SingleTickerProviderStateMixin {
  late final AnimationController _pulse;
  late final TextEditingController _keywordController;
  late String _apiBase;
  late String _keyword;
  late bool _showControls;
  late bool _split;

  String _scene = 'boot';
  String _status = 'MENYIAPKAN';
  String _narration = 'Menyambungkan katalog Alkaff di database NML.';
  String _themeName = '';
  String _cta = 'QUOTE';
  String _notes = '';
  String _limitation =
      'Notes adalah gambaran keluarga, bukan komposisi resmi pabrik.';
  List<dynamic> _products = const [];
  String? _error;
  final List<Timer> _timers = [];

  @override
  void initState() {
    super.initState();
    final params = Uri.base.queryParameters;
    _apiBase = params['api'] ?? _defaultApiBase;
    _keyword = params['keyword'] ?? 'kopi dingin';
    _showControls = params['controls'] == '1';
    _split = params['mode'] == 'split';
    _keywordController = TextEditingController(text: _keyword);
    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 6),
    )..repeat();
    _boot();
  }

  @override
  void dispose() {
    for (final timer in _timers) {
      timer.cancel();
    }
    _pulse.dispose();
    _keywordController.dispose();
    super.dispose();
  }

  Future<Map<String, dynamic>> _getJson(String path) async {
    final uri = Uri.parse('$_apiBase$path');
    final response = await html.HttpRequest.request(
      uri.toString(),
      method: 'GET',
    );
    if (response.status != 200) {
      throw StateError('HTTP ${response.status} dari $uri');
    }
    final decoded = jsonDecode(response.responseText ?? '{}');
    if (decoded is! Map) {
      throw StateError('Respons bukan objek JSON dari $uri');
    }
    return Map<String, dynamic>.from(decoded);
  }

  Future<void> _boot() async {
    try {
      final health = await _getJson('/health');
      if (health['database'] != 'nml') {
        throw StateError('Endpoint bukan database nml');
      }
      await _loadRecommendations();
      if (!mounted) return;
      _startScenes();
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _error = '$error';
        _status = 'ERROR';
        _narration = 'Katalog belum tersedia. Periksa koneksi ke Odoo nml.';
      });
    }
  }

  Future<void> _loadRecommendations() async {
    final encoded = Uri.encodeComponent(_keyword);
    final data = await _getJson('/recommendations?keyword=$encoded&limit=3');
    final theme = data['theme'] is Map
        ? Map<String, dynamic>.from(data['theme'] as Map)
        : <String, dynamic>{};
    final limitation = data['batasan'];
    if (!mounted) return;
    setState(() {
      _themeName = '${theme['tema'] ?? 'Parfum'}';
      _cta = '${theme['ctaKeyword'] ?? 'QUOTE'}';
      _notes = '${theme['notesKunci'] ?? ''}';
      if (limitation != null) _limitation = '$limitation';
      _products = (data['products'] as List?) ?? const [];
      _error = null;
    });
  }

  void _setScene(String scene, String status, String narration) {
    if (!mounted) return;
    setState(() {
      _scene = scene;
      _status = status;
      _narration = narration;
    });
  }

  void _startScenes() {
    for (final timer in _timers) {
      timer.cancel();
    }
    _timers.clear();
    _setScene('boot', 'MENYIAPKAN', 'Menyambungkan katalog Alkaff di database NML.');
    _timers.add(Timer(const Duration(milliseconds: 900), () {
      _setScene('scan', 'MEMINDAI', 'Memindai notes aroma dari katalog Alkaff.');
    }));
    _timers.add(Timer(const Duration(milliseconds: 2400), () {
      _setScene('mix', 'MENCOCOKKAN',
          'Mencocokkan keluarga $_notes dengan tema $_themeName.');
    }));
    _timers.add(Timer(const Duration(milliseconds: 3900), () {
      _setScene('analyze', 'MENGANALISIS',
          'Menganalisis karakter aroma. Harga dan stok dicek saat LIVE.');
    }));
    _timers.add(Timer(const Duration(milliseconds: 5400), () {
      _setScene('result', 'READY',
          'Rekomendasi $_themeName siap. CTA $_cta dimulai dari penonton.');
    }));
  }

  Future<void> _rerun() async {
    final next = _keywordController.text.trim();
    if (next.isEmpty) return;
    for (final timer in _timers) {
      timer.cancel();
    }
    _timers.clear();
    setState(() {
      _keyword = next;
      _scene = 'boot';
      _status = 'MENGAMBIL DATA';
      _narration = 'Mengambil rekomendasi untuk "$next".';
      _products = const [];
    });
    try {
      await _loadRecommendations();
      if (!mounted) return;
      _startScenes();
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _error = '$error';
        _status = 'ERROR';
        _narration = 'Gagal mengambil data dari Odoo nml.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF050B09),
      body: LayoutBuilder(
        builder: (context, constraints) {
          if (_split) {
            return Column(
              children: [
                SizedBox(
                  height: constraints.maxHeight * 0.4,
                  width: double.infinity,
                  child: _cameraZone(),
                ),
                Expanded(child: _fitStage()),
              ],
            );
          }
          return Center(child: _fitStage());
        },
      ),
    );
  }

  Widget _fitStage() {
    return FittedBox(
      fit: BoxFit.contain,
      child: SizedBox(width: _stageSize.width, height: _stageSize.height, child: _stage()),
    );
  }

  Widget _cameraZone() {
    return Container(
      color: const Color(0xFF020604),
      alignment: Alignment.center,
      child: Container(
        width: 560,
        height: 150,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: const Color(0xFF3A6656), width: 2),
          color: const Color(0xFF08120E),
        ),
        child: const Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.videocam_outlined, color: Color(0xFF8FC7B1), size: 30),
            SizedBox(height: 6),
            Text(
              'ZONA KAMERA HOST',
              style: TextStyle(color: Color(0xFFE8F3EE), fontSize: 16, letterSpacing: 2),
            ),
            Text(
              'Opsional · isi dari kamera browser atau overlay OBS',
              style: TextStyle(color: Color(0xFF88A79A), fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }

  Widget _stage() {
    return Stack(
      children: [
        AnimatedBuilder(
          animation: _pulse,
          builder: (context, _) => CustomPaint(
            painter: LabPainter(scene: _scene, progress: _pulse.value),
            child: const SizedBox.expand(),
          ),
        ),
        _topPlate(),
        _bottleLabel(),
        _narrationBoard(),
        _productCards(),
        if (_showControls) _controlDeck(),
      ],
    );
  }

  Widget _topPlate() {
    return Positioned(
      left: 46,
      top: 40,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        decoration: BoxDecoration(
          color: const Color(0xE80C1A15),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0x55D7B36B)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.science_outlined, color: Color(0xFFD7B36B), size: 20),
            const SizedBox(width: 10),
            const Text(
              'ALKAFF · SCENT LAB',
              style: TextStyle(color: Color(0xFFE8F3EE), fontSize: 14, letterSpacing: 2),
            ),
            const SizedBox(width: 14),
            Text(
              _status,
              style: TextStyle(color: _status == 'ERROR' ? Colors.redAccent : Color(0xFF7ED5B2), fontSize: 13),
            ),
          ],
        ),
      ),
    );
  }

  Widget _bottleLabel() {
    return Positioned(
      left: 686,
      top: 342,
      child: Container(
        width: 228,
        height: 176,
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: const Color(0xF6F1E7DC),
          borderRadius: BorderRadius.circular(14),
          boxShadow: const [BoxShadow(color: Color(0x66000000), blurRadius: 22, offset: Offset(0, 10))],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'TEMA',
              style: TextStyle(color: Color(0xFF7A6A4F), fontSize: 11, letterSpacing: 3),
            ),
            const SizedBox(height: 8),
            Text(
              _themeName.isEmpty ? 'Menunggu tema' : _themeName,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: Color(0xFF17231D), fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              _notes.isEmpty ? 'notes: —' : 'notes: $_notes',
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: Color(0xFF4B5C52), fontSize: 12),
            ),
            const Spacer(),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: const Color(0xFF17231D),
                borderRadius: BorderRadius.circular(999),
              ),
              child: Text(
                'CTA · $_cta',
                style: const TextStyle(color: Color(0xFFD7B36B), fontSize: 12, letterSpacing: 1),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _narrationBoard() {
    return Positioned(
      right: 46,
      top: 150,
      child: Container(
        width: 300,
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: const Color(0xE80B1511),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0x44FFFFFF)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.description_outlined, color: Color(0xFFD7B36B), size: 18),
                SizedBox(width: 8),
                Text(
                  'NARASI',
                  style: TextStyle(color: Color(0xFFD7B36B), fontSize: 12, letterSpacing: 2),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              _narration,
              style: const TextStyle(color: Color(0xFFE8F3EE), fontSize: 15, height: 1.5),
            ),
            const SizedBox(height: 16),
            Text(
              _limitation,
              style: const TextStyle(color: Color(0xFF9CB4A9), fontSize: 11, height: 1.4),
            ),
            if (_error != null) ...[
              const SizedBox(height: 10),
              Text(_error!, style: const TextStyle(color: Colors.redAccent, fontSize: 11)),
            ],
          ],
        ),
      ),
    );
  }

  Widget _productCards() {
    final cards = _products.isEmpty
        ? [
            {
              'ref': '—',
              'name': 'Menunggu katalog',
              'family': 'Odoo nml',
              'notesTop': 'Periksa koneksi API',
              'notesHeart': '',
              'notesBase': '',
            }
          ]
        : _products;
    return Positioned(
      left: 180,
      right: 180,
      bottom: 34,
      height: 142,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          for (final item in cards.take(3))
            Expanded(child: _productCard(Map<String, dynamic>.from(item as Map))),
        ],
      ),
    );
  }

  Widget _productCard(Map<String, dynamic> product) {
    final notes = [
      product['notesTop'],
      product['notesHeart'],
      product['notesBase'],
    ].where((value) => value != null && '$value'.isNotEmpty).join(' · ');
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 8),
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
      decoration: BoxDecoration(
        color: const Color(0xEE0C1A15),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0x44D7B36B)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '${product['ref'] ?? ''}',
            style: const TextStyle(color: Color(0xFFD7B36B), fontSize: 12, letterSpacing: 1),
          ),
          const SizedBox(height: 4),
          Text(
            '${product['name'] ?? ''}',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: Color(0xFFF3FAF6), fontSize: 18, fontWeight: FontWeight.w600),
          ),
          Text(
            '${product['family'] ?? ''}',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: Color(0xFF8FC7B1), fontSize: 12),
          ),
          const SizedBox(height: 8),
          Text(
            notes.isEmpty ? 'notes: —' : 'notes: $notes',
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: Color(0xFFA9BFB5), fontSize: 11, height: 1.35),
          ),
        ],
      ),
    );
  }

  Widget _controlDeck() {
    return Positioned(
      left: 46,
      bottom: 196,
      child: Container(
        width: 390,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xF208120E),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0x55D7B36B)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'KONTROL HOST',
              style: TextStyle(color: Color(0xFFD7B36B), fontSize: 12, letterSpacing: 2),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _keywordController,
              onSubmitted: (_) => _rerun(),
              style: const TextStyle(color: Color(0xFFE8F3EE)),
              decoration: const InputDecoration(
                hintText: 'keyword viewer, mis. kopi dingin',
                hintStyle: TextStyle(color: Color(0xFF6E8B7E)),
                filled: true,
                fillColor: Color(0xFF102019),
                border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(10))),
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _rerun,
                icon: const Icon(Icons.play_arrow),
                label: const Text('Jalankan adegan'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class LabPainter extends CustomPainter {
  final String scene;
  final double progress;

  const LabPainter({required this.scene, required this.progress});

  @override
  void paint(Canvas canvas, Size size) {
    final width = size.width;
    final height = size.height;
    final center = Offset(width / 2, height / 2);

    canvas.drawRect(
      Offset.zero & size,
      Paint()..shader = const LinearGradient(
        colors: [Color(0xFF06100C), Color(0xFF0A1712), Color(0xFF040906)],
        stops: [0, 0.6, 1],
      ).createShader(Offset.zero & size),
    );
    _glow(canvas, center, width * 0.36, const Color(0x55285C48));
    _glow(canvas, Offset(width * 0.1, height * 0.92), width * 0.22, const Color(0x22C69643));

    final grid = Paint()..color = const Color(0x12FFFFFF)..strokeWidth = 1;
    for (double x = 0; x < width; x += 96) {
      canvas.drawLine(Offset(x, 0), Offset(x, height), grid);
    }
    for (double y = 0; y < height; y += 96) {
      canvas.drawLine(Offset(0, y), Offset(width, y), grid);
    }

    canvas.drawOval(
      Rect.fromCenter(center: Offset(width / 2, height * 0.84), width: width * 0.66, height: height * 0.16),
      Paint()..shader = const LinearGradient(
        colors: [Color(0x221E7A5C), Color(0x00050B09)],
      ).createShader(Rect.fromCenter(center: Offset(width / 2, height * 0.84), width: width * 0.66, height: height * 0.16)),
    );

    _glow(canvas, Offset(width / 2, height * 0.52), 210, const Color(0x44C6A15B));

    final bottleRect = Rect.fromCenter(center: Offset(width / 2, height * 0.52), width: 240, height: 360);
    final bottle = RRect.fromRectAndRadius(bottleRect, const Radius.circular(36));
    canvas.drawRRect(
      bottle,
      Paint()..shader = const LinearGradient(
        colors: [Color(0x33FFFFFF), Color(0x6612B48A), Color(0x22050B09)],
      ).createShader(bottleRect),
    );

    final fill = scene == 'mix' ? 0.66 : scene == 'analyze' ? 0.78 : 0.52;
    final liquidHeight = (bottleRect.height - 24) * fill;
    final liquidRect = Rect.fromLTWH(
      bottleRect.left + 12,
      bottleRect.bottom - 12 - liquidHeight,
      bottleRect.width - 24,
      liquidHeight,
    );
    canvas.save();
    canvas.clipRRect(bottle);
    canvas.drawRect(
      liquidRect,
      Paint()..shader = const LinearGradient(
        colors: [Color(0xFF1E8F6A), Color(0xFF0C3B2D)],
      ).createShader(liquidRect),
    );
    canvas.restore();

    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromCenter(center: Offset(width / 2, height * 0.52 - 212), width: 96, height: 70),
        const Radius.circular(12),
      ),
      Paint()..color = const Color(0xFFD7B36B),
    );

    for (var i = 0; i < 16; i++) {
      final phase = (progress + i / 16) % 1;
      final angle = i * 0.61 + progress * math.pi * 2;
      final radius = 70 + phase * 150;
      final particle = Offset(
        width / 2 + math.cos(angle) * radius * 0.55,
        height * 0.52 - 150 + math.sin(angle) * radius * 0.35 - phase * 70,
      );
      canvas.drawCircle(
        particle,
        2 + (1 - phase) * 3,
        Paint()..color = Color(0x33C6E8D2).withValues(alpha: 0.18 * (1 - phase)),
      );
    }

    if (scene == 'scan' || scene == 'analyze') {
      final ringRadius = 90 + ((progress * 2) % 1) * 120;
      canvas.drawCircle(
        center,
        ringRadius,
        Paint()
          ..color = const Color(0x5548E0B0)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2,
      );
    }
  }

  @override
  bool shouldRepaint(covariant LabPainter oldDelegate) =>
      oldDelegate.scene != scene || oldDelegate.progress != progress;

  void _glow(Canvas canvas, Offset center, double radius, Color color) {
    canvas.drawCircle(
      center,
      radius,
      Paint()..shader = RadialGradient(
        colors: [color, const Color(0x00000000)],
      ).createShader(Rect.fromCircle(center: center, radius: radius)),
    );
  }
}
