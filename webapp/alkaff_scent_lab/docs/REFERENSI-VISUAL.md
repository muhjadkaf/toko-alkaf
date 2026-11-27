# Referensi Visual — Alkaff Maklon Hall

Dokumen ini mencatat riset multi-agen untuk merancang ulang dunia theater
menjadi pabrik maklon parfum dengan nuansa ruang hangat dan profesional seperti
butik parfum. **Semua halaman diakses tanggal 2026-11-27.**

Keputusan penting: **foto internet dipakai sebagai referensi nuansa, bukan
disalin ke dalam repo.** Seluruh piksel plate dibuat ulang secara prosedural
dengan numpy + PIL oleh `tools/generate_world_plates.py` dan
`tools/texture_utils.py`. Tidak ada gambar pihak ketiga yang disimpan, tidak ada
logo/merek botol yang ditiru, dan tidak ada sosok manusia di dunia theater.

Batasan klaim: dokumen ini hanya membahas estetika, material, dan peralatan.
Tidak ada klaim medis, kosmetik, khasiat 24 jam, bebas alergi, afrodisiak,
menghangatkan tubuh, halal, maupun formula produksi.

---

## 1. Nuansa butik parfum (rak, cahaya, material)

| URL sumber | Akses | Status verifikasi | Observasi |
|---|---|---|---|
| https://www.pexels.com/photo/perfume-bottles-displayed-in-fragrance-store-19663386/ | 2026-11-27 | Halaman berhasil di-fetch; metadata warna tersedia | Dominan hitang arang `#1A1A1A`, olive, abu, tan `#CD853F`; botol rapat dan berulang horizontal; label hangat kontras dengan rak gelap. |
| https://www.pexels.com/photo/elegant-fragrance-display-in-a-boutique-28664164/ | 2026-11-27 | Halaman berhasil di-fetch; metadata warna tersedia | `#000000`, saddle brown `#A0522D`, tan `#D2B48C`; kaca amber dengan latar abu terang; rak bertingkat dengan pantulan lembut, kesan elegan bersih. |
| https://www.pexels.com/photo/shelves-with-perfume-bottles-5206892/ | 2026-11-27 | Halaman berhasil di-fetch; metadata warna tersedia | Rak menyala dari belakang/bawah; simetri botol berulang; goldenrod `#DAA520` dan wheat `#F5DEB3` memberi efek etalase premium. |
| https://www.pexels.com/photo/bottles-in-glass-domes-arranged-on-display-7702795/ | 2026-11-27 | Halaman berhasil di-fetch; metadata warna tersedia | Botol di dalam kubah kaca di atas plinth abu; presentasi "hero product" monokrom, fokus pada siluet kaca. |
| https://www.dezeen.com/2025/07/27/elorea-los-angeles-studio-paul-chan/ | 2026-11-27 | Halaman berhasil di-fetch; artikel + foto proyek | Podium hitam bertekstur dengan kaki aluminium; kaca reflektif gelap, sconce hangat, cove lighting; kayu Shou Sugi Ban memberi kedalaman. |
| https://www.dezeen.com/2026/03/19/all-matters-studio-store-scent-brand-en-doft-stockholm/ | 2026-11-27 | Halaman berhasil di-fetch; artikel + foto proyek | Minimalis dengan ruang belakang merah tua; meja batu kapur, profil aluminium, rak baja lipat; silinder translusen dan karpet bertekstur melemahkan kesan steril. |
| https://www.dezeen.com/2024/04/12/esrawe-cadena-xinu-marsella-fragrance-boutique-mexico-city/ | 2026-11-27 | Halaman berhasil di-fetch; artikel + foto proyek | Paviliun kayu laminated, louvre vertikal sekaligus penyangga vitrine; panel kaca dengan track lighting; props botanis dan lilin memberi nuansa workshop. |
| https://www.dezeen.com/2026/07/12/costa-brazil-store-hudson-yards-new-york-alexander-may/ | 2026-11-27 | Halaman berhasil di-fetch; artikel + foto proyek | Plinth hitam, lempengan beton, kayu hitam, rak panjang ~30 kaki; light box plafon dan lantai kayu; buku/kerajinan/meja rendah membuat toko terasa seperti salon. |

