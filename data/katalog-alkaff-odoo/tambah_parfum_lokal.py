import csv, html, os
from copy import copy
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

OUT = '/home/mintbag/Desktop/NUAMLAH/katalog-alkaff-odoo'
XLSX = OUT + '/katalog_parfum_alkaff_odoo.xlsx'
CSV = OUT + '/katalog_parfum_alkaff_odoo.csv'

wb = load_workbook(XLSX)
ws = wb['IMPORT_odoo']
detail = wb['Detail_Harga_Sumber']
guide = wb['Panduan_Import']

HEADERS = [c.value for c in ws[1]]
DETAIL_HEADERS = [c.value for c in detail[1]]

# ---------------------------------------------------------------------------
# DATA SUPPLIER / BRAND OWNER (semua dari sumber publik, divalidasi 2026-11-26)
# ---------------------------------------------------------------------------
SUPPLIERS = [
    # brand, rank, share, perusahaan, jenis, alamat, kota, kontak, email, web, kanal, sertifikasi, catatan, sumber
    ('MyKonos', '1 (Databoks/Compas)', '6,75%', 'PT Mykonos Parfume Indonesia',
     'Brand owner (pendiri/CEO: Koyal Shankar Harjani, 2019)',
     'Kawasan Industri Pulogadung, Blok III, Jl. Rawagatel No.2-2A, RW.3, Jatinegara, Cakung',
     'Jakarta Timur 13920', '+62 816-609-189', 'form kontak di situs resmi',
     'officialmykonos.com', 'Website resmi, toko fisik, Shopee/TikTok',
     'BPOM (klaim brand), diproduksi di fasilitas bersertifikat, no animal testing',
     'Populer Gen Alpha; strategi scarcity + kolaborasi e-sports. Harga resmi Marbella/Sorrento mulai Rp449.000 (50/100 ml). Toko fisik Purworejo & eceran Bandung tercatat di peta (bukan pusat).',
     'officialmykonos.com; officialmykonos.com/pages/contact; facebook.com/Officialmykonos; suara.com 11/07/2026'),

    ('Scarlett', '2 (Databoks/Compas)', '5,43%', 'PT Sinar Alfa Omega',
     'Brand owner',
     'HQ: Jakarta Barat; mitra operasional/produksi tercatat di Kp. Cibejog, Girimekar, Cilengkrang',
     'Jakarta Barat / Bandung, Jawa Barat 40619', 'melalui situs & reseller resmi', 'cs@scarlett.id',
     'scarlett.co.id; scarlettofficial.id', 'Website, Shopee, Tokopedia, TikTok Shop, Lazada, Zalora, minimarket & modern trade',
     'BPOM',
     'Sejak 2017. 21 aroma parfum, Extrait de Parfum 30 ml. Ada program "Reseller Resmi Scarlett" & "Official Partner" — jalur yang tepat untuk toko. Harga resmi Garden of Whisper 30 ml Rp60.900.',
     'scarlett.co.id/about; scarlett.co.id; linkedin.com/company/scarlett-indonesia'),

    ('HMNS', '3 (Databoks/Compas)', '5,06%', 'PT Hadir Mengharumkan Nusantara',
     'Brand owner (CEO/founder: Rizky Prakoso, 2019)',
     'Mastro Center, Jl. Kebon Sirih No.63, RT.4/RW.2, Kb. Sirih, Menteng',
     'Jakarta Pusat 10340', '+62 813-9555-3352 (+62 813-1558-3002 untuk komplain internasional)',
     'care@madeforhmns.com; hmnsperfume@gmail.com', 'hmnsperfume.com; madeforhmns.com',
     'Website, Shopee, Tokopedia, TikTok Shop; offline store Grand Indonesia, Margocity Depok, Paskal23 & Summarecon Bandung',
     'BPOM (produk terdaftar)',
     'Teknik "Soliflore" (menonjolkan satu jenis bunga) dengan bahan lokal. Farhampton 100 ml Rp563.343 di situs resmi. Alpha 100 ml best seller.',
     'hmnsperfume.com/pages/terms-conditions-revamp (29/06/2026); hmnsperfume.com/pages/about; Glints'),

    ('Saff & Co', '4 (Databoks/Compas)', '3,52%', 'PT Flexo Solusi Indonesia (alamat retur/operasional)',
     'Brand owner (didirikan 2019/2020)',
     'Jl. Tanjung Duren Raya, Grogol Petamburan; ruko Kota Indah A14, Jl. Pangeran Jayakarta, Taman Sari',
     'Jakarta Barat 11470', '+62 851-7440-7675',
     'customerservice@saffnco.com; partnership@saffnco.com (bisnis); hello@saffnco.com',
     'saffnco.com', 'Website, marketplace resmi, 9 offline store official partner',
     'BPOM; halal (seri Heavenly Potion sudah bersertifikat halal, lainnya dalam proses)',
     '100+ authorized reseller. Berkolaborasi dengan master perfumer Shyamala Maisondieu. Harga resmi Rp249.000–Rp409.000. Gunakan email partnership@ untuk kerja sama reseller.',
     'saffnco.com/pages/contact; saffnco.com/pages/returns-exchanges; saffnco.com/pages/offline-store; linkedin.com/company/saffnco'),

    ('Octarine', '5 (Databoks/Compas)', '2,98%', 'PT Octarine Creativescent Indonesia',
     'Brand owner (didirikan Mei 2022)',
     'Cluster The Cliff No.68, Kec. Mulyaharja, Bogor Selatan',
     'Bogor, Jawa Barat', '0851-2123-0946 / +62 851-2330-0738',
     'customercare@octarine.co.id; octarineperfume@gmail.com', 'octarine.co.id',
     'Website, Shopee, Tokopedia, TikTok Shop, Mewwa Beauty Bogor',
     'BPOM (contoh: NA18250600337 untuk Vanilla Laice)',
     'Konsep "inspired perfume" playful/klasik + edisi terbatas. Harga resmi 50 ml Rp73.800, 20 ml Rp29.900–Rp34.000. Pernah kolaborasi dengan Dust La Stella & Kadam Sidik.',
     'octarine.co.id; octarineparfume.com; linkedin.com/company/99422236'),

    ('Macbrame', '6 (Databoks/Compas)', '1,57%', 'PT Macbramindo Harum Abadi / Maharum Group',
     'Supplier bibit & konsentrat wewangian (B2B)',
     'Kantor: Ruko ICE Business Park Blok E/15, Pagedangan. Operasional: Taman Tekno Sektor XI Blok J1 No.5, BSD, Setu. Pabrik: Taman Tekno Blok H08 No.23 (BSD) & Kawasan Blessindo Blok O 11, Jl. H. Tabri No.228, Legok',
     'Tangerang / Tangerang Selatan, Banten 15339 / 15314',
     '0811-8881-7899; 021-756-85303', 'cs@maharumgroup.com; hary@macbrame.com',
     'macbrame.com; maharum.group', 'B2B langsung, agen/distributor area',
     'Halal (konsentrat); GMP',
     'PENTING UNTUK ALKAFF: sudah terdaftar sebagai "factory" di nota toko untuk banyak aroma (ameer al oud, aqua di gio, dll.). 900+ aroma, kemasan 100 gr–25 kg. Pricelist & sampel via form maharum.group/sample-request. Pabrik kedua diresmikan 20/11/2026.',
     'macbrame.com; maharum.group/macbrame; kompas.com 20/11/2026; kc.umn.ac.id/id/eprint/38720'),

    ('Morris', '7 (Databoks/Compas)', '1,49%', 'PT Aroma Prima Livindo',
     'Brand owner (CEO: Olivia Regina)',
     'Kantor pusat: Rukan Crown, Jl. Green Lake City Boulevard No.28-30 Blok A, Petir, Cipondoh. Pabrik: Graha Industrial Balaraja Estate Kav. B2',
     'Tangerang 15147 / 15610, Banten', '021-5433-0013',
     'morristalenthire@gmail.com (email rekrutmen — CS perlu dikonfirmasi)', 'livindo.co.id',
     'Website, Shopee, Guardian, supermarket & retail nasional',
     'BPOM',
     'Harga retail Guardian Rp28.500–Rp52.500. Varian: Frosted Edition, Black Edition, Travel Edition, Teen, pocket. Tahun berdiri disebut 2004/2007/2009 di berbagai sumber — perlu konfirmasi.',
     'livindo.co.id/morris; livindo.co.id/brands; guardianindonesia.co.id/brand/morris.html; infobrand.id 17/10/2023'),

    ('Velixir', '8 (Databoks/Compas, ditulis "Velixlr")', '1,36%', 'Velixir Parfums (badan hukum belum dikonfirmasi)',
     'Brand owner (didirikan 2025 oleh dua bersaudara)',
     'Jakarta (alamat lengkap belum dipublikasikan di situs resmi)',
     'Jakarta', '+62 851-3636-3657', 'info@velixirparfums.com', 'velixirparfums.com',
     'Website resmi, marketplace, 172 toko retail (klaim brand)',
     'BPOM (perlu dicek per SKU)',
     'Klaim brand: 10+ negara & 172 toko retail di Indonesia; angka 350.000+ botol berasal dari distributor UK, bukan situs resmi. Harga di situs resmi USD 30–60 (region-dependent) — belum ada harga IDR terverifikasi. Ada menu "Become Our Partner".',
     'velixirparfums.com/pages/about-us; velixirparfums.com/pages/contact; velixirparfums.com/pages/faq; fragrantica.com/designers/Velixir'),

    ('Fres & Natural', '9 (Databoks/Compas)', '1,26%', 'PT Wings Surya (WINGS Care)',
     'Brand owner / produsen',
     'Head office: Jl. Tipar Cakung Kav. F5-7, Cakung Barat. Surabaya: Jl. Embong Malang No.61-65 Lt.7',
     'Jakarta Timur 13910 / Surabaya 60261', '021-460-2696; bebas pulsa 0-800-18-18-818; 031-532-5005',
     'layanan konsumen via situs wingscorp.com', 'wingscorp.com',
     'Watsons, Guardian, supermarket & marketplace resmi',
     'BPOM (contoh NA18230602907); halal MUI pada seri BT21',
     'Diproduksi oleh Wings. Harga retail Rp11.900–Rp28.000. Notes Ocean Secrets tercantum resmi di Watsons. Ini brand mass-market, bukan parfum refill — cocok sebagai pelengkap katalog.',
     'wingscorp.com/brand-detail/fres-natural-soap; watsons.co.id/id/fres-natural-spray-eau-de-toilette-ocean-secrets-100ml/p/BP_42451; guardianindonesia.co.id/brand/fres-natural.html'),

    ('Evangeline', '10 (Databoks/Compas)', '0,93%', 'PT Griff Prima Abadi',
     'Brand owner (pemilik: Jimmy Liong; CEO: Gilbert Liong; sejak 1993, brand 2008)',
     'Gandaria 8 Office Tower 21-D, Jl. Sultan Iskandar Muda No.8, RT.10/RW.6, Gandaria, Kebayoran Lama',
     'Jakarta Selatan 12240', '+62 21 5239-1603', 'info@griff.co.id', 'griff.co.id',
     'Shopee, Tokopedia, Lazada, TikTok Shop; Alfamart, Indomaret, Indogrosir, Guardian, Century; eksporAsia/Pasifik',
     'BPOM, Halal MUI, GMP',
     'Merek terdaftar DJKI kelas 3 sejak 24/02/2006. Harga EDP Rp35.000 (2023). Varian terlaris: Baby Powder, Black Vanilla, White Musk, Black Sakura. Juga memiliki brand Braven & Musk by Lilian Ashley.',
     'griff.co.id/about-us; antaranews.com 22/08/2023; inews.id 18/12/2024; kosmetikpedia.co.id'),

    ('Parfarome (tambahan)', '9 (GoodStats, bukan daftar Databoks)', '1,49%', 'Brand owner belum terverifikasi',
     'Supplier bibit parfum / pendatang baru',
     'Distributor terdeteksi: Jl. Banteng No.108 B, Turangga, Lengkong',
     'Bandung 40264, Jawa Barat', '+62 838-7885-6975 (distributor Bandung)', 'tidak tersedia',
     'tidak ada situs resmi terverifikasi', 'Marketplace (repack 100 gr Rp52.000–Rp76.998)',
     'Perlu verifikasi BPOM/halal per produk',
     'Sudah dipakai sebagai "factory" di nota toko Alkaff (aqua kiss, fantasy, gissah, dll.). Data ini adalah DISTRIBUTOR, bukan pabrik/brand owner — konfirmasi sebelum order besar.',
     'data.goodstats.id (Q2 2026); google maps distributor Bandung; tokopedia.com/find/chemarome'),

    ('Ashar Grosir Parfum (referensi grosir)', '—', '—', 'Ashar Grosir Parfum',
     'Grosir/refill (bukan brand owner), sejak 2004', 'Bekasi, Jawa Barat',
     'Bekasi', 'melalui situs/chat', 'melalui situs', 'ashargrosirparfum.com',
     'Website, chat', 'Perlu verifikasi',
     'Contoh harga grosir: 1000 Bunga 100 ml Rp63.000. Situs gagal diakses saat validasi (HTTP 403) — alamat & kontak lengkap WAJIB dikonfirmasi sebelum transaksi.',
     'ashargrosirparfum.com (hasil pencarian 2026-11-26)'),
]

