# Virtual Clean Lab — Sinematik

Overlay TikTok LIVE Alkaff berupa **ruang virtual realistis 1920×1080**. Setiap
langkah kerja memakai **scene terpisah dengan framing sinematik**, bukan satu
ruangan statis. Kamera seolah bergerak masuk ke ruang berikutnya lewat efek
warp/zoom saat transisi.

## Prinsip visual

- **Satu aktivitas utama di tengah per scene**, latar diburamkan (depth of field)
  sehingga hampir tidak ada ruang kosong.
- **Teks besar** (27–30 px) dan **hanya menempel pada benda fisik**: layar
  konsol, panel scanner, panel kontrol mixer, monitor AI, plakat hasil, label
  vial, dan label botol. Tidak ada teks mengambang.
- Botol hasil dirender detail tinggi dengan SVG: kaca tebal, refraksi,
  caustic, tetesan kondensasi, cap logam berfacet, label kertas, dan sapuan
  cahaya — bukan bentuk vektor/kartun.
- Tanpa sosok manusia. Narasi AI berbahasa Indonesia dari file MP3, dengan
  teks pada panel fisik sebagai fallback.

## Lima scene

| Scene | Fokus utama | Permukaan teks |
|---|---|---|
| `boot` | Konsol menyala, "SCENT LAB" | Layar konsol |
| `scan` | Tiga vial besar disapu laser | Panel scanner + label vial |
| `mix` | Vortex chamber + pipet robot menetes | Panel kontrol mixer |
| `analyze` | Monitor AI ber-waveform, chip karakter | Layar monitor |
| `result` | Botol Marbella fotorealistik di tengah | Plakat hasil + label botol |

Transisi antarscene: scene lama mengecil & blur, scene baru masuk dengan
zoom, disertai sapangan `warp` berarah dan garis perspektif yang melaju.

## Durasi dan audio

| Scene | Durasi | Audio |
|---|---|---|
| `boot` | 7 dtk | 6,5 dtk |
| `scan` | 10,5 dtk | 9,9 dtk |
| `mix` | 9,5 dtk | 8,7 dtk |
| `analyze` | 7 dtk | 6,5 dtk |
| `result` | — | 7,3 dtk |

File MP3 ada di `audio/` (`gTTS`, `lang='id'`). Aktifkan lewat tombol
**🔊 Suara AI** di bilah pratinjau atau `?voice=1`. Web Speech dipakai hanya
sebagai fallback bila MP3 gagal diputar.

## Parameter URL

- `?scene=boot|scan|mix|analyze|result` — langsung ke scene tertentu.
- `?freeze=1&at=2` — bekukan animasi pada detik tertentu (screenshot).
- `?obs=1` — mode OBS: tanpa kontrol, latar transparan.
- `?voice=1` — nyalakan narasi MP3 sejak awal.

## Pratinjau

`preview.html` menaruh kontrol di bilah terpisah **di luar** adegan. Tombol
mengirim `postMessage` ke iframe, sehingga kontrol tidak pernah tampil di
LIVE/OBS. Untuk OBS gunakan `index.html?obs=1`.

## Dipakai oleh live-bridge

`alkaff_live.overlay` memakai `index.html` ini sebagai template untuk
`build/overlay.html`. Status orchestrator dikirim lewat `postMessage` lokal
dengan bentuk:

```js
{
  scene: "mix",
  auto: true,
  sequence: ["mix", "analyze"],
  narrations: { mix: "Meracik ALK-01 ...", analyze: "Analisis profil ..." },
  visible: true,
  voice: true
}
```

Pemutar menerima `scene`, `sequence`, `narrations`, `visible`, dan `voice`;
urutan `PROCESSING` otomatis lanjut `mix → analyze`. Narasi per scene
menggantikan teks demo bawaan. Folder `audio/` ikut disalin ke `build/`.

## Batasan

- Ini mock visual, bukan koneksi TikTok dan bukan AI generatif sungguhan.
- Narasi ditulis tetap; MP3 hanya membacakannya.
- Harga `Rp449.000` adalah referensi resmi Marbella; harga jual final milik toko.
- Realisme dibangun dari gradien/filter SVG/CSS, bukan foto atau video.
