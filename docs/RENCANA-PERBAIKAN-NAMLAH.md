# Rencana Perbaikan Multi-Agent — Suite Odoo Namlah

Tanggal: 2026-11-26  
Objek: repo privat `muhjadkaf/Namlah`, cabang `master` (snapshot source: `/tmp/opencode/namlah-src`, dihapus setelah uji selesai)  
Mode: **rencana dulu, lalu uji coba localhost**. Belum ada perubahan kode yang diterapkan dari rencana ini.

## 1. Fakta dasar (baseline)

- 41 addon Odoo 20, 319 file Python, ~33.975 baris.
- `compileall` bersih, semua XML well-formed, tidak ada file data manifest yang hilang, tidak ada route duplikat.
- Hanya 5/41 addon yang punya tes: `namlah_catalog`, `namlah_jastip`, `namlah_pinjam`, `namlah_telegram`, `namlah_whatsapp` (6 file tes, 48 fungsi tes).
- `namlah_api` adalah modul paling kritis: ~13k LOC, 0 tes.
- 326 dekorator route; 248 `auth='none'`, 269 `csrf=False`, 245 `cors='*'`.
- 614 `sudo()`, 221 `except Exception`, 1 `_sql_constraints`, 11 titik raw SQL.
- **Koreksi:** tidak ada file `.pyc` yang ter-commit di repo (0 dari GitHub tree). Angka 319 sebelumnya adalah artefak `compileall` saat audit, bukan isi repo.
- Path addons di `/home/mintbag/odoo-dev/odoo.conf` (`/home/mintbag/Desktop/Namlah/namlah-odoo-addons`) sudah tidak ada, sehingga instance lokal `namlah_local` saat ini **tidak memuat addon Namlah**. Uji lokal memakai snapshot + DB terpisah agar instance kamu tidak terganggu.

## 2. Pembagian agen (file ownership non-overlap)

| Agen | Fokus | Kepemilikan eksklusif | Dokumen |
|---|---|---|---|
| A | Keamanan API & autentikasi | `namlah_api/controllers/*`, `scripts/check_deny_by_default.py` | `01-security-auth.md` |
| B | Tes & CI | `.github/workflows/ci.yml`, `**/tests/*`, script tes lokal | `02-tests-ci.md` |
| C | Isolasi tenant, ACL & integritas data | model/security/hooks/migrasi di `namlah_core`, `namlah_security`, `namlah_web_backend`, `namlah_accounting`, `namlah_catalog`, addon ACL lain | `03-tenant-acl.md` |
| D | Maintainability, dokumentasi & rilis | `README.md`, `namlah-odoo-addons/README.md`, `Docs/`, `.gitignore`, panduan deploy | `04-hygiene-docs.md` |

Aturan: satu file hanya satu owner. Agen A tidak menyentuh tes/CI, agen B tidak menyentuh controller, agen C tidak menyentuh `namlah_api/controllers`, agen D tidak menyentuh kode sumber/CI. Saya (orchestrator) yang menggabungkan dan menjalankan uji localhost.

### Resolusi kepemilikan yang sempat tumpang tindih

- **File tes `namlah_api/tests/`:** Agen B owns `test_auth_flow.py`, `test_http_contract.py`, `test_tenant_isolation.py`, `test_models.py`, `test_migration.py`, `test_smoke_install.py`, `test_regression_*.py`, serta selftest guard. Agen A owns **hanya** `test_security_*.py` (CSRF/CORS, PIN, rate limit, 2FA, scope) dan `namlah_security/tests/test_rate_limit.py`. Tidak ada nama file yang sama.
- **`namlah_security/__init__.py` & `__manifest__.py`:** Agen A hanya menambah pendaftaran model `namlah.rate.limit` dan cron cleanup; Agen C hanya mengubah bagian ACL/grup/data keamanan. Keduanya masuk PR terpisah dengan urutan: Agen C dulu (ACL dasar), baru Agen A (model rate limit), atau digabung oleh owner dalam satu commit dengan reviewer sama.
- **Controller selain `namlah_api`:** selama jendela deklarasi otorisasi, Agen A adalah satu-satunya penulis semua `**/controllers/*.py`. Agen B/C/D dilarang menyentuhnya; koordinasi lewat daftar deklarasi, bukan edit langsung.
- **`Docs/VERSIONS.md`:** Agen D owns format & isi; Agen B hanya menambah pengecekan drift di CI berdasarkan format yang disepakati Agen D.

## 3. Urutan eksekusi (dependency-aware)

| Fase | Agen | Hasil | Gate sebelum lanjut |
|---|---|---|---|
| F0 — Fondasi pengaman | A + B | Guard `/api` nyata, CI menjalankan tes Odoo, tes auth/CSRF/tenant gagal lebih dulu (red) | Guard terbukti tidak vacuous |
| F1 — Isolasi & ACL | C (+ B tes) | `su=True` dikurangi, record rules jadi safety net, ACL terverifikasi | Tes lintas koloni lulus |
| F2 — Auth hardening | A | KDF PIN, rate limit DB, endpoint 2FA `/code` dibatasi | Tes brute-force & 2FA lulus |
| F3 — Maintainability | D + (A/C refactor) | Doc sinkron, deploy Linux, controller monolit dipecah bertahap | CI hijau & doc drift = 0 |
| F4 — Rilis | Semua | Changelog, versi, rollback runbook | Smoke test produksi mirror |

## 4. Ringkasan eksekutif masalah

1. **P0** — CSRF/CORS pada API berbasis session cookie; tidak ada `Origin`/`Referer` check.
2. **P0** — Isolasi koloni hanya di controller karena `service_env()` memakai `su=True`; DB rules dilewati.
3. **P0** — Guard deny-by-default hanya memeriksa `/v0`, padahal semua route nyata `/api`; CI selalu hijau.
4. **P1** — PIN SHA-256 + pepper global, tanpa KDF/per-user salt; throttle in-memory.
5. **P1** — 2FA `/api/admin/authenticator/code` mengembalikan kode aktif ke sesi admin.
6. **P1** — Tes tidak jalan di CI; 36 dari 41 modul tanpa tes, termasuk `namlah_api`.
7. **P2** — Utang maintainability: `sudo()` 614, `except Exception` 221, controller monolit, doc drift/versi, path Windows absolut.
8. **P1 (temuan baru dari uji localhost)** — Drift API Odoo 20: `ir.config_parameter.get_param/set_param` sudah diganti `get_str/set_str` (`get_bool` masih ada). Masih ada 3 pemanggil `set_param` di kode produksi (`namlah_api/controllers/livekit.py` 2x, `semut_academy_bridge/controllers/main.py` 1x) dan 1 di tes `namlah_telegram`. Ini akan error saat runtime, bukan hanya saat tes.

## 5. Uji coba localhost

DB terpisah `namlah_test_20261126`, port 8071, snapshot addon `/tmp/opencode/namlah-src`, Odoo 20.0-20261114, `--without-demo=True`. Instance `namlah_local` di port 8069 **tidak** diganggu; config asli tidak diubah. Snapshot dan DB uji dibersihkan setelah sesi ini; untuk mengulang, unduh snapshot lagi atau arahkan `addons_path` ke source lokal yang valid.

Perintah inti:

```bash
cd /home/mintbag/odoo-dev/odoo-20.0.post20261114
/home/mintbag/odoo-dev/venv/bin/python -m odoo server \
  -c /home/mintbag/odoo-dev/odoo.conf -d namlah_test_20261126 \
  --addons-path=/tmp/opencode/namlah-src/namlah-odoo-addons,/home/mintbag/odoo-dev/odoo-20.0.post20261114/odoo/addons,/home/mintbag/Desktop/librarian \
  --http-port=8071 \
  -i namlah_pinjam,namlah_catalog,namlah_jastip,namlah_whatsapp,namlah_telegram \
  --without-demo=True --test-enable \
  --test-tags=/namlah_pinjam,/namlah_catalog,/namlah_jastip,/namlah_whatsapp,/namlah_telegram \
  --stop-after-init --log-level=warn --logfile=/tmp/opencode/odoo-test.log
```

### Hasil

**EXIT 1 — 50 tes dijalankan: 38 lulus, 1 gagal, 11 error.** Instalasi modul berhasil; kegagalan ada di fixture tes, bukan kegagalan install.

| Modul | Hasil | Akar masalah |
|---|---|---|
| `namlah_pinjam`, `namlah_jastip` | Lulus | — |
| `namlah_catalog` (`test_koloni_dashboard.py`) | 5 error | Fixture membuat user Ratu dengan `company_ids=[company_a]` tapi `company_id` default masih "My Company". Odoo 20 `_check_user_company` menolak (`ValidationError`), transaksi abort, lalu 4 tes berikutnya kena `duplicate key res_company_name_uniq` / `InFailedSqlTransaction`. Nama company juga memakai string tetap `koloni_dash_a` (tidak UUID). |
| `namlah_telegram` | 6 error | `setUp` memanggil `ir.config_parameter.set_param()`, yang **tidak ada lagi** di Odoo 20 (`AttributeError`). Kode produksi telegram sudah memakai `get_bool()`, jadi ini bug tes. |
| `namlah_whatsapp` | 1 gagal | `test_task_assignment_notifies_assignee` membuat task tanpa `x_namlah_koloni_code`. `project.task.write()` sengaja melewati task tanpa kode koloni (`if not koloni: continue`), jadi event `misi.diambil` tidak terbit dan log WA tidak dibuat. Fixture perlu kode koloni. |

Peringatan non-fatal saat install:
- `Skipping deletion for missing XML ID namlah_pinjam.product_template_form_namlah_pinjam` — data drift di `namlah_pinjam`.
- Dua field `res.config.settings` punya label sama ("Mode simulasi (dry-run)") dari `namlah_telegram` dan `namlah_whatsapp`.
- `markdown2` tidak terpasang (diagnosa mail, tidak memblokir).

### Tindak lanjut yang dimasukkan ke rencana

1. **Agen B** — perbaiki 3 fixture tes: set `company_id=company_a` + UUID pada nama company di `test_koloni_dashboard.py`; ganti `set_param` → `set_str` di `test_namlah_telegram.py`; tambah `x_namlah_koloni_code` pada task di `test_namlah_whatsapp.py`. Ulangi `--test-tags` yang sama sampai 50/50 hijau.
2. **Agen A** — ganti 3 pemanggil `set_param` di `namlah_api/controllers/livekit.py` dan `semut_academy_bridge/controllers/main.py` ke API Odoo 20 (`set_str`), atau satu helper kompatibilitas. Tambah test regresi.
3. **Agen C** — bersihkan XML ID `product_template_form_namlah_pinjam` yang sudah tidak ada (hapus entri `<delete>` atau pulihkan view).
4. **Agen D** — samakan label dua field dry-run dan catat perubahan API Odoo 20 di panduan migrasi.

**Status uji saat ini: MERAH.** Rencana perbaikan di atas harus dikerjakan sebelum CI dianggap hijau; gate F0 belum terpenuhi.

## 6. Catatan keamanan

Token akses GitHub pernah ditempel di chat dan masih valid pada saat audit. **Segera revoke/rotate** di GitHub. Token tidak disimpan ke file mana pun; snapshot privat dibaca melalui header Authorization dan akan dihapus setelah uji selesai.

---

## Bagian teknis dari agen

# Rencana Agen A — Security & Auth

> Repository: `muhjadkaf/Namlah` (private), cabang `master`.
> Dasar: snapshot source di `/tmp/opencode/namlah-src` (read-only, tidak diubah).
> Dokumen ini **rencana**, bukan implementasi. Tidak ada kode implementasi penuh di sini.

---

## 1. Ringkasan tanggung jawab & file kepemilikan eksklusif

Agen A bertanggung jawab atas **primitive keamanan lintas-addon**, **autentikasi/PIN/OTP/2FA**, **guard deny-by-default**, **isolasi tenant di layer API**, dan **bukti teruji (test acceptance)** untuk kesemua itu. Agen A tidak mengubah fitur bisnis, skema UI, atau alur data kecuali lewat primitive bersama yang disepakati.

### 1.1 Kepemilikan eksklusif (Agen A satu-satunya yang menulis)

| Path relatif (dari root repo) | Isi yang diubah |
|---|---|
| `namlah-odoo-addons/namlah_api/controllers/_decorators.py` | Dekorator universal `namlah_route` / `namlah_authz`, registry deklarasi runtime, enforcement peran/scope |
| `namlah-odoo-addons/namlah_api/controllers/helpers.py` | `service_env` → pemisahan `system_env` / `tenant_env`, scope koloni terpusat, verifikasi PIN KDF, helper Origin/Referer |
| `namlah-odoo-addons/namlah_api/controllers/auth.py` | Login (PIN + password), throttle, session |
| `namlah-odoo-addons/namlah_api/controllers/auth2.py` | PIN set/delete, change-password, sapaan |
| `namlah-odoo-addons/namlah_api/controllers/recovery.py` | Forgot/reset PIN & password, verifikasi email (integrasi rate limit DB) |
| `namlah-odoo-addons/namlah_api/controllers/authenticator.py` | Endpoint 2FA `/api/admin/authenticator/*` |
| `namlah-odoo-addons/namlah_api/controllers/__init__.py` | Import modul baru & assertion registry saat load |
| `namlah-odoo-addons/namlah_security/models/__init__.py` **(baru)** | Export model rate limit |
| `namlah-odoo-addons/namlah_security/models/namlah_rate_limit.py` **(baru)** | Model event rate-limit DB-backed |
| `namlah-odoo-addons/namlah_security/__init__.py`, `__manifest__.py` | Daftar model + data cron cleanup (perubahan minimal, dikoordinasikan dengan Agen ACL/DB) |
| `namlah-odoo-addons/namlah_security/security/rate_limit_cron.xml` **(baru)** | Cron retensi event rate limit |
| `scripts/check_deny_by_default.py` | Guard AST yang benar-benar memindai `/api/` |
| `scripts/api_route_inventory.json` **(baru)** | Baseline inventaris route → peran/scope |
| `namlah-odoo-addons/namlah_api/tests/test_security_*.py` **(baru)** | Test CSRF/CORS, PIN, rate limit, 2FA, scope |
| `namlah-odoo-addons/namlah_security/tests/test_rate_limit.py` **(baru)** | Test model rate limit lintas-"worker" |

### 1.2 Kepemilikan bersama / koordinasi (Agen A **tidak** menulis sendiri)

| Path relatif | Agen mitra | Peran Agen A |
|---|---|---|
| `.github/workflows/ci.yml` | CI/tests | Kirim definisi step (guard + test Odoo + dependency KDF); minta hapus `continue-on-error` |
| `namlah-odoo-addons/*/controllers/*.py` selain di atas (326 route) | Feature/endpoint agent | Agen A menyiapkan **daftar deklarasi** per route; suntingan dilakukan dalam **jendela khusus** agar tidak tabrakan |
| `namlah_web_backend/security/restrictions.xml`, `namlah_security/security/ir.access.csv` | ACL/DB | Spesifikasi domain `company_id` yang dibutuhkan; Agen A tidak mengubah aturan akses DB |
| `packages/namlah_shared/lib/src/api_client_base.dart` | Client/Flutter | Spesifikasi header wajib & penanganan 403; perubahan klien oleh mitra |
| `Docs/PRODUCTION-CUTOVER.md`, `Docs/Perencanaan-Namlah.md` | Docs/ops | Narasi risiko, flag, dan keputusan owner; Agen A hanya menyuplai konten |

### 1.3 Prinsip batasan kerja

- Tidak ada pencarian atau penggunaan kredensial/rahasia nyata di snapshot; tidak ada nilai rahasia yang ditulis ke dokumen ini.
- Semua perubahan keamanan **additive & berflag** (`ir.config_parameter`) agar bisa dimatikan tanpa migrate mundur.
- Identitas tetap di-resolve server-side dari sesi Odoo (`request.session.uid` / `get_actor()`), bukan dari body klien — ini **tidak diubah**.

---

## 2. Tabel masalah → dampak → solusi → prioritas → acceptance criteria