# ---------------------------------------------------------------------------
# PRODUK: (nama, brand, harga_ecer, family, top, heart, base, karakter, audiens, momen, catatan_harga)
# ---------------------------------------------------------------------------
P = []
def prod(nama, brand, price, fam, top, heart, base, char, aud, occ, note=''):
    P.append((nama, brand, price, fam, top, heart, base, char, aud, occ, note))

# MyKonos
prod('Mykonos Marbella Extrait de Parfum', 'Mykonos', 449000, 'Citrus Aromatic',
     'Amalfi lemon, Lavender', 'Clean musk, Airy notes', 'White musk, Cedar',
     'Segar, lapang, bersih seperti laundry di angin laut', 'Pria & wanita, penyuka aroma clean',
     'Siang, pantai, kantor, after-shower', 'Harga resmi mulai Rp449.000 (50/100 ml); deskripsi aroma dari situs resmi.')
prod('Mykonos Sorrento Extrait de Parfum', 'Mykonos', 449000, 'Citrus Fresh',
     'Bergamot, Lemon', 'Neroli, Jasmine', 'Musk, Amber',
     'Cerah, manis segar, feminin ringan', 'Wanita & unisex, usia muda',
     'Pagi, kampus, liburan', 'Harga resmi mulai Rp449.000 (50/100 ml). Notes gambaran keluarga aroma.')
