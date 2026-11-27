import 'dart:async';
import 'dart:convert';
import 'dart:html' as html;

import 'package:flutter/material.dart';

import 'world_stage.dart';

void main() => runApp(const AlkaffApp());

/// API dibaca same-origin lewat proxy `/alkaff/api/` pada serve.py, sehingga
/// theater bisa dipakai di `alkaff...` maupun `alkaf...` tanpa CORS khusus.
/// Bisa dioverride lewat query string untuk pengujian lokal:
/// ?api=http://127.0.0.1:8071/alkaff/api&control=http://127.0.0.1:8085/alkaff/control
const String _defaultApiBase = '/alkaff/api';
const String _defaultControlBase = '/alkaff/control';
const Size _stageSize = Size(1600, 900);
const String _consoleSource = 'namlah-alkaff-console';
const List<String> _consoleOrigins = [
  'https://app.lokal.or.id',
  'http://localhost:8085',
];

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
  /// Narasi audio bahasa Indonesia. Tidak ada subtitle mengambang.
  /// Path sudah mengikuti hasil build Flutter Web: source `assets/audio/...`
  /// disalin ke `build/web/assets/assets/audio/...`.
  static const Map<String, String> _narration = {
    'boot': 'assets/assets/audio/narasi_boot.mp3',
    'scan': 'assets/assets/audio/narasi_scan.mp3',
    'mix': 'assets/assets/audio/narasi_mix.mp3',
    'analyze': 'assets/assets/audio/narasi_analyze.mp3',
    'result': 'assets/assets/audio/narasi_result.mp3',
  };

  late final AnimationController _pulse;
  late final html.AudioElement _narrationAudio;
  String? _currentNarration;
  late final TextEditingController _keywordController;
  late String _apiBase;
  late String _controlBase;
  late String _controlChannel;
  late String _keyword;
  late bool _showControls;
  late bool _split;
  bool _autoPaused = false;

  String _scene = 'boot';
  String _status = 'MENYIAPKAN';
  String _themeName = '';
  String _cta = 'QUOTE';
  String _notes = '';
  String _limitation =
      'Notes adalah gambaran keluarga, bukan komposisi resmi pabrik.';
  List<dynamic> _products = const [];
  String _chatUser = '';
  String _chatText = '';
  String _chatTime = '';
  String? _error;
  final List<Timer> _timers = [];
  Timer? _controlTimer;
  int _controlCursor = -1;
  late final html.EventListener _consoleListener;
  String _consoleOrigin = _consoleOrigins.first;

  @override
  void initState() {
    super.initState();
    final params = Uri.base.queryParameters;
    _apiBase = params['api'] ?? _defaultApiBase;
    _controlBase = params['control'] ?? _defaultControlBase;
    _controlChannel = params['channel'] ?? 'live';
    _keyword = params['keyword'] ?? 'kopi dingin';
    _showControls = params['controls'] == '1';
    _split = params['mode'] == 'split';
    _keywordController = TextEditingController(text: _keyword);
    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 6),
    )..repeat();
    _narrationAudio = html.AudioElement()
      ..preload = 'auto'
      ..autoplay = true;
    _consoleListener = (event) => _onConsoleMessage(event);
    html.window.addEventListener('message', _consoleListener);
    // Bentuk cursor segera setelah widget hidup agar perintah yang dikirim
    // host tidak dianggap "perintah lama" saat poll pertama.
    _pollControl();
    _controlTimer = Timer.periodic(
      const Duration(milliseconds: 1200),
      (_) => _pollControl(),
    );
    _boot();
  }

  @override
  void dispose() {
    html.window.removeEventListener('message', _consoleListener);
    _controlTimer?.cancel();
    for (final timer in _timers) {
      timer.cancel();
    }
    _narrationAudio.pause();
    _narrationAudio.src = '';
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

  Future<void> _postJson(String url, Map<String, dynamic> body) async {
    final response = await html.HttpRequest.request(
      url,
      method: 'POST',
      requestHeaders: {'Content-Type': 'application/json'},
      sendData: jsonEncode(body),
    );
    final status = response.status ?? 0;
    if (status >= 400) {
      throw StateError('HTTP $status dari $url');
    }
  }

  Future<void> _pollControl() async {
    final encodedChannel = Uri.encodeComponent(_controlChannel);
    final uri = Uri.parse(
      '$_controlBase?channel=$encodedChannel&since=$_controlCursor&limit=40',
    );
    try {
      final response = await html.HttpRequest.request(uri.toString(), method: 'GET');
      if (response.status != 200) return;
      final decoded = jsonDecode(response.responseText ?? '{}');
      if (decoded is! Map) return;
      final data = Map<String, dynamic>.from(decoded);
      final cursor = data['cursor'];
      if (cursor is int) _controlCursor = cursor;
      final commands = data['commands'];
      if (commands is! List) return;
      for (final raw in commands) {
        if (raw is! Map) continue;
        final item = Map<String, dynamic>.from(raw);
        _applyCommand(
          '${item['command'] ?? ''}',
          item['payload'] is Map
              ? Map<String, dynamic>.from(item['payload'] as Map)
              : <String, dynamic>{},
        );
      }
    } catch (_) {
      // Bus kontrol belum tersedia — theater tetap berjalan dengan scene lokal.
    }
  }

  void _onConsoleMessage(html.Event event) {
    if (event is! html.MessageEvent) return;
    if (!_consoleOrigins.contains(event.origin)) return;
    _consoleOrigin = event.origin;

    Map<String, dynamic> message;
    try {
      final data = event.data;
      if (data is String) {
        message = Map<String, dynamic>.from(jsonDecode(data) as Map);
      } else if (data is Map) {
        message = Map<String, dynamic>.from(data);
      } else {
        return;
      }
    } catch (_) {
      return;
    }
    if (message['source'] != _consoleSource) return;

    final command = '${message['command'] ?? ''}';
    final payload = message['payload'] is Map
        ? Map<String, dynamic>.from(message['payload'] as Map)
        : <String, dynamic>{};
    _applyCommand(command, payload);
  }

  /// Dipakai baik oleh pesan postMessage lokal maupun polling bus kontrol.
  void _applyCommand(String command, Map<String, dynamic> payload) {
    switch (command) {
      case 'keyword':
        final text = '${payload['keyword'] ?? ''}'.trim();
        if (text.isNotEmpty) {
          _keywordController.text = text;
          _keyword = text;
          _rerun();
        }
        break;
      case 'scene':
        _cutScene('${payload['scene'] ?? 'boot'}');
        break;
      case 'play':
        _autoPaused = false;
        _startScenes();
        break;
      case 'reset':
        _autoPaused = false;
        _rerun();
        break;
      case 'split':
        setState(() {
          _split = payload['enabled'] is bool ? payload['enabled'] as bool : !_split;
        });
        break;
      case 'chat':
        final user = '${payload['username'] ?? ''}'.trim();
        final text = '${payload['comment'] ?? ''}'.trim();
        final clock = DateTime.now().toString().split(' ').last.substring(0, 8);
        setState(() {
          _chatUser = user;
          _chatText = text;
          _chatTime = clock;
        });
        if (text.isNotEmpty) {
          _keywordController.text = text;
          _keyword = text;
          _rerun();
        }
        break;
      case 'clearChat':
        setState(() {
          _chatUser = '';
          _chatText = '';
          _chatTime = '';
        });
        break;
    }
  }

  void _cutScene(String scene) {
    // Perintah sutradara manual menghentikan auto-sequence, termasuk bila
    // perintah datang sebelum katalog selesai dimuat.
    _autoPaused = true;
    for (final timer in _timers) {
      timer.cancel();
    }
    _timers.clear();
    String status;
    switch (scene) {
      case 'scan':
        status = 'MEMINDAI';
        break;
      case 'mix':
        status = 'MENCOCOKKAN';
        break;
      case 'analyze':
        status = 'MENGANALISIS';
        break;
      case 'result':
        status = 'READY';
        break;
      default:
        scene = 'boot';
        status = 'MENYIAPKAN';
    }
    _setScene(scene, status);
  }

  void _postState() {
    final payload = jsonEncode({
      'source': 'alkaff-app',
      'type': 'alkaff:state',
      'scene': _scene,
      'status': _status,
      'theme': _themeName,
      'cta': _cta,
      'products': _products.length,
      'split': _split,
      'chat': {
        'username': _chatUser,
        'comment': _chatText,
        'time': _chatTime,
      },
    });
    html.window.postMessage(payload, _consoleOrigin);

    // Publikasikan status ke bus kontrol agar konsol tanpa iframe bisa
    // menampilkan scene/tema tanpa bergantung pada jendela yang sama.
    final channel = Uri.encodeComponent(_controlChannel);
    unawaited(_postJson('$_controlBase/state?channel=$channel', {
      'channel': _controlChannel,
      'source': 'alkaff-app',
      'scene': _scene,
      'status': _status,
      'theme': _themeName,
      'cta': _cta,
      'products': _products.length,
      'split': _split,
      'chat': {
        'username': _chatUser,
        'comment': _chatText,
        'time': _chatTime,
      },
    }).catchError((_) {}));
  }

  /// Putar narasi scene dari asset lokal. Autoplay browser bisa ditolak sampai
  /// ada gesture pengguna; kegagalan diabaikan agar theater tetap berjalan.
  void _playNarration(String scene) {
    final src = _narration[scene];
    if (src == null) return;
    if (_currentNarration != src) {
      _narrationAudio.src = src;
      _currentNarration = src;
    }
    _narrationAudio.currentTime = 0;
    _narrationAudio.play().catchError((_) {});
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
    _postState();
  }

  void _setScene(String scene, String status) {
    if (!mounted) return;
    setState(() {
      _scene = scene;
      _status = status;
    });
    _playNarration(scene);
    _postState();
  }

  void _startScenes() {
    if (_autoPaused) return;
    for (final timer in _timers) {
      timer.cancel();
    }
    _timers.clear();
    _setScene('boot', 'MENYIAPKAN');
    _timers.add(Timer(const Duration(milliseconds: 900), () {
      _setScene('scan', 'MEMINDAI');
    }));
    _timers.add(Timer(const Duration(milliseconds: 2400), () {
      _setScene('mix', 'MENCOCOKKAN');
    }));
    _timers.add(Timer(const Duration(milliseconds: 3900), () {
      _setScene('analyze', 'MENGANALISIS');
    }));
    _timers.add(Timer(const Duration(milliseconds: 5400), () {
      _setScene('result', 'READY');
    }));
  }

  Future<void> _rerun() async {
    final next = _keywordController.text.trim();
    if (next.isEmpty) return;
    _autoPaused = false;
    for (final timer in _timers) {
      timer.cancel();
    }
    _timers.clear();
    setState(() {
      _keyword = next;
      _scene = 'boot';
      _status = 'MENGAMBIL DATA';
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
        WorldStage(
          scene: _scene,
          status: _status,
          themeName: _themeName,
          cta: _cta,
          notes: _notes,
          limitation: _limitation,
          error: _error ?? '',
          chatUser: _chatUser,
          chatText: _chatText,
          chatTime: _chatTime,
          products: _products,
          motion: _pulse,
        ),
        if (_showControls) _controlDeck(),
      ],
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