| ID | Masalah (fakta snapshot) | Dampak | Solusi konkret | Prioritas | Acceptance criteria (lihat §6) |
|---|---|---|---|---|---|
| **S1** | 326 `@http.route`; 248 `auth='none'`, 269 `csrf=False`, 245 `cors='*'`; **tidak ada** pengecekan `Origin`/`Referer` di controller. Identitas dari cookie sesi. | Situs jahat dapat memicu POST/DELETE lintas-origin dengan cookie korban (CSRF); wildcard CORS menghapus perlindungan same-origin untuk traffic non-credentialed dan melebarkan surface WebView/web build. | Rekomendasi utama: harden API session-based = Origin/Referer allowlist + header wajib untuk mutasi + `SameSite` cookie + hapus `cors='*'` → allowlist. Alternatif: kredensial bearer + `device_session` (ADR Fase 3). | **P0** | `T04–T08`, `T03b` |
| **S2** | `scripts/check_deny_by_default.py` hanya memindai `/v0/`; **tidak ada** route `/v0` nyata ⇒ CI lolos vacuous. `namlah_route` tidak pernah dipakai dan **melewati validasi untuk `/api/`**. Guard "no files found → exit 0". | Ilusi keamanan: CI hijau tanpa satu pun endpoint terlindungi; peran/scope tidak pernah dideklarasikan. | Guard memindai `/api/`, deklarasi `peran` + `scope` wajib, baseline count, negative test, runtime registry assertion, job CI tanpa `continue-on-error`. | **P0** | `T01–T03`, `T19` |
| **S3** | `helpers.py:service_env()` = `request.env(user=2, su=True)`; 274 pemanggil. Isolasi koloni hanya domain di controller; manifest `namlah_web_backend` mengakui API tidak kena rules. | Satu domain yang terlewat = kebocoran lintas koloni; `ir.access`/record rules tidak pernah melindungi jalur API. | Pusatkan `tenant_env(actor)` (tanpa `su`) + `koloni_domain(actor)` + `assert_koloni_scope()`; `su=True` hanya di `system_env()` untuk tugas sistem; kompensasi record rules + tes oleh Agen ACL/DB. | **P0** (bertahap) | `T09–T11` |
| **S4** | `hash_pin()` = SHA-256 + pepper global ICP (default bawaan), tanpa KDF & tanpa salt per user; 11 pemanggil, PIN disimpan di `namlah.pin.<uid>` ICP. | Offline cracking murah; semua user dengan PIN sama punya hash sama; rotasi rahasia tidak mungkin tanpa reset massal. | KDF (Argon2id utama; bcrypt/scrypt alternatif) + salt acak per user + model kredensial baru; upgrade saat login/reset berhasil; legacy dibaca sebentar lalu dipensiunkan. | **P0** | `T12`, `T13` |
| **S5** | Throttle login (`_attempts`) & OTP request (`_rate_buckets`) = `threading.Lock` + dict in-memory; hilang saat restart, tidak jalan multi-worker. | Brute-force PIN & banjir OTP bisa diulang dengan restart /lintas worker; OTP email bisa dipakai untuk spam biaya. | Model `namlah.rate.limit` DB-backed (insert-only event + indeks), identitas di-HMAC, cleanup cron, atomic count; reuse tabel rate-limit TOTP bawaan Odoo; fail-closed untuk login. | **P0** | `T14`, `T15`, `T21` |
| **S6** | `GET /api/admin/authenticator/code` mengembalikan kode TOTP aktif ke pemegang sesi admin; `activate` menyimpan secret di server. | Faktor kedua melebur ke sesi: XSS/session theft/CSRF ⇒ 2FA bypass. Keputusan owner dicatat, tapi perlu opsi aman. | Hapus `/code` setelah enrollment; `setup`/`enable`/`disable` butuh re-authentication (step-up); `activate` di balik flag + audit; tawarkan mode "perangkat eksternal saja". | **P1** | `T17`, `T18`, `T22` |
| **S7** | Heuristik AST: ~74 route POST/PUT/DELETE tanpa pola otorisasi eksplisit (dari ~173 route mutasi). | Sebagian bisa jadi celah (admin/roles/wallet/checkout), sebagian aman via helper — **belum bisa divonis**. | Inventarisasi + verifikasi per route, kategori A–E, deklarasi `namlah_authz`, test wrong-role 403. Default: belum terverifikasi = deny. | **P1** | `T19`, `T20` |
| **S8** | OTP email `namlah.email.otp` sudah salt+hash, TTL 10 mnt, 5 attempts, cooldown 60 dtk, once-used. | Regresi jika diubah saat integrasi rate limit. | **Jangan ubah** logika inti; hanya integrasikan throttle request di `recovery.py` + regresi test. | P2 (jaga) | `T16` |

Catatan S1: `Access-Control-Allow-Origin: *` tidak otomatis mengizinkan *credentialed read* di browser, tetapi kombinasi `auth='none'` + `csrf=False` + cookie sesi tetap menerima mutasi lintas-origin (simple request), jadi risikonya nyata.

---

## 3. Detail langkah

### (a) CSRF/CORS untuk API session-based — **rekomendasi utama**

**Pilih: harden session cookie (defense-in-depth), bukan migrasi besar di sprint ini.**

Alasan: seluruh klien sudah memakai cookie sesi (Flutter `Dio` + `PersistCookieJar` di `packages/namlah_shared/lib/src/api_client_base.dart`; web build Flutter same-origin di `/app/`), 326 route sudah berbasis session, dan ADR menyebut migrasi kredensial sebagai target menengah — bukan sesuatu yang bisa dilewati dalam satu perbaikan. Mekanismenya:

1. **Origin/Referer check** di satu helper pusat, dipanggil otomatis oleh `namlah_route` untuk `methods` mutasi (POST/PUT/PATCH/DELETE):
   - Jika `Origin` ada → harus `scheme://host[:port]` yang ada di allowlist ICP `namlah.security.allowed_origins` ( default: origin aplikasi `https://namlah.lokal.or.id` dan host same-origin).
   - Jika `Origin` absen → jatuhkan ke `Referer` (untuk WebView lama); `Referer` harus origin yang sama/allowlisted.
   - Keduanya absen → **wajib** header `X-Namlah-Client` (client id sederhana, bukan rahasia). Client native/web menambahkannya; browser lintas-origin tidak bisa mengirim header ini tanpa preflight CORS, dan preflight dari origin di luar allowlist ditolak.
   - Tolak dengan `403` + `Cache-Control: no-store`, tanpa efek samping.
2. **SameSite cookie**: pastikan cookie sesi API `HttpOnly`, `Secure`, dan `SameSite=Lax` (cukup karena mutasi hanya POST); untuk `/api/admin/*` pakai `SameSite=Strict`. Jangan pernah `SameSite=None` tanpa `Secure`. Perlu verifikasi terhadap konfigurasi Odoo/Caddy — Agen A menulis spesifikasi, ops yang menerapkan.
3. **Batu CORS**: hapus semua `cors='*'`. `namlah_route` menerima `cors` dari allowlist ICP yang sama; `Access-Control-Allow-Credentials` hanya dikirim untuk origin yang benar-benar diizinkan. `/api/admin/*` = same-origin only (tanpa CORS).
4. **Flag rollback** per kontrol: `namlah.security.origin_check_enabled`, `namlah.security.require_client_header`, `namlah.security.cors_allowlist`, `namlah.security.samesite`. Default ON di staging/prod setelah canary; OFF hanya break-glass.
5. **Pengecualianterkontrol**: webhook masuk (`inbound_email`, `telegram`) dan health check dideklarasikan `scope='public'` + justifikasi, tetap tidak boleh menerima cookie Untuk webhook, verifikasi ditandatangani oleh mitra (bukan Agen A.)

**Alternatif (dicatat, bukan dipilih sekarang):** migrasi ke kredensial bearer opak + `device_session` lewat header `Authorization`, cookie API dihapus — sesuai arah ADR Fase 3. Keuntungan: CSRF structibeliminasi, cocok multi-worker/offline-first. Biaya: migrasi 326 route + seluruh klien + mekanisme refresh/revoke; risiko regressi tinggi. Jika owner memilih ini, lakukan **setelah** S1–S5 hijau, dengan mode dual-auth sementara (cookie + header) dan sunset cookie yang diumumkan.

**Ketergantungan**: Agen Client/Flutter menambah header & menangani 403; Agen Ops mengunci SameSite/Caddy; Agen Docs mencatat allowlist.

### (b) Deny-by-default guard yang benar-benar memindai `/api/`

**Dekorator (`_decorators.py`)**
- Ganti kontrak `namlah_route(rule, methods, peran, scope, ...)`. `scope` ∈ `{'koloni', 'global', 'public'}`; `peran` non-kosong, kecuali `scope='public'` yang wajib `justification` non-kosong.
- **Hapus** cabang `if not rule.startswith('/v0/'): return http.route(...)` — untuk `/api/` dekorator wajib memvalidasi, bukan memotong. `/v0` boleh dipertahankan sebagai alias kompatibel.
- Dekorator juga mendaftar `(rule, methods, peran, scope, file, line)` ke `_REGISTERED_API_ROUTES`; `namlah_api/controllers/__init__.py` membandingkan registry saat load terhadap `scripts/api_route_inventory.json` dan **raise** bila ada route yang tidak terdaftar/selenarasa saat modul dijalankan dengan mode `test`/`prod`.

**Guard AST (`scripts/check_deny_by_default.py`)**
- Scan `namlah-odoo-addons/**/controllers/*.py`; kumpulkan semua `@http.route` **dan** `@namlah_route` yang argumen pertama berawalan `/api/`.
- Violation bila: memakai `@http.route` biasa; `peran` tidak ada/kosong; `scope` tidak ada; `scope='public'` tanpa justifikasi; `cors='*'`; `auth='none'` pada mutasi tanpa deklarasi; path tidak ada di inventory atau inventory punya entri yang tidak ditemukan di source.
- **Anti-vacuous**: (1) `files == 0` atau `routes == 0` ⇒ **exit 1** (ubah perilaku lama); (2) jumlah route ter-scan harus ≥ baseline yang dikunci (≈300) dan sama dengan inventory; (3) negative fixture test: file dengan `@http.route('/api/x', ...)` tanpa `peran` harus menghasilkan exit 1; (4) CI job `deny-by-default` tanpa `continue-on-error`; (5) guard juga memeriksa `namlah_route` tidak lagi mengandung `startswith('/v0/')` bypass.

**Rollout**: 2 minggu mode `warn` (lapor violation tapi exit 0) sambil mitra menambah deklarasi → lalu `enforce`. Inventory di-commit sebagai kontrak, bukan dihitung diam-diam dari source yang sama (kalau tidak, guard self-fulfilling).

### (c) Isolasi tenant — pusatkan scope, kurangi `su=True`

**Trade-off yang harus diterima**: menghapus `su=True` dari 274 pemanggil berisiko memunculkan ACL yang belum ada ⇒ 403/500 di produksi. Record rules/`ir.access` **tidak berlaku** untuk `su=True`, sehingga aturan DB hanya melindungi sesi `/web`, bukan API — jadi rules saja bukan solusi. Sebaliknya, domain di controller rapuh: satu `search()` lupa domain = bocor.

**Rencana:**
1. Perkenalkan di `helpers.py`:
   - `tenant_env(actor)`: `request.env(user=actor['uid'])`, `allowed_company_ids` = company koloni actor + turunannya; **tanpa `su`**. Dipakai untuk semua baca/tulis data tenant.
   - `system_env()`: mantan `service_env()`, `su=True` eksplisit, hanya untuk peerjaan sistem (mail, ID mapping, agregasi global ratu/admin, cron).
   - `koloni_domain(actor, field='x_koloni_code')`: satu-satunya sumber domain koloni; `koloni_or_admin` / `koloni_or_global` didelegasikan ke sini atau dideprecasi dengan warning.
   - `assert_koloni_scope(actor, koloni_code)`: dipanggil **sebelum** `tenant_env()`, menggantikan pengecekan tersebar.
2. Migrasi bertahap per kelompok model, bukan big bang: **(i)** uang & PII (`sale.order`, `payment.transaction`, `res.partner`, `wallet`, `project.task`), **(ii)** konten koloni (catalog, forum, task), **(iii)** sisa. Setiap kelompok punya test isolasi dua koloni.
3. **Shadow mode** 1–2 minggu: log ketidaksesuaian antara domain `x_koloni_code` dan domain `company_id`; setelah nol mismatch, enforce.
4. Endpoint yang sah lintas-koloni (KPI admin, kurasi, dashboard agregat) tetap pakai `system_env()` **tetapi** wajib `scope='global'` + `peran=['admin', 'ratu']` + audit log. Tidak ada `su=True` "karena malas".
5. Agen ACL/DB menambah/menguat `ir.access` restriction `(company_id in company_ids)` pada model yang dipakai API, plus indeks `company_id`/`x_koloni_code`. Ini **kompensasi**, bukan pengganti langkah 1–4.
6. Audit 15 lokasi `su=True` di luar `service_env()` (telegram, store, qr, website, jastip, project_task) — masuk daftar S3 sebagai utang teknis yang diberi `scope='global'`/`system_env()` atau dikonversi ke `tenant_env`.

### (d) PIN: KDF + salt per user + migrasi bertahap

- Model kredensial baru (di `namlah_security` atau field baru di `res.users`): `user_id`, `kdf` (`argon2id`), `salt` (acak per user), `hash`, `params`, `created_at`, `rotated_at`. PIN **tidak lagi** disimpan di `namlah.pin.<uid>` ICP untuk data baru.
- Fungsi verifikasi terpusat di `helpers.py`: baca kredensial baru → verifikasi KDF (constant-time). Bila belum ada → verifikasi legacy (SHA-256 + pepper yang sudah ada) → **jika berhasil, tulis ulang (upgrade) ke KDF** secara opportunistic. PIN plaintext tidak pernah masuk log/response.
- Semua jalur tulis PIN (`auth2.py` POST/DELETE, `recovery.py` reset, seed awal) memakai fungsi tulis yang sama; seed dengan format lama ditandai perlu upgrade.
- Pepper dipindah dari nilai bawaan ICP ke rahasia yang di-inject lingkungan; nilai lama tetap dibaca hanya selama masa transisi (label versi, bukan nilai). Tidak ada hardcode default baru.
- Parameter Argon2id awal: memory ≈64 MiB, time=2, parallelism=1 (dapat diatur via ICP, tapi ada batas aman). Dependency (`argon2-cffi` atau passlib setara) ditambahkan oleh Agen CI.
- Cutoff: setelah ~90 hari atau 95% akun ter-upgrade, legacy path dimatikan via flag; akun dormant dipaksa reset PIN melalui OTP. `namlah.pin.<uid>` lama **jangan dihapus** sampai cutoff (rollback aman).

### (e) Rate limit DB-backed & strategi multi-worker

- Model baru `namlah.rate.limit` (di `namlah_security`): `scope` (`login_pin`, `otp_request`, `otp_verify`, `totp_check`), `identifier_hash` (HMAC dari identifier + IP, kunci rahasia terpisah; **tidak** menyimpan plaintext/email/HP), `create_date`, `metadata` minimal. Indeks `(scope, identifier_hash, create_date)`.
- **Insert-only event** dipilih daripada counter upsert: konkurensi aman dengan sendirinya (setiap worker tinggal `CREATE`), keputusan = `COUNT(*)` dalam window dengan indeks; tidak ada race `read-then-write`. Cron hapus event > 24 jam.
- `auth.py` dan `recovery.py` memanggil helper `rate_check(scope, identifier, ip, limit, window)` yang sama; `threading.Lock`/dict dihapus. Untuk TOTP, **pakai** `auth.totp.rate.limit.log` bawaan Odoo (jangan duplikat).
- Multi-worker: DB adalah sumber kebenaran; semua worker (proses Odoo berbeda) melihat counter sama. Opsi optimasi cache lokal diperbolehkan hanya untuk *short-circuit reject*, bukan untuk mengizinkan saat DB belum dibaca.
- **Fail-closed** untuk `login_pin` saat DB error ⇒ `503` (lebih baik menolak daripada brute-force tak terbatas); untuk `otp_request` boleh fail-closed `503` dengan pesan netral. Tidak pernah jatuh ke "allow" diam-diam.
- Respons pemulihan tetap netral (tidak membocorkan ada/tidaknya akun) — kontrak lama dipertahankan.