prod('Mykonos Silent Whisper Extrait de Parfum', 'Mykonos', None, 'Floral Musk',
     'Pear, Bergamot', 'Jasmine, Rose', 'White musk, Sandalwood',
     'Lembut, romantis, skin-scent', 'Wanita, penyuka aroma subtle',
     'Siang, kencan santai', 'Situs resmi menandai sold out saat riset — cek stok ke brand.')
prod('Mykonos Matcha Latte Extrait de Parfum', 'Mykonos', None, 'Gourmand Tea',
     'Matcha, Bergamot', 'Vanilla, Milk', 'Musk, Amber',
     'Manis creamy dengan twist teh hijau, viral', 'Gen Z & Milenial, pecinta aroma dessert',
     'Hangout, konten live, malam', 'Produk viral andalan MyKonos; harga belum terverifikasi di situs resmi.')
prod('Mykonos Black Opera Extrait de Parfum', 'Mykonos', None, 'Amber Woody',
     'Saffron, Bergamot', 'Oud, Rose', 'Amber, Musk',
     'Gelap, mewah, berani', 'Pria & wanita dewasa',
     'Malam, acara formal', 'Juga dijual reseller dengan nama Black Opera — pastikan versi MyKonos.')

# Scarlett
prod('Scarlett Extrait de Parfum Garden of Whisper 30ml', 'Scarlett', 60900, 'Floral Fruity',
     'Bergamot, Pear', 'Jasmine, Peony', 'Musk, Vanilla',
     'Manis bunga lembut, feminin, ringan', 'Wanita muda, pemula parfum',
     'Siang, kampus, kantor', 'Harga resmi scarlett.co.id Rp60.900 (diskon dari Rp75.000).')
