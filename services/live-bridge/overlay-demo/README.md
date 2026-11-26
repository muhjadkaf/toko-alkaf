# Overlay Demo — Animasi Racik Parfum

Prototipe visual untuk overlay TikTok LIVE Alkaff. Satu file HTML mandiri
(HTML5 + CSS + JavaScript, tanpa dependency dan tanpa network call).

Buka `preview.html` atau `index.html` di browser untuk melihat animasi berjalan.
`index.html` juga bisa dipakai langsung sebagai **OBS Browser Source**.

## Alur animasi

| Waktu | Adegan | Isi |
|---|---|---|
| 0–2 dtk | `idle` | Brand Alkaff, partikel emas, badge LIVE |
| 2–7 dtk | `card` | Kartu produk Marbella, botol kaca, notes, contoh komentar |
| 7–11 dtk | `choose` | Tiga varian (1/2/3) dengan pilihan aktif |
| 11–18 dtk | `mix` | Dropper menetes, swirl, botol terisi, progress bar |
| 18+ dtk | `result` | Harga referensi + CTA `DM "QUOTE"` |

## Cara pakai di OBS

1. Tambah **Browser Source**, ukuran `1920 × 1080`.
2. Centang **Shutdown source when not visible** dan **Refresh browser when scene becomes active**.
3. URL: `file:///.../overlay-demo/index.html?obs=1`
4. Background transparan; panel berada di kanan agar kamera tetap terlihat di kiri.
5. Di produksi, ganti auto-play demo dengan event dari orchestrator (state
   `LIVE`, `COLLECTING`, `PROCESSING`, `READY`) agar overlay mengikuti chat asli.

## Parameter pratinjau

- `?scene=card|choose|mix|result` — lompat ke adegan tertentu.
- `?freeze=1&at=2.5` — hentikan animasi pada detik tertentu (untuk screenshot).
- `?bg=1` — latar studio gelap untuk pratinjau.
- `?obs=1` — sembunyikan kontrol dan buat background transparan.
- `?lowfx=1` — matikan blur berat (mesin lambat/perekaman).

## Batasan

- Ini **mock visual**, bukan koneksi TikTok. Komentar di sisi kiri adalah contoh,
  bukan chat asli.
- Harga `Rp449.000` adalah harga eceran referensi Marbella dari situs resmi
  MyKonos; keputusan harga jual tetap milik toko.
- Animasi berat (blur, partikel) dijalankan di GPU OBS. Jika mesin lemah,
  gunakan `?lowfx=1` atau kurangi jumlah partikel.