**Palet yang dipakai:** arang `#1A1A1A`, amber `#A0522D`, kuningan `#B08D57`,
wheat `#F5DEB3`, merah tua `#7A1F1F`.

**Props paling sering muncul:** botol kaca berlabel, podium/plinth, rak/vitrine,
permukaan reflektif, aksesori atmosfer (lilin, botanis, buku, bangku rendah).

**Terjemahan ke plate:** dinding beton hangat, lantai epoksi kilap lembut, rak
kayu berrel kuningan berisi botol amber berlabel matte, lampu high-bay hangat,
vignette dan film grain halus. Tidak ada garis grid atau kotak polos.

---

## 2. Peralatan maklon / lab nyata

| URL sumber | Akses | Status verifikasi | Observasi dan catatan render |
|---|---|---|---|
| https://suncombe.com/products/jacketed-mixing-vessels | 2026-11-27 | HTTP 200 (curl + fetch) | Tangki berjaket 75 L, 316L interior, finish 180 grit; tutup dengan grid pengaman, mixer atas, tri-clamp + katup diafragma, panel kontrol VFD, kaki/roda. → silinder vertikal + jaket + kubah + kaki + highlight logam sempit. |
| https://www.sansunstainless.com/Stainless-Steel-Tri-Clamp-End-Diaphragm-Pressure-Gauge-pd721134298.html | 2026-11-27 | HTTP 200 (curl + fetch) | Gauge diafragma tri-clamp, bezel stainless, dial melingkar, leher pendek, ferrule berbibir. → lingkaran konsentrik + jarum + tick mark + gradient cermin. |
| https://www.zonesunpackaging.com/product/automatic-4-head-vacuum-perfume-liquid-bottle-filling-capping-machine-line/ | 2026-11-27 | HTTP 200 (curl + fetch) | Empat nozzle vertikal paralel, conveyor rantai, tangki penampung, PLC/touchscreen, sensor. → modul stainless dengan empat nosel dan botol di bawahnya. |
| https://unista.fr/en/portfolio/ligne-de-remplissage-fragrance-avec-convoyeur-magnetique/ | 2026-11-27 | HTTP 200 (curl + fetch) | Lini ~16 m: conveyor magnetik, peniupan, timbangan per botol, penutup/pump, label + laser marking, inspeksi kamera, robot case packer, pintu kaca + light curtain. → modul berurutan sepanjang frame dengan bayangan panel berulang. |
| https://usines-parfum.fragonard.com/usines/la-fabrique-des-fleurs/ | 2026-11-27 | HTTP 200 (curl + fetch) | Dokumentasi pabrik: penimbangan, *orgue du parfumeur* (lemari deretan botol esensi), lini semi-otomatik dengan godet, stasiun isi, pemasangan pompa, kode inkjet, mesin label, QC di ujung lini. → deretan wadah mangkuk kecil dan meja QC. |
| https://www.scientificamerican.com/article/how-chemists-engineer-the-signature-smells-of-luxury-perfumes/ | 2026-11-27 | HTTP 200 (curl + fetch) | Lab: teknisi memakai pipet di atas vial kaca dan timbangan digital; dinding penuh toples; ~50.000 vial percobaan di rak. → grid vial, pipet panjang tipis, timbangan display miring, bayangan lembut. |
| https://www.hamiltoncompany.com/syringes/80300 | 2026-11-27 | Terverifikasi (fetch API sukses; `curl` 403 anti-bot) | Syringe mikroliter 10 µL: barrel borosilikat ramping, plunger stainless, jarum 26s gauge 51 mm, ujung bevel, color band. → silinder kaca transparat sangat ramping + plunger logam + jarum + garis gradasi mikro. |
| https://vestil.com/product.php?FID=759 | 2026-11-27 | HTTP 200 (curl + fetch) | Rak drum stainless stackable untuk 3 drum 55 galon, cradle setengah lingkaran, akses forklift. → cradle melengkung + drum silindris + bayangan lamparan panjang. |

