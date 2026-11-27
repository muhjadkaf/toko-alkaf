# Alkaff Scent Lab — Flutter Web

Tampilan Interactive Scent Theater berbasis Flutter Web. Data tidak disimpan di
browser: aplikasi membaca langsung endpoint baca-saja dari modul Odoo
`alkaff_catalog` di database **`nml`**.

Theater memakai dunia **Alkaff Maklon Hall**: visualisasi pabrik maklon skala
besar dengan tangki berjaket, pipa, katup, catwalk, drum, meja QC, conveyor, dan
label batch. Lima plate CG dirender lokal lalu diberi parallax ringan. Teks
hanya menempel pada benda fisik (papan dinding, monitor QC, kertas batch); tidak
ada sosok manusia, neon, partikel ajaib, atau panel mengambang di mode LIVE.
Narasi disajikan **audio saja, tanpa subtitle**.

## Alur

```text
Browser (https://alkaf.lokal.or.id / https://alkaff.lokal.or.id)
  └─ GET /alkaff/api/health                 (proxy same-origin → Odoo nml)
  └─ GET /alkaff/api/recommendations?keyword=...
       └─ Odoo nml (127.0.0.1:8071) → product.template + bundle tema
  └─ GET /alkaff/control?channel=live        (bus kontrol bersama)
  └─ POST /alkaff/control/state              (publikasi scene ke konsol)
OBS / TikTok Live Studio
  └─ Window Capture → jendela browser yang menampilkan web app ini
```

Tidak ada koneksi TikTok API dan tidak ada auto-DM. CTA (`COFFEE`, `QUOTE`, dst.)
hanya ditampilkan; penonton yang memulai DM.

## Query string

| Parameter | Default | Fungsi |
|---|---|---|
| `keyword` | `kopi dingin` | Keyword viewer yang dipakai saat app dibuka |
| `controls` | `0` | `1` menampilkan panel kontrol host (hanya saat persiapan) |
| `mode` | `clean` | `split` menyediakan zona atas 40% untuk kamera host |
| `channel` | `live` | Channel bus kontrol; harus sama dengan channel di konsol |
| `api` | `/alkaff/api` | Override URL API untuk pengujian lokal |
| `control` | `/alkaff/control` | Override URL bus kontrol untuk pengujian lokal |

Contoh untuk penyiapan host:

```text
https://alkaff.lokal.or.id/?controls=1&keyword=kopi%20dingin
```

Contoh siap LIVE (tanpa panel kontrol, full-screen):

```text
https://alkaff.lokal.or.id/?keyword=kopi%20dingin
```

Mode split dengan zona kamera di 40% atas:

```text
https://alkaff.lokal.or.id/?mode=split&keyword=kopi%20dingin
```

## Dunia dan aset

Lima adegan memakai plate CG yang dirender lokal dengan PIL, sehingga bisa
dibuat ulang tanpa layanan gambar eksternal:

| Scene | Plate | Narasi audio |
|---|---|---|
| `boot` | `assets/world/scene_boot.jpg` | `assets/audio/narasi_boot.mp3` |
| `scan` | `assets/world/scene_scan.jpg` | `assets/audio/narasi_scan.mp3` |
| `mix` | `assets/world/scene_mix.jpg` | `assets/audio/narasi_mix.mp3` |
| `analyze` | `assets/world/scene_analyze.jpg` | `assets/audio/narasi_analyze.mp3` |
| `result` | `assets/world/scene_result.jpg` | `assets/audio/narasi_result.mp3` |

Generator:

```bash
python3 tools/generate_world_plates.py   # butuh Pillow
python3 tools/generate_narration.py      # butuh gTTS, bahasa Indonesia
```

`WorldStage` melakukan parallax ringan dan menempelkan UI diegetik: papan logam
identitas di dinding, monitor QC untuk chat simulasi, dan kertas batch untuk
tema/produk/CTA. Perpindahan scene mengganti plate dan memutar narasi audio
yang bersangkutan. Tidak ada teks narasi di layar.

