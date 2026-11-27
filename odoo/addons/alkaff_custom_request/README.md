# Alkaff Custom Request

Draft custom/rebrand untuk penonton LIVE Alkaff. Modul ini **terpisah** dari
`alkaff_catalog` agar tidak menyentuh perubahan pihak lain dan tidak pernah
menulis `product.template`.

## Pagar desain

- Tidak ada field harga, supplier, `Cost Price`, atau publish e-commerce.
- Tidak ada `userId` TikTok; hanya `alias` (nama tampilan).
- `label_name` diisi hanya bila `consent_opt_in = True`, dan hanya dipakai
  sebagai label produk nyata setelah admin menekan **Setujui**.
- Klaim terlarang ditolak: `24 jam`, `bebas alergi`, `afrodisiak`,
  `menghangatkan tubuh`, `formula produksi`, `komposisi resmi`, `gratis`,
  `diskon`, `auto-DM`, `obat`, `menyembuhkan`, `dijamin`, dan `halal` tanpa bukti.
- Draft tidak muncul di `/alkaff/api/recommendations`, tidak masuk
  `/alkaff/reward/allowlist`, dan tidak menghasilkan QR `/a/<token>`.

## Alur

```text
decision engine -> custom_draft -> draft (status draft)
                -> operator: Kirim ke Review (status review)
                -> admin: Setujui / Tolak
                -> admin membuat produk + URL terverifikasi SECARA MANUAL
                -> siklus existing_product yang boleh membuat QR
```

Status `approved` berarti **disetujui untuk ditindaklanjuti manual**, bukan
“produk jadi” dan bukan “siap dibeli”.

## Endpoint internal (JSON-RPC, `auth="user"`)

| Route | Fungsi |
|---|---|
| `POST /alkaff/api/custom-request` | Buat draft dari konsol yang sudah login Odoo |
| `POST /alkaff/api/custom-request/list` | Lihat 50 draft terakhir |
| `POST /alkaff/api/custom-request/review` | Approve/reject (guard `base.group_system` di model) |

Contoh envelope JSON-RPC:

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "alias": "viewer_demo",
    "labelName": "",
    "consentOptIn": false,
    "themeRef": "Parfum Kopi",
    "notesAman": "Keluarga aroma kopi dan vanilla (edukasi).",
    "bottleType": "spray"
  },
  "id": 1
}
```

Instalasi/upgrade hanya di DB `nml` memakai config turunan `db_filter=nml`;
jangan arahkan ke instance `8069`/`8070`.