### (f) Endpoint 2FA `/code` — hapus/batasi hanya enrollment

- **Rekomendasi**: hapus `GET /api/admin/authenticator/code` setelah fitur enrollment tersedia. Kode TOTP tidak boleh bisa diambil dari sesi yang sama dengan faktor pertama.
- Jika owner tetap ingin kenyamanan: `/code` **hanya** tersedia sebelum `totp_enabled=True` (fase enrollment), untuk memverifikasi kode QR; setelah aktif → `404/410` untuk semua, termasuk admin. Flag `namlah.auth.totp.allow_server_code` default **False**.
- `setup`, `enable`, `disable`, `activate` wajib **step-up**: login ulang password atau verifikasi OTP dalam ≤5 menit (field `last_auth_at` di sesi). `activate` (standalone, secret disimpan server) tetap boleh hanya dengan flag eksplisit + peringatan di UI + audit log.
- Audit log: setiap `enable`/`disable`/`activate`/akses `/code` ditulis dengan `uid`, IP, waktu, hasil (via model audit baru atau `ir.logging`).
- Tawarkan opsi aman: mode "perangkat eksternal wajib" (nonaktifkan `activate`, hapus `/code`) sebagai default baru untuk akun admin.

### (g) Inventarisasi & verifikasi ~74 route mutasi tanpa otorisasi eksplisit

1. Generate laporan AST: `file:line`, path, method, `auth`, apakah `get_actor()` dipanggil, helper otorisasi yang dipakai (`koloni_scope_error`, `is_ratu_or_admin`, `has_active_role`, ...), dan apakah sudah ada deklarasi `namlah_authz`.
2. Klasifikasi:
   - **A – public by design**: health, customer promo, webhook → `scope='public'` + justifikasi.
   - **B – session any actor**: ada `get_actor()`, tidak ada pembatasan peran → `peran=['member']`, `scope='koloni'`.
   - **C – role-gated**: kasir/kurir/ratu/admin → `peran=[...]` eksplisit.
   - **D – global**: agregat lintas koloni → `scope='global'`, `peran=['admin', 'ratu']` + audit.
   - **E – unknown**: **default deny**; tidak boleh masuk produksi sebelum diverifikasi manual.
3. Prioritas verifikasi: `admin.py`, `roles.py`, `wallet.py`, `checkout.py`, `colonies.py`, `phototasks.py` (uang, izin, identitas) lebih dulu.
4. Setiap route yang diklasifikasi A–D mendapat deklarasi + satu test wrong-role → `403`. Tidak ada vonis "rentan" tanpa verifikasi; laporan menyebut status "terverifikasi"/"butuh review".

---

## 4. Urutan kerja & ketergantungan

| Tahap | Kerja Agen A | Ketergantungan |
|---|---|---|
| **0 — Fondasi (tanpa perilaku berubah)** | Inventory AST 326 route + 74 mutasi; perbaiki guard jadi scan `/api/`; commit `api_route_inventory.json`; negative test guard | CI: pasang step guard (warn mode dulu), jangan `continue-on-error` |
| **1 — Guard enforce + deklarasi** | `namlah_route`/`namlah_authz` + registry; deklarasi massal lewat jendela suntingan; alias `/v0` dihapus bypass-nya | Feature agent: terima daftar deklarasi; CI: flip warn → enforce |
| **2 — CSRF/CORS hardening** | Helper Origin/Referer + header + flag; hapus `cors='*'`; spesifikasi SameSite | Client/Flutter: header `X-Namlah-Client` & 403 handling; Ops: cookie/Caddy; Docs: allowlist & keputusan |
| **3 — PIN + rate limit** | Model `namlah.rate.limit`, cron; KDF + upgrade opportunistic; pindahkan throttle `auth.py`/`recovery.py` | CI: dependency KDF & runner Postgres; ACL/DB: indeks & migrasi; Ops: injection rahasia |
| **4 — Isolasi tenant** | `tenant_env`/`system_env`/`koloni_domain`/`assert_koloni_scope`; shadow mode → enforce per kelompok model | ACL/DB: `ir.access` + computed `company_id`; Feature agent: ganti pemanggil `service_env()` |
| **5 — 2FA `/code` + audit** | Hapus/batasi `/code`, step-up, flag, audit log | Docs/owner: tanda tangan perubahan perilaku; Client: alur enrollment baru |
| **6 — Verifikasi akhir** | Seluruh test acceptance hijau; laporan S7 tidak ada status `unknown` | CI: Odoo `--test-tags`; Docs: update `PRODUCTION-CUTOVER.md` |

**Ketergantungan lintas-agent ringkas**
- **CI/tests**: wiring guard + test Odoo (butuh instance + Postgres), negative test guard, dependency KDF, hapus `continue-on-error`.
- **ACL/DB**: aturan `ir.access` berbasis `company_id`, indeks rate-limit, cron cleanup, migrasi skema — Agen A hanya memberi spesifikasi domain.
- **Client/Flutter**: header mutasi, penanganan 403, alur 2FA; tanpa ini S1/S6 tidak bisa diaktifkan penuh.
- **Docs/ops**: keputusan owner (strategi CSRF vs kredensial bearer; opsi 2FA aman), rotasi rahasia, allowlist origin, status checklist produksi.

---

## 5. Risiko & rollback

| Risiko | Mitigasi | Rollback |
|---|---|---|
| Origin/header check memutus Telegram Mini App / WebView / web build | Allowlist eksplisit + canary staging + flag per kontrol | Set `namlah.security.origin_check_enabled=False` & `require_client_header=False`; CORS allowlist dikembalikan sementara (bukan `*` di produksi) |
| SameSite=Strict memutus alur redirect login | Mulai `Lax`; Strict hanya `/api/admin/*`; uji WebView | Flag samesite → `Lax` |
| Guard enforce membuat CI merah di semua branch | 2 minggu warn mode + baseline inventory + daftar deklarasi siap | Kembalikan mode warn (job tetap jalan, violations dilaporkan) — **jangan** hapus guard |
| `tenant_env` menimbulkan 403/500 karena ACL belum lengkap | Shadow mode + migrasi per kelompok model + test dua koloni per kelompok | Flag per kelompok: fallback ke `system_env()` hanya untuk kelompok itu, dengan log; perbaiki ACL lalu aktifkan lagi |
| KDF menaikkan CPU / latency login | Parameter konservatif + throttle saat backfill + tidak ada backfill plaintext | Kembalikan verifikasi legacy path (flag), kredensial baru tetap tersimpan |
| Tabel rate limit membengkak | Cron >24 jam + indeks + HMAC identifier | Matikan cron sementara = tidak ada penghapusan; penghapusan manual aman karena event bersifat agregat |
| Fail-closed rate limit membuat user tidak bisa login saat DB error | Alerting + circuit breaker jangka pendek (≤5 mnt) dengan log | Flag `namlah.security.rate_fail_open` HANYA untuk insiden, wajib dicatat & diaudit |
| Penghapusan `/code` mengganggu admin | Flag + mode enrollment-only + opsi perangkat eksternal | Aktifkan kembali `/code` hanya saat enrollment via flag, bukan setelah 2FA aktif |

**Aturan rollback umum**: satu commit per kontrol, skema **additive** (kolom/model baru, tidak ada `DROP` dalam jendela rollback), flag ICP untuk setiap perubahan perilaku, dan log audit setiap perubahan flag. Tidak ada penghapusan hash legacy / event lama sebelum cutoff yang ditandatangani.

---

## 6. Daftar tes acceptance

| ID | Nama test | Skenario | Ekspektasi |
|---|---|---|---|
| `T01` | `test_guard_detects_api_route_without_authz` | Beri AST fixture `@http.route('/api/x', ...)` tanpa `peran` | `check_deny_by_default.py` exit 1, pesan menyebut path & baris |
| `T02` | `test_guard_fails_when_zero_routes_scanned` | Jalankan guard pada direktori controller kosong | exit 1 (tidak lagi "skipping OK") |
| `T03` | `test_guard_baseline_matches_inventory` | Hitung route `/api/` dari source vs `api_route_inventory.json` | Jumlah sama; selisih ⇒ exit 1 |
| `T03b` | `test_no_wildcard_cors` | Scan AST seluruh `@http.route`/`@namlah_route` | Tidak ada `cors='*'`; preflight dari origin di luar allowlist tanpa `Access-Control-Allow-Origin` |
| `T04` | `test_origin_rejects_foreign_origin_on_post` | POST `/api/...` dengan `Origin: https://evil.example`, sesi valid | 403, tidak ada perubahan DB |
| `T05` | `test_origin_allows_same_origin_and_allowlisted` | POST dengan Origin same-origin / allowlisted (Mini App) | 200, respons normal |
| `T06` | `test_referer_fallback` | POST tanpa `Origin`, `Referer` allowlisted | 200; `Referer` asing ⇒ 403 |
| `T07` | `test_session_cookie_attributes` | Login lalu periksa `Set-Cookie` | `HttpOnly`, `Secure`, `SameSite=Lax` (admin: `Strict`); tidak ada `SameSite=None` tanpa `Secure` |
| `T08` | `test_custom_header_required_for_mutations` | POST tanpa `X-Namlah-Client` vs dengan header | Tanpa header ⇒ 403; dengan header + sesi ⇒ 200; GET publik tidak terpengaruh |
| `T09` | `test_service_env_no_su_for_tenant_scope` | Scan AST helper tenant-scoped | Tidak ada `env(user=2, su=True)` di jalur tenant; hanya di `system_env()` |
| `T10` | `test_cross_koloni_read_denied` | User koloni A panggil `/api/...?koloniCode=B` (dan read ORM langsung) | 403 / hasil kosong; ORM non-su juga ditolak aturan DB |
| `T11` | `test_admin_global_scope_explicit` | Admin dengan `scope='global'` baca agregat lintas koloni | 200 + entri audit; actor biasa ⇒ 403 |
| `T12` | `test_pin_kdf_verify_and_upgrade` | PIN legacy: login sekali, lalu login lagi | Login pertama sukses & kredensial berubah ke KDF; login kedua verifikasi KDF; plaintext tidak tersimpan |
| `T13` | `test_pin_per_user_salt_unique` | Dua user dengan PIN 6 digit sama | Hash berbeda; `kdf`/`salt` terisi |
| `T14` | `test_pin_rate_limit_shared_across_workers` | Dua worker/proses secara bergantian kirim PIN salah | 6th attempt dalam window ⇒ 429; setelah window ⇒ diizinkan; counter di DB |
| `T15` | `test_otp_request_rate_limit_survives_restart` | 5 request OTP, restart proses, request ke-6 | 429; counter tetap (DB-backed); respons tidak membocorkan keberadaan akun |
| `T16` | `test_otp_existing_security_preserved` | Uji OTP kedaluwarsa, 5 attempts salah, cooldown 60 dtk, pemakaian ulang | TTL 10 mnt / `too_many` / cooldown / once-used masih berlaku (regresi) |
| `T17` | `test_authenticator_code_not_available_after_enable` | Aktifkan TOTP lalu GET `/api/admin/authenticator/code` | 404/410 untuk semua peran; saat enrollment (nonaktif) boleh jika flag diizinkan |
| `T18` | `test_authenticator_enrollment_requires_stepup` | `setup`/`enable`/`disable`/`activate` tanpa re-auth ≤5 mnt | 403; dengan step-up ⇒ 200 + entri audit |
| `T19` | `test_authorization_inventory_no_unknown` | Laporan S7 setelah deklarasi | 0 kategori `unknown`; semua 74 route punya kategori A–D & deklarasi |
| `T20` | `test_wrong_role_mutating_route_403` | Parameterized untuk route uang/role/PIN/2FA: actor `member` memanggil endpoint ratu/admin | 403 untuk semua; tidak ada efek samping |
| `T21` | `test_fail_closed_on_rate_limit_db_error` | Patch DB rate-limit agar raise saat login | 503, bukan "allow"; log insiden tercatat |
| `T22` | `test_audit_log_on_totp_change` | Enable + disable 2FA | Dua entri audit berisi uid, IP, waktu, hasil |

**Exit criteria Agen A**: S1–S5 hijau (P0), S6–S7 hijau (P1), tidak ada test yang dilewati, guard tidak vacuous (T01–T03), dan semua perubahan perilaku memiliki flag rollback yang terdokumentasi.

---

*Menjaga batas: dokumen ini tidak berisi nilai rahasia, tidak menyarankan pencarian kredensial di snapshot, dan tidak mengubah file source apa pun.*

---

# Rencana Agen B — Tests & CI

## 0. Kondisi awal (ringkas)

- 41 addon Odoo 20; hanya 5 yang punya tes: `namlah_catalog`, `namlah_jastip`, `namlah_pinjam`, `namlah_telegram`, `namlah_whatsapp` — total 6 file `test_*.py`, 48 fungsi `def test_`.
- Modul paling kritis, `namlah_api` (~50 file controller/model, ~13k LOC), **0 tes**. Route nyata semuanya di bawah `/api/...`.
- `.github/workflows/ci.yml` saat ini hanya: `compileall`, sanity manifest, guard `/v0`, pengecekan owner, dan Flutter analyze/test. **Belum ada job Odoo + PostgreSQL yang menjalankan tes Python.**
- Guard `scripts/check_deny_by_default.py` memindai awalan `/v0/`, sedangkan endpoint produksi memakai `/api/...` → guard lolos secara *vacuous*. `controllers/_decorators.py` juga secara eksplisit melewati validasi untuk `/api/`.
- Mesin lokal: Odoo 20 di `/home/mintbag/odoo-dev/odoo-20.0.post20261114`, venv `/home/mintbag/odoo-dev/venv/bin/python`, config `/home/mintbag/odoo-dev/odoo.conf` (addons_path-nya menunjuk path lama yang sudah hilang), Postgres bundled dengan socket dir `/home/mintbag/odoo-dev/pgdata`, user DB `odoo`, binary di `/home/mintbag/odoo-dev/venv/lib/python3.12/site-packages/pgserver/pginstall/bin/`. Odoo existing jalan di port 8069 dengan DB `namlah_local` dan **tidak boleh diganggu**.
- Snapshot source baca-saja: `/tmp/opencode/namlah-src/namlah-odoo-addons`.

---

## 1. Tanggung jawab & file kepemilikan eksklusif

### 1.1 Milik Agen B (boleh dibuat/diubah)

| File | Tujuan |
| --- | --- |
| `.github/workflows/ci.yml` | Tambah job Odoo+Postgres, perluas job guard dengan tes negatif, simpan job Flutter/node apa adanya. |
| `namlah-odoo-addons/namlah_api/tests/__init__.py` | Daftar test module `namlah_api`. |
| `namlah-odoo-addons/namlah_api/tests/test_auth_flow.py` | Login password/PIN, sesi, identitas/role, ganti/hapus PIN, throttling. |
| `namlah-odoo-addons/namlah_api/tests/test_http_contract.py` | HTTP controller: method, format JSON, CSRF/bad-origin, kode status. |
| `namlah-odoo-addons/namlah_api/tests/test_tenant_isolation.py` | Isolasi lintas koloni & pembatasan role. |
| `namlah-odoo-addons/namlah_api/tests/test_models.py` | Unit/model: `sale_order`, `project_task`, `activity`, helper `helpers.py`. |
| `namlah-odoo-addons/namlah_api/tests/test_migration.py` | Backfill `20.0.18.0.0`. |
| `namlah-odoo-addons/namlah_api/tests/test_smoke_install.py` | Install bersih + endpoint health. |
| `namlah-odoo-addons/namlah_api/tests/fixtures/` | Fixture SQL/AST untuk migrasi & guard (tanpa data rahasia). |
| `namlah-odoo-addons/namlah_{catalog,jastip,pinjam,telegram,whatsapp}/tests/test_regression_*.py` | Penambahan regresi; **tidak menimpa** file test yang sudah ada. |
| `scripts/tests/test_guard_deny_by_default.py` | Tes positif + negatif guard, berbasis `unittest` stdlib. |
| `scripts/tests/fixtures/` | Fixture route baik/buruk untuk guard. |
| `scripts/tests/run_local_odoo_tests.sh` | Pembungkus perintah lokal pada mesin ini (DB terpisah, port 8070). |