Perintah sutradara manual menghentikan auto-sequence, termasuk bila perintah
datang sebelum katalog selesai dimuat. `play` atau perubahan keyword
mengembalikan theater ke auto-sequence.

## Konsol manual dari Namlah superapp

Menu **Alkaff Live Console** di `https://app.lokal.or.id` (Beranda → kategori Kurasi)
**tidak memuat iframe/pratinjau**. Konsol mengirim perintah ke bus kontrol bersama
dan theater yang dibuka di perangkat lain melakukan polling ke bus yang sama.
Konsol menyediakan:

- input username TikTok + komentar/perintah palsu yang tampil sebagai chat simulasi;
- tombol kirim komen yang sekaligus memakai komentar sebagai keyword rekomendasi;
- tombol sutradara untuk memotong langsung ke `boot`, `scan`, `mix`, `analyze`, `result`;
- tombol `Auto`, `Reset`, `Split/Full`, dan `Hapus chat`;
- field channel bersama dan tautan theater untuk dibuka di HP lain;
- status theater (scene, status, tema, CTA, jumlah produk) dari bus kontrol.

Endpoint bus kontrol (same-origin, diproksikan oleh `serve.py`):

| Metode | Path | Fungsi |
| --- | --- | --- |
| `POST` | `/alkaff/control` | antrekan perintah konsol |
| `GET` | `/alkaff/control?channel=live&since=0` | theater mengambil perintah baru |
| `POST` | `/alkaff/control/state` | theater mempublikasikan status |
| `GET` | `/alkaff/control/state?channel=live` | konsol membaca status |

Contoh body perintah:

```json
{
  "source": "namlah-alkaff-console",
  "channel": "live",
  "command": "chat",
  "payload": {"username": "viewer_demo", "comment": "kopi dingin"}
}
```

Perintah yang diterima: `keyword`, `scene`, `play`, `reset`, `split`, `chat`, `clearChat`.
Cursor `since=-1` berarti bootstrap: theater tidak memutar ulang perintah lama.
`postMessage` lokal masih diterima sebagai fallback bila theater disematkan,
tetapi bukan lagi jalur utama. Ini **simulasi manual**: bukan API TikTok, bukan
auto-DM, dan tidak menyimpan data sensitif ke server.

## Build

```bash
cd webapp/alkaff_scent_lab
/home/mintbag/flutter-sdk/bin/flutter pub get
/home/mintbag/flutter-sdk/bin/flutter build web --release --no-wasm-dry-run
```

Hasil build ada di `build/web/` dan **sengaja tidak di-commit**.
Service systemd `alkaff-web.service` menyajikan folder tersebut di
`127.0.0.1:8088`; Cloudflare Tunnel meneruskan `alkaff.lokal.or.id` dan alias
`alkaf.lokal.or.id` ke port itu. Query string `?channel=live` harus sama dengan
channel di konsol.

## Pakai di OBS / TikTok Live Studio

1. Buka URL siap LIVE di Chrome/Edge, tekan `F11` untuk full-screen.
2. Klik sekali di halaman bila browser memerlukan gesture sebelum memutar audio.
3. Di OBS, tambahkan **Window Capture** → jendela browser tersebut.
4. Untuk mode `split`, isi 40% atas dari kamera host melalui overlay OBS atau
   kamera browser (zona ini disediakan oleh app).
5. Ambil audio narasi dari tab browser tersebut di OBS/TikTok Live Studio, atau
   sembunyikan bila host menyampaikan narasi langsung. File MP3 narasi sudah
   ada di `assets/audio/` dan tidak mengandung klaim medis/kosmetik/formula.

## Pagar katalog

- Harga mentah dan supplier tidak pernah dikirim API atau ditampilkan UI.
- Notes adalah gambaran keluarga wewangian, bukan komposisi resmi pabrik.
- Tidak ada klaim tahan 24 jam, bebas alergi, afrodisiak, menghangatkan tubuh,
  halal, energi, atau kesehatan tanpa bukti/sertifikasi.