prod('Scarlett Extrait de Parfum Safa Ather 30ml', 'Scarlett', None, 'Amber Oriental',
     'Saffron, Bergamot', 'Rose, Jasmine', 'Amber, Oud, Musk',
     'Hangat, mewah, khas Timur Tengah', 'Pria & wanita, penyuka aroma Arab',
     'Malam, acara spesial', 'Seri Golden SCENTS of Arabia; harga belum terverifikasi.')
prod('Scarlett Extrait de Parfum Desert Lumina 30ml', 'Scarlett', None, 'Amber Spicy',
     'Bergamot, Spices', 'Rose, Jasmine', 'Amber, Sandalwood, Musk',
     'Hangat, rempah elegan', 'Pria & wanita dewasa', 'Malam, formal', 'Varian 2026; harga belum terverifikasi.')
prod('Scarlett Extrait de Parfum Sahara Mirage 30ml', 'Scarlett', None, 'Woody Amber',
     'Bergamot, Cardamom', 'Rose, Iris', 'Amber, Oud, Vanilla',
     'Misterius, kering, hangat', 'Pria & wanita dewasa', 'Malam, acara', 'Varian 2026; harga belum terverifikasi.')

# HMNS
prod('HMNS Alpha Eau de Parfum 100ml', 'HMNS', None, 'Woody Spicy',
     'Bergamot, Cardamom', 'Iris, Cedar', 'Sandalwood, Tonka, Musk',
     'Maskulin hangat, elegan, berani', 'Pria 25-45', 'Malam, kantor, acara',
     'Best seller situs resmi; harga promo berubah-rubah, cek hmnsperfume.com.')
prod('HMNS Farhampton Extrait de Parfum 100ml', 'HMNS', 563343, 'Woody Aromatic',
     'Bergamot, Lemon', 'Lavender, Geranium', 'Cedar, Amber, Musk',
     'Segar kayu, klasik, tahan lama', 'Pria & wanita, 25+', 'Siang, kantor, malam santai',
     'Harga resmi Rp563.343 di hmnsperfume.com (2026).')
prod('HMNS Melting Temptation Eau de Parfum', 'HMNS', None, 'Gourmand Vanilla',
     'Caramel, Bergamot', 'Vanilla Orchid, Jasmine', 'Tonka, Musk, Amber',
     'Manis meleleh, creamy, nyaman', 'Penyuka aroma dessert', 'Malam, cozy',
     'Direkomendasikan staf toko offline HMNS; harga belum terverifikasi.')
prod('HMNS Unrosed Eau de Parfum', 'HMNS', None, 'Floral Rose',
     'Bergamot, Peach', 'Rose, Jasmine', 'Musk, Sandalwood',
     'Mawar modern, feminin, bersih', 'Wanita 20-35', 'Siang, kencan',
     'Teknik Soliflore khas HMNS; harga belum terverifikasi.')

# SAFF & Co
prod('SAFF & Co EULALIE Extrait de Parfum', 'SAFF & Co', 249000, 'Floral Gourmand',
     'Pear, Pink Pepper', 'Jasmine, Rose', 'Vanilla, Musk, Sandalwood',
     'Feminine, manis elegan', 'Wanita 20-35', 'Kencan, malam', 'Harga resmi saffnco.com Rp249.000.')
prod('SAFF & Co POSTOJNA Extrait de Parfum', 'SAFF & Co', 269000, 'Aquatic Woody',
     'Bergamot, Citrus', 'Sea Notes, Jasmine', 'Cedar, Amber, Musk',
     'Segar, tenang, atmosfer blue hour', 'Pria & wanita', 'Siang, santai', 'Harga resmi saffnco.com Rp269.000.')
prod('SAFF & Co ALENCINE Extrait de Parfum', 'SAFF & Co', 319000, 'Floral Powdery',
     'Peach, Bergamot', 'Iris, Jasmine', 'Musk, Sandalwood, Vanilla',
     'Feminine, lembut, ekspresif', 'Wanita, self-expression', 'Siang, acara',
     'Dikembangkan bersama master perfumer Shyamala Maisondieu. Rp319.000 (dari Rp409.000).')
prod('SAFF & Co MECHLINE Extrait de Parfum', 'SAFF & Co', 319000, 'Woody Floral',
     'Bergamot, Spices', 'Rose, Violet', 'Leather, Amber, Musk',
     'Berani, modern, kontras', 'Wanita dewasa', 'Malam, acara',
     'Dikembangkan bersama Shyamala Maisondieu. Rp319.000 (dari Rp409.000).')