### 1.2 Tidak dimiliki Agen B

Agen B **tidak mengubah**: `scripts/check_deny_by_default.py`, `scripts/check_project_owner.py`, `namlah_api/controllers/_decorators.py`, seluruh file controller/model/view/security/manifest, source Flutter, dan snapshot di `/tmp/opencode/namlah-src`. Perubahan guard asli ada di Agen A; Agen B hanya mendefinisikan **kriteria tes** (bagian 4) dan mengonsumsi API yang disepakati.

---

## 2. Matriks tes

| Area | File | Teknik | Prioritas | Turunan dari kondisi nyata |
| --- | --- | --- | --- | --- |
| Unit/model | `test_models.py` | `TransactionCase`, `@tagged('post_install','-at_install')` | P0 | `_namlah_backfill_koloni_code`, auto-fill koloni `sale.order`, activity assignment, helper `hash_pin`/`get_actor`/`read_json_body`. |
| HTTP controller — auth | `test_auth_flow.py` | `HttpCase` + `url_open`/`authenticate`, JSON body | P0 | `/api/auth/login` (email / HP / Semut-ID + password atau PIN 6 digit), `/api/auth/session` (tidak pernah 401), `logout`, `identity`, `GET|POST|DELETE /api/auth/pin` dengan `currentPin` **atau** `currentPassword`. |
| HTTP controller — CSRF | `test_http_contract.py` | `HttpCase`, header `Origin`/`Referer` | P0 | POST tanpa origin valid harus ditolak; origin valid diterima; endpoint `csrf=False` yang memang publik tetap terdokumentasi dan diuji. |
| HTTP controller — tenant | `test_tenant_isolation.py` | `HttpCase` dua koloni + `TransactionCase` untuk constraint | P0 | Session koloni A tidak bisa membaca/mengubah resource koloni B; join koloni butuh approval Ratu tujuan; `/api/kpi/detail` scope semut vs global; `/api/beranda/notifications` hanya data koloni sendiri. |
| Migrasi | `test_migration.py` + job CI terpisah | `TransactionCase` untuk helper + restore fixture DB lama lalu `-u namlah_api` | P1 | `migrations/20.0.18.0.0/post-migration.py`: backfill `x_namlah_koloni_code`, fallback `namlah.default_koloni`, tidak menghasilkan activity duplikat (`namlah_skip_activity`). |
| Regresi 5 modul | `test_regression_*.py` | `TransactionCase`, tag module existing | P1 | Pinjam: kuota & bukti foto; catalog: dashboard koloni; jastip: alur titip; telegram/whatsapp: log dry-run dan **isi PIN/kode rahasia tidak pernah masuk log** (sudah ada pola bagus di `test_namlah_telegram.py`). |
| Smoke install | `test_smoke_install.py` + step CI | DB kosong, `-i` modul + dependensi | P0 | Install `namlah_api` beserta `namlah_core`, `namlah_project`, `namlah_email`, `namlah_wallet`, `namlah_security`, `project`, `mail`, `auth_totp`, plus 5 modul ber-tes; `GET /api/odoo/health` → 200. |

### 2.1 Unit/model — detail

- `sale.order`: koloni terisi dari partner → project/task → membership → namespace user → parameter; constraint konsisten dengan `x_namlah_koloni_code`.
- `project.task` / `mail.activity`: activity dibuat saat order/task dibuat & selesai, assign ke kasir/agen/ratu/admin sesuai role, tidak duplikat saat update berulang.
- Helper `helpers.py`: `hash_pin` deterministik terhadap pepper `namlah.pin_pepper`, `read_json_body` menolak body bukan JSON, `json_error`/`json_ok` menghasilkan envelope yang sama dengan kontrak aplikasi.
- Semua test memakai UUID pada kode koloni/SKU agar bisa dijalankan paralel dan berulang di DB yang sama (pola dari `test_namlah_pinjam.py`).

### 2.2 HTTP controller — detail

- Gunakan `@tagged('post_install', '-at_install')` dan `HttpCase` untuk request nyata; `TransactionCase` hanya untuk logika model murni.
- Auth:
  1. `POST /api/auth/login` dengan email + password → 200, cookie sesi terbentuk.
  2. `POST /api/auth/login` dengan nomor HP ternormalisasi + PIN → 200; PIN salah → 401; 6 digit bukan angka → 400; identifier kosong → 400.
  3. Semut-ID/ref partner → 200; user inactive → 401.
  4. Lima kegagalan PIN berturut-turut → ditolak (throttle in-memory), lalu pulih setelah jendela 15 menit disimulasikan.
  5. `GET /api/auth/session` tanpa sesi → payload valid, **bukan 401**; dengan sesi → identitas sesuai actor.
  6. `POST /api/auth/logout` → sesi berikutnya tidak lagi mengakses endpoint terlindungi.
  7. `GET|POST /api/auth/identity` → ganti role aktif hanya ke role yang memang dimiliki; role tidak valid ditolak.
  8. `DELETE /api/auth/pin` hanya lewat `currentPin` **atau** `currentPassword`; keduanya salah → 401; nilai PIN tidak boleh muncul di log/body respons.
- CSRF/bad-origin:
  1. POST ke endpoint stateful dengan `Origin: https://evil.example` → 403.
  2. POST dengan `Referer` beda host → 403.
  3. POST tanpa `Origin`/`Referer` → 403 (deny-by-default, bukan allow-by-default).
  4. POST dengan origin lokal yang sah → 200.
  5. `GET` tetap idempoten dan tidak berubah karena header origin.
- Semua assertion memeriksa **status code + envelope JSON**, bukan hanya "tidak exception".

### 2.3 Tenant isolation — detail

- Buat dua koloni `A`/`B` dengan anggota & user masing-masing; login sebagai A, coba akses resource B lewat endpoint nyata (`/api/colonies/...`, `/api/order`, `/api/task`, `/api/kpi/detail`, `/api/beranda/notifications`, `/api/driver/jobs`).
- Harapan: 403 untuk role tidak berhak, 404 untuk resource yang memang tidak boleh terlihat (hindari leak keberadaan lewat 403 vs 404 yang inkonsisten — pilih satu kontrak dan uji konsistensinya).
- `POST /api/colonies/<code>/join`: anggota mengajukan → task template `koloni-join-request` muncul di antrean Ratu koloni **tujuan**, bukan koloni asal; approve/reject hanya Ratu/admin tujuan; sebelum approve, membership belum aktif.
- Semut hanya melihat agregat koloni sendiri; Ratu/admin melihat agregat global; mencoba `kind` di luar daftar → 400.
- Test harus gagal bila filter koloni dihapus dari query (uji negatif dengan memberi payload `koloni_code` dari body — actor tidak boleh dipercaya dari body).

### 2.4 Migrasi — detail

- Level 1 (cepat, selalu di CI): panggil helper backfill pada data yang sengaja dibuat tanpa koloni, lalu cek fallback parameter dan tidak ada activity duplikat.
- Level 2 (job terpisah, manual/nightly atau PR yang menyentuh `migrations/`): restore dump fixture DB versi sebelum `20.0.18.0.0` ke DB sementara, jalankan `-u namlah_api --test-tags /namlah_api:TestMigrationFixture`, verifikasi order lama (mis. pola `S00011`) masuk filter Beranda.
- Fixture dump **tidak mengandung data produksi atau nilai rahasia**; dibuat dari data sintetis.

### 2.5 Regresi & smoke — detail

- File regresi baru ditambahkan, bukan mengganti 6 file existing; 48 fungsi lama harus tetap hijau (ini baseline, bukan target baru).
- Smoke install memakai DB kosong yang dibuat fresh, bukan `namlah_local`.
- Jika install 41 addon sekaligus terlalu lama, smoke mencakup `namlah_api` + dependensi + 5 modul ber-tes; sisanya tetap oleh `compileall` + sanity manifest.

### 2.6 Konvensi tag

- `@tagged('post_install', '-at_install')` untuk seluruh test Odoo baru, mengikuti contoh `namlah_pinjam`.
- `--test-tags /<module>` memakai **nama modul**, bukan path file; contoh: `/namlah_api`, `/namlah_pinjam`.
- Nama class `Test<Module><Area>`, nama method `test_<perilaku>_<harapan>` agar log CI mudah dibaca.

---

## 3. Rencana job CI

### 3.1 Desain

- Tambah job `odoo-tests` dengan service `postgres:16` (auth trust via socket/TCP lokal, tanpa nilai rahasia tertanam), checkout repo + checkout Odoo 20 (shallow), Python 3.12 untuk parity dengan venv lokal, install dependency Odoo dari `requirements.txt`.
- Buat config Odoo sementara di workspace runner dengan `addons_path` = core `odoo/addons` + core `addons` + `namlah-odoo-addons`. Config ini tidak mengandung nilai rahasia; koneksi DB memakai user lokal `odoo`.
- Buat DB segar `namlah_ci`, jalankan `--test-enable --test-tags ... --stop-after-init`, lalu `dropdb` di `if: always()`.
- Tahap 1 (langsung aktif): tag 5 modul yang sudah punya tes.
- Tahap 2 (aktif setelah file test `namlah_api` masuk): tambahkan `/namlah_api` ke daftar tag yang sama, atau jalankan step terpisah dengan DB segar lain agar isolasi.
- Job `deny-by-default` diperluas: jalankan guard asli **dan** `scripts/tests/test_guard_deny_by_default.py` (fixture positif + negatif).
- Cache: `~/.cache/pip` dengan kunci `hashFiles('.ci/odoo/requirements.txt')` + `restore-keys`. Opsional cache `~/.cache/odoo` untuk attachment/data generator bila dipakai. Checkout Odoo tetap shallow agar murah.

### 3.2 Contoh YAML ringkas (skema, dapat disesuaikan)

```yaml
odoo-tests:
  runs-on: ubuntu-latest
  services:
    postgres:
      image: postgres:16
      env:
        POSTGRES_USER: odoo
        POSTGRES_HOST_AUTH_METHOD: trust
      ports: ['5432:5432']
      options: >-
        --health-cmd "pg_isready -U odoo"
        --health-interval 10s --health-timeout 5s --health-retries 5
  env:
    ODOO_ROOT: ${{ github.workspace }}/.ci/odoo
    ADDONS: ${{ github.workspace }}/namlah-odoo-addons
    CI_DB: namlah_ci
  steps:
    - uses: actions/checkout@v4
    - uses: actions/checkout@v4
      with:
        repository: odoo/odoo
        ref: '20.0'
        path: .ci/odoo
        fetch-depth: 1
    - uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    - uses: actions/cache@v4
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('.ci/odoo/requirements.txt') }}
        restore-keys: ${{ runner.os }}-pip-
    - name: Dependensi sistem + Python
      run: |
        sudo apt-get update
        sudo apt-get install -y libpq-dev libxml2-dev libxslt1-dev \
          libldap2-dev libsasl2-dev libssl-dev libffi-dev libjpeg-dev zlib1g-dev
        python -m pip install --upgrade pip
        python -m pip install -r "$ODOO_ROOT/requirements.txt"
    - name: Config Odoo sementara
      run: |
        python - <<'PY'
        import configparser, os
        c = configparser.ConfigParser(interpolation=None)
        c.add_section('options')
        o = c['options']
        root, addons = os.environ['ODOO_ROOT'], os.environ['ADDONS']
        o['addons_path'] = f'{root}/odoo/addons,{root}/addons,{addons}'
        o['db_host'] = 'localhost'
        o['db_port'] = '5432'
        o['db_user'] = 'odoo'
        o['db_name'] = os.environ['CI_DB']
        o['db_filter'] = os.environ['CI_DB']
        o['http_port'] = '8069'
        with open('/tmp/odoo-ci.conf', 'w', encoding='utf-8') as fh:
            c.write(fh)
        PY
    - name: Buat DB + jalankan tes
      env:
        PGHOST: localhost
        PGUSER: odoo
      run: |
        createdb "$CI_DB"
        python -m odoo server -c /tmp/odoo-ci.conf -d "$CI_DB" \
          -i namlah_pinjam,namlah_catalog,namlah_jastip,namlah_whatsapp,namlah_telegram \
          --test-enable \
          --test-tags '/namlah_pinjam,/namlah_catalog,/namlah_jastip,/namlah_whatsapp,/namlah_telegram' \
          --stop-after-init --log-level=test
        # Setelah tes namlah_api masuk: tambahkan -i namlah_api dan /namlah_api
        # pada dua baris di atas (atau step terpisah dengan DB namlah_ci_api).
    - name: Bersihkan DB
      if: always()
      env:
        PGHOST: localhost
        PGUSER: odoo
      run: dropdb --if-exists "$CI_DB"

  deny-by-default:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Guard asli + selftest positif/negatif
        run: |
          python scripts/check_deny_by_default.py
          python scripts/tests/test_guard_deny_by_default.py
```

Catatan: job Flutter, `namlah-shared`, dan `node-scripts` tidak disentuh. Guard `/v0` lama diganti/diperluas oleh Agen A; Agen B hanya menambah selftest di bawahnya.

---

## 4. Guard deny-by-default — kriteria tes (koordinasi dengan Agen A)

Agen A mengubah guard asli agar berlaku untuk route produksi `/api/...` (bukan hanya `/v0/`), dengan kontrak: **setiap route `/api/...` wajib dideklarasikan dengan daftar peran yang diizinkan; tanpa deklarasi → gagal saat import**. Agen B tidak menyentuh implementasinya, hanya menetapkan kriteria berikut.

### 4.1 Kontrak yang dibutuhkan dari Agen A

- `scripts/check_deny_by_default.py` tetap dapat dipanggil sebagai CLI (`exit 0` bersih, `exit 1` + daftar pelanggaran) **dan** mengekspos fungsi scan dengan tanda tangan stabil `scan(path) -> list[str]` (atau entrypoint setara yang bisa menerima path arbitrer).
- `controllers/_decorators.py` tetap mengekspos `namlah_route(...)` dan melakukan validasi runtime pada `/api/...` (melempar exception saat import bila peran kosong/tidak ada).
- Kedua perubahan di atas harus bisa diuji terhadap **fixture**, bukan terhadap source repo, agar tes tidak bergantung pada keadaan dashboard/source yang sedang diedit.

### 4.2 Fixture (milik Agen B, di `scripts/tests/fixtures/`)

| Fixture | Isi | Harapan |
| --- | --- | --- |
| `bad_api_no_role.py` | `@namlah_route('/api/selftest/bad', methods=['GET'])` tanpa argumen peran | `scan()` mengembalikan ≥ 1 pelanggaran; import modul via subprocess gagal (nonzero). |
| `bad_api_empty_role.py` | `@namlah_route('/api/selftest/bad2', methods=['POST'], peran=[])` | ≥ 1 pelanggaran; import gagal. |
| `bad_api_plain_route.py` | `@http.route('/api/selftest/bad3', ...)` biasa | ≥ 1 pelanggaran (karena tidak memakai dekorator turunan). |
| `good_api_with_role.py` | `@namlah_route('/api/selftest/ok', methods=['GET'], peran=['member'])` | 0 pelanggaran; import sukses. |
| `legacy_v0_no_role.py` | `@namlah_route('/v0/selftest/bad', methods=['GET'])` | Tetap terdeteksi (regresi terhadap perilaku lama). |

### 4.3 Kriteria penerimaan tes

