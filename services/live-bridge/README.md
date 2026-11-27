# Alkaff Live Bridge — Skeleton

Kerangka Python ringan untuk fondasi **event ingest → orchestrator/state machine →
overlay OBS** pada proyek Toko Alkaff.

> **Ini kerangka lokal, bukan integrasi resmi TikTok dan bukan implementasi
> koneksi API.** Tidak ada WebSocket, HTTP, scraping, auto-DM, atau pengiriman
> pesan. Semua data berasal dari file JSONL di direktori ini.

## Tujuan

1. Menyeragamkan payload event menjadi envelope internal (`events.py`).
2. Menjaga status pipeline di satu tempat dengan transisi tervalidasi
   (`orchestrator.py`).
3. Menghasilkan snapshot JSON dan halaman HTML transparan untuk OBS Browser
   Source (`overlay.py`).
4. Menyediakan demo event lokal sehingga alur bisa diuji tanpa akun TikTok.

## Batasan

- Python 3.10+, **stdlib saja**, tanpa dependency pihak ketiga.
- Tidak ada jaringan: tidak ada klien TikTok, tidak ada server, tidak ada `fetch`.
- Tidak ada kredensial/token; `config.py` menolak field yang menyerupai kredensial.
- Tidak ada auto-DM. CTA quotation hanya berupa ajakan agar **viewer memulai DM**
  dengan keyword (viewer-initiated).
- Kasta botol, "ANTREAN #1", dan easter egg hanya **tampilan teater** dari event
  yang diterima; tidak ada antrean nyata, prioritas server, atau pengiriman gift.
- Status/transisi dan skema event masih kontrak internal, bukan API publik TikTok.
- Tidak ada rate limiting sungguhan, TTL sesi per viewer, atau quotation service;
  field konfigurasi untuk itu baru sebagai contoh nilai.

## Struktur

```text
services/live-bridge/
├── pyproject.toml
├── README.md
├── config/example.json
├── docs/EVENT_CONTRACT.md
├── examples/events.jsonl
├── examples/events-theater.jsonl  # demo 5 klien + recap
├── schemas/live_event.schema.json
├── src/alkaff_live/
│   ├── __init__.py
│   ├── config.py         # loader JSON/dict tanpa PyYAML
│   ├── events.py         # LiveEvent + normalisasi + eventId SHA-256
│   ├── orchestrator.py   # state machine + dedupe + filter streak gift
│   ├── overlay.py        # OverlayState + adapter lima scene Clean Lab
│   ├── themes.py         # pembaca 05_tema_layanan.csv (narasi + CTA)
│   └── main.py           # demo JSONL
└── tests/
    ├── test_events.py
    ├── test_orchestrator.py
    └── test_overlay.py
```

## Menjalankan tes

Dari folder `services/live-bridge`:

```bash
python3 -m unittest discover -s tests
```

Semua tes memakai `unittest` dan menambahkan `src/` ke `sys.path` sendiri;
tidak perlu instalasi paket.

## Menjalankan demo event lokal

Dari folder `services/live-bridge`:

```bash
PYTHONPATH=src python3 -m alkaff_live.main \
  --config config/example.json \
  --events examples/events.jsonl \
  --out build
```

Untuk melihat lima klien, kasta botol, easter egg, dan papan recap:

```bash
PYTHONPATH=src python3 -m alkaff_live.main \
  --config config/example.json \
  --events examples/events-theater.jsonl \
  --out build
```

Alternatif tanpa `PYTHONPATH`:

```bash
python3 src/alkaff_live/main.py --events examples/events.jsonl --out build
```

Log transisi tampil di `stderr`, state overlay (JSON) tampil di `stdout`, dan dua
file ditulis ke `build/`:

- `build/overlay.json` — snapshot state.
- `build/overlay.html` — halaman 1920×1080 background transparan untuk
  OBS Browser Source. Memakai lima babak (`boot`, `scan`, `mix`, `analyze`,
  `result`) dan menyalin `build/audio/` untuk narasi MP3. Contoh konfigurasi
  memakai `voice: false` sehingga episode berdurasi 20 detik dengan SFX sintesis;
  `voice: true` memakai durasi narasi MP3 penuh. Buka sebagai file lokal;
  tidak memerlukan server.