# Octarine
prod('Octarine Noctis Obscura Eau de Parfum 50ml', 'Octarine', 73800, 'Woody Dark',
     'Bergamot, Pink Pepper', 'Rose, Jasmine', 'Oud, Amber, Musk',
     'Gelap, misterius, elegan', 'Pria & wanita, 25+', 'Malam, acara', 'Harga resmi octarine.co.id Rp73.800/50 ml.')
prod('Octarine Sanctum Arcanum Eau de Parfum 50ml', 'Octarine', 73800, 'Amber Woody',
     'Saffron, Bergamot', 'Rose, Jasmine', 'Amber, Sandalwood, Musk',
     'Sakral, hangat, premium', 'Pria & wanita dewasa', 'Malam, formal', 'Harga resmi Rp73.800/50 ml.')
prod('Octarine Elixir One Eau de Parfum 50ml', 'Octarine', 73800, 'Aromatic Fresh',
     'Lemon, Bergamot', 'Lavender, Geranium', 'Cedar, Amber, Musk',
     'Segar maskulin, percaya diri', 'Pria 20-40', 'Siang, gym, kantor', 'Harga resmi Rp73.800/50 ml.')
prod('Octarine Elixir Homme Eau de Parfum 50ml', 'Octarine', 73800, 'Spicy Woody',
     'Bergamot, Cardamom', 'Pepper, Jasmine', 'Leather, Tonka, Amber',
     'Maskulin hangat, urban', 'Pria 25-45', 'Malam, kantor', 'Harga resmi Rp73.800/50 ml.')
prod('Octarine Boujee Fluff Eau de Parfum 50ml', 'Octarine', 73800, 'Gourmand Floral',
     'Pear, Raspberry', 'Jasmine, Whipped Cream', 'Vanilla, Musk',
     'Manis fluffy, playful', 'Wanita muda', 'Hangout, konten live', 'Harga resmi Rp73.800/50 ml.')
prod('Octarine Vanilla Laice Eau de Parfum 20ml', 'Octarine', 29900, 'Gourmand Vanilla',
     'Whipped Cream, Vanilla', 'Musk, Floral Notes', 'Woody Notes',
     'Creamy lembut, manis bersih, airy', 'Penyuka vanilla, pemula', 'Sehari-hari, siang & malam',
     'Notes dari "Story Behind" situs resmi. BPOM NA18250600337. Harga Rp29.900/20 ml.')

# Macbrame (B2B, tanpa duplikat aroma yang sudah ada)
prod('Macbrame Bibit Parfum Konsentrat (900+ aroma, B2B)', 'Macbrame', None,
     'Bahan Baku /,wewangian'.replace(',', ' '), 'Bergamot, Citrus', 'Jasmine, Rose',
     'Musk, Amber, Woody', 'Konsentrat stabil antar batch, halal, untuk refill/laundry/air care',
     'Pengusaha parfum refill & brand lokal (B2B)', 'Produksi',
     'Harga pricelist via sales area: maharum.group/sample-request. Jangan dicampur dengan harga per gram di katalog utama. Aroma spesifik (Ameer Al Oud, dll.) SUDAH ada di sheet IMPORT_odoo.')
# perbaiki family typo di atas
P[-1] = (P[-1][0], P[-1][1], P[-1][2], 'Bahan Baku Wewangian', P[-1][4], P[-1][5], P[-1][6], P[-1][7], P[-1][8], P[-1][9], P[-1][10])

# Morris
prod('Morris Eau de Parfum Frosted Edition Rose Vanilla 100ml', 'Morris', 50000, 'Floral Gourmand',
     'Bergamot, Pear', 'Rose, Vanilla Orchid', 'Musk, Sandalwood',
     'Manis mawar-vanila, feminin', 'Wanita muda', 'Siang, kencan', 'Harga referensi Guardian Rp50.000.')
prod('Morris Eau de Parfum Frosted Edition Eternal Glacier 100ml', 'Morris', 50000, 'Aquatic Floral',
     'Bergamot, Lemon', 'Jasmine, Sea Notes', 'Musk, Cedar',
     'Dingin, segar, bersih', 'Wanita, penyuka aroma fresh', 'Pagi, kantor', 'Harga referensi Guardian Rp50.000.')
prod('Morris Eau de Parfum Black Edition Woody 100ml', 'Morris', 52500, 'Woody Aromatic',
     'Bergamot, Pepper', 'Cedar, Jasmine', 'Sandalwood, Amber, Musk',
     'Maskulin, gelap, elegan', 'Pria 25-45', 'Malam, formal', 'Harga referensi Guardian Rp52.500.')
prod('Morris Parfum Travel Edition 100ml - Paris', 'Morris', None, 'Floral Chypre',
     'Bergamot, Peach', 'Rose, Jasmine', 'Patchouli, Musk, Amber',
     'Romantis,BPOP feminine khas kota', 'Wanita, pecinta edisi travel', 'Liburan, kencan',
     'Varian Travel Edition (Bali/Paris/Santorini/Hokkaido/Cappadocia/Venice); harga per varian perlu dicek.'.replace(',BPOP', ''))
prod('Morris Teen EDP Infinite Space 50ml', 'Morris', 28500, 'Fruity Aquatic',
     'Bergamot, Apple', 'Jasmine, Freesia', 'Musk, Amber',
     'Segar, ceria, remaja', 'Remaja & wanita muda', 'Sekolah, kampus, siang', 'Harga referensi Guardian Rp28.500.')