1. Tes **membuktikan guard tidak vacuous**: dengan sengaja memasukkan route `/api/...` tanpa deklarasi peran ke fixture, guard harus **gagal**. Kalau guard masih lolos, tes merah — ini inversi dari tes positif biasa.
2. Tes positif: fixture dengan `peran=['member']` lolos; CLI guard pada source asli tetap exit 0.
3. Tes runtime: import fixture buruk di subprocess menghasilkan exit nonzero; import fixture baik exit 0. Ini menutup jurang antara "static analyzer lolos" dan "endpoint benar-benar terdaftar".
4. Tes tidak boleh menulis/mengubah file di luar `scripts/tests/fixtures/` atau temp dir; fixture dibuat di `tempfile.TemporaryDirectory()` saat test berjalan.
5. Pesan pelanggaran harus menyertakan path + nomor baris + rule, sehingga Agen A bisa langsung memperbaiki.
6. Setelah Agen A mengubah guard, Agen B menjalankan ulang selftest **sebelum** mengaktifkan tag `/namlah_api` di CI.

---

## 5. Perintah uji lokal (mesin ini, aman untuk Odoo yang sudah jalan)

Semua perintah di bawah akan dibungkus di `scripts/tests/run_local_odoo_tests.sh`. Prinsip: DB baru `namlah_test_b`, port 8070, config baru di `/tmp/opencode`, tidak menyentuh `namlah_local` / port 8069 / snapshot source.

### 5.0 Variabel

```bash
SRC=/tmp/opencode/namlah-src
ODOO_ROOT=/home/mintbag/odoo-dev/odoo-20.0.post20261114
PY=/home/mintbag/odoo-dev/venv/bin/python
PGBIN=/home/mintbag/odoo-dev/venv/lib/python3.12/site-packages/pgserver/pginstall/bin
PGDATA=/home/mintbag/odoo-dev/pgdata
DB=namlah_test_b
PORT=8070
CONF=/tmp/opencode/namlah-test.conf
```

### 5.1 Ambil nilai rahasia dari config tanpa menampilkannya

Jangan aktifkan `set -x`. Nilai dibaca langsung ke variabel lingkungan untuk koneksi bundled Postgres; tidak pernah di-`echo`, tidak ditulis ke dokumen, tidak masuk argumen perintah yang terlihat di log.

```bash
export PGHOST="$PGDATA" PGUSER=odoo
export PGPASSWORD="$("$PY" - <<'PY'
import configparser
c = configparser.ConfigParser(interpolation=None)
c.read('/home/mintbag/odoo-dev/odoo.conf')
print(c.get('options', 'db_password', fallback=''))
PY
)"
```

Jika socket bundled memakai trust, `PGPASSWORD` boleh kosong; baris di atas tetap aman karena tidak mencetak apa pun ke layar.

### 5.2 Buat config test (addons_path snapshot + core)

```bash
"$PY" - <<'PY'
import configparser, os
src = '/home/mintbag/odoo-dev/odoo.conf'
dst = '/tmp/opencode/namlah-test.conf'
c = configparser.ConfigParser(interpolation=None)
c.read(src)
o = c['options']
o['addons_path'] = ','.join([
    '/home/mintbag/odoo-dev/odoo-20.0.post20261114/odoo/addons',
    '/home/mintbag/odoo-dev/odoo-20.0.post20261114/addons',
    '/tmp/opencode/namlah-src/namlah-odoo-addons',
])
o['db_name'] = 'namlah_test_b'
o['db_filter'] = 'namlah_test_b'
o['http_port'] = '8070'
# Nilai db_password dari config asli sengaja dibiarkan apa adanya dan TIDAK dicetak.
with open(dst, 'w', encoding='utf-8') as fh:
    c.write(fh)
os.chmod(dst, 0o600)
PY
```

### 5.3 Buat / drop DB test lewat binary pgserver

```bash
"$PGBIN/pg_isready" -h "$PGDATA" -U odoo
"$PGBIN/dropdb"  -h "$PGDATA" -U odoo --if-exists "$DB"
"$PGBIN/createdb" -h "$PGDATA" -U odoo "$DB"
```

### 5.4 Jalankan baseline 5 modul

```bash
"$PY" -m odoo server \
  -c "$CONF" \
  -d "$DB" \
  --http-port="$PORT" \
  -i namlah_pinjam,namlah_catalog,namlah_jastip,namlah_whatsapp,namlah_telegram \
  --test-enable \
  --test-tags '/namlah_pinjam,/namlah_catalog,/namlah_jastip,/namlah_whatsapp,/namlah_telegram' \
  --stop-after-init \
  --log-level=test
```

`--test-enable` dan `--test-tags` sama-sama mengimplikasikan stop-after-init; flag eksplisit tetap ditulis agar perilaku jelas. Odoo 20 memakai subcommand `server`.

### 5.5 Perluasan ke `namlah_api` (setelah tes ditambahkan)

Gunakan DB segar lain agar tidak tercampur dengan baseline:

```bash
DB=namlah_test_api
CONF=/tmp/opencode/namlah-test-api.conf
"$PGBIN/dropdb" -h "$PGDATA" -U odoo --if-exists "$DB"
"$PGBIN/createdb" -h "$PGDATA" -U odoo "$DB"
# ulang 5.2 dengan db_name/db_filter = "$DB" dan http_port 8071

"$PY" -m odoo server \
  -c "$CONF" -d "$DB" --http-port=8071 \
  -i namlah_api,namlah_pinjam,namlah_catalog,namlah_jastip,namlah_whatsapp,namlah_telegram \
  --test-enable \
  --test-tags '/namlah_api,/namlah_pinjam,/namlah_catalog,/namlah_jastip,/namlah_whatsapp,/namlah_telegram' \
  --stop-after-init --log-level=test
```

### 5.6 Selftest guard

```bash
"$PY" scripts/check_deny_by_default.py
"$PY" scripts/tests/test_guard_deny_by_default.py
```

### 5.7 Catatan operasional

- `addons_path` di config asli pointing ke path yang sudah hilang; seluruh run memakai config turunan yang dibuat di 5.2, bukan meng edit config asli.
- Port 8070/8071 dipilih supaya tidak bentrok dengan instance 8069. Karena `--stop-after-init`, server tidak perlu mendengarkan port dalam waktu lama, tetapi port tetap di-set eksplisit.
- Snapshot `/tmp/opencode/namlah-src` hanya dibaca; segala fixture/config/test baru ditulis ke workspace kerja atau `/tmp/opencode`.
- DB `namlah_test_b` / `namlah_test_api` boleh di-drop setelah run; jangan pernah menjalankan `dropdb namlah_local`.

---

## 6. Target coverage realistis & Definition of Done

### 6.1 Target

- Baseline 48 fungsi existing tetap hijau (tidak ada regresi).
- Tambah **~45–60 fungsi test baru** untuk `namlah_api` (fase pertama), dibagi: auth/session/PIN ~15, HTTP/CSRF ~10, tenant isolation ~10, model/activity ~6, migrasi ~3, smoke ~2.
- Cakupan garis `namlah_api`: dari 0% → target realistis **25–35%**, dengan fokus pada route kritis; **tidak** menjanjikan 80% pada fase ini.
- Cakupan kontrak: ≥ 60% route kritis (`/api/auth/*`, `/api/driver/*`, `/api/colonies/requests/*`, `/api/kpi/detail`, `/api/beranda/notifications`) punya minimal 1 test positif + 1 test negatif.
- 100% route produksi tercakup audit statis guard (bukan coverage garis, melainkan invariant deklarasi peran).
- 5 modul existing: masing-masing minimal +1 test regresi baru tanpa mengubah test lama.

### 6.2 Definition of Done

- [ ] Job `odoo-tests` dengan service PostgreSQL ada di `.github/workflows/ci.yml` dan hijau pada PR.
- [ ] Perintah `--test-enable --test-tags /namlah_pinjam,/namlah_catalog,/namlah_jastip,/namlah_whatsapp,/namlah_telegram` benar-benar menjalankan tes (log menunjukkan test dijalankan, bukan "0 tests").
- [ ] Setelah tes `namlah_api` masuk, tag `/namlah_api` diaktifkan dan log CI menunjukkan test module tersebut ikut berjalan.
- [ ] Selftest guard negatif **gagal** untuk fixture `/api/...` tanpa peran; fixture baik lolos; guard CLI pada source asli exit 0.
- [ ] Test tenant isolation membuktikan koloni A tidak bisa membaca/mengubah data koloni B lewat HTTP nyata.
- [ ] Test CSRF membuktikan bad-origin ditolak dan origin sah diterima.
- [ ] Test migrasi membuktikan backfill koloni berjalan tanpa duplikasi activity.
- [ ] Test telegram/whatsapp membuktikan kode rahasia tidak tersimpan di log.
- [ ] Perintah lokal di bagian 5 bisa dijalankan berulang tanpa mengganggu Odoo 8069 / DB `namlah_local`, dan tanpa menampilkan nilai rahasia apa pun di terminal maupun artifacts CI.
- [ ] Tidak ada perubahan Agen B di luar file kepemilikan bag 1.1; snapshot source tetap utuh.

### 6.3 Urutan & handshake

1. Agen B kirim bagian 4 (kriteria guard) ke Agen A sebelum Agen A mengubah `_decorators.py` / `check_deny_by_default.py`.
2. Agen A konfirmasi API `scan(path)` dan perilaku runtime `/api/...`.
3. Agen B tulis fixture + selftest guard, jalankan; jika merah karena guard belum diperluas, tahan aktivasi tag `/namlah_api`.
4. Agen B tambah test `namlah_api` bertahap: auth → HTTP/CSRF → tenant → model → migrasi → smoke.
5. Aktifkan tag `/namlah_api` di CI, verifikasi log, lalu tutup DoD.

---

# Rencana Agen C — Tenant Isolation, ACL & Data Integrity

Ru lingkup: perencanaan saja. Source di `/tmp/opencode/namlah-src` dibaca, tidak diubah. Tidak ada pengambilan/penyebutan kredensial. Artefak `.pyc` **bukan** masalah (hitungan sebelumnya artefak `compileall`), tidak masuk rencana.

## 1. Tanggung jawab & file kepemilikan eksklusif

Agen C memiliki **model, security, hook, dan migrasi** pada addon berikut (termasuk file manifest hanya untuk bagian `data`/`post_init_hook`/`depends` yang terkait keamanan):

| Addon | File/direktori kepemilikan C |
|---|---|
| `namlah_core` | `models/*` (field `company_id`, `_sql_constraints`, scope), `security/ir.access.csv`, `security/restrictions.xml` bila ditambah, `migrations/*`, entri `data` manifest |
| `namlah_security` | `security/groups.xml`, `security/ir.access.csv`, `migrations/*`, entri `data` manifest |
| `namlah_web_backend` | `hooks.py`, `models/koloni_scope.py`, `models/x_namlah_models.py`, `models/project_project.py`, `security/restrictions.xml`, entri `data`/`post_init_hook` manifest |
| `namlah_accounting` | `hooks.py`, `models/res_partner.py` (bagian scope/ACL/analytic), `security/*` bila ditambah, `migrations/*` |
| `namlah_catalog` | `security/ir.access.csv`, `models/*` (bagian scope `company_ids` pada dashboard/kurasi), `migrations/*` |
| ACL addon lain | `security/ir.access.csv` + `security/*.xml` + `migrations/*` pada: `lokalmart_company`, `namlah_project` (`security/project_rules.xml`), `namlah_cctv`, `namlah_ebook`, `namlah_catalog`, `namlah_pinjam`, `namlah_wallet`, `namlah_telegram`, `namlah_subscription`, `namlah_qr`, `namlah_qr_trace`, `namlah_whatsapp`, `namlah_discuss`, `namlah_email`, `namlah_theme`, `namlah_jastip`, dll.; `hooks.py` tempat ada backfill/indeks unik (`namlah_jastip`) |

**Tidak dimiliki C:** `namlah_api/controllers/*` dan helper `service_env()` milik **Agen A**; CI/workflow, test harness, dan test suite milik **Agen B**; dokumentasi kebijakan milik **Agen D**. C hanya memberi kontrak, criteria, dan fixture data/ACL kepada agen tersebut.

## 2. Tabel masalah → dampak → solusi → prioritas → acceptance criteria

| # | Masalah (bukti snapshot) | Dampak | Solusi (C) | Prioritas | Acceptance criteria |
|---|---|---|---|---|---|
| T1 | `namlah_api/controllers/helpers.py::service_env()` = `request.env(user=2, su=True)`; dokumen `namlah_web_backend` mengakui API Flutter bypass rules | Semua domain manual di controller adalah satu-satunya penghalang bocor lintas koloni; satu helper yang lupa filter = lintas tenant | Sediakan service user non-super + `ir.access` global yang tetap aktif untuk semua jalur; kontrak impersonasi terbatas untuk Agen A (§3) | **P0** (bersama A) | Dengan service env baru, `search()` tanpa domain koloni tidak mengembalikan record koloni lain; `su=True` tidak lagi dipakai untuk data tenant |
| T2 | Aturan global bertabrakan: `namlah_web_backend/security/restrictions.xml` + `namlah_project/security/project_rules.xml` ketat `company_id in company_ids`, tetapi `lokalmart_company/security/ir.access.csv` baris 157–164 masih `company_id = False OR in company_ids`; duplikat XMLID lama sudah pernah dibersihkan via migrasi `namlah_project/20.0.4.0.0` | Jika salah satu rule dinonaktifkan/gagal load, record tanpa company langsung terbaca semua koloni; AND dua rule bisa bikin perilaku sulit diprediksi | Satu pemilik rule global per model; samplekan/verifikasi semantics AND di Odoo 20; migrasi non-destruktif untuk menonaktifkan rule longgar `lokalmart_company` (bukan menghapus baris ACL pemberi akses) | **P0** | Inventory `ir.access` global per model tidak ada yang mengandung `= False` untuk model tenant; uji dua tenant lolos/gagal sesuai ekspektasi |
| T3 | 17 addon memuat `security/ir.access.csv` header `id,name,model_id,group_id/id,operation,domain` lewat manifest `data` (mis. `namlah_core`), tapi format Odoo 20 belum diverifikasi | Bisa saja ACL tidak termuat sama sekali → either semua terbuka atau semua gagal | **Jangan asumsi.** Verifikasi lewat tes instalasi DB bersih + query `ir.access` (xmlid, `group_id` kosong = global, `operation`, `domain` ter-evaluasi). Bila tidak dimuat, konversi ke `<record model="ir.access">` seperti `restrictions.xml` | **P0** | `ir.access` terisi sesuai CSV pada `-i`/`-u`; baris dengan `group_id` kosong benar-benar global; domain dengan `company_ids`/`user.*` ter-evaluasi tanpa error |
| T4 | ACL portal di `namlah_security/ir.access.csv` (chat/comment) tidak membatasi `company_id`; `namlah_cctv` & `namlah_ebook` mengizinkan `x_koloni_code = False` secara eksplisit; `namlah_security` memberi `r` portal pada banyak model custom | Portal bisa membaca record lintas koloni bila kode koloni kosong / lewat chat partner lain | Tambah/sempurnakan domain: `company_id in company_ids` **dan** `x_koloni_code = user.x_namlah_active_koloni_code`; hapus cabang `= False` kecuali record memang root Institute; untuk model tanpa `company_id`, tambahkan company_id atau rule berbasis kode yang terverifikasi | **P0** | User portal koloni A count=0 untuk data koloni B termasuk record berkode kosong; chat hanya percakapan sendiri; tidak ada `AccessError` pada alur portal sah |
| T5 | `company_id` di `namlah_web_backend/models/x_namlah_models.py` adalah stored computed dari kode koloni, `@api.depends` hanya field kode; hook `hooks.py` backfill raw SQL; `project_task` disinkron dari project. Jika mapping/company baru berubah, compute tidak otomatis reload | `company_id` NULL/salah → record masuk root Institute (hanya admin lihat) atau sebaliknya bocor ke koloni lain | Preflight NULL/mismatch; pastikan `company_id` always non-null di scope (root Institute fallback); sinkronkan mapping code→company di hook dan compute; rename/alias kode ditangani migrasi eksplisit | **P0** | Pasca hook: 0 NULL pada 9 tabel custom + `project_project`/`project_task`; recompute hook kedua kali menghasilkan 0 perubahan; Ratu melihat datanya di `/web` |
| T6 | 614 pemanggilan `sudo()` di 83 file; sebagian besar di model/service, bukan semuanya di controller A | `sudo` melewati `ir.access` bahkan setelah `su=True` dihapus; scope melebar lewat nested call | Audit berdampingan dengan A: matriks modul→method→alasan; hapus `sudo` pada akses data tenant; pertahankan hanya dengan justifikasi tertulis (§4) | **P1** | Baseline 614 tercatat; 0 `sudo()` baru tanpa komentar `ACL:`; 0 `sudo().search/write` pada model tenant tanpa validasi koloni; alur publik/portal tetap lolos tes |
| T7 | Hanya **1** `_sql_constraints` di seluruh codebase (`namlah_ebook/models/x_namlah_ebook_progress.py`); duplikat dicegah partial index di `namlah_jastip/hooks.py` tetapi exception-nya cuma di-log | Race condition bikin duplikat project/SO/update; data dobel merusak idempotensi helper dan akuntansi | Tambah `_sql_constraints` untuk kunci unik kritis setelah dedupe: `x_namlah_koloni_code` (partner/company), `(template_code, plan_code)` task, `client_order_ref` jastip, `(code, plan_id)` analytic, external ref wallet/QR/topup, `(partner, koloni, role)` membership aktif. Partial index lama dijadikan cadangan, bukan pengganti constraint | **P1** | Preflight duplikat = 0; constraint aktif dan mencolot pada insert duplikat; hook jastip tidak lagi "warning then skip" tanpa tindak lanjut |
| T8 | 11 titik raw SQL; nilai sudah parameterized, identifier nama tabel/kolom memakai f-string dari konstanta (`hooks.py`, `namlah_accounting/models/res_partner.py`); hook `post_init` mengUPDATE banyak tabel + `company_ids` user | identifier dari konstanta relatif aman tetapi rawan regresi; UPDATE salah arah/urutan bisa merusak scope admin | Whitelist identifier + helper quote; pertahankan `IS DISTINCT FROM` & `IF NOT EXISTS`; urutan migrasi eksplisit; backup & dry-run hitungan sebelum/sesudah; SAVEPOINT untuk indeks opsional | **P1** | Semua SQL lolos tes whitelist identifier; tidak ada input user/field bebas masuk ke f-string; hook bisa diulang tanpa efek samping; rollback drill berhasil |
| T9 | 221 `except Exception`, termasuk di hook/JASTIP/index unik dan helper scope | Error ACL/DB ditelan → gagal silently, keamanan tampak aktif padahal tidak | Audit bersama A/B: error keamanan/integritas harus fail-closed; hanya error non-kritis (menu opsional, API versi berbeda) yang ditelan dengan log + flag | **P1** | Tidak ada `except Exception` yang menelan `AccessError`/integrity error pada jalur authorisasi; tes negatif memastikan denial tidak diubah jadi success |
| T10 | `hooks.py` sudah menambah company koloni ke user aktif dan mencabut root dari non-admin; grup Ratu/Admin dipromosikan ke `base.group_user`; tapi `base.group_system` tetap bypass rule via `su`/superuser | Admin Institute bisa melihat semua (disengaja), tetapi Ratu yang masih punya root melihat record Institute; sebaliknya admin yang kehilangan root tidak melihat data global | Kebijakan tertulis: root + semua pilot hanya untuk `group_system`/admin Institute; Ratu hanya `company_ids` koloninya; verifikasi `company_ids` dan `company_id` utama di hook/migrasi | **P0** | Matrix user: Ratu A=1 koloni, admin Institute=root+semua pilot, portal=koloninya; tidak ada Ratu dengan root di `company_ids` |
| T11 | Dokumentasi `namlah_core` menyatakan "TIDAK membatasi akses via record rules", `namlah_web_backend` menyatakan API bypass; keduanya akan berubah | Operator mengira bypass masih diperbolehkan | Serahkan ke Agen D setelah implementasi: kebijakan dua lapis, matrix peran, runbook migrasi/rollback | **P2** | Dokumen tidak lagi menyatakan API kebal rules; ada catatan service user & company_ids |

