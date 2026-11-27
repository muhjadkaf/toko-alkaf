# Alkaff LIVE — reward, QR, dan custom draft

> Salinan dokumen induk di repo `NUAMLAH`: `Docs/alkaff-reward-qr-custom-draft.md`.
> Status: simulasi manual, siap dipakai dengan operator
> Review terakhir: 2026-11-27
> Implementasi: `/home/mintbag/namlah-web/serve.py` (bus + ledger),
> `toko-alkaf/webapp/alkaff_scent_lab/` (theater),
> `apps/namlah_app/lib/screens/alkaff_live_console_screen.dart` (konsol),
> `toko-alkaf/odoo/addons/alkaff_custom_request/` (draft Odoo).

Dokumen ini menjelaskan jalur **reward poin → QR → produk nyata** dan jalur
**custom/rebrand → draft admin**. Keduanya memakai alias penonton, bukan `userId`
TikTok. Tidak ada API TikTok, auto-DM, auto-cart, atau auto-checkout; pembelian
selalu dimulai dari penonton.

## 1. Reward Theater

| Poin | Tier | Botol | Tampilan |
| --- | --- | --- | --- |
| 1 | `basic` | `rollon` | foto kecil, tanpa nama |
| 5 | `signature` | `spray` | foto lebih besar + nama (hanya bila opt-in) |

`usap` tersedia sebagai format pilihan untuk kedua tier; perilaku poin tetap
sama. Progres penonton deterministik: lima kali 1 poin menjadi `signature`.
Saldo maksimal 5, cooldown 60 detik per alias, dan idempotency
**first-seen-wins** (duplikat tidak mengantrekan reward kedua). Tidak ada janji
hadiah, gratis, diskon, atau leaderboard uang.

Perintah bus yang dipakai:

```json
{"command":"reward","payload":{"points":"5","delivery":"spray",
  "productRef":"ALK-L-042","recipeRef":"Parfum Kopi",
  "viewerAlias":"viewer_demo","displayName":"",
  "decisionKind":"existing_product","idempotencyKey":"..."}}
```

`rewardReplay`, `rewardClear`, dan `rewardRevoke` memakai `rewardId`. Revoke
hanya berlaku untuk reward yang sedang tampil; reward lama sengaja diabaikan.

Botol digambar lokal oleh `lib/reward_bottle.dart`. `photoUrl` kosong →
placeholder bermerek `ALK`; tidak ada foto produk per-SKU yang dikarang.

## 2. QR aman

QR hanya muncul setelah PNG selesai dimuat, lalu hilang setelah **≈3000 ms**
jam dinding. Animasi latar dan lip-sync dijeda selama jendela itu supaya
headless/OBS tidak melesetkan timing (bukti QA: 3002, 3016, 3010 ms).

- URL QR: `https://alkaff.lokal.or.id/a/<token>` (**bukan** `/q/<kode>`).
- Token opaque, TTL 24 jam, replay maksimal 2 kali, bisa dicabut.
- Response QR dan redirect memakai `Cache-Control: no-store`,
  `X-Robots-Tag: noindex,nofollow,noarchive`, `Referrer-Policy: no-referrer`.
- Screenshot dan scan sepenuhnya sukarela; tidak ada paksaan, auto-DM, atau
  auto-buka keranjang.
- `/q/<kode>` milik `namlah_qr` sengaja **tidak** dipakai karena dapat
  menampilkan harga dan identitas pen-scan.
- State theater hanya memuat `qrCodeMasked`, bukan token penuh.

Ledger lokal (tidak pernah dikirim ke browser):

| File | Isi |
| --- | --- |
| `/home/mintbag/namlah-web/state/alkaff-rewards.json` | reward, hash token, replay, revoke |
| `/home/mintbag/namlah-web/state/alkaff-reward-allowlist.json` | SKU allowlist + URL tujuan |
| `/home/mintbag/namlah-web/state/alkaff-custom-drafts.json` | draft custom lokal |

**Penting:** `productUrl` per-SKU saat ini masih fallback
`https://mart.lokal.or.id/`. Admin wajib menggantinya dengan URL produk
terverifikasi sebelum dipakai di kanal live. Jangan isi harga atau supplier di
allowlist.

## 3. Decision engine

Endpoint: `POST /alkaff/reward/decide`, source boleh
`namlah-alkaff-console`, `alkaff-bus`, atau `alkaff-admin`.

Body minimal:

```json
{
  "source": "namlah-alkaff-console", "channel": "live",
  "alias": "viewer_demo", "keyword": "kopi dingin",
  "points": "5", "delivery": "spray", "intent": "auto",
  "consentOptIn": false, "labelName": "", "notesAman": "Keluarga kopi."
}
```

