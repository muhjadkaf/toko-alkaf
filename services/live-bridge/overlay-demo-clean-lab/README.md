# Virtual Clean Lab — AI Perfumer

Overlay TikTok LIVE Alkaff versi **ruang virtual 3D full-screen (1920×1080)**.
Fokus pada proses mixing dan perfilman aroma dengan mesin presisi, tanpa sosok
manusia. Narasi AI berbahasa Indonesia diputar dari file MP3 dan juga tampil
sebagai teks — tetapi **hanya menempel pada benda fisik** (layar monitor, label
vial, plakat meja, dan panel mesin). Tidak ada teks yang melayang di ruangan.

Buka `preview.html` untuk pratinjau. Untuk OBS gunakan `index.html?obs=1`
(kontrol tidak ikut tampil, background transparan).

## Ruang dan properti

- Lantai dan dinding dengan perspektif, garis lantai konvergen, pencahayaan
  langit-langit, bayangan, dan pantulan meja.
- Meja kerja dengan laci, rak sampel, gantry scanner, vortex chamber, robot
  arm, pedestal botol, kartu spesimen, dan monitor AI.
- Teks hanya pada: layar monitor, label tiga vial, plakat kartu di meja,
  serta engraving `SCAN·01`, `MIX·02`, `ARM·03` pada badan mesin dan label
  botol `ALKAFF / MARBELLA`.

## Alur

| Adegan | Durasi | Gerak mesin | Narasi AI |
|---|---|---|---|
| `boot` | 7 dtk | Lampu menyala, monitor inisialisasi | Perkenalan AI perfumer |
| `scan` | 10,5 dtk | Beam pemindai menyapu vial | Membaca top/heart/base notes |
| `mix` | 9,5 dtk | Robot arm menetes, cairan ber-vortex | Menjelaskan racik presisi |
| `analyze` | 7 dtk | Waveform pada layar monitor | Mendeskripsikan karakter aroma |
| `result` | — | Botol tersorot, kartu menampilkan harga | CTA DM `QUOTE` |

## Suara AI

- Narasi adalah 5 file MP3 di `audio/` yang dibuat dengan `gTTS` (`lang='id'`),
  bukan Web Speech API murni. Browser sesi tertentu tidak memiliki voice
  `id-ID`, sehingga MP3 dipakai sebagai sumber utama.
- Aktifkan dari tombol **🔊 Suara AI** di bilah pratinjau (di luar adegan),
  atau tambahkan `?voice=1` pada URL. Fallback Web Speech tetap ada bila file
  audio gagal diputar.
- Autoplay audio biasanya diblokir browser sampai ada interaksi. Karena itu
  teks di layar monitor selalu menjadi fallback.
- Durasi klip: boot 6,5 dtk · scan 9,9 dtk · mix 8,7 dtk · analyze 6,5 dtk ·
  result 7,3 dtk. Durasi adegan disetel lebih panjang agar narasi tidak terpotong.

## Parameter URL

- `?scene=boot|scan|mix|analyze|result` — lompat ke adegan tertentu.
- `?freeze=1&at=2` — bekukan animasi pada detik tertentu (untuk screenshot).
- `?obs=1` — mode OBS: tanpa kontrol, latar transparan.
- `?voice=1` — aktifkan narasi MP3 sejak awal (masih tergantung kebijakan autoplay).

## Pratinjau

`preview.html` memuat adegan dalam iframe dan menaruh kontrol di bilah terpisah
di bawah adegan. Tombol-tombol itu mengirim `postMessage` ke iframe, sehingga
tidak pernah muncul di dalam ruang virtual maupun di OBS.

## Batasan

- Ini mock visual, bukan koneksi TikTok dan bukan AI generatif sungguhan.
  Narasi ditulis tetap; MP3 hanya membacakannya.
- Harga `Rp449.000` adalah referensi resmi Marbella; harga jual final milik toko.
- Klaim “AI” pada layar adalah gaya presentasi, bukan sertifikasi laboratorium.