Catatan: tidak ada `_sql_constraints` massal yang bisa dianggap "sudah ada"; hanya satu. Tidak ada `.pyc` ter-commit yang perlu dibersihkan.

## 3. Strategi tenant isolation dua lapis

### Lapis (a) — hilangkan/kurangi `su=True`, impersonasi terbatas (kontrak untuk Agen A)

1. **Service user non-super**: buat user teknis dengan grup minimal, `company_ids` = root + company pilot yang diperlukan untuk operasi lintas koloni, **bukan** `su=True`. Helper `service_env()` A menjadi `with_user(service_uid)` + `with_company(target_company)` yang ditentukan dari actor/koloni yang sudah divalidasi, bukan dari body request.
2. **Impersonasi terbatas**: actor dari session (`get_actor()`) menentukan `koloniCode`; target company harus `∈ company_ids` actor (kecuali admin Institute). Ratu A tidak boleh menulis data koloni B walaupun ia memanggil helper dengan `koloniCode` lain. Service user hanya "minggu" ke company yang diizinkan, dan seluruh write membawa `company_id` hasil compute yang sama dengan rules.
3. **Pengecualian terkontrol**: operasi teknis (ir.config_parameter, ir.model.data, mail template, analytic plan, post_init) boleh `sudo()` dengan komentar `ACL:`; akuntansi tetap `with_company()` pada company ber-chart-of-accounts. Tidak pernah `sudo()` untuk `search`/`write` data tenant tanpa domain actor + rule.
4. **Trade-off**: service user non-super memicu `AccessError` pada controller yang sebelumnya mengandalkan superuser; ada biaya migrasi domain dan urutan company. Manfaatnya, `ir.access` benar-benar berlaku untuk Flutter/API. Strategi: landapkan rules + data dulu (dual-run: `su=True` masih ada tapi rules sudah benar), lalu switch helper dalam satu deploy dengan feature flag/rollback, baru terakhir hapus `su=True`.

### Lapis (b) — record/company rules sebagai safety net

1. Satu restriction global per model tenant: `[('company_id', 'in', company_ids)]` — **tanpa `+ [False]`**. Record tanpa kode koloni adalah milik root Institute, jadi hanya terlihat oleh admin Institute (`company_ids` memuat root).
2. Model tanpa `company_id` (mis. cctv/ebook/dashboard) wajib dapat field `company_id` atau rule ketat berbasis `user.x_namlah_active_koloni_code`; hapus cabang `('x_koloni_code', '=', False)`.
3. Rule `project.*` tetap di `namlah_project/security/project_rules.xml` (deaktivasi rule bawaan `project.*_comp_rule`), rule `x_namlah.*` di `namlah_web_backend/security/restrictions.xml`; rule longgar di `lokalmart_company` dinonaktifkan/disejajarkan agar tidak ada `False` yang membuka akses.
4. **Trade-off**: superuser/Odoo admin teknis tetap bypass rule → lapis (b) tidak cukup tanpa (a); sebaliknya (a) saja rapuh karena controller mudah lupa domain. Keduanya wajib.

### Urutan migrasi data (blocking order)

1. Backup DB + preflight: hitung NULL/mismatch `company_id`, duplikat kunci unik, user dengan root di `company_ids`, rule global aktif.
2. Backfill/additive: `company_id` (kode→company, sisanya root), sinkron `project_task` dari project, `company_ids` user (tambah koloni, cabut root dari non-admin). Idempoten, tidak menghapus data.
3. Dedupe data duplikat (hanya setelah laporan & persetujuan) → baru pasang `_sql_constraints`.
4. Aktifkan/verifikasi restriction ketat & nonaktifkan rule longgar; uji dua tenant.
5. Agen A switch `service_env()` ke user non-super; uji API + `/web` paralel.
6. Kurangi `sudo()` bertahap; tutup `except Exception` pada jalur keamanan.
7. Agen D perbarui dokumentasi kebijakan.

## 4. Audit ACL, constraint, dan `sudo()`

### `ir.access.csv` di Odoo 20

- Verifikasi nyata (tes, bukan asumsi): install `-i` DB bersih dan `-u` modul; cek `ir.access` punya xmlid/baris sesuai 17 CSV, `group_id` kosong → global, `operation` (`r`, `cru`, `crud`, `ru`, `cud`) terbaca, `model_id` (nama model di CSV) ter-resolve, dan domain `company_ids` / `user.x_namlah_active_koloni_code` evaluable.
- Uji semantics global vs grup: apakah global AND-ed dengan grant grup; apakah `group_id/id` benar-benar kolom yang benar; apakah `namlah_core` grant `base.group_user crud` + restriction global benar-benar membatasi. Jika loader tidak menerima format CSV, konversi ke XML `<record model="ir.access">` (pola yang sudah dipakai `restrictions.xml` dan `project_rules.xml`) tanpa mengubah perilaku.
- Perbaikan domain: hapus `company_id = False OR ...`; untuk chat: gabungkan `('company_id','in',company_ids)` **dan** percakapan sendiri; comment: koloni aktif **dan** company; cctv/ebook: tanpa `False`; `namlah_catalog` dashboard sudah memakai `company_ids` server-side — verifikasi bukan hanya UI.
- Hindari grant baru ke `base.group_portal` pada model bisnis standar (`sale.order`, `res.partner`, `product.pricelist`) — menambah grant = melebarkan akses.

### `_sql_constraints`

Target uniqueness kritis (dedupe dulu): kode koloni unik di `res.partner`/`res.company`, `x_namlah_plan_code` per template/task, `client_order_ref` untuk jastip, `(code, plan_id)` analytic account, external id wallet/topup/QR, membership aktif `(partner, koloni, role)`. Rule: constraint harus punya nama eksplisit, preflight 0 duplikat, migrasi gagal keras bila duplikat muncul (tidak di-`except`), dan tidak boleh dipasang pada tabel yang masih dipakai hook lama tanpa koordinasi urutan.

### Audit `sudo()` — kriteria boleh tetap

| Boleh tetap | Tidak boleh |
|---|---|
| `post_init_hook`/migrasi, bootstrap data master (`res.company`, analytic plan, mail template) | `sudo().search()` pada `x_namlah.*`, `project.*`, `sale.order`, `account.move` tanpa domain actor/company |
| Metadata teknis: `ir.model.data`, `ir.config_parameter`, `ir.mail_server`, template | `sudo()` untuk mengabaikan `check_company`/rule karena "biar langsung jadi" |
| Alur publik/portal **dengan** domain eksplisit + validasi partner/actor + rule aktif | `sudo()` hasil copy-paste di helper yang dipanggil API; `sudo()` bersarang yang mewarisi scope melebar |
| Operasi lintas company admin Institute yang sudah tervalidasi `company_ids` | `sudo()` pada method yang menerima `koloni_code`/`partner_id` dari body tanpa `koloni_scope_error()` |

Metode: daftar 614 titik → kelompokkan per modul/method → tandai `keep/remove/needs-A` → terapkan bertahap; setiap `sudo` yang tetap wajib memuat komentar alasan. Agen A mengubah controller; C mengubah model/hook. `except Exception` yang menutupi `AccessError`/integrity error di jalur authorisasi harus fail-closed.

## 5. Audit raw SQL & hook

- 11 titik: `namlah_accounting/models/res_partner.py` (information_schema + query dinamis kolom `x_planN_id`), `namlah_wallet/models/x_namlah_wallet_topup.py` (2), `namlah_web_backend/hooks.py` (5), `namlah_jastip/hooks.py` (2). Semua nilai sudah parameterized; f-string hanya untuk identifier dari konstanta/`information_schema` → aman tetapi perlu audit: identifier masuk whitelist + helper quoting, tidak pernah dari input user/field DB.
- `hooks.py` backfill:UPDATE `project_project` → task ikut project → task berkode → project uncoded → `x_namlah.*` → event → `company_ids` user → promosi grup; memakai `IS DISTINCT FROM` dan additive `(4)/(3)`. Pastikan urutan ini tidak dibalik dan `invalidate_all()` fallback tidak menutup kegagalan SQL.
- `namlah_jastip/hooks.py`: partial unique index dibuat dengan `IF NOT EXISTS` tapi exception hanya di-log; ubah menjadi preflight + gagal keras (atau migration terpisah yang wajib sukses) setelah duplikat dibersihkan.
- Backup/rollback: sebelum deploy ambil dump; setiap hook/migrasi mencatat `rowcount`; jalankan dry-run count; SAVEPOINT untuk operasi opsional; bila tidak bisa rollback otomatis, sediakan SQL restore yang diuji. Perubahan `company_ids` bersifat additive/cabut root dengan log user id — masa depan bisa dibatalkan via backup.
- Urutan migrasi mengikuti §3; versi modul dinaikkan hanya sekali per tahap agar Odoo menjalankan hook/migration tepat satu kali.

## 6. Koordinasi antar agen

- **Agen A** (`namlah_api/controllers/*`, `service_env()`): terima kontrak service user non-super + aturan impersonasi; pastikan `get_actor()`, `koloni_scope_error()`, `koloni_or_admin()`, `koloni_or_global()` tidak dijadikan satu-satunya pertahanan; sepakati siapa yang men-set `company_id` saat create; dual-run sebelum penghapusan `su=True`. C tidak menyentuh file controller.
- **Agen B** (CI/tests): sediakan tes negatif lintas tenant, tes loader `ir.access.csv` DB bersih, tes idempotensi hook/unique constraint, tes regresi API; C menyediakan fixture ACL/domain dan daftar acceptance (§7). C tidak mengubah workflow/test.
- **Agen D** (dokumentasi): perbarui klaim "API tidak kena rules", matrix peran→`company_ids`, prosedur backup/rollback, dan daftar pengecualian `sudo()`. C memberi daftar keputusan setelah verifikasi.
- Titik serah: C menulis rules/model/migrasi → A verifikasi helper → B jalankan tes → D dokumentasi; keputusan format `ir.access` ditetapkan sebelum B menulis tes akhir.

## 7. Risiko & rollback

| Risiko | Mitigasi / rollback |
|---|---|
| Rule terlalu ketat → Ratu tidak melihat data / tidak bisa edit | Uji dua koloni sebelum deploy; flag `ir.access.active` bisa dibalik via `-u`/migrasi; kembalikan rule lama dari backup |
| Admin Institute kehilangan akses record root | Pastikan `group_system` mempertahankan root + semua pilot; preflight `company_ids` admin; rollback `company_ids` dari dump |
| Format `ir.access.csv` tidak dimuat di Odoo 20 | Verifikasi lebih awal; fallback konversi XML; jangan hapus CSV sampai tes lolos |
| Duplikat data bikin `_sql_constraints` gagal | Preflight & dedupe dengan laporan; constraint dipasang terakhir; rollback = drop constraint yang baru dibuat |
| `sudo()` dihapus terlalu cepat → alur publik/akuntansi gagal | Daftar pengecualian; deploy bertahap per modul; kembalikan `sudo()` hanya pada method yang terdokumentasi |
| Hook SQL_update salah arah/urutan | Backup + hitungan pre/post + idempotensi; restore dump; jalankan hook ulang setelah perbaikan |
| Rule global ganda AND → deny tak terduga | Inventory satu rule/model; nonaktifkan rule longgar lewat XMLID (bukan hapus grant); uji matrix peran |
| Mapping code→company berubah | Simpan helper `koloni_scope` satu sumber; migrasi alias eksplisit; recompute + hook; audit NULL setelah upgrade |

### Daftar tes acceptance