Intent: `auto` (pilih produk allowlist bila cukup cocok, kalau tidak → draft),
`existing` (tetap menguji existing; bila tidak ada yang lolos → draft), dan
`custom` (selalu `custom_draft`). Respons memuat `decision`, `reason`, `notice`,
`qrEligible`, `rewardPayload` **atau** `draftCommand`, tetapi tidak keduanya.

### `existing_product`

- Produk harus ada di allowlist dan URL-nya lulus `https` + host allowlist.
- QR tetap memakai jalur `_mint_reward` → `/a/<token>`.
- Nama penonton hanya dipakai sebagai `displayName` bila `consentOptIn: true`.

### `custom_draft`

- Draft disimpan lokal dengan `qrEligible:false`, `rewardPayload:null`.
- Theater menampilkan kartu kertas laboratorium: “Permintaan dicatat. Menunggu
  tinjauan admin. Bukan produk jadi; belum bisa dipesan atau dibayar.”
- Tidak ada QR, harga, supplier, atau janji produk jadi.
- Bedakan label produk nyata dengan `labelName`: hanya terisi bila opt-in,
  dan hanya dipakai setelah admin menyetujui draft lalu membuat produk/URL
  terverifikasi secara manual.

### Pagar klaim

Keyword, notes, dan label ditolak `422 CLAIM_NOT_ALLOWED` bila mengandung:
`24 jam`, `bebas alergi`, `afrodisiak`, `menghangatkan tubuh`,
`formula produksi`, `komposisi resmi`, `gratis`, `diskon`, `auto-dm`,
`auto dm`, `obat`, `menyembuhkan`, `dijamin`, `halal tanpa bukti`, `halal`.

Ini edukasi keluarga wewangian, bukan klaim medis, kosmetik, khasiat, atau
formula produksi.

## 4. Admin draft

Token admin **hanya** dari environment `NAMLAH_WEB_ADMIN_TOKEN`, tidak pernah
disimpan di repo. Bila kosong, endpoint review menjawab `503
ADMIN_TOKEN_NOT_CONFIGURED`; token salah menjawab `403 FORBIDDEN`.

| Metode | Path | Kebutuhan |
| --- | --- | --- |
| `GET` | `/alkaff/reward/drafts` | `X-Admin-Token` |
| `POST` | `/alkaff/reward/drafts/<ref>/approve` | body `source:"alkaff-admin"` + token |
| `POST` | `/alkaff/reward/drafts/<ref>/reject` | sama, opsional `reviewNote` |

Konsol menyediakan field token (di-`obscureText`), tombol **Muat draft untuk
review**, lalu **Setujui**/**Tolak**. Token tidak ditulis ke state atau log.

Alur Odoo terpisah di addon `alkaff_custom_request` (sudah di-install hanya di
DB `nml`):

```text
custom_draft → draft → Kirim ke Review → admin Setujui/Tolak
             → admin buat produk + URL terverifikasi SECARA MANUAL
             → siklus existing_product yang boleh membuat QR
```

Model `alkaff.custom.request` tidak turunan `product.template`, tidak punya
field harga/supplier, tidak menulis produk, dan tidak publish. Endpoint
JSON-RPC internal memakai `auth="user"`, bukan publik. ACL Odoo 20 ada di
`security/ir.access.csv` dan termuat sebagai `ir_access`.

## 5. QA yang sudah dijalankan (2026-11-27)

- Reward CDP: tier basic/signature/usap, botol + nama, QR 3002/3016/3010 ms,
  replay maks 2, revoke, tanpa error console.
- Decision: `"kopi dingin"` + auto → `existing_product` `ALK-L-042`;
  intent `custom` → `custom_draft` dengan `qrEligible:false`; klaim
  `tahan 24 jam` → 422.
- Opt-in kosong → `labelName` kosong; opt-in terisi → `labelName` terisi +
  `consentAt`.
- Admin: tanpa token 403, token salah 403, token benar → list/approve/reject.
- Theater `customDraft`: kartu draft tampil, `qrVisible:false`, `qrStartedAt:0`,
  kartu hilang setelah 6 detik tanpa QR.
- Odoo: health `database == "nml"`, modul `alkaff_custom_request` `installed`,
  ACL `cru`/`crud` hadir, endpoint rekomendasi tetap berjalan.

Skrip QA ada di `/tmp/opencode/` (bukan bagian repo):
`qa_reward_cdp.py`, `qa_custom_draft.py`, `qa_timer_probe.py`.

## 6. Belum selesai / risiko

- URL produk per-SKU dan foto per-SKU belum terverifikasi; theater memakai
  placeholder `ALK` dan URL fallback mart.
- Bus kontrol belum punya HMAC/sesi wajib; jangan dipakai untuk kanal `live`
  publik sebelum ditutup.
- Autoplay audio bisa diblokir sampai ada gesture di tab theater/OBS.
- Deploy superapp `nuamlah` masih menunggu perubahan pihak lain di luar konsol.
