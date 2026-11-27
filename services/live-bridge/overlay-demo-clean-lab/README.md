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
- Kabut parfum halus melayang di latar; lens flare emas menyala saat botol
  merek penonton muncul.
- Nama penonton, kode resep, dan kasta botol ditulis pada label fisik botol
  dan plakat hasil — bukan teks mengambang.

## Lima scene

| Babak | Durasi episode | Fokus utama | Permukaan teks |
|---|---|---|---|
| 1 `boot` | 2 dtk | Konsol menyala, kartu klien masuk | Layar konsol |
| 2 `scan` | 4 dtk | Tiga vial disapu laser, kata kunci menyala | Panel scanner + label vial |
| 3 `mix` | 4 dtk | Vortex chamber + pipet robot menetes | Panel kontrol mixer |
| 4 `analyze` | 4 dtk | Monitor AI ber-waveform, uji spektrum | Layar monitor |
| 5 `result` | 6 dtk | Botol merek penonton + lens flare | Plakat hasil + label botol |

Transisi antarbabak: babak lama mengecil & blur, babak baru masuk dengan
zoom, disertai sapangan `warp` berarah dan garis perspektif yang melaju.

Lima babak dirangkai menjadi **episode 20 detik** per klien. Urutan dari status
`LIVE → COLLECTING → PROCESSING → READY` adalah
`boot → scan → mix → analyze → result`.

## Durasi dan audio

| Babak | Profil episode | Profil narasi | MP3 narasi |
|---|---|---|---|
| `boot` | 2 dtk | 7 dtk | 6,5 dtk |
| `scan` | 4 dtk | 10,5 dtk | 9,9 dtk |
| `mix` | 4 dtk | 9,5 dtk | 8,7 dtk |
| `analyze` | 4 dtk | 7 dtk | 6,5 dtk |
| `result` | 6 dtk | 8 dtk | 7,3 dtk |

File MP3 ada di `audio/` (`gTTS`, `lang='id'`). Aktifkan lewat tombol
**🔊 Suara AI** di bilah pratinjau atau `?voice=1`. Web Speech dipakai hanya
sebagai fallback bila MP3 gagal diputar. Profil narasi dipakai otomatis saat
`voice: true`; profil episode 20 detik dipakai saat `voice: false`.

SFX disintesis dengan Web Audio (tanpa aset baru): blip radar di `boot`/`scan`,
tuangan cairan dan dengung sentrifugal di `mix`, sub-bass + chime di `analyze`,
serta desisan atomizer `psshh!` sebelum akor kemenangan di `result`. Matikan
dengan `?sfx=0` atau `"overlay": {"sfx": false}`.

## Parameter URL

- `?scene=boot|scan|mix|analyze|result` — langsung ke scene tertentu.
- `?freeze=1&at=2` — bekukan animasi pada detik tertentu (screenshot).
- `?obs=1` — mode OBS: tanpa kontrol, latar transparan.
- `?voice=1` — nyalakan narasi MP3 sejak awal.
- `?stage=split` — 40% atas transparan untuk kamera fisik host.
- `?sfx=0` — matikan SFX sintesis.

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
  scene: "result",
  auto: true,
  sequence: ["result"],
  narrations: { result: "Resmi rilis: ALKAFF x ALKAFF FAN ..." },
  visible: true,
  voice: false,
  sfx: true,
  stage: "full",
  durations: { boot: 2000, scan: 4000, mix: 4000, analyze: 4000, result: 6000 },
  viewer: "alkaff_fan",
  keyword: "oud dong kak",
  brand: "ALKAFF FAN",
  code: "ALK-385",
  tier: "founder",
  tierLabel: "Founder Edition · Kristal Hitam-Emas",
  priority: true,
  eggName: "",
  recap: [{ brand: "EAU DE KENANGAN", code: "ALK-194", tier: "emerald" }]
}
```

Pemutar menerima `scene`, `sequence`, `narrations`, `visible`, `voice`, `sfx`,
`stage`, `durations`, identitas klien, kasta botol, dan papan recap. Narasi per
babak menggantikan teks demo bawaan. Folder `audio/` ikut disalin ke `build/`.

## Kasta botol

| Sinyal | Kasta | Tampilan |
|---|---|---|
| `!racik ...` biasa | `classic` | Kaca bening, label Classic Lab Edition |
| Share/tap tinggi | `emerald` | Kaca doff zamrud, tutup emas |
| Gift | `founder` | Kristal hitam-emas, plakat "VIP MAKLON UNLOCKED! · ANTREAN #1" |

Nama merek jenaka dari `easterEggs` menggantikan nama botol dan memicu reaksi
robot pusing pada panel scanner. Tiap `recapEvery` klien, plakat hasil menampilkan
lima merek terakhir beserta kode resepnya.

## Batasan

- Ini mock visual, bukan koneksi TikTok dan bukan AI generatif sungguhan.
- Narasi ditulis tetap; MP3 hanya membacakannya.
- Label harga diganti kode resep; tidak ada harga jual final di overlay.
- "ANTREAN #1" hanya penanda visual, bukan antrean sungguhan di server.
- Browser dapat menolak Web Audio/MP3 tanpa gesture; di OBS gunakan
  `--autoplay-policy=no-user-gesture-required` bila perlu.
- Realisme dibangun dari gradien/filter SVG/CSS, bukan foto atau video.