# Velixir
for nm, fam, top, heart, base, char, aud, occ in [
    ('Velixir Panacea Extrait de Parfum', 'Amber Gourmand', 'Bergamot, Saffron', 'Rose, Vanilla', 'Amber, Musk, Oud', 'Mewah, manis hangat', 'Pria & wanita dewasa', 'Malam, formal'),
    ('Velixir Comus Extrait de Parfum', 'Woody Oriental', 'Bergamot, Cardamom', 'Oud, Rose', 'Sandalwood, Amber', 'Hangat, berwibawa', 'Pria & wanita, pecinta oud', 'Malam, acara'),
    ('Velixir Harmonia Eau de Parfum', 'Floral Amber', 'Pear, Bergamot', 'Jasmine, Rose', 'Amber, Musk, Vanilla', 'Seimbang, elegan, harmonis', 'Semua usia', 'Siang & malam'),
    ('Velixir Ares Eau de Parfum', 'Spicy Woody', 'Lemon, Pink Pepper', 'Cardamom, Jasmine', 'Cedar, Leather, Amber', 'Maskulin berani', 'Pria 25-45', 'Malam, gym'),
    ('Velixir Aphrodite Eau de Parfum', 'Floral Fruity', 'Peach, Raspberry', 'Jasmine, Rose', 'Musk, Vanilla', 'Feminine, romantis', 'Wanita muda', 'Kencan, acara'),
]:
    prod(nm, 'Velixir', None, fam, top, heart, base, char, aud, occ,
         'Harga situs resmi USD 30–60 (tergantung region); belum ada harga IDR terverifikasi. Stok Panacea sempat sold out. Notes gambaran keluarga aroma.')

# Fres & Natural
prod('Fres & Natural EDT Ocean Secrets 100ml', 'Fres & Natural', 27900, 'Floral Fruity Aquatic',
     'Leafy Green, Green, Plum, Peach', 'Rosewood, Jasmine', 'Heliotrope, Amber, Sandalwood, Vanilla, Musk',
     'Segar laut, manis buah, feminin', 'Wanita muda, remaja akhir', 'Siang, pantai, kampus',
     'Notes resmi dari Watsons. BPOM NA18230602907. Harga Rp27.900 (dari Rp32.900). Diproduksi Wings.')
prod('Fres & Natural EDT Fairy Feathers 100ml', 'Fres & Natural', 28000, 'Floral Powdery',
     'Bergamot, Pear', 'Jasmine, Lily', 'Musk, Vanilla, Sandalwood',
     'Ringan, manis, feminin', 'Remaja & wanita muda', 'Siang, sehari-hari',
     'Harga referensi Guardian Rp28.000. Notes gambaran keluarga aroma.')
prod('Fres & Natural Cologne Viva La Fresh 100ml', 'Fres & Natural', 12500, 'Citrus Fresh',
     'Lemon, Bergamot', 'Jasmine, Green Notes', 'Musk, Cedar',
     'Segar sederhana, affordable', 'Semua usia', 'Siang, olahraga', 'Harga referensi Guardian Rp12.500.')
prod('Fres & Natural BT21 Yellow In Luv 100ml', 'Fres & Natural', 11900, 'Fruity Fresh',
     'Peach, Apple', 'Jasmine, Freesia', 'Musk, Amber',
     'Manis buah ceria, edisi kolaborasi', 'Remaja, penggemar BT21', 'Siang, hangout',
     'BPOM NA18220603096; bersertifikat halal MUI. Harga referensi Watsons Rp11.900.')
prod('Fres & Natural Dessert Collection Pink Cupcake', 'Fres & Natural', None, 'Gourmand Dessert',
     'Vanilla, Juicy Fruits', 'Cream, Jasmine', 'Vanilla, Musk, Sugar',
     'Manis dessert, cheerful', 'Gen Z & Milenial', 'Hangout, konten live',
     'Deskripsi resmi: perpaduan vanila & juicy fruits; harga belum terverifikasi.')

# Evangeline
prod('Evangeline Premium EDP Baby Powder', 'Evangeline', 35000, 'Floral Powdery Musk',
     'Bergamot, Peach', 'Jasmine, Rose', 'White Musk, Vanilla, Sandalwood',
     'Feminine bunga, powdery & musky lembut, manis seperti vanila', 'Wanita, penyuka aroma baby powder',
     'Sehari-hari, after-shower', 'Notes & harga (Rp35.000) dari siaran pers ANTARA 22/08/2023. BPOM, halal, GMP.')
prod('Evangeline Premium EDP Bakkarat', 'Evangeline', 35000, 'Amber Gourmand',
     'Saffron, Bergamot', 'Jasmine, Caramel', 'Amber, Fir, Musk',
     'Manis transparan, hangat, mewah', 'Pria & wanita', 'Malam, formal', 'Harga referensi Rp35.000 (ANTARA 2023).')
prod('Evangeline Premium EDP Black Opi', 'Evangeline', 35000, 'Gourmand Coffee',
     'Pear, Pink Pepper', 'Coffee, Jasmine', 'Vanilla, Patchouli, Musk',
     'Manis kopi-vanila, feminin berani', 'Wanita muda', 'Night out, kencan', 'Harga referensi Rp35.000 (ANTARA 2023).')