Narasi dan CTA diambil dari `data/pengetahuan-parfum/05_tema_layanan.csv`
lewat `themes.py`: keyword viewer, SKU/varian, atau field `tema`/`ctaKeyword`
memilih satu baris tema. `notes` tema dipakai sebagai peta aroma dengan catatan
"gambaran keluarga, bukan komposisi resmi"; `CTA Keyword` tema menggantikan
keyword DM generik. Bila tidak ada yang cocok, tema `QUOTE` dipakai. Tidak ada
harga, supplier, atau klaim baru yang ditambahkan oleh modul ini.

Catatan: `build/` adalah hasil demo lokal dan sengaja tidak di-commit.
Audio ducking/musik latar diatur di OBS atau TikTok Live Studio, bukan di repo ini.
Jika browser menolak Web Audio tanpa gesture, tambahkan
`--autoplay-policy=no-user-gesture-required` pada Browser Source OBS.

Contoh urutan pada `examples/events.jsonl`:

```text
IDLE -> LIVE -> COLLECTING -> PROCESSING -> READY -> ENDED
```

File JSONL berisi satu objek JSON per baris, boleh memakai nama field camelCase
dari payload LIVE (`uniqueId`, `comment`, `gift`, `repeatEnd`). Baris kosong
diabaikan. Jika event tidak cocok dengan status aktual, demo berhenti dengan
kode keluar `2` dan pesan di `stderr`.

## Konfigurasi

`config/example.json` berisi pengaturan demo: TTL, batas antrean, ukuran overlay,
mode panggung, narasi/SFX, durasi babak, tier gift, easter egg, frekuensi recap,
dan keyword CTA. Semua nilai bisa diganti lewat file JSON atau langsung berupa
`dict`:

| Kunci | Default | Fungsi |
|---|---|---|
| `overlay.stage` | `full` | `split` menyisihkan 40% atas untuk kamera host. |
| `overlay.voice` | `true` | Narasi MP3 bahasa Indonesia; contoh memakai `false`. |
| `overlay.sfx` | `true` | SFX Web Audio: blip, tuangan, sentrifugal, thump, chime, semprotan. |
| `overlay.durations` | otomatis | Durasi per babak dalam ms; mengganti profil 20 dtk/narasi. |
| `easterEggs` | `{}` | Peta `kata kunci rahasia → merek jenaka`. |
| `recapEvery` | `5` | Papan "5 Merek Terakhir" tiap N klien pada status `READY`. |
| `giftTiers` | `{}` | Daftar nama gift yang dikenal; gift apa pun ber-kasta `founder`. |
| `themesCsv` | `05_tema_layanan.csv` | Path tema layanan relatif terhadap folder basis pengetahuan; kosong/`tidak ada` → keyword `QUOTE`. |

```python
from alkaff_live.config import load_config
config = load_config("config/example.json")  # atau load_config({...})
```

Kunci menerima camelCase maupun snake_case. Konfigurasi tidak boleh memuat
field `token`, `secret`, `password`, `api_key`, atau sejenisnya.

## Status machine singkat

| Status | Arti |
|---|---|
| `IDLE` | Belum ada LIVE aktif. |
| `LIVE` | Sesi terbuka, menunggu interaksi. |
| `COLLECTING` | Mengumpulkan pilihan/intent viewer. |
| `PROCESSING` | Racikan/quotation sedang disiapkan. |
| `READY` | Quotation siap; overlay menampilkan CTA DM keyword. |
| `ERROR` | Proses gagal; bisa retry. |
| `ENDED` | Stream selesai; konteks dibersihkan. |

Detail field, matriks transisi, dan kontrak overlay ada di
[`docs/EVENT_CONTRACT.md`](docs/EVENT_CONTRACT.md).
