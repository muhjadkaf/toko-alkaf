import 'dart:async';
import 'dart:convert';
import 'dart:html' as html;
import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'robot_presenter.dart';
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
  /// disalin ke `build/web/assets/assets/audio/...`. Query `?v=` ditambahkan
  /// saat runtime dari `version.json` agar tablet/PC tidak memakai cache lama.
  static const Map<String, String> _narration = {
    'boot': 'assets/assets/audio/narasi_boot.mp3',
    'scan': 'assets/assets/audio/narasi_scan.mp3',
    'mix': 'assets/assets/audio/narasi_mix.mp3',
    'analyze': 'assets/assets/audio/narasi_analyze.mp3',
    'result': 'assets/assets/audio/narasi_result.mp3',
  };

  /// Teks narasi dipakai untuk memperkirakan suku kata saat menggerakkan
  /// rahang robot. Sama persis dengan tools/generate_narration.py.
  static const Map<String, String> _narrationText = {
    'boot': 'Selamat datang di Alkaff Scent Lab. Visualisasi ini menunjukkan '
        'alur maklon parfum dari penerimaan bahan hingga pengemasan.',
    'scan': 'Penerimaan bahan dimulai dari pemeriksaan kode dan kondisi '
        'kemasan. Setiap batch dicatat agar dapat ditelusuri.',
    'mix': 'Di ruang pencampuran, tangki berjaket dan pengaduk bekerja dengan '
        'kendali suhu. Skala ini menggambarkan kapasitas produksi.',
    'analyze': 'Pemeriksaan mutu dilakukan sebelum proses lanjut. Fokusnya '
        'adalah konsistensi keluarga aroma dan kesesuaian dokumen.',
    'result': 'Botol diberi label, lalu dikemas. Rekomendasi yang Anda lihat '
        'berasal dari katalog Alkaff. CTA dimulai dari penonton.',
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

  /// host = CG jadi latar, mic host dari OBS, robot mati.
  /// robot = operator yang menggerakkan dan menyuruh robot bicara.
  /// autopilot = robot mengikuti script lima adegan.
  String _presenterMode = 'autopilot';
  String _robotAction = 'idle';
  bool _speaking = false;
  bool _blink = false;
  double _mouth = 0;
  Timer? _mouthTimer;
  int _mouthTick = 0;

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
  String _assetVersion = '1';
  String? _error;

  /// Reward manual dari konsol. Token penuh hanya ada di URL PNG yang diminta
  /// theater; state yang dipublikasikan memakai `qrCodeMasked` saja.
  String _rewardId = '';
  String _rewardTier = '';
  String _rewardDelivery = '';
  String _rewardPoints = '';
  String _rewardName = '';
  String _rewardRecipe = '';
  String _rewardStatus = '';
  /// `existing_product` memakai QR produk terverifikasi. `custom_draft`
  /// hanya mengumumkan permintaan; tidak ada QR, harga, atau janji produk jadi.
  String _rewardDecision = '';
  String _draftRef = '';
  bool _draftNoticeVisible = false;
  String _draftNoticeRef = '';
  String _draftNoticeName = '';
  String _draftNoticeTheme = '';
  String _draftNoticeNotes = '';
  String _qrPngUrl = '';
  String _qrCodeMasked = '';
  int _qrWindowMs = 3000;
  bool _qrVisible = false;
  bool _qrLoading = false;
  int _qrStartedAt = 0;
  int _qrEndedAt = 0;
  /// Saat QR tampil, animasi latar dan lip-sync dimatikan sementara supaya
  /// jendela 3 detik tidak meleset karena repaint berat di browser/OBS.
  bool _stageMotionPaused = false;
  int _qrEpoch = 0;
  String _bottleType = '';
  String _bottlePhoto = '';
  String _bottleName = '';

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
    final presenter = params['presenter'] ?? '';
    if (presenter == 'host' || presenter == 'robot' || presenter == 'autopilot') {
      _presenterMode = presenter;
    }
    _keywordController = TextEditingController(text: _keyword);
    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 6),
    )..repeat();
    _narrationAudio = html.AudioElement()
      ..preload = 'auto'
      ..autoplay = true;
    _narrationAudio.onEnded.listen((_) => _stopSpeaking());
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
    _mouthTimer?.cancel();
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
      case 'presenter':
        _setPresenterMode('${payload['mode'] ?? ''}');
        break;
      case 'robot':
        final action = '${payload['action'] ?? 'idle'}';
        const allowedActions = {'idle', 'scan', 'mix', 'qc', 'pour', 'point'};
        _autoPaused = true;
        setState(() {
          _presenterMode = 'robot';
          _robotAction = allowedActions.contains(action) ? action : 'idle';
        });
        _postState();
        break;
      case 'speak':
        final text = '${payload['text'] ?? ''}'.trim();
        _speakCommand(text);
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
      case 'reward':
        _showReward(payload, replay: false);
        break;
      case 'rewardReplay':
        _showReward(payload, replay: true);
        break;
      case 'rewardClear':
        _clearReward();
        break;
      case 'rewardRevoke':
        _revokeReward(payload);
        break;
      case 'customDraft':
        _showDraftNotice(payload);
        break;
    }
  }

  void _cutScene(String scene) {
    // Perintah sutradara manual menghentikan auto-sequence, termasuk bila
    // perintah datang sebelum katalog selesai dimuat.
    _autoPaused = true;
    _qrEpoch++;
    if (_qrVisible || _qrLoading) {
      setState(() {
        _qrVisible = false;
        _qrLoading = false;
        _qrStartedAt = 0;
        _qrEndedAt = 0;
        _rewardDecision = '';
        _draftRef = '';
        _draftNoticeVisible = false;
      });
    }
    _cancelTimers();
    _resumeStageMotion();
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

  void _cancelTimers() {
    for (final timer in _timers) {
      timer.cancel();
    }
    _timers.clear();
  }

  void _pauseStageMotion() {
    if (_stageMotionPaused) return;
    _stageMotionPaused = true;
    _pulse.stop();
    _mouthTimer?.cancel();
    _mouthTimer = null;
  }

  void _resumeStageMotion() {
    if (!_stageMotionPaused) return;
    _stageMotionPaused = false;
    if (!_pulse.isAnimating) _pulse.repeat();
  }

  /// Reward ditampilkan lebih dulu sebagai botol + foto + nama (5 poin), lalu
  /// QR dimunculkan setelah PNG selesai dimuat dan hanya selama 3 detik nyata.
  void _showReward(Map<String, dynamic> payload, {required bool replay}) {
    final rewardId = '${payload['rewardId'] ?? ''}'.trim();
    if (rewardId.isEmpty) return;
    final png = '${payload['qrPngUrl'] ?? ''}'.trim();
    final parsedWindow = int.tryParse('${payload['qrWindowMs'] ?? '3000'}') ?? 3000;
    final windowMs = parsedWindow.clamp(1000, 10000);
    final tier = '${payload['tier'] ?? ''}'.trim();
    final delivery = '${payload['delivery'] ?? ''}'.trim();
    const allowedBottles = {'rollon', 'spray', 'usap'};
    final epoch = ++_qrEpoch;
    _autoPaused = true;
    _cancelTimers();
    setState(() {
      _rewardId = rewardId;
      _rewardTier = tier == 'signature' ? 'signature' : 'basic';
      _rewardDelivery = delivery;
      _rewardPoints = '${payload['points'] ?? ''}'.trim();
      _rewardRecipe = '${payload['recipeRef'] ?? ''}'.trim();
      _rewardDecision = '${payload['decisionKind'] ?? 'existing_product'}'.trim();
      _draftRef = '${payload['draftRef'] ?? ''}'.trim();
      _rewardName = _rewardTier == 'signature'
          ? '${payload['displayName'] ?? ''}'.trim()
          : '';
      _bottleType = allowedBottles.contains(delivery) ? delivery : '';
      _bottlePhoto = '${payload['photoUrl'] ?? ''}'.trim();
      _bottleName = _rewardName;
      _qrPngUrl = png;
      _qrWindowMs = windowMs;
      _qrCodeMasked = rewardId.length > 5
          ? '${rewardId.substring(rewardId.length - 5)}••••'
          : '••••';
      _qrVisible = false;
      _qrLoading = false;
      _qrStartedAt = 0;
      _qrEndedAt = 0;
      _rewardStatus = replay ? 'qr' : 'reveal';
      _scene = 'result';
      _status = replay ? 'QR' : 'REWARD';
      if (_rewardRecipe.isNotEmpty) _themeName = _rewardRecipe;
      if (_presenterMode != 'host') _robotAction = 'point';
    });
    _postState();

    // Jika decision engine salah mengirim custom draft lewat perintah reward,
    // jangan pernah menampilkan QR produk. Tampilkan kartu draft saja.
    if (_rewardDecision == 'custom_draft') {
      _showDraftNotice({
        'draftRef': _draftRef.isNotEmpty ? _draftRef : rewardId,
        'displayName': _rewardName,
        'themeRef': _rewardRecipe,
      });
      return;
    }

    if (replay) {
      _preloadQr(epoch);
      return;
    }
    _timers.add(Timer(const Duration(milliseconds: 2200), () {
      if (!mounted || epoch != _qrEpoch) return;
      _preloadQr(epoch);
    }));
  }

  void _preloadQr(int epoch) {
    if (_qrPngUrl.isEmpty) {
      _qrFailed(epoch);
      return;
    }
    setState(() => _qrLoading = true);
    final image = html.ImageElement();
    image.onLoad.listen((_) {
      if (!mounted || epoch != _qrEpoch) return;
      _startQrWindow(epoch);
    });
    image.onError.listen((_) {
      if (!mounted || epoch != _qrEpoch) return;
      _qrFailed(epoch);
    });
    image.src = _qrPngUrl;
  }

  void _qrFailed(int epoch) {
    if (!mounted || epoch != _qrEpoch) return;
    setState(() {
      _qrLoading = false;
      _qrVisible = false;
      _rewardStatus = 'qr-gagal';
      _status = 'QR TIDAK TERSEDIA';
    });
    _resumeStageMotion();
    _postState();
  }

  void _startQrWindow(int epoch) {
    if (!mounted || epoch != _qrEpoch) return;
    final started = DateTime.now().millisecondsSinceEpoch;
    setState(() {
      _qrLoading = false;
      _qrVisible = true;
      _qrStartedAt = started;
      _qrEndedAt = 0;
      _rewardStatus = 'qr';
      _scene = 'result';
      _status = 'QR';
    });
    _postState();
    _pauseStageMotion();
    // Timer Dart bisa tertunda di browser headless/OBS. Kami memakai frame
    // browser (requestAnimationFrame) supaya jendela QR benar-benar ~3 detik
    // sesuai jam dinding; setiap frame menjadwalkan frame berikutnya sampai
    // deadline tercapai. Epoch membatalkan loop bila reward diganti/cabut.
    final deadline = started + _qrWindowMs;
    void frame(num _) {
      if (!mounted || epoch != _qrEpoch) return;
      final now = DateTime.now().millisecondsSinceEpoch;
      if (now < deadline) {
        html.window.requestAnimationFrame(frame);
        return;
      }
      setState(() {
        _qrVisible = false;
        _qrEndedAt = now;
        _rewardStatus = 'done';
        _status = 'READY';
      });
      _resumeStageMotion();
      _postState();
    }
    html.window.requestAnimationFrame(frame);
  }

  void _clearReward() {
    _qrEpoch++;
    _cancelTimers();
    setState(() {
      _qrVisible = false;
      _qrLoading = false;
      _qrStartedAt = 0;
      _qrEndedAt = 0;
      _qrPngUrl = '';
      _rewardDecision = '';
      _draftRef = '';
      _draftNoticeVisible = false;
      _rewardStatus = 'done';
      _status = 'READY';
    });
    _resumeStageMotion();
    _postState();
  }

  void _revokeReward(Map<String, dynamic> payload) {
    final rewardId = '${payload['rewardId'] ?? ''}'.trim();
    if (rewardId.isNotEmpty && rewardId != _rewardId) return;
    _qrEpoch++;
    _cancelTimers();
    setState(() {
      _qrVisible = false;
      _qrLoading = false;
      _qrStartedAt = 0;
      _qrEndedAt = 0;
      _qrPngUrl = '';
      _rewardDecision = '';
      _draftRef = '';
      _draftNoticeVisible = false;
      _rewardStatus = 'revoked';
      _status = 'QR DICABUT';
    });
    _resumeStageMotion();
    _postState();
  }

  /// Custom draft sengaja TIDAK memakai QR /a/<token>: belum ada produk jadi,
  /// harga, atau URL terverifikasi. Layar hanya mengumumkan bahwa permintaan
  /// dicatat dan menunggu tinjauan admin.
  void _showDraftNotice(Map<String, dynamic> payload) {
    final ref = '${payload['draftRef'] ?? ''}'.trim();
    if (ref.isEmpty) return;
    final epoch = ++_qrEpoch;
    _autoPaused = true;
    _cancelTimers();
    _resumeStageMotion();
    setState(() {
      _qrVisible = false;
      _qrLoading = false;
      _qrStartedAt = 0;
      _qrEndedAt = 0;
      _rewardDecision = 'custom_draft';
      _draftRef = ref;
      _draftNoticeVisible = true;
      _draftNoticeRef = ref;
      _draftNoticeName = '${payload['displayName'] ?? ''}'.trim();
      _draftNoticeTheme = '${payload['themeRef'] ?? ''}'.trim();
      _draftNoticeNotes = '${payload['notesAman'] ?? ''}'.trim();
      _rewardStatus = 'draft';
      _scene = 'result';
      _status = 'DRAFT';
      if (_presenterMode != 'host') _robotAction = 'point';
    });
    _postState();
    _timers.add(Timer(const Duration(seconds: 6), () {
      if (!mounted || epoch != _qrEpoch) return;
      setState(() {
        _draftNoticeVisible = false;
        _rewardStatus = 'done';
        _status = 'READY';
      });
      _postState();
    }));
  }

  /// Ringkasan reward untuk konsol. Tidak pernah memuat token QR penuh.
  Map<String, dynamic> _rewardState() => {
    'rewardId': _rewardId,
    'rewardTier': _rewardTier,
    'rewardDelivery': _rewardDelivery,
    'rewardPoints': _rewardPoints,
    'rewardName': _rewardName,
    'rewardRecipe': _rewardRecipe,
    'rewardStatus': _rewardStatus,
    'rewardDecision': _rewardDecision,
    'draftRef': _draftRef,
    'draftNoticeVisible': _draftNoticeVisible,
    'draftNoticeRef': _draftNoticeRef,
    'qrVisible': _qrVisible,
    'qrWindowMs': _qrWindowMs,
    'qrCodeMasked': _qrCodeMasked,
    'qrStartedAt': _qrStartedAt,
    'qrEndedAt': _qrEndedAt,
    'bottleType': _bottleType,
    'bottlePhoto': _bottlePhoto,
    'bottleName': _bottleName,
  };

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
      'presenterMode': _presenterMode,
      'robotAction': _robotAction,
      'speaking': _speaking,
      ..._rewardState(),
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
      'presenterMode': _presenterMode,
      'robotAction': _robotAction,
      'speaking': _speaking,
      ..._rewardState(),
      'chat': {
        'username': _chatUser,
        'comment': _chatText,
        'time': _chatTime,
      },
    }).catchError((_) {}));
  }

  /// Ambil nomor build dari `version.json`. Nomor ini dipakai sebagai query
  /// string pada semua asset, sehingga build baru otomatis mengganti cache lama.
  Future<void> _loadVersion() async {
    try {
      // File ini di root build/web, bukan di bawah prefix /alkaff/api.
      final response = await html.HttpRequest.request('/version.json', method: 'GET');
      if (response.status != 200 || !mounted) return;
      final decoded = jsonDecode(response.responseText ?? '{}');
      if (decoded is! Map) return;
      setState(() {
        _assetVersion = '${decoded['build_number'] ?? '1'}';
        _currentNarration = null;
      });
    } catch (_) {
      // version.json opsional; theater tetap memakai fallback '1'.
    }
  }

  /// Putar narasi scene dari asset lokal. Autoplay browser bisa ditolak sampai
  /// ada gesture pengguna; kegagalan diabaikan agar theater tetap berjalan.
  void _playNarration(String scene) {
    if (_presenterMode == 'host') return;
    final base = _narration[scene];
    if (base == null) return;
    final src = '$base?v=$_assetVersion';
    if (_currentNarration != src) {
      _narrationAudio.src = src;
      _currentNarration = src;
    }
    _narrationAudio.currentTime = 0;
    _narrationAudio.play().catchError((_) {});
    _startSpeaking(_narrationText[scene] ?? '');
  }

  /// Mode host memakai CG sebagai latar dan mic host dari OBS. Robot dan
  /// narasi theater dimatikan, tetapi katalog/chat tetap jalan.
  void _setPresenterMode(String requested) {
    const modes = {'host', 'robot', 'autopilot'};
    final mode = modes.contains(requested) ? requested : 'autopilot';
    if (mode == _presenterMode) return;
    setState(() {
      _presenterMode = mode;
      if (mode == 'host') {
        _robotAction = 'idle';
        _stopSpeakingSilently();
      } else {
        _robotAction = _actionForScene(_scene);
      }
    });
    if (mode == 'host') {
      _mouthTimer?.cancel();
      _mouthTimer = null;
      _narrationAudio.pause();
    } else if (mode == 'autopilot') {
      _autoPaused = false;
      _startScenes();
      return;
    } else {
      _autoPaused = true;
    }
    _postState();
  }

  String _actionForScene(String scene) {
    switch (scene) {
      case 'scan':
        return 'scan';
      case 'mix':
        return 'mix';
      case 'analyze':
        return 'qc';
      case 'result':
        return 'pour';
      default:
        return 'idle';
    }
  }

  /// Perintah bicara manual dari konsol. Tanpa teks = narasi scene berjalan;
  /// dengan teks = Web Speech id-ID bila tersedia, rahang tetap digerakkan.
  void _speakCommand(String text) {
    _autoPaused = true;
    setState(() {
      _presenterMode = 'robot';
      _robotAction = 'point';
    });
    if (text.isEmpty) {
      _playNarration(_scene);
      _postState();
      return;
    }
    _narrationAudio.pause();
    _startSpeaking(text);
    try {
      final utterance = html.SpeechSynthesisUtterance(text)
        ..lang = 'id-ID'
        ..rate = 0.95;
      utterance.onBoundary.listen((event) {
        if (!mounted) return;
        final start = event.charIndex ?? 0;
        final chunk = start < text.length ? text.substring(start) : '';
        setState(() => _mouth = _syllables(chunk) > 0 ? 0.85 : 0.55);
      });
      utterance.onEnd.listen((_) => _stopSpeaking());
      html.window.speechSynthesis?.speak(utterance);
    } catch (_) {
      // Web Speech tidak tersedia: rahang tetap berjalan dari perkiraan suku kata.
    }
    _postState();
  }

  /// Gerakkan rahang mengikuti perkiraan suku kata. Ini bukan forced alignment,
  /// tetapi cukup untuk presenter CG stilirisasi dan tidak butuh dependency.
  void _startSpeaking(String text) {
    _mouthTimer?.cancel();
    _mouthTick = 0;
    final syllables = math.max(2, _syllables(text));
    final cycle = math.max(6, (syllables * 2.4).round());
    setState(() {
      _speaking = true;
      _mouth = 0;
    });
    _mouthTimer = Timer.periodic(const Duration(milliseconds: 70), (timer) {
      if (!mounted || !_speaking) {
        timer.cancel();
        return;
      }
      final phase = _mouthTick % cycle;
      final open = phase < cycle * 0.52;
      final level = open
          ? 0.35 + 0.65 * (0.5 + 0.5 * math.sin(_mouthTick * 0.85))
          : 0.0;
      setState(() {
        _mouth = level;
        _blink = _mouthTick % 53 == 0;
      });
      _mouthTick++;
    });
  }

  void _stopSpeaking() {
    _mouthTimer?.cancel();
    _mouthTimer = null;
    if (!mounted) return;
    setState(() {
      _speaking = false;
      _mouth = 0;
      _blink = false;
    });
    _postState();
  }

  void _stopSpeakingSilently() {
    _speaking = false;
    _mouth = 0;
    _blink = false;
  }

  int _syllables(String text) {
    final lower = text.toLowerCase();
    var count = 0;
    var inVowel = false;
    for (final codeUnit in lower.codeUnits) {
      final ch = String.fromCharCode(codeUnit);
      final vowel = 'aiueo'.contains(ch);
      if (vowel && !inVowel) count++;
      inVowel = vowel;
    }
    return count;
  }

  Future<void> _boot() async {
    await _loadVersion();
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
      if (_presenterMode != 'host') _robotAction = _actionForScene(scene);
    });
    _playNarration(scene);
    _postState();
  }

  void _startScenes() {
    if (_autoPaused) return;
    _qrEpoch++;
    if (_qrVisible || _qrLoading) {
      setState(() {
        _qrVisible = false;
        _qrLoading = false;
        _qrStartedAt = 0;
        _qrEndedAt = 0;
        _rewardDecision = '';
        _draftRef = '';
        _draftNoticeVisible = false;
      });
    }
    _cancelTimers();
    _resumeStageMotion();
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
          assetVersion: _assetVersion,
        ),
        if (_presenterMode != 'host')
          RobotPresenter(
            mouth: _mouth,
            action: _robotAction,
            speaking: _speaking,
            blink: _blink,
            bottleType: _bottleType,
            bottleTier: _rewardTier,
            bottlePhoto: _bottlePhoto,
            bottleName: _bottleName,
            assetVersion: _assetVersion,
          ),
        if (_qrVisible || _qrLoading) _rewardQrOverlay(),
        if (_draftNoticeVisible) _draftNoticeOverlay(),
        if (_showControls) _controlDeck(),
      ],
    );
  }

  /// Kartu QR bersifat diegetik: seluruh teks tercetak di kartu, tidak ada
  /// teks melayang di atas panggung. Timer 3 detik dihitung setelah PNG siap.
  Widget _rewardQrOverlay() {
    return Positioned.fill(
      child: IgnorePointer(
        child: Container(
          color: const Color(0xFFFFFFFF),
          alignment: Alignment.center,
          child: Container(
            padding: const EdgeInsets.all(22),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: const Color(0xFF0C2F21), width: 2),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  'ALKaff · QR NAMLAH',
                  style: TextStyle(
                    color: Color(0xFF0C2F21),
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 2,
                  ),
                ),
                const SizedBox(height: 14),
                if (_qrLoading)
                  const SizedBox(
                    width: 340,
                    height: 340,
                    child: Center(
                      child: CircularProgressIndicator(
                        valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF0C2F21)),
                      ),
                    ),
                  )
                else
                  SizedBox(
                    width: 340,
                    height: 340,
                    child: Image.network(
                      _qrPngUrl,
                      fit: BoxFit.contain,
                      filterQuality: FilterQuality.none,
                      errorBuilder: (_, __, ___) => const Center(
                        child: Text(
                          'QR sedang disiapkan',
                          style: TextStyle(color: Color(0xFF0C2F21), fontSize: 16),
                        ),
                      ),
                    ),
                  ),
                const SizedBox(height: 14),
                const Text(
                  'Screenshot QR ini. Buka sendiri dari galeri.',
                  style: TextStyle(
                    color: Color(0xFF0C2F21),
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Kode $_qrCodeMasked · $_qrWindowMs ms',
                  style: const TextStyle(color: Color(0xFF50645A), fontSize: 12),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  /// Kartu kertas laboratorium untuk custom draft. Tidak ada QR, tidak ada
  /// harga, tidak ada janji produk jadi — hanya status permintaan.
  Widget _draftNoticeOverlay() {
    return Positioned.fill(
      child: IgnorePointer(
        child: Container(
          color: const Color(0xB30A1712),
          alignment: Alignment.center,
          child: Container(
            width: 620,
            padding: const EdgeInsets.all(26),
            decoration: BoxDecoration(
              color: const Color(0xFFF4EFE2),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFF0C2F21), width: 2),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'PERMINTAAN DICATAT',
                  style: TextStyle(
                    color: Color(0xFF0C2F21),
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.5,
                  ),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Menunggu tinjauan admin. Bukan produk jadi; belum bisa '
                  'dipesan atau dibayar.',
                  style: TextStyle(color: Color(0xFF50645A), fontSize: 14, height: 1.4),
                ),
                const SizedBox(height: 14),
                Text(
                  'Ref $_draftNoticeRef',
                  style: const TextStyle(
                    color: Color(0xFF0C2F21), fontSize: 13, fontWeight: FontWeight.w700,
                  ),
                ),
                if (_draftNoticeName.isNotEmpty)
                  Text(
                    'Label: $_draftNoticeName',
                    style: const TextStyle(color: Color(0xFF0C2F21), fontSize: 13),
                  ),
                if (_draftNoticeTheme.isNotEmpty)
                  Text(
                    'Tema: $_draftNoticeTheme',
                    style: const TextStyle(color: Color(0xFF50645A), fontSize: 13),
                  ),
                if (_draftNoticeNotes.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(
                    _draftNoticeNotes,
                    style: const TextStyle(color: Color(0xFF50645A), fontSize: 12, height: 1.4),
                  ),
                ],
              ],
            ),
          ),
        ),
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