prod('Evangeline Premium EDP Creamy Butter', 'Evangeline', 35000, 'Gourmand Creamy',
     'Vanilla, Bergamot', 'Butter, Jasmine', 'Vanilla, Musk, Amber',
     'Creamy, hangat, comfort', 'Penyuka aroma dessert', 'Malam, cozy', 'Harga referensi Rp35.000 (ANTARA 2023).')
prod('Evangeline Premium EDP Flirt', 'Evangeline', 35000, 'Fruity Floral',
     'Peach, Raspberry', 'Jasmine, Rose', 'Musk, Vanilla',
     'Playful, manis, feminin', 'Wanita muda', 'Hangout, kencan', 'Harga referensi Rp35.000 (ANTARA 2023).')
prod('Evangeline Premium EDP French Pear', 'Evangeline', 35000, 'Fruity Gourmand',
     'Pear, Bergamot', 'Jasmine, Caramel', 'Vanilla, Musk, Amber',
     'Buah pir manis, lembut', 'Wanita & remaja', 'Siang, santai', 'Harga referensi Rp35.000 (ANTARA 2023).')
prod('Evangeline Premium EDP Sea Salt', 'Evangeline', 35000, 'Aquatic Mineral',
     'Sea Salt, Bergamot', 'Jasmine, Water Lily', 'Musk, Amber, Driftwood',
     'Asin segar, bersih, menenangkan', 'Pria & wanita', 'Siang, pantai', 'Harga referensi Rp35.000 (ANTARA 2023).')

CATEGORY_LOCAL = 'Parfum / Lokal Indonesia'

# ---------------------------------------------------------------------------
# TULIS PRODUK KE IMPORT_odoo + Detail_Harga_Sumber
# ---------------------------------------------------------------------------
style_src = ws[2]
base_row = ws.max_row
ref_no = 0
for nama, brand, price, fam, top, heart, base, char, aud, occ, note in P:
    ref_no += 1
    ref = f'ALK-L-{ref_no:03d}'
    is_b2b = brand == 'Macbrame'
    cat = 'Bahan Baku / Bibit Parfum' if is_b2b else CATEGORY_LOCAL
    desc = (f'{nama} — {fam} ({brand}). Notes: Top {top}; Heart {heart}; Base {base}. '
            f'Karakter: {char}. Cocok untuk: {aud}. Cocok dipakai: {occ}. '
            f'{note} Notes adalah gambaran keluarga wewangian, bukan komposisi resmi pabrik. '
            f'Produk lokal Indonesia; bukan klaim identik dengan brand parfum lain.')
    webdesc = (f'<p><strong>{html.escape(nama)}</strong> — {html.escape(fam)} '
               f'({html.escape(brand)}).</p>'
               f'<ul><li><strong>Top notes:</strong> {html.escape(top)}</li>'
               f'<li><strong>Heart notes:</strong> {html.escape(heart)}</li>'
               f'<li><strong>Base notes:</strong> {html.escape(base)}</li></ul>'
               f'<p><strong>Karakter:</strong> {html.escape(char)}<br/>'
               f'<strong>Cocok untuk:</strong> {html.escape(aud)}<br/>'
               f'<strong>Momen:</strong> {html.escape(occ)}.</p>'
               f'<p><em>{html.escape(note)}</em></p>'
               f'<p><small>Notes adalah gambaran keluarga wewangian, bukan komposisi resmi pabrik. '
               f'Produk lokal Indonesia.</small></p>')
    values = [nama, ref, cat, 'Consumable', price if price else None, None,
              'TRUE', 'TRUE', 'TRUE', desc, webdesc]
    ws.append(values)
    r = ws.max_row
    for c in range(1, len(values) + 1):
        ws.cell(r, c)._style = copy(style_src[c - 1]._style)

    drow = [nama, ref, 'Riset web 2026 (Databoks/Compas + situs resmi)', brand, None,
            'eceran (referensi)' if price else 'belum ada', None, None,
            price if price else None,
            'Harga eceran referensi' if price else 'Perlu diisi',
            '', '', '', 'Supplier_Lokal']
    detail.append(drow)
    dr = detail.max_row
    dstyle = detail[2]
    for c in range(1, len(drow) + 1):
        detail.cell(dr, c)._style = copy(dstyle[c - 1]._style)

print('produk lokal ditambahkan:', len(P), '| total IMPORT_odoo:', ws.max_row - 1)

# ---------------------------------------------------------------------------
# SHEET SUPPLIER_LOKAL
# ---------------------------------------------------------------------------
if 'Supplier_Lokal' in wb.sheetnames:
    del wb['Supplier_Lokal']
sup = wb.create_sheet('Supplier_Lokal')
sup_headers = ['Brand', 'Peringkat (Compas Q2 2026)', 'Pangsa Pasar', 'Perusahaan / Badan Hukum',
               'Jenis Supplier', 'Alamat', 'Kota', 'Telepon / WhatsApp', 'Email', 'Website',
               'Kanal Pembelian', 'Sertifikasi', 'Catatan Penting untuk Alkaff', 'Sumber Data']
sup.append(sup_headers)
for row in SUPPLIERS:
    sup.append(list(row))

# ---------------------------------------------------------------------------
# SHEET REFERENSI_RANKING
# ---------------------------------------------------------------------------
if 'Referensi_Ranking' in wb.sheetnames:
    del wb['Referensi_Ranking']