**Delapan props prioritas:** meja QC stainless; tray vial + rak botol berbaris;
pipet mikro + syringe mikroliter; timbangan digital; botol sampel + rol label;
tangki berjaket mini di latar; pipa tri-clamp + katup + gauge dial; rak gudang +
drum.

**Terjemahan ke plate:** `scene_scan` memakai drum di atas palet kayu dan meja
QC; `scene_mix` memakai lima tangki berjaket, pipa berflange, gauge dial, dan
catwalk; `scene_analyze` memakai meja QC dengan enam vial, dua suntikan/pipet,
dan timbangan kaca; `scene_result` memakai conveyor dengan botol berlabel.

---

## 3. Sumber foto/tekstur berlisensi

| URL sumber | Akses | Status verifikasi | Lisensi dan pemakaian |
|---|---|---|---|
| https://unsplash.com/license | 2026-11-27 | Verifikasi tidak langsung (401 bot-protection; dikonfirmasi lewat indeks + halaman bantuan resmi) | Unsplash License: gratis komersial, tanpa atribusi wajib, boleh dimodifikasi; merek/orang dalam foto tidak ikut terlisensi. → aman sebagai referensi. |
| https://help.unsplash.com/en/articles/2612315-can-i-use-unsplash-images-for-personal-or-commercial-projects | 2026-11-27 | Terverifikasi langsung | Menegaskan pemakaian komersial/personal/editorial tanpa kredit wajib. → referensi gaya. |
| https://www.pexels.com/license/ | 2026-11-27 | Terverifikasi langsung | Pexels License: bebas pakai & modifikasi, komersial OK; dilarang jual salinan utuh atau menyiratkan dukungan merek. → referensi boleh, latar sebaiknya dimodifikasi. |
| https://www.pexels.com/photo/perfume-15096784/ | 2026-11-27 | Terverifikasi langsung (foto "Free", botol di atas kayu rustik) | Mengikuti Pexels License. → referensi hangat-butik; latar dirender ulang agar label botol tidak disalin. |
| https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia | 2026-11-27 | Terverifikasi langsung (revisi 2 Nov 2026) | Lisensi per file (CC BY / BY-SA / CC0 / PD); cek satu per satu. → aman sebagai referensi. |
| https://creativecommons.org/publicdomain/zero/1.0/ | 2026-11-27 | Terverifikasi langsung | CC0 1.0: boleh salin, modifikasi, distribusikan, komersial, tanpa izin; tidak menghapus hak merek dagang. → paling aman untuk tekstur latar generik. |
| https://ambientcg.com/about/license | 2026-11-27 | Terverifikasi langsung | Semua aset ambientCG CC0 termasuk preview render; kredit opsional. → aman untuk tekstur kayu/batu/kertas. |
| https://polyhaven.com/license | 2026-11-27 | Terverifikasi langsung | HDRI, tekstur, model CC0; logo/teks/contoh render pengguna tidak otomatis CC0. → aman untuk tekstur & pencahayaan, jangan ambil elemen UI situs. |

**Keputusan:** pakai foto Unsplash/Pexels/Wikimedia untuk *mood* dan komposisi,
lalu render ulang dengan PIL. Alasannya: konsistensi palet, grain, kontras,
bayangan, dan margin antar plate jauh lebih mudah dijaga; risiko hak cipta dan
merek botol berkurang karena hasilnya karya baru, bukan salinan utuh. Bila tetap
memakai foto langsung, harus dimodifikasi signifikan dan disimpan catatan
sumber + tanggal akses. Tidak ada foto yang diunduh untuk proyek ini.
