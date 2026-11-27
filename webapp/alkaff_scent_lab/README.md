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

Lima adegan memakai plate CG yang dirender lokal dengan numpy + PIL, sehingga
bisa dibuat ulang tanpa layanan gambar eksternal. Ruangnya adalah perpaduan
**pabrik maklon stainless** dan **butik parfum hangat**: dinding beton bertekstur,
lantai epoksi berkilap lembut, rak kayu berrel kuningan berisi botol kaca amber
berlabel matte, lampu high-bay hangat, tangki berjaket, drum di atas palet,
pipa ber-flange, gauge dial, catwalk, meja QC stainless dengan vial/pipet/suntikan,
serta conveyor botol di akhir lini. Tidak ada garis grid atau kotak generik,
manusia, teks mengambang, neon, atau partikel ajaib.

Riset multi-agen (nuansa butik, peralatan maklon, dan lisensi foto/tekstur)
tercatat di `docs/REFERENSI-VISUAL.md` lengkap dengan URL, tanggal akses
`2026-11-27`, dan status verifikasi. Foto internet dipakai hanya sebagai
referensi nuansa; tidak ada foto yang disalin atau disimpan di repo.

| Scene | Plate | Narasi audio |
|---|---|---|
| `boot` | `assets/world/scene_boot.jpg` | `assets/audio/narasi_boot.mp3` |
| `scan` | `assets/world/scene_scan.jpg` | `assets/audio/narasi_scan.mp3` |
| `mix` | `assets/world/scene_mix.jpg` | `assets/audio/narasi_mix.mp3` |
| `analyze` | `assets/world/scene_analyze.jpg` | `assets/audio/narasi_analyze.mp3` |
| `result` | `assets/world/scene_result.jpg` | `assets/audio/narasi_result.mp3` |

Generator:

```bash
python3 tools/generate_world_plates.py   # butuh Pillow + numpy
python3 tools/generate_narration.py      # butuh gTTS, bahasa Indonesia
```

`tools/texture_utils.py` menyediakan tekstur prosedural yang dipakai generator:
`concrete` (dinding), `epoxy` (lantai), `brushed_steel` (tangki/meja/pipa),
`warm_wood` (rak/palet), `fbm`/`grain` (ketidakteraturan alami), dan
`radial_light` (cahaya hangat dengan jatuhan mulus). Semua tekstur dibuat dari
nol; tidak ada aset gambar pihak ketiga.

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

Perintah yang diterima: `keyword`, `scene`, `play`, `reset`, `split`, `chat`,
`clearChat`, `presenter`, `speak`, `robot`, `reward`, `rewardReplay`,
`rewardClear`, `rewardRevoke`, `customDraft`. Cursor `since=-1` berarti
bootstrap: theater tidak memutar ulang perintah lama. `postMessage` lokal masih
diterima sebagai fallback bila theater disematkan, tetapi bukan lagi jalur
utama. Ini **simulasi manual**: bukan API TikTok, bukan auto-DM, dan tidak
menyimpan data sensitif ke server.

Status yang dipublikasikan ke bus juga memuat `rewardId`, `rewardTier`,
`rewardDelivery`, `rewardPoints`, `rewardName`, `rewardRecipe`,
`rewardStatus`, `rewardDecision`, `draftRef`, `draftNoticeVisible`,
`qrVisible`, `qrWindowMs`, `qrCodeMasked`, `qrStartedAt`, `qrEndedAt`,
`bottleType`, `bottlePhoto`, dan `bottleName`. Token QR penuh tidak pernah
dipublikasikan.

### Mode presenter

| Mode | Perilaku |
| --- | --- |
| `host` | CG pabrik tetap jadi latar; narasi dan robot dimatikan. Audio host diambil dari mic/OBS. |
| `robot` | Operator menyuruh robot bicara dan bergerak lewat perintah `speak` / `robot`. |
| `autopilot` | Robot mengikuti script lima adegan otomatis; ini default theater. |

Contoh:

```json
{"command":"presenter","payload":{"mode":"robot"}}
{"command":"speak","payload":{"text":"Selamat datang di Alkaff Scent Lab"}}
{"command":"robot","payload":{"action":"qc"}}
```

