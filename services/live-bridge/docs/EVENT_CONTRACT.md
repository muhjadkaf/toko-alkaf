# Kontrak Event — Alkaff Live Bridge

Dokumen ini menjelaskan kontrak internal skeleton. Ini **bukan** dokumentasi API TikTok
dan **bukan** integrasi resmi. Tidak ada koneksi jaringan di dalam paket ini.

## 1. Envelope event

Semua event masuk dinormalisasi oleh `alkaff_live.events.normalize_event` menjadi:

```json
{
  "eventId": "evt-demo-001",
  "type": "chat",
  "occurredAt": "2026-11-26T09:31:12Z",
  "user": {"id": "677...", "uniqueId": "alkaff_fan", "nickname": "Fan Alkaff"},
  "payload": {"comment": "oud dong kak"}
}
```

Skema minimal ada di [`schemas/live_event.schema.json`](../schemas/live_event.schema.json).

| Field | Wajib | Tipe | Keterangan |
|---|---|---|---|
| `eventId` | ya | string | Kunci idempotency. Bila tidak dikirim, dihitung SHA-256 dari envelope kanonik. |
| `type` | ya | string | Jenis event (lihat tabel berikut). |
| `occurredAt` | ya | string | ISO-8601 UTC berakhiran `Z`; tanpa timezone ditolak. |
| `user` | tidak | object | `id`, `uniqueId`, `nickname`. Boleh absen untuk `streamStart`/`streamEnd`. |
| `payload` | ya | object | Isi event. Field mentah di luar envelope/user otomatis masuk ke sini. |

### Jenis event

| Jenis | Sumber | Payload minimal | Catatan |
|---|---|---|---|
| `streamStart` | kontrol | `{}` | Membuka sesi pipeline. |
| `streamEnd` | LIVE / kontrol | `{}` | Membersihkan konteks dan menutup overlay. |
| `chat` | komentar LIVE | `comment` | Juga menerima alias `comment` sebagai `type`. |
| `gift` | gift LIVE | `gift` (objek) | `giftType = 1` hanya diproses saat `repeatEnd = 1`. |
| `member`, `like`, `share`, `follow`, `questionNew` | LIVE | bebas | Efek ringan; tidak mengubah urutan quotation. |
| `control.submit` | internal | `sku`, `variant` | Permintaan racikan/quotation dimulai. |
| `control.result` | internal | `quoteId`, `quoteUrl` | Quotation siap ditampilkan. |
| `control.error` | internal | bebas | Menandai kegagalan proses. |
| `control.retry` | internal | bebas | Mencoba lagi dari `COLLECTING`. |
| `control.reset` | internal | `{}` | Kembali ke `IDLE` hanya dari `ENDED`. |

> Normalisasi hanya membaca data. Tidak ada pengiriman pesan, tidak ada auto-DM,
> dan tidak ada pemanggilan API TikTok.

## 2. State machine

Status didefinisikan di `alkaff_live.orchestrator.State`:
`IDLE`, `LIVE`, `COLLECTING`, `PROCESSING`, `READY`, `ERROR`, `ENDED`.

Transisi yang diizinkan:

| Dari | Ke |
|---|---|
| `IDLE` | `LIVE`, `ENDED` |
| `LIVE` | `LIVE`, `COLLECTING`, `ENDED`, `ERROR` |
| `COLLECTING` | `COLLECTING`, `PROCESSING`, `ENDED`, `ERROR` |
| `PROCESSING` | `READY`, `ERROR`, `ENDED` |
| `READY` | `COLLECTING`, `ENDED`, `ERROR` |
| `ERROR` | `COLLECTING`, `LIVE`, `ENDED` |
| `ENDED` | `IDLE` |

Aturan tambahan:

- `eventId` yang sama hanya diproses sekali (no-op pada pemrosesan ulang).
- Event yang tidak punya aturan pada status aktual menimbulkan
  `InvalidTransitionError` dan state tidak berubah.
- Gift streak (`giftType = 1`, `repeatEnd != 1`) menjadi no-op agar animasi tidak dobel.
- `streamEnd` mengosongkan konteks (`sku`, `variant`, `quoteId`, `quoteUrl`).

Alur tipikal:

```text
IDLE --streamStart--> LIVE --chat--> COLLECTING --control.submit--> PROCESSING
    --control.result--> READY --streamEnd--> ENDED --control.reset--> IDLE
```

## 3. Kontrak overlay

`Orchestrator.snapshot()` menghasilkan:

```json
{
  "status": "READY",
  "eventCount": 4,
  "lastEventId": "e4",
  "context": {"sku": "ALK-01", "variant": "EDT", "quoteId": "Q-1"},
  "history": []
}
```

`history` memuat pula no-op (duplikat/streak) untuk keperluan audit; hanya
10 entri terakhir yang disertakan dalam snapshot.

`alkaff_live.overlay.build_overlay_state` mengubahnya menjadi state overlay:

```json
{
  "status": "READY",
  "scene": "result",
  "visible": true,
  "message": "Quotation ALK-01 · EDT siap.",
  "detail": "ALK-01 · EDT",
  "cta": "DM kata kunci QUOTE ke akun Alkaff",
  "updatedAt": "2026-11-26T09:31:26Z",
  "eventCount": 4,
  "sequence": ["result"],
  "narrations": {
    "result": "Profil ALK-01 · EDT siap. DM kata kunci QUOTE untuk detail quotation."
  }
}
```

| Field | Tipe | Keterangan |
|---|---|---|
| `status` | string | Sama dengan status orchestrator. |
| `scene` | string | Scene Clean Lab pertama: `boot`, `scan`, `mix`, `analyze`, `result`. |
| `visible` | boolean | `false` pada `IDLE`/`ENDED`; overlay disembunyikan. |
| `message`, `detail` | string | Teks tampilan, sudah di-escape saat dirender fallback HTML. |
| `cta` | string/null | Hanya ada pada `READY`; berupa ajakan DM keyword. |
| `updatedAt` | string | Waktu render dalam UTC `Z`. |
| `eventCount` | integer | Jumlah event unik yang diproses. |
| `sequence` | array | Urutan scene otomatis. `PROCESSING` memutar `mix` lalu `analyze`. |
| `narrations` | object | Teks narasi per scene, menggantikan narasi demo bawaan. |

Pemetaan status ke scene:

| Status | Scene | Urutan otomatis |
|---|---|---|
| `IDLE` | `boot` | `boot` (tersembunyi) |
| `LIVE` | `boot` | `boot` |
| `COLLECTING` | `scan` | `scan` |
| `PROCESSING` | `mix` | `mix` → `analyze` |
| `READY` | `result` | `result` |
| `ERROR` | `boot` | `boot` (narasi gangguan) |
| `ENDED` | `boot` | `boot` (tersembunyi) |

`write_overlay()` menulis dua file lokal:

- `overlay.json` — snapshot untuk konsumen lain. Transport (SSE/Socket.IO)
  **sengaja belum diimplementasikan**.
- `overlay.html` — halaman transparan 1920×1080 untuk OBS Browser Source.
  Diambil dari template `overlay-demo-clean-lab/index.html`, sehingga lima scene
  sinematik dipakai langsung tanpa `fetch` atau CDN. Data disematkan di dalam
  dokumen (`<script type="application/json">`) lalu dikirim ke pemutar scene
  lewat `postMessage` lokal. Folder `audio/` ikut disalin agar narasi MP3
  tetap berjalan dari hasil build. Narasi bisa dimatikan lewat
  `overlay.voice = false` pada konfigurasi.

## 4. Batas platform TikTok

- Tidak ada API publik resmi untuk membaca komentar/gift LIVE secara real-time.
  Produksi memerlukan penyedia event yang sah/akses resmi; ini bukan bagian skeleton.
- TikTok tidak mengizinkan auto-DM yang memulai percakapan dari komentar LIVE.
  Pola yang didukung adalah **viewer-initiated**: viewer mengirim DM keyword lebih
  dulu, lalu balasan dikirim melalui jalur resmi yang memenuhi syarat.
- `cta` pada overlay hanya berupa ajakan, bukan tindakan pengiriman pesan.
- Overlay masuk ke layar LIVE melalui OBS/LIVE Studio (virtual camera), bukan API
  "gambar langsung ke LIVE".

> Karena itu modul ini berhenti pada snapshot overlay. Gate quotation/DM,
> autentikasi, dan izin platform harus dirancang terpisah dengan audit trail.