1. `ir.access` ter-load pada DB bersih: 17 CSV menghasilkan baris dengan xmlid benar; global `group_id` kosong terdeteksi; domain evaluable.
2. Dua koloni A/B + Ratu A: `search()` tanpa domain pada `x_namlah.*`, `project.*` → 0 record B; `write()` record B → `AccessError`; admin Institute → melihat keduanya.
3. Portal A: tidak bisa membaca record B, termasuk yang `x_koloni_code` kosong (cctv/ebook/comment); chat hanya partner sendiri.
4. API dengan service env baru: helper yang "lupa" domain tetap tidak mengembalikan data koloni lain; old `su=True` tidak dipakai untuk data tenant.
5. Hook backfill dijalankan dua kali: 0 `company_id` NULL; baris kedua `rowcount=0` untuk update yang sama; `company_ids` Ratu tidak memuat root.
6. Preflight duplikat = 0; `_sql_constraints` menolak insert duplikat; partial index jastip tidak lagi swallowed-error.
7. Raw SQL: semua identifier berasal dari whitelist/konstanta; tidak ada f-string yang menerima input request.
8. `sudo()` audit: tidak ada penambahan tanpa justifikasi; 221 `except Exception` tidak menyembunyikan denial pada jalur auth.
9. Rollback drill: restore dump + nonaktifkan rule baru → perilaku kembali ke baseline tanpa kehilangan data.

Tidak ada implementasi penuh dalam dokumen ini; ini hanya rencana dan criteria untuk eksekusi oleh Agen C bersama A/B/D.

---

# Rencana Agen D — Maintainability, Dokumentasi & Release Hygiene

Repo: `muhjadkaf/Namlah`, cabang `master`. Sumber dibaca dari snapshot `/tmp/opencode/namlah-src` (read-only). Rencana ini hanya mencakup dokumentasi, hygiene repo, dan disiplin rilis. Tidak ada perubahan source modul, CI, atau guard dalam scope Agen D.

---

## 1. Tanggung jawab & kepemilikan eksklusif

### Kepemilikan eksklusif Agen D

| Area | File/direktori | Catatan |
|---|---|---|
| README entry point | `README.md` (root), `namlah-odoo-addons/README.md` | Satu-satunya tempat tabel status & versi ringkas yang harus sinkron dengan manifest. |
| Dokumentasi | `Docs/` (34 file saat ini), termasuk indeks `Docs/README.md` | Indeks menjadi peta: kanonik / historis / superseded / usulan. |
| Panduan deploy Linux/self-host | File baru, mis. `Docs/DEPLOY-LINUX-SELFHOST.md` | Menggantikan prosedur berbasis path absolut Windows di README addons. |
| Runbook & troubleshooting | File baru, mis. `Docs/RUNBOOK-LOKAL.md`, `Docs/RUNBOOK-PRODUKSI.md`, `Docs/TROUBLESHOOTING.md` | Prosedur harian, rollback, dan diagnosa. |
| Arsitektur dokumenter | File baru, mis. `Docs/API-SESSION-TENANT.md` | Merangkum keputusan yang sudah diambil owner; tidak menciptakan keputusan baru. |
| Template & backfill README modul | File baru, mis. `Docs/MODULE-README-TEMPLATE.md` | Template + indeks; penulisan README per modul menyusul dengan persetujuan owner. |
| Release/versioning | File baru, mis. `Docs/RELEASE-CHECKLIST.md`, `Docs/CHANGELOG.md`, `Docs/VERSIONS.md` | `Docs/VERSIONS.md` bisa dihasilkan otomatis dari manifest. |
| Hygiene repo | `.gitignore` | Menjaga artefak Python, env, rahasia, dump, log, cookie lokal tetap tidak ter-commit. |

### Bukan kepemilikan Agen D (disebut hanya sebagai koordinasi)

- Source modul Odoo, controller, model, migration, dan `sudo()`/service identity → Agen C / owner domain.
- `.github/workflows/ci.yml` dan pengecekan otomatis di CI → Agen B.
- `scripts/check_deny_by_default.py` dan guard sejenis → Agen A.
- `namlah-odoo-addons/NAMLAH_ODOO_ONLY_ROADMAP.md` dan `namlah-odoo-addons/NAMLAH_CUTOVER_CHECKLIST.md` → input/keputusan owner; Agen D menautkan dan mengutip, tidak mengambil alih statusnya.
- README per modul yang sudah ada tetap dihormati; Agen D menyiapkan template dan daftar prioritas, lalu backfill sebagai perubahan dokumen setelah owner menyetujui cakupannya.

### Prinsip

Dokumen adalah **peta, bukan sumber kebenaran tersembunyi**. Untuk kode: manifest, source, dan keputusan owner bertanda tangan adalah kebenaran. Untuk operasi: checklist cutover dan roadmap adalah kebenaran status. Agen D hanya menyelaraskan tampilannya agar pembaca tidak menemukan versi, path, atau status yang saling bertentangan.

---

## 2. Tabel masalah → dampak → solusi → prioritas → acceptance criteria

| # | Masalah (fakta snapshot) | Dampak | Solusi Agen D | Prioritas | Acceptance criteria |
|---|---|---|---|---|---|
| M1 | Drift versi: README addons menyebut `namlah_core` `20.0.1.1.0`, manifest aktual `20.0.9.0.1`; versi lain juga tersebar di narasi docs. | Operator mengira modul lawas, salah memilih paket/update, review rilis jadi tidak bisa dipercaya. | Jadikan manifest single source of truth; tabel versi di `README.md`/`namlah-odoo-addons/README.md` dihasilkan/divalidasi dari 41 `__manifest__.py`; format `20.0.<major>.<minor>.<patch>` didefinisikan di `Docs/RELEASE-CHECKLIST.md`. | **P0** | 41/41 versi di tabel sama dengan manifest; diff rilis menunjukkan 0 selisih; tanggal generasi tercantum. |
| M2 | Path instalasi absolut Windows (`C:\Users\semua\...`) di README addons dan beberapa docs; layanan produksi mengarah ke mesin lokal tertentu. | Tidak bisa diikuti di VM/VPS Linux; membocorkan topologi mesin developer; self-host gagal. | Tulis `Docs/DEPLOY-LINUX-SELFHOST.md` dengan path relatif repo, venv, `odoo.conf` contoh tanpa nilai rahasia, systemd unit, reverse proxy, backup/restore; README addons hanya menautkan. | **P0** | Tidak ada path `C:\Users\...` di README root/addons dan docs aktif; clean VM Debian/Ubuntu mengikuti panduan sampai `/api/odoo/health` internal merespons. |
| M3 | Tabel status modul di README addons tidak sinkron dengan 41 manifest aktual; status bercampur "installed", "dev", "produksi belum", "perlu restart". | Tidak ada jawaban tunggal "modul apa yang aman di produksi?". | Definisikan 4 label status (terpasang & terverifikasi / terpasang di dev / belum terpasang / tidak installable) + kolom "sumber status" + tanggal; regenerasi daftar dari manifest; hapus status duplikat di narasi. | **P0** | Setiap dari 41 modul muncul tepat satu kali; setiap klaim status punya sumber (manifest, roadmap, atau checklist); tidak ada kontradiksi dengan `NAMLAH_ODOO_ONLY_ROADMAP.md`. |
| M4 | Hanya 13 dari 41 modul punya README; sisanya hanya deskripsi satu baris di README addons. | Onboarding maintenance lambat; modul kritis seperti `namlah_api` tidak punya kontrak lokal. | Template README modul ringkas (tujuan, dependensi, route/model utama, status, cara uji, rollback); backfill bertahap dimulai dari modul yang disentuh rilis & modul dengan migrasi (`namlah_api`, `namlah_project`). | **P1** | 100% modul dengan `migrations/` punya README; ≥80% modul berstatus "terpasang & terverifikasi" punya README; semua README memakai template. |
| M5 | `Docs/README.md` masih menyatakan struktur lama: `namlah_shared` git dependency repo terpisah, submodule `namlah-mobile`, `git clone --recurse-submodules`, sementara README root menyatakan konsolidasi 14 Nov 2026. | Developer menyiapkan kredensial & clone yang tidak perlu; kebingungan arsitektur. | Tandai dokumen lama `SUPERSEDED` dengan tanggal + tautan ke `Spesifikasi-Namlah-Yayasan.md` dan README root; indeks dibersihkan; hanya satu narasi struktur aktif. | **P0** | Tidak ada instruksi `--recurse-submodules` di docs aktif; setiap dokumen superseded punya penanda & pengganti. |
| M6 | Arsitektur API/sesi/tenant tersebar di roadmap, ADR-001, `API-BASE-URL.md`, checklist; sebagian menyebut proxy Vercel (sudah diputuskan dihentikan). | Refactor dan debugging lintas koloni berisiko mengubah perilaku yang disengaja. | `Docs/API-SESSION-TENANT.md` merangkum **keputusan owner yang sudah ada**: klien langsung ke Odoo/same-origin, cookie sesi Odoo native + PIN fallback API-only, identitas actor di field `x_namlah_*`/chatter, write via service identity, scope koloni server-side, record rule Project dimiliki `namlah_project` (ADR-001). | **P1** | Semua klaim memiliki tautan ke dokumen keputusan; tidak ada kalimat yang membalikkan keputusan owner; owner menandatangani dokumen ringkas ini. |
| M7 | Tidak ada runbook lokal/produksi dan troubleshooting terpusat; langkah verifikasi tersebar di README addons & docs per fitur. | Saat insiden, operator menebak; rollback tidak konsisten. | Buat runbook lokal (start/stop, seed, update modul, smoke), produksi (deploy, health, backup, rollback, observasi 30 menit), troubleshooting (401/403, sesi, 500, migration gagal, upload 0-byte, log). | **P1** | Runbook dijalankan sekali di lingkungan lokal & staging; setiap langkah punya perintah/verifikasi dan jalur rollback; tautan dari README root. |
| M8 | Controller monolit: `colonies.py` ~55 KB, `trace_admin.py` ~41 KB, `misc.py` ~31 KB, `beranda_notifications.py` ~29 KB, `products.py` ~28 KB (plus `dashboard.py` ~28 KB). | Review sulit, konflik merge sering, perubahan kecil berisiko route lain; onboarding lambat. | Dokumen kriteria pemecahan, batas ukuran, urutan dominan risiko & churn, dan checklist "tanpa perubahan perilaku" (lihat §4). Implementasi oleh owner/Agen C, bukan Agen D. | **P1** | Setiap file yang dipecah memiliki golden test kontrak sebelum/sesudah; batas ukuran disepakati; 0 perubahan status code/payload/idempotensi. |
| M9 | 221 `except Exception`; sebagian tanpa logging atau logging minimal. | Error hilang, 200 palsu, debugging produksi butuh reproduced locally. | Konvensi penanganan error terstruktur: kelas expected vs bug vs integrasi vs authz; aturan logging, re-raise, HTTP status, dan transaction (lihat §5). | **P1** | 0 `except Exception: pass` pada file yang disentuh; setiap broad catch punya kategori + log dengan konteks; tidak ada error yang diubah jadi sukses. Catatan: 614 `sudo()` adalah scope Agen C. |
| M10 | Tidak ada changelog/format catatan rilis; versi modul dan perubahan dokumen tidak berkorelasi. | Sulit menjawab "apa yang berubah sejak tag sebelumnya?" saat cutover. | `Docs/CHANGELOG.md` bergaya Keep a Changelog (Added/Changed/Fixed/Removed/Security) per komponen; setiap rilis wajib mencantumkan bump manifest, migrasi yang dijalankan, dan status smoke. | **P2** | Setiap bump versi memiliki entri changelog; entri rilis terakhir memiliki tautan ke checklist hasil uji. |
| M11 | `.gitignore` sudah menutup `__pycache__/`, `*.pyc`, `.env`, kunci, dump, log, `odoo.conf`, tetapi komentar submodule lama menyesatkan dan artefak curl lokal (`cookies*.txt`) belum tertutup eksplisit. | Risiko commit file sesi lokal; developer mengikuti instruksi clone lama. | Perbarui komentar, tambah pola artefak lokal/sesi & credential file bila perlu; uji dengan `git check-ignore`. **Tidak ada masalah `.pyc` ter-commit** (verifikasi tree: 0) — ini bukan item pembersihan. | **P2** | `git check-ignore -v` lolos untuk contoh `x.pyc`, `__pycache__/x.pyc`, `.env`, `cookies.txt`, `odoo.conf`; tidak ada pola yang mengabaikan `*.example`. |
| M12 | README addons memuat baris kredensial/lokasi rahasia (nilai tidak dicantumkan di sini) dan path ke berkas konfigurasi mesin tertentu. | Informasi sensitif terekspos & tidak bisa dipakai ulang. | Ganti seluruh tabel "Kredensial & lokasi" menjadi "Variabel lingkungan yang dibutuhkan" + placeholder jelas; rujuk pengamanan pada checklist cutover. | **P0** | Tidak ada nilai rahasia, wildcard kredensial, atau path mesin dinamis di dokumen; hanya nama env var & contoh `.example`. |

Prioritas berarti: **P0** sebelum rilis/cutover berikutnya; **P1** sebelum refactor besar selesai; **P2** hygiene berkelanjutan.

---

## 3. Rencana dokumentasi

### 3.1 Single source of truth versi

1. **Kebenaran:** field `'version'` di 41 `__manifest__.py` (contoh aktual `namlah_core` = `20.0.9.0.1`).
2. **Turunan:** `Docs/VERSIONS.md` berisi tabel `modul | versi | status | sumber status | tanggal generasi`. Tabel yang sama (atau ringkasannya) dipakai di `README.md` dan `namlah-odoo-addons/README.md`.
3. **Mekanisme:** generator ringan yang membaca manifest → Markdown. Jika generator belum tersedia, pembaruan manual + pengecekan keselarasan di CI (dikoordinasikan dengan Agen B; Agen D tidak mengubah `ci.yml`). Format dan daftar modul ditentukan Agen D.
4. **Aturan bump:** perubahan skema/data butuh bump minor; perbaikan kompatibel butuh bump patch; perubahan kontrak API butuh keputusan owner + changelog. Versi Odoo `20.0.x.y.z` tidak dicampur dengan versi app Flutter (`v0.4.0+5`) — keduanya diberi label berbeda di README root.
5. **Konten yang tidak boleh lagi jadi kebenaran:** angka versi yang ditulis bebas di narasi docs; harus merujuk ke tabel hasil generasi.

### 3.2 Instalasi Linux/self-host menggantikan path Windows

- File baru `Docs/DEPLOY-LINUX-SELFHOST.md`, struktur usulan:
  1. Prasyarat: Debian/Ubuntu, Python venv, PostgreSQL 17, Odoo 20 Community, `addons_path` relatif terhadap repo.
  2. Konfigurasi: contoh `odoo.conf` dengan placeholder (tanpa nilai asli), `http_interface = 127.0.0.1`, `proxy_mode`, `list_db = False`, logrotate.
  3. Service: unit systemd, start/stop/restart, `-u`/`-i` hanya saat perubahan data/aset; restart cukup untuk perubahan Python.
  4. Reverse proxy & TLS: Caddy/Nginx, header `X-Forwarded-*`, WebSocket, batas upload; rujuk `NAMLAH_CUTOVER_CHECKLIST.md` Phase 2.
  5. Verifikasi: health internal, smoke auth/session, role gate, daftar modul terpasang.
  6. Backup/restore: DB + filestore, uji restore, enkripsi; jangan taruh dump di repo.
- README addons: ubah bagian "Cara menjalankan", "Verifikasi", "Kredensial & lokasi", "OCA addons" menjadi ringkasan + tautan. OCA yang belum di-port ke 20.0 diberi tabel status tersendiri, bukan campuran dengan modul Namlah.

### 3.3 Arsitektur API/session/tenant yang jujur

`Docs/API-SESSION-TENANT.md` hanya merekap keputusan yang sumbernya sudah ada:

