# Alkaff Scent Lab — Flutter Web

Tampilan Interactive Scent Theater berbasis Flutter Web. Data tidak disimpan di
browser: aplikasi membaca langsung endpoint baca-saja dari modul Odoo
`alkaff_catalog` di database **`nml`**.

## Alur

```text
Browser (https://alkaff.lokal.or.id)
  └─ GET https://nml.lokal.or.id/alkaff/api/health
  └─ GET https://nml.lokal.or.id/alkaff/api/recommendations?keyword=...
       └─ Odoo nml (127.0.0.1:8071) → product.template + bundle tema
OBS / TikTok Live Studio
  └─ Window Capture → jendela browser yang menampilkan web app ini
```

Tidak ada koneksi TikTok API dan tidak ada auto-DM. CTA (`COFFEE`, `QUOTE`, dst.)
hanya ditampilkan; penonton yang memulai DM.

## Query string

| Parameter | Default | Fungsi |
|---|---|---|
| `keyword` | `kopi dingin` | Keyword viewer yang dipakai saat app dibuka |
| `controls` | `0` | `1` menampilkan panel kontrol host |
| `mode` | `clean` | `split` menyediakan zona atas 40% untuk kamera host |
| `api` | `https://nml.lokal.or.id/alkaff/api` | Override URL API untuk pengujian lokal |

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

## Konsol manual dari Namlah superapp

Menu **Alkaff Live Console** di `https://app.lokal.or.id` (Beranda → kategori Kurasi)
menyematkan theater ini dalam iframe dan mengirim perintah lewat `postMessage`.
Konsol menyediakan:

- input username TikTok + komentar/perintah palsu yang tampil sebagai chat simulasi;
- tombol kirim komen yang sekaligus memakai komentar sebagai keyword rekomendasi;
- tombol sutradara untuk memotong langsung ke `boot`, `scan`, `mix`, `analyze`, `result`;
- tombol `Auto`, `Reset`, `Split/Full`, dan `Hapus chat`;
- status balasan dari theater (scene, status, tema, CTA, jumlah produk).

Protokol pesan dari konsol ke theater:

```json
{
  "source": "namlah-alkaff-console",
  "command": "chat",
  "payload": {"username": "viewer_demo", "comment": "kopi dingin"}
}
```

Perintah yang diterima: `keyword`, `scene`, `play`, `reset`, `split`, `chat`, `clearChat`.
Theater hanya menerima pesan dari origin `https://app.lokal.or.id` (atau
`http://localhost:8085` untuk pengujian lokal) dan membalas status ke origin itu.
Ini **simulasi manual**: bukan API TikTok, bukan auto-DM, dan tidak menyimpan
data viewer ke server.

## Build

```bash
cd webapp/alkaff_scent_lab
/home/mintbag/flutter-sdk/bin/flutter pub get
/home/mintbag/flutter-sdk/bin/flutter build web --release --no-wasm-dry-run
```

Hasil build ada di `build/web/` dan **sengaja tidak di-commit**.
Service systemd `alkaff-web.service` menyajikan folder tersebut di
`127.0.0.1:8088`; Cloudflare Tunnel meneruskan `alkaff.lokal.or.id` ke port itu.

## Pakai di OBS / TikTok Live Studio

1. Buka URL siap LIVE di Chrome/Edge, tekan `F11` untuk full-screen.
2. Klik sekali di halaman bila audio/animasi browser memerlukan gesture.
3. Di OBS, tambahkan **Window Capture** → jendela browser tersebut.
4. Untuk mode `split`, isi 40% atas dari kamera host melalui overlay OBS atau
   kamera browser (zona ini disediakan oleh app).
5. Audio narasi/SFX diatur di OBS atau TikTok Live Studio. Tidak ada file audio
   yang di-commit di proyek ini.

## Pagar katalog

- Harga mentah dan supplier tidak pernah dikirim API atau ditampilkan UI.
- Notes adalah gambaran keluarga wewangian, bukan komposisi resmi pabrik.
- Tidak ada klaim tahan 24 jam, bebas alergi, afrodisiak, menghangatkan tubuh,
  halal, energi, atau kesehatan tanpa bukti/sertifikasi.