rank = wb.create_sheet('Referensi_Ranking')
rank_rows = [
    ['SUMBER RANKING PARFUM LOKAL TERLARIS — SHOPEE INDONESIA, Q2 2026', ''],
    ['', ''],
    ['Sumber 1', 'Databoks/Katadata, 12/11/2026 — "10 Best-Selling Local Perfume Brands on Shopee Indonesia in Q2 2026"'],
    ['Metode', 'Compas, online crawling 1 April–30 Juni 2026; toko resmi & nonresmi, rating > 4 bintang'],
    ['URL', 'databoks.katadata.co.id/en/consumer-durables-apparel/statistics/6af55e3e43df0/...'],
    ['', ''],
    ['No', 'Brand lokal & pangsa pasar (versi Databoks)'],
]
for i, (b, s) in enumerate([
    ('MyKonos', '6,75%'), ('Scarlett', '5,43%'), ('HMNS', '5,06%'),
    ('Saff & Co', '3,52%'), ('Octarine', '2,98%'), ('Macbrame', '1,57%'),
    ('Morris', '1,49%'), ('Velixlr (diduga Velixir)', '1,36%'),
    ('Fres & Natural', '1,26%'), ('Evangeline', '0,93%'),
], 1):
    rank_rows.append([i, f'{b} — {s}'])
rank_rows += [
    ['', ''],
    ['Sumber 2', 'GoodStats Data, 05/10/2026 — "10 Brand Parfum & Wewangian Terlaris di Shopee Q2 2026"'],
    ['URL', 'data.goodstats.id/statistic/10-brand-parfum-wewangian-terlaris-di-shopee-pada-q2-2026-peringkat-atas-kebal-YAF3P'],
    ['Catatan', 'Daftar ini mencampur brand lokal & global. 5 besar identik: Mykonos 6,78%; Scarlett 5,46%; HMNS 5,09%; Saff & Co 3,53%; Octarine 2,99%.'],
    ['Perbedaan', 'Selisih persentase kecil (mis. 6,75% vs 6,78%) kemungkinan perbedaan pembulatan/waktu tarik data. Peringkat lokal memakai versi Databoks.'],
    ['Tambahan', 'GoodStats memasukkan Parfarome (1,49%, pendatang baru) di posisi 9; Afnan & Ahmed Al Maghribi adalah brand global, tidak dimasukkan sebagai parfum lokal.'],
    ['', ''],
    ['DISCLAIMER', 'Peringkat adalah pangsa nilai penjualan Shopee Q2 2026, BUKAN jaminan kualitas atau ketersediaan stok. Data supplier dikumpulkan dari situs resmi/ publik dan perlu dikonfirmasi ulang sebelum kontrak.'],
]
for r in rank_rows:
    rank.append(r)

# ---------------------------------------------------------------------------
# UPDATE PANDUAN & STYLE
# ---------------------------------------------------------------------------
guide.append([])
guide.append(['TAMBAHAN 2026-11-26: PARFUM LOKAL INDONESIA'])
guide.append(['Produk lokal', f'{len(P)} produk ditambahkan ke IMPORT_odoo dengan internal reference ALK-L-001 … ALK-L-{ref_no:03d}.'])
guide.append(['Supplier', 'Lihat sheet Supplier_Lokal — berisi brand owner/produsen, alamat, kontak, website, kanal pembelian & catatan.'])
guide.append(['Ranking', 'Lihat sheet Referensi_Ranking — sumber Databoks/Compas & GoodStats untuk Q2 2026.'])
guide.append(['Harga', 'Sales Price diisi hanya bila harga eceran terverifikasi dari situs resmi/retailer resmi. Cost Price sengaja KOSONG (belum ada harga beli).'])
guide.append(['Macbrame', 'Dicatat sebagai B2B bibit/konsentrat. Aroma spesifik Macbrame sudah ada di katalog utama — jangan diduplikasi.'])
guide.append(['Velixir', 'Harga baru tersedia dalam USD di situs resmi; belum dikonversi ke IDR agar tidak menyesatkan.'])
guide.append(['Konfirmasi', 'Data supplier publik dapat berubah. Verifikasi alamat, kontak, MOQ & stok sebelum order.'])

for sh, widths in [
    (sup, {1: 24, 2: 28, 3: 12, 4: 40, 5: 36, 6: 62, 7: 28, 8: 34, 9: 44, 10: 30, 11: 46, 12: 40, 13: 88, 14: 70}),
    (rank, {1: 24, 2: 130}),
]:
    sh.freeze_panes = 'A2'
    for col in range(1, sh.max_column + 1):
        sh.column_dimensions[get_column_letter(col)].width = widths.get(col, 18)
    for c in sh[1]:
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = PatternFill('solid', fgColor='1F4E78')
        c.alignment = Alignment(vertical='center')
    for row in sh.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(vertical='top', wrap_text=True)

for row in guide.iter_rows():
    for c in row:
        if isinstance(c.value, str) and c.value.startswith('TAMBAHAN'):
            c.font = Font(bold=True)

wb.save(XLSX)

# ---------------------------------------------------------------------------
# TULIS ULANG CSV DARI IMPORT_odoo
# ---------------------------------------------------------------------------
with open(CSV, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    for row in ws.iter_rows(values_only=True):
        w.writerow(['' if v is None else v for v in row])

print(' sheets:', wb.sheetnames)
print(' supplier rows:', sup.max_row - 1)
print(' csv rows:', ws.max_row - 1)