- **Base URL:** proxy Vercel dipensiunkan; klien langsung ke Odoo; web superapp & LokalMart same-origin; pilot LAN vs tunnel vs produksi dibedakan oleh environment, bukan per app. Sumber: `Docs/API-BASE-URL.md`.
- **Sesi:** sesi Odoo native (cookie `session_id`, `HttpOnly`/`Secure` di belakang proxy) + PIN fallback sebagai sesi API-only. Sumber: `NAMLAH_ODOO_ONLY_ROADMAP.md`, `NAMLAH_CUTOVER_CHECKLIST.md`.
- **Identitas actor:** identitas asli disimpan di field `x_namlah_*` dan chatter; write dieksekusi service identity, bukan berarti user bebas lintas data. Sumber: roadmap.
- **Tenant/koloni:** pembatasan scope dilakukan server-side (domain/query), bukan dengan memberi ACL portal luas; `ir.access` bersifat memberi akses, sehingga record rule koloni tidak dipasang secara naif di `namlah_security`. Project dimiliki tunggal oleh `namlah_project` (ADR-001). Sumber: README addons catatan desain, `Docs/ADR-001-pemilik-modul-project.md`, `Docs/ARSITEKTUR-NAMLAH-PROJECT.md`.
- **Yang masih terbuka:** apex domain, infra produksi, backup, monitoring, dan keputusan owner bertanda `[isi]` di checklist cutover — tetap ditulis sebagai **belum diputuskan**, tidak diarang-anggap selesai.
- Dokumen lama yang menyebut struktur lama/submodule/proxy diberi label `SUPERSEDED` + tanggal + pengganti, bukan dihapus tanpa jejak.

### 3.4 Runbook lokal & produksi, troubleshooting

- **Runbook lokal:** bootstrap venv & DB pilot, seed idempotent, update modul, jalankan verifikasi lokal, reset data uji, restart, log yang sesuai.
- **Runbook produksi:** preflight (versi manifest, backup terverifikasi, freeze), deploy, smoke pasca-deploy, observasi, rollback (revert kode + restore DB/filestore + `-u`), eskalasi ke owner. Rujuk Phase 5–6 checklist cutover tanpa mengklaim infra sudah ada.
- **Troubleshooting:** gejala → penyebab → diagnosa → remedy. Minimal: 401/403 (sesi & role), 500 tanpa pesan (lihat konvensi logging §5), `/api/odoo/health`, migration gagal (2 modul dengan `migrations/`), attachment 0-byte (rujuk `Docs/CODING-GUIDE.md`), dashboard/KPI kosong karena kualitas data, dan websocket gagal lewat reverse proxy.
- Setiap runbook punya baris "kewajiban konfirmasi owner" untuk aksi yang bersifat produksi.

### 3.5 Backfill README modul

- Template singkat: tujuan & domain; dependensi; route/model utama; status (sama dengan tabel pusat); cara uji; migrasi/rollback; tautan dokumen terkait.
- Urutan: `namlah_api`, `namlah_project` (keduanya punya migrasi), modul dengan status produksi/terpasang, lalu modul baru/dev. Tidak ada README yang boleh mengulang versi secara bebas — selalu rujuk `Docs/VERSIONS.md`.

---

## 4. Rencana refactor bertahap controller monolit (dokumen pendukung, bukan implementasi Agen D)

### 4.1 Kriteria pemecahan

Sebuah controller masuk antrean bila memenuhi **minimal dua** dari:

- Ukuran > ~20–25 KB atau > ~800 baris (saat ini lima file terbesar 28–55 KB).
- > ~10 route/endpoint publik dalam satu file, atau lebih dari satu domain bisnis (mis. campuran koloni, anggota, dan kasir).
- Churn tinggi: `git log --follow --name-only` menunjukkan file itu termasuk 20% teratas yang paling sering berubah dalam 90 hari terakhir. Churn harus **diukur**, bukan diasumsikan dari ukuran.
- Risiko: menyentuh authz, scope koloni/tenant, uang/order, ledger append-only, atau efek samping eksternal (notifikasi).
- Sulit diuji: tidak bisa dijalankan tanpa DB pilot penuh, atau tidak ada golden test kontrak.

### 4.2 Batas ukuran & bentuk target

- Target file hasil pemecahan: ~300–600 baris, **maksimum ~800 baris**; satu file = satu domain route prefix (mis. `colonies_*.py`, `colonies_members.py`), bukan satu file per endpoint.
- Ekstraksi bertingkat:
  1. **Helper murni** (parsing, validasi, format respons, constant) → `controllers/helpers.py` yang sudah ada atau helper baru di modul yang sama; tidak mengakses DB.
  2. **Service layer** (query, guard tenant/role, operasi tulis, chatter) → lapisan service modul; koordinasikan dengan Agen C agar tidak menduplikasi kebijakan identitas/`sudo()`.
  3. **Controller tipis** → routing, auth guard, serialisasi JSON, status code.
- Batas PR refactor: satu domain per PR, diff bisa direview (< ~400 baris per PR bila memungkinkan), satu commit revertible.
- Tidak ada perubahan nama route, status code, bentuk payload, urutan field, pagination, idempotensi, atau pesan error tanpa keputusan owner terpisah.

### 4.3 Urutan prioritas (risiko × frekuensi perubahan)

| Gelombang | Kandidat | Alasan | Gerbang |
|---|---|---|---|
| 0 — fondasi | Golden test kontrak untuk route yang akan dipecah; daftar churn dari git log | Tanpa baseline, "tanpa perubahan perilaku" tidak bisa dibuktikan. | Test lulus sebelum diff refactor. |
| 1 — risiko rendah, churn tinggi | `misc.py` (~31 KB), helper bersama di `namlah_api/controllers/helpers.py`, route baca sederhana | Permukaan lebar tapi efek samping relatif kecil; latihan pola ekstraksi. | Diff status/payload = 0; review Agen C untuk service boundary. |
| 2 — domain bisnis menengah | `products.py` (~28 KB), `beranda_notifications.py` (~29 KB), `dashboard.py` (~28 KB) | Sering dipakai, menyentuh kualitas data & KPI; perlu uji per role. | Uji per role + payload snapshot identik. |
| 3 — tenant & koloni | `colonies.py` (~55 KB) | Terbesar, paling berisiko scope lintas koloni/authz. | Uji isolasi tenant, role gate, dan guard 401/403 eksplisit; review owner. |
| 4 — ledger & trace | `namlah_qr_trace/controllers/trace_admin.py` (~41 KB) | Serial unik, kardus, ledger append-only; blast radius tinggi dan lintas modul. | Uji append-only/urutan ledger & endpoint publik `/trace/<serial>`; gelombang terakhir. |

Catatan: `trace_admin.py` berada di modul `namlah_qr_trace`, bukan `namlah_api`; pemecahan tidak boleh memindahkan kepemilikan ke modul lain tanpa keputusan arsitektur.

### 4.4 Acceptance criteria refactor

- Sebelum/sesudah: status code, header relevan, keys JSON, tipe nilai, pagination, urutan, dan idempotensi identik (diff golden test kosong).
- Tidak ada perubahan logika authz/tenant; jika ditemukan bug selama refactor, dicatat sebagai temuan terpisah dan diperbaiki di PR terpisah.
- Setiap file baru punya satu tanggung jawab dan README modul menyebutnya.
- Rollback = revert satu PR; tidak memerlukan migrasi data baru.
- Agen D hanya menyediakan kriteria, templat checklist review, dan dokumentasi hasil; implementasi tetap oleh pemilik source.

---

## 5. Standarisasi error handling/logging (221 `except Exception`)

### 5.1 Kategori

| Kategori | Contoh | Perlakuan |
|---|---|---|
| **Expected validation / kontrol alur** | input buruk, duplikat, guard stage, role tidak sesuai | Tangani dengan exception spesifik bila bisa; kembalikan 4xx yang jelas; log level `info`/`warning` dengan konteks, jangan stack trace penuh ke klien. |
| **Authz/sesi** | anonim, role salah, sesi berakhir | 401/403 konsisten; pesan tidak membocorkan detail tenant/akun; jangan `except Exception` yang menelan guard. |
| **Integrasi eksternal sementara** | WhatsApp, Telegram, email, LiveKit, Xendit, Cloudflare | Tangani exception spesifik + timeout; retry terbatas bila idempoten; log `warning`/`error` dengan nama provider, endpoint logis, dan correlation id; jangan jatuhkan transaksi bisnis tanpa keputusan. |
| **Bug / kondisi tak terduga** | `KeyError`, query gagal, tipe salah | Log `error` dengan `exc_info=True`, kembalikan 5xx generik ke klien, biarkan transaksi di-rollback; jangan diubah jadi 200. |
| **Migration/startup** | script migrasi gagal | Fail-fast, log lengkap, hentikan deploy; tidak boleh ditelan agar DB tidak setengah berubah. |

### 5.2 Strategi logging terstruktur

- Satu logger per modul (`logging.getLogger(__name__)`), satu titik log per kejadian (hindari duplikasi di helper + controller).
- Konteks minimum: route/method, kode status, actor (Semut-ID/user id bila tersedia), koloni/company scope, request/correlation id, durasi untuk operasi eksternal, dan versi modul dari manifest.
- Gunakan placeholder `%s` / structured key-value; jangan meng-interpolasi string secara manual pada hot path.
- **Dilarang** mencatat kredensial, kata sandi, data rahasia, isi cookie/sesi, atau PII berlebih; gunakan redaksi/identifier bukan nilai.
- `log_level = warn` di produksi (lihat checklist cutover) harus tetap memberi visibility: error & bug tetap tercatat; expected 4xx tidak membanjiri log.
- `except Exception:` tanpa `as e`, tanpa konteks, atau hanya `pass`/`return {}` dianggap tidak memenuhi standar. Bila memang disengaja, wajib ada komentar alasan + kondisi sempit.
- Jangan menimpa exception asli saat melakukan cleanup; gunakan `raise` (bukan `raise Exception(...)`) bila tidak ada penambahan informasi.

### 5.3 Rollout

1. Dokumentasi konvensi di `Docs/CODING-GUIDE.md` + ringkasan di template README modul (Agen D).
2. Gelombang 1: helper/shared dan endpoint baca; gelombang 2: endpoint tulis & role gate; gelombang 3: integrasi eksternal; gelombang 4: migration/startup.
3. Setiap gelombang: golden test kontrak + uji log (pesan error tidak bocor, stack trace hanya di server).
4. Metrik: jumlah `except Exception` tanpa kategori turun ke 0 pada file yang disentuh; tidak ada kenaikan 5xx yang tidak dijelaskan; tidak ada error yang berubah menjadi respons sukses.

Catatan koordinasi: 614 `sudo()` tidak dibahas di sini selain sebagai penanda bahwa perubahan service layer harus melewati Agen C.

---

## 6. Release/versioning, changelog, `.gitignore`, definition of done dokumentasi

### 6.1 Release & versioning

- Format entri rilis: versi/tanggal, komponen (Odoo modul / Flutter app / docs), Added, Changed, Fixed, Removed, Security, migrasi yang dijalankan, hasil smoke, dan pemilik keputusan.
- Sebelum rilis: bump manifest yang berubah → regenerasi `Docs/VERSIONS.md` → sinkronkan README → tulis changelog → jalankan checklist rilis → konfirmasi owner.
- Migration: dua modul punya folder `migrations` (`namlah_api`, `namlah_project`); checklist wajib mencatat urutan, DB staging yang dipakai, dan hasil verifikasi. Tidak ada migrasi baru yang diandaikan.
- Hubungan dengan cutover: `NAMLAH_CUTOVER_CHECKLIST.md` tetap menjadi sumber status produksi; `Docs/RELEASE-CHECKLIST.md` adalah preflight rilis berulang, bukan pengganti keputusan `[isi]` owner.

### 6.2 Hygiene `.gitignore`

- Pertahankan cakupan existing: `__pycache__/`, `*.pyc`, `.env`/`.env.*` dengan pengecualian `*.example`, `*.pem`/`*.key`/keystore, `*.log`, dump SQL, `odoo.conf`.
- Tambah/perjelas: pola cookie/sesi lokal (`cookies*.txt`) dan credential file tambahan bila dipakai; hapus/koreksi komentar submodule lama yang bertentangan dengan README root.
- **Tidak ada item "hapus `.pyc` ter-commit"**: verifikasi GitHub tree menunjukkan 0 file `.pyc`; ini hanya pencegahan.
- Uji: `git check-ignore -v` untuk contoh artefak; pastikan file contoh (`*.example`) tetap ter-track.

### 6.3 Definition of done (dokumentasi)

Sebuah perubahan docs selesai bila:

1. Setiap angka versi/status bersumber dari manifest atau dokumen keputusan, bukan ingatan.
2. Tidak ada path absolut mesin tertentu, nilai kredensial, atau lokasi berkas rahasia di dokumen aktif.
3. Dokumen lama yang bertentangan diberi `SUPERSEDED`/`historis` + tautan pengganti; tidak ada dua instruksi instalasi yang aktif bersamaan.
4. Prosedur Linux/self-host dan runbook telah dicoba minimal sekali di lingkungan bersih (lokal/staging), lengkap dengan verifikasi & rollback.
5. Setiap klaim arsitektur memiliki tautan ke keputusan owner; item yang belum diputuskan tetap berstatus terbuka.
6. Changelog & checklist rilis diperbarui bila perubahan menyentuh rilis/versi/migrasi.
7. `.gitignore` lolos uji `check-ignore` dan tidak mengabaikan contoh yang harus dibagikan.
8. Reviewer: owner untuk keputusan arsitektur/produksi; Agen B untuk klaim CI; Agen A/C untuk klaim guard/service bila disebut.

---

## 7. Koordinasi, risiko, dan acceptance criteria akhir

### Koordinasi

| Pihak | Antarmuka dengan Agen D |
|---|---|
| **Agen A** | Agen D mendokumentasikan keberadaan & cara menjalankan guard deny-by-default, tanpa mengedit `scripts/check_deny_by_default.py`. Perubahan aturan guard → Agen A, lalu docs mengikuti. |
| **Agen B** | Agen D menyediakan daftar modul & format tabel untuk pengecekan drift versi/status di CI; Agen B yang mengubah `.github/workflows/ci.yml`. Hasil check CI menjadi bukti acceptance M1/M3. |
| **Agen C** | Agen D menulis kriteria pemecahan controller, konvensi error/logging, dan service boundary; Agen C memastikan refactor tidak duplikasi/melebarkan kebijakan `sudo()`/service identity. Tidak ada detail kepemilikan `sudo()` yang diklaim Agen D. |
| **Owner** | Menetapkan item `[isi]` cutover, status produksi, ratifikasi arsitektur & perubahan kontrak API, serta review README modul. |

### Risiko & mitigasi

| Risiko | Mitigasi |
|---|---|
| Tabel versi kembali drift setelah rilis | Generator/manual + CI check dari Agen B; versi hanya di README hasil turunan manifest. |
| Panduan Linux ditulis tapi kenyataannya masih Windows-only | Uji di VM bersih; path & env var relatif; catat deviasi sebagai temuan, bukan disembunyikan. |
| Refactor mengubah perilaku | Golden test kontrak sebelum/sesudah, PR per domain, rollback satu commit, bug baru dipisah PR. |
| Logging meluas/membocorkan data | Aturan redaksi, konteks terbatas, review contoh log; tidak mencatat kredensial/PII. |
| Docs lama dianggap masih berlaku | Penanda `SUPERSEDED`, indeks `Docs/README.md` sebagai satu pintu, tautan ke spec/ADR. |
| Agen D tertarik mengubah source/CI/guard | Batas kepemilikan eksplisit di §1; semua perubahan di luar itu dikirim sebagai permintaan ke A/B/C/owner. |

### Acceptance criteria akhir Agen D

- README root & addons: 41 modul sinkron dengan manifest, 0 versi drifting, 0 path Windows absolut, 0 kredensial nyata.
- `Docs/VERSIONS.md`, indeks `Docs/README.md`, `Docs/API-SESSION-TENANT.md`, `Docs/DEPLOY-LINUX-SELFHOST.md`, runbook lokal/produksi, troubleshooting, changelog, dan checklist rilis tersedia & saling menaut.
- Setiap dokumen lama yang bertentangan berstatus jelas; keputusan owner tidak ditulis ulang sebagai keputusan baru.
- Kriteria refactor 5 controller terbesar & konvensi 221 `except Exception` terdokumentasi, dengan gerbang uji yang jelas; tidak ada implementasi source/CI/guard oleh Agen D.
- `.gitignore` terverifikasi untuk artefak Python/env/rahasia; tidak ada klaim pembersihan `.pyc` (tree bersih).
- Semua item yang masih menunggu owner ditandai `[isi]`/`belum diputuskan`, bukan ditutup secara fiktif.