Aksi robot yang dikenal: `idle`, `scan`, `mix`, `qc`, `pour`, `point`. Status
`presenterMode`, `robotAction`, dan `speaking` ikut dipublikasikan ke
`/alkaff/control/state`. Rahang robot digerakkan dari perkiraan suku kata narasi;
bila teks diketik di konsol, Web Speech `id-ID` dipakai bila tersedia dengan
fallback ke perkiraan tersebut. Tidak ada subtitle dan tidak ada sosok manusia.

## Reward, QR, dan draft custom

1 poin menampilkan botol `basic` (`rollon`, foto kecil, tanpa nama); 5 poin
menampilkan `signature` (`spray`, foto lebih besar + nama bila opt-in). Format
`usap` juga tersedia. Botol lokal memakai placeholder bermerek `ALK` bila
`photoUrl` kosong. Progres deterministik, saldo maksimal 5, cooldown 60 detik,
idempotency first-seen-wins, tanpa janji hadiah/gratis/diskon.

QR hanya muncul setelah PNG siap dan hilang setelah ~3 detik jam dinding.
Selama jendela itu, animasi latar dan lip-sync dijeda supaya timing tidak
meleset di browser headless/OBS. QR memakai `/a/<token>` (bukan `/q/<kode>`),
token opaque TTL 24 jam, replay maksimal 2, dan bisa dicabut. Screenshot/scan
sukarela; tidak ada auto-beli.

Keputusan `POST /alkaff/reward/decide` menghasilkan salah satu dari:

- `existing_product` → produk allowlist dengan URL terverifikasi; QR diperbolehkan.
- `custom_draft` → kartu “permintaan dicatat, menunggu tinjauan admin”; **tanpa
  QR, harga, atau janji produk jadi**. Nama penonton dipakai sebagai label hanya
  dengan opt-in + approval admin.

Klaim terlarang (`24 jam`, `bebas alergi`, `afrodisiak`, `menghangatkan tubuh`,
`formula produksi`, `komposisi resmi`, `gratis`, `diskon`, `auto-DM`, `obat`,
`menyembuhkan`, `dijamin`, `halal` tanpa bukti) ditolak 422. Kontrak lengkap,
allowlist, token admin, dan QA ada di
[`../../../docs/ALKAFF-REWARD-QR-DRAFT.md`](../../../docs/ALKAFF-REWARD-QR-DRAFT.md).

## Build

```bash
cd webapp/alkaff_scent_lab
/home/mintbag/flutter-sdk/bin/flutter pub get
./build_web.sh
```

`build_web.sh` memakai nomor build UNIX timestamp. Nomor itu ditulis ke
`version.json` dan dipakai theater sebagai query string `?v=<build>` pada plate
JPG dan narasi MP3. Service `alkaff-web.service` juga dijalankan dengan
`NAMLAH_WEB_CACHE_BUST=1`, sehingga `index.html` memuat
`flutter_bootstrap.js?v=<build>` dan bootstrap memuat `main.dart.js?v=<build>`,
serta semua file statis dikirim dengan `Cache-Control: no-store`.

Hasilnya: tablet Opera maupun PC tidak perlu `Ctrl+Shift+R`. Setiap build baru
otomatis memakai URL aset yang berbeda, jadi cache lama tidak dipakai. Setelah
deploy, cache Cloudflare tetap perlu di-purge sekali agar edge tidak menyimpan
`main.dart.js` lama.

Hasil build ada di `build/web/` dan **sengaja tidak di-commit**.
Service systemd `alkaff-web.service` menyajikan folder tersebut di
`127.0.0.1:8088`; Cloudflare Tunnel meneruskan `alkaff.lokal.or.id` dan alias
`alkaf.lokal.or.id` ke port itu. Query string `?channel=live` harus sama dengan
channel di konsol.

## Pakai di OBS / TikTok Live Studio

1. Buka URL siap LIVE di Chrome/Edge/Opera, tekan `F11` untuk full-screen.
   Build baru otomatis terambil; tidak perlu hard refresh atau hapus cache.
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
