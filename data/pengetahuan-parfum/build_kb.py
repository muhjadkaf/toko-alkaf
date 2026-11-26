#!/usr/bin/env python3
"""Bangun basis pengetahuan parfum dari katalog Alkaff.

Membaca:  ../katalog-alkaff-odoo/katalog_parfum_alkaff_odoo.csv
Menulis:  file CSV + JSON di direktori ini.

Data yang dihasilkan bersifat **edukatif dan komersial-ringan**: taksonomi,
deskriptor, ide accord, dan tema layanan. Bukan komposisi resmi pabrik, bukan
formula produksi, dan bukan klaim kosmetik/obat.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT.parent / "katalog-alkaff-odoo" / "katalog_parfum_alkaff_odoo.csv"

# ---------------------------------------------------------------------------
# Normalisasi
# ---------------------------------------------------------------------------
NOTE_ALIASES = {
    "melati": "jasmine",
    "kasturi": "musk",
    "white musk": "white musk",
    "vanilla orchid": "vanilla",
    "sea notes": "marine",
    "woody": "woody accord",
    "mixed flowers": "floral accord",
    "green notes": "green notes",
    "vanilla": "vanilla",
}

# Urutan penting: aturan yang lebih spesifik harus lebih dulu.
# Contoh: "Floral Fruity" harus menang sebelum "Fruity", dan "Spicy" sebelum
# "Woody"/"Amber" agar produk tidak jatuh ke keluarga generik.
FAMILY_RULES = [
    ("Attar & Oud", ["attar", "oud"]),
    ("Laundry & Clean", ["laundry"]),
    ("Bibit / Konsentrat", ["bibit", "konsentrat"]),
    ("Floral Fruity", ["floral fruity", "fruity floral", "floral fruity aquatic"]),
    ("Gourmand", ["gourmand", "vanilla", "caramel", "chocolate", "coffee", "candy", "tonka", "dessert", "creamy"]),
    ("Fruity", ["fruity", "fruit"]),
    ("Spicy Leather", ["spicy", "leather", "pepper"]),
    ("Musk & Powdery", ["musk", "powdery", "animalic"]),
    ("Aquatik / Laut", ["aquatic", "marine", "mineral", "sea", "water"]),
    ("Floral Putih & Bouquet", ["floral", "flower", "bouquet", "rose", "jasmine", "lily"]),
    ("Amber / Oriental", ["oriental", "amber", "saffron"]),
    ("Woody", ["woody", "wood", "cedar", "sandal", "chypre"]),
    ("Citrus Segar", ["citrus", "green", "fresh"]),
    ("Aromatic Herbal", ["aromatic", "blend", "herbal", "spices"]),
]

FAMILY_META = {
    "Citrus Segar": dict(
        deskriptor="Cerah, asam-manis, ringan, menyegarkan",
        notes="Bergamot, lemon, lime, mandarin, neroli",
        karakter="Segar di awal, cepat kering, mudah disukai banyak orang",
        momen="Pagi, kantor, olahraga, cuaca panas, live shopping",
        ketahanan="2–4 jam (tergantung konsentrasi)", sillage="Ringan–sedang",
        tema="Parfum harian yang tidak menempel berat"),
    "Aquatik / Laut": dict(
        deskriptor="Sejuk, berair, bersih, lapang",
        notes="Marine, sea notes, lotus, water lily, cedar",
        karakter="Seperti udara laut setelah hujan, transparan dan modern",
        momen="Pantai, liburan, siang hari, setelah mandi",
        ketahanan="3–5 jam", sillage="Ringan–sedang",
        tema="Liburan, pantai, dan kesan bersih"),
    "Floral Putih & Bouquet": dict(
        deskriptor="Bunga putih, lembut, feminin, elegan",
        notes="Jasmine, rose, lily, peony, freesia, orange blossom",
        karakter="Manis bunga, lembut, cocok untuk tampilan rapi",
        momen="Kantor, kencan siang, acara formal siang, foto",
        ketahanan="4–7 jam", sillage="Sedang",
        tema="Hadiah bunga, kencan siang, konten feminine"),
    "Floral Fruity": dict(
        deskriptor="Bunga + buah, manis segar, playful",
        notes="Jasmine, rose, peach, raspberry, pear, apple",
        karakter="Ceria, manis, mudah dipakai usia muda",
        momen="Hangout, kampus, live, kencan santai",
        ketahanan="3–6 jam", sillage="Sedang",
        tema="Gaya muda, konten live, hadiah ramah"),
    "Fruity": dict(
        deskriptor="Buah-buahan, manis, juicy, cerah",
        notes="Pear, peach, apple, raspberry, melon, pineapple",
        karakter="Manis buah di awal, cocok untuk kesan energik",
        momen="Siang, hangout, musim panas, konten cerah",
        ketahanan="2–5 jam", sillage="Sedang",
        tema="Wangi buah, konten warna cerah, upsell variant"),
    "Gourmand": dict(
        deskriptor="Manis makanan, hangat, creamy, menggoda",
        notes="Vanilla, caramel, tonka, coffee, chocolate, almond",
        karakter="Manis dan hangat, terasa 'mewah' di kulit",
        momen="Malam, musim hujan, kencan, acara santai",
        ketahanan="6–10 jam", sillage="Sedang–kuat",
        tema="Dessert scent, parfum musim hujan, evening edit"),
    "Woody": dict(
        deskriptor="Kayu, kering, hangat, stabil",
        notes="Cedar, sandalwood, woody accord, patchouli, oakmoss",
        karakter="Solid dan dewasa, cepat memberi kesan 'mahal'",
        momen="Malam, kantor formal, meeting, musim hujan",
        ketahanan="6–10 jam", sillage="Sedang",
        tema="Parfum maskulin/neutral, workwear, evening"),
    "Amber / Oriental": dict(
        deskriptor="Hangat, resin, manis-balsamik, dramatis",
        notes="Amber, saffron, cinnamon, vanilla, oud, tonka",
        karakter="Kaya dan berlapis, lebih cocok untuk malam",
        momen="Malam, pesta, sesi foto, acara spesial",
        ketahanan="8–12 jam", sillage="Kuat",
        tema="Malam formal, signature scent, konten dramatis"),
    "Musk & Powdery": dict(
        deskriptor="Bersih, lembut, dekat kulit, powdery",
        notes="Musk, white musk, iris, violet, cream",
        karakter="Skin scent, nyaman, aman untuk kantor",
        momen="Setelah mandi, kantor, tidur, keluarga",
        ketahanan="4–8 jam", sillage="Ringan",
        tema="Clean girl, after shower, parfum pertama"),
    "Aromatic Herbal": dict(
        deskriptor="Herbal, hijau, rempah kering, maskulin",
        notes="Lavender, rosemary, spices, cardamom, bergamot",
        karakter="Segar-kering, tidak manis, sering dipakai pria",
        momen="Kantor, olahraga, siang, perjalanan",
        ketahanan="4–7 jam", sillage="Sedang",
        tema="Grooming, parfum pria, harian rapi"),
    "Spicy Leather": dict(
        deskriptor="Pedas, kulit, gelap, urban",
        notes="Pink pepper, black pepper, leather, tonka, amber",
        karakter="Tajam dan maskulin, cocok untuk gaya kota",
        momen="Malam, night out, meeting penting",
        ketahanan="7–10 jam", sillage="Sedang–kuat",
        tema="Urban gentleman, night out, gaya jaket"),
    "Attar & Oud": dict(
        deskriptor="Resin, kayu gaharu, balsam, tradisional",
        notes="Oud, amber, rose, saffron, musk",
        karakter="Padat, hangat, kuat, sering dipakai sedikit",
        momen="Acara keluarga, malam, ibadah, hadiah",
        ketahanan="8–14 jam", sillage="Kuat",
        tema="Attar, oud, hadiah premium, momen keluarga"),
    "Laundry & Clean": dict(
        deskriptor="Bersih, segar, seperti pakaian baru",
        notes="White musk, marine, lavender, clean accord",
        karakter="Ringan dan serbaguna, bukan untuk kulit saja",
        momen="Cuci pakaian, rumah, handuk, sprei",
        ketahanan="Tergantung pemakaian", sillage="Ringan",
        tema="Laundry care, bundle rumah tangga, restock"),
    "Bibit / Konsentrat": dict(
        deskriptor="Konsentrat aroma, bahan baku, siap diracik",
        notes="Bergamot, jasmine, musk, amber, vanilla",
        karakter="Bahan dasar, bukan produk jadi untuk dipakai langsung",
        momen="Produksi, eksperimen, reseller, workshop",
        ketahanan="Tergantung formula akhir", sillage="Tergantung formula",
        tema="Workshop racik, B2B, sampel bibit"),
}

NOTE_META = {
    "bergamot": ("Bergamot", "jeruk pahit", "Citrus", 3, "2–3 jam", "Asam-manis cerah, pembuka klasik", "Lavender, jasmine, cedar"),
    "lemon": ("Lemon", "jeruk lemon", "Citrus", 3, "2–3 jam", "Asam segar, tajam, energik", "Lavender, marine, musk"),
    "lime": ("Lime", "jeruk nipis", "Citrus", 3, "2 jam", "Asam hijau, lebih tajam dari lemon", "Ginger, mint, musk"),
    "mandarin": ("Mandarin", "jeruk keprok", "Citrus", 2, "2–3 jam", "Manis juicy, lembut, ramah", "Rose, vanilla, musk"),
    "marine": ("Marine / Sea Notes", "aroma laut, sea notes", "Aquatic", 2, "3–4 jam", "Sejuk, berair, seperti angin laut", "Bergamot, cedar, white musk"),
    "green notes": ("Green Notes", "aroma hijau", "Green", 2, "2–3 jam", "Daun segar, baru dipetik", "Lavender, pear, jasmine"),
    "pear": ("Pear", "pir", "Fruity", 2, "2–3 jam", "Manis air, lembut, transparan", "Jasmine, musk, vanilla"),
    "apple": ("Apple", "apel", "Fruity", 2, "2–3 jam", "Manis renyah, familiar", "Cinnamon, cedar, vanilla"),
    "peach": ("Peach", "persik", "Fruity", 2, "2–3 jam", "Manis lembut, sedikit berbulu", "Rose, jasmine, musk"),
    "raspberry": ("Raspberry", "raspberi", "Fruity", 3, "2–3 jam", "Manis-asam beri, cerah", "Rose, vanilla, amber"),
    "strawberry": ("Strawberry", "stroberi", "Fruity", 2, "2 jam", "Manis buah merah, playful", "Vanilla, cream, jasmine"),
    "pineapple": ("Pineapple", "nanas", "Fruity", 3, "2 jam", "Manis-asam tropis", "Coconut, musk, cedar"),
    "watermelon": ("Watermelon", "semangka", "Fruity", 2, "2 jam", "Air manis segar", "Marine, lemon, musk"),
    "melon": ("Melon", "melon", "Fruity", 2, "2 jam", "Manis air, lembut", "Lotus, jasmine, musk"),
    "kiwi": ("Kiwi", "kiwi", "Fruity", 2, "2 jam", "Asam-manis hijau", "Lime, pear, green notes"),
    "plum": ("Plum", "plum", "Fruity", 3, "3–4 jam", "Manis gelap, berair", "Rose, amber, vanilla"),
    "jasmine": ("Jasmine", "melati", "Floral", 4, "5–8 jam", "Bunga putih manis, kuat, feminin", "Bergamot, cedar, musk"),
    "rose": ("Rose", "mawar", "Floral", 4, "5–8 jam", "Bunga klasik, romantis, bisa pedas", "Saffron, oud, vanilla"),
    "lily": ("Lily", "lili", "Floral", 3, "4–6 jam", "Bunga putih lembut, sedikit hijau", "Jasmine, musk, peony"),
    "peony": ("Peony", "peoni", "Floral", 2, "3–5 jam", "Bunga merah muda, ringan", "Pear, rose, musk"),
    "geranium": ("Geranium", "geranium", "Floral", 3, "4–6 jam", "Hijau-rosy, agak pedas", "Rose, cedar, bergamot"),
    "freesia": ("Freesia", "fresia", "Floral", 2, "3–5 jam", "Bunga cerah, segar", "Pear, jasmine, white musk"),
    "neroli": ("Neroli", "bunga jeruk", "Floral", 3, "4–6 jam", "Bunga jeruk pahit-manis, elegan", "Bergamot, orange blossom, musk"),
    "orange blossom": ("Orange Blossom", "bunga jeruk manis", "Floral", 3, "5–7 jam", "Manis bunga, madu, klasik", "Neroli, vanilla, musk"),
    "violet": ("Violet", "ungu", "Floral", 2, "3–5 jam", "Powdery, lunak, nostalgik", "Iris, violet leaf, musk"),
    "water lily": ("Water Lily", "teratai", "Floral", 2, "3–4 jam", "Bunga air, sejuk", "Marine, lotus, jasmine"),
    "lotus": ("Lotus", "teratai", "Floral", 2, "3–4 jam", "Bersih, hijau-air, tenang", "Marine, green notes, musk"),
    "iris": ("Iris", "iris", "Floral", 4, "6–9 jam", "Powdery, dingin, mewah", "Violet, cedar, musk"),
    "lavender": ("Lavender", "lavender", "Herbal", 3, "4–6 jam", "Herbal, bersih, sedikit manis", "Bergamot, tonka, cedar"),
    "rosemary": ("Rosemary", "rosemari", "Herbal", 3, "4–5 jam", "Herbal tajam, menyegarkan", "Lemon, lavender, thyme"),
    "cardamom": ("Cardamom", "kapulaga", "Spice", 3, "5–6 jam", "Pedas hijau, hangat", "Rose, saffron, sandalwood"),
    "pink pepper": ("Pink Pepper", "lada merah muda", "Spice", 3, "4–6 jam", "Pedas ringan, buah, cerah", "Rose, bergamot, musk"),
    "cinnamon": ("Cinnamon", "kayu manis", "Spice", 4, "6–8 jam", "Hangat, manis-pedas", "Apple, vanilla, amber"),
    "ginger": ("Ginger", "jahe", "Spice", 3, "4–5 jam", "Pedas segar, menghangatkan", "Lime, lemongrass, musk"),
    "saffron": ("Saffron", "kunyit kasmir", "Spice", 4, "8–10 jam", "Pedas-manis, kuning, mewah", "Rose, amber, oud"),
    "spices": ("Spices", "rempah campuran", "Spice", 3, "5–7 jam", "Hangat, kompleks, dewasa", "Vanilla, cedar, amber"),
    "vanilla": ("Vanilla", "vanili", "Gourmand", 4, "8–12 jam", "Manis krim, hangat, populer", "Tonka, caramel, musk"),
    "tonka": ("Tonka", "tonka", "Gourmand", 4, "8–12 jam", "Manis almond, balsam, stabil", "Vanilla, amber, lavender"),
    "caramel": ("Caramel", "karamel", "Gourmand", 4, "7–10 jam", "Manis gula hangat", "Vanilla, coffee, salt"),
    "coffee": ("Coffee", "kopi", "Gourmand", 4, "7–10 jam", "Pahit-manis, gelap, energik", "Vanilla, tonka, hazelnut"),
    "chocolate": ("Chocolate", "cokelat", "Gourmand", 4, "7–10 jam", "Manis gelap, creamy", "Vanilla, almond, tonka"),
    "almond": ("Almond", "almond", "Gourmand", 3, "6–8 jam", "Manis kacang, lembut", "Cherry, vanilla, tonka"),
    "cream": ("Cream", "krim", "Gourmand", 2, "4–6 jam", "Lembut, susu, menenangkan", "Vanilla, iris, musk"),
    "whipped cream": ("Whipped Cream", "krim kocok", "Gourmand", 2, "4–6 jam", "Manis ringan, berbusa", "Vanilla, caramel, berry"),
    "sugar": ("Sugar", "gula", "Gourmand", 3, "6–8 jam", "Manis murni, candied", "Vanilla, caramel, cotton candy"),
    "musk": ("Musk", "kasturi", "Musk", 4, "8–12 jam", "Hangat, kulit, klasik", "Rose, amber, jasmine"),
    "white musk": ("White Musk", "kasturi putih", "Musk", 3, "6–9 jam", "Bersih, lembut, dekat kulit", "Jasmine, cedar, marine"),
    "amber": ("Amber", "amber", "Amber", 5, "10–14 jam", "Resin hangat, manis, kuat", "Vanilla, oud, saffron"),
    "woody accord": ("Woody Accord", "akorda kayu", "Woody", 3, "6–9 jam", "Kering, kayu, penopang", "Bergamot, jasmine, musk"),
    "cedar": ("Cedar", "cedar", "Woody", 3, "6–9 jam", "Kayu kering, pensil, stabil", "Bergamot, lavender, vanilla"),
    "sandalwood": ("Sandalwood", "cendana", "Woody", 4, "8–12 jam", "Kayu krim, hangat, halus", "Rose, cardamom, amber"),
    "oud": ("Oud", "gaharu", "Woody", 5, "12–16 jam", "Resin kayu gelap, kuat dan padat", "Rose, saffron, amber"),
    "patchouli": ("Patchouli", "patchouli", "Woody", 4, "8–12 jam", "Tanah, hijau, berat", "Rose, vanilla, cedar"),
    "oakmoss": ("Oakmoss", "lumut oak", "Woody", 4, "8–12 jam", "Hutan, lembap, klasik", "Bergamot, lavender, amber"),
    "leather": ("Leather", "kulit", "Leather", 4, "8–12 jam", "Kulit, asap, maskulin", "Saffron, tonka, cedar"),
    "floral accord": ("Floral Accord", "akorda bunga campuran", "Floral", 3, "5–7 jam", "Bunga campuran, umum", "Musk, amber, bergamot"),
}

# Deskriptor: (id, english, dimensi, makna, contoh kalimat)
DESCRIPTORS = [
    ("Segar", "Fresh", "karakter", "Efek dingin/bersih di awal pemakaian", "Bergamot memberi kesan segar saat pertama disemprotkan."),
    ("Cerah", "Bright", "karakter", "Terang, tidak gelap atau berat", "Aroma cerah cocok untuk pagi dan kantor."),
    ("Lapang", "Airy", "tekstur", "Ringan, tidak menumpuk di kulit", "Marine membuat parfum terasa lapang."),
    ("Bersih", "Clean", "karakter", "Seperti kulit bersih atau pakaian baru", "White musk memberi kesan bersih yang lembut."),
    ("Hangat", "Warm", "karakter", "Aroma resin/rempah yang menghangatkan", "Amber dan tonka terasa hangat di malam hari."),
    ("Manis", "Sweet", "karakter", "Gula, vanili, atau buah matang", "Vanilla memberi manis krim yang ramah."),
    ("Pahit", "Bitter", "karakter", "Kesan kopi/kulit jeruk pahit", "Kopi memberi kontras pahit pada gourmand."),
    ("Pedas", "Spicy", "karakter", "Rempah tajam seperti lada/kayu manis", "Pink pepper menambah pedas ringan."),
    ("Kayu", "Woody", "karakter", "Kering, seperti kayu/serat", "Cedar memberi dasar kayu yang stabil."),
    ("Berbunga", "Floral", "karakter", "Bunga mawar, melati, lili", "Jasmine mendominasi heart note."),
    ("Buah", "Fruity", "karakter", "Pear, peach, berry", "Pear memberi manis buah di top note."),
    ("Krim", "Creamy", "tekstur", "Lembut seperti susu/krim", "Sandalwood terasa krim dan halus."),
    ("Powdery", "Powdery", "tekstur", "Bedak halus, nostalgik", "Iris memberi efek powdery yang elegan."),
    ("Kulit", "Skin-like", "tekstur", "Sangat dekat dengan kulit", "Musk ini bersifat skin scent."),
    ("Resin", "Resinous", "karakter", "Lengket, balsam, amber/oud", "Oud memberi kesan resin yang padat."),
    ("Hijau", "Green", "karakter", "Daun segar, batang, belum matang", "Green notes mengingatkan pada daun baru."),
    ("Air", "Aquatic", "karakter", "Sejuk, seperti air laut", "Marine cocok untuk tema pantai."),
    ("Asap", "Smoky", "karakter", "Bau bakar/kulit hangus", "Leather smoky cocok untuk malam."),
    ("Tanah", "Earthy", "karakter", "Tanah basah, akar, hutan", "Patchouli memberi sisi tanah."),
    ("Dewasa", "Mature", "audiens", "Cocok untuk usia 30+ atau gaya formal", "Woody oriental terasa dewasa."),
    ("Muda", "Youthful", "audiens", "Ceria, ringan, mudah diterima", "Floral fruity cocok untuk kampus."),
    ("Maskulin", "Masculine", "audiens", "Kesan tradisional maskulin", "Spicy leather dipasarkan untuk pria."),
    ("Feminin", "Feminine", "audiens", "Kesan bunga/manis tradisional feminin", "Floral putih sering dipilih untuk hadiah."),
    ("Netral", "Unisex", "audiens", "Tidak terikat gender", "Musk powdery mudah dipakai siapa saja."),
    ("Formal", "Formal", "momen", "Acara rapi, meeting, foto", "Amber wood cocok untuk meeting malam."),
    ("Santai", "Casual", "momen", "Harian, hangout, warung, live", "Citrus fresh cocok untuk live shopping."),
    ("Romantis", "Romantic", "momen", "Kencan, hadiah, perhatian", "Rose vanilla cocok untuk kencan."),
    ("Energetik", "Energetic", "suasana", "Naikkan mood, aktif", "Citrus lemon memberi energi pagi."),
    ("Tenang", "Calming", "suasana", "Lembut, tidak mengganggu", "Lavender powdery terasa menenangkan."),
    ("Mewah", "Luxurious", "suasana", "Kesan mahal, berlapis", "Oud saffron diposisikan mewah."),
    ("Nostalgik", "Nostalgic", "suasana", "Mengingatkan masa lalu", "Baby powder memicu nostalgia."),
    ("Minimalis", "Minimalist", "suasana", "Sederhana, tidak ribet", "White musk adalah pilihan minimalis."),
    ("Dramatis", "Dramatic", "suasana", "Kuat, mudah tercium, berkesan", "Amber oud cocok untuk konten dramatis."),
    ("Segar-Manis", "Fresh Sweet", "karakter", "Kombinasi citrus dan gula", "Pear bergamot manis tapi segar."),
    ("Kering", "Dry", "tekstur", "Tidak manis, tidak berair", "Cedar kering cocok untuk pria."),
    ("Berat", "Heavy", "proyeksi", "Padat, menempel lama", "Gourmand vanilla tergolong berat."),
    ("Ringan", "Light", "proyeksi", "Tidak mengganggu di dekat orang", "Aquatic ringan untuk kantor."),
    ("Dekat Kulit", "Close to skin", "proyeksi", "Tidak menyebar jauh", "White musk tetap dekat kulit."),
    ("Menyebar", "Diffusive", "proyeksi", "Mudah tercium dari jarak", "Amber kuat dan menyebar."),
    ("Tahan Lama", "Long-lasting", "ketahanan", "Bertahan berjam-jam", "Oud dikenal tahan lama."),
    ("Cepat Hilang", "Short-lived", "ketahanan", "Perlu disemprot ulang", "Citrus segar cepat menguap."),
    ("Musim Panas", "Summer", "musim", "Cocok cuaca panas", "Aquatic cocok untuk musim panas."),
    ("Musim Hujan", "Rainy", "musim", "Cocok dingin/lembap", "Coffee vanilla cocok musim hujan."),
    ("Pagi", "Morning", "momen", "Awal hari, segar", "Citrus untuk rutinitas pagi."),
    ("Siang", "Daytime", "momen", "Aktivitas siang", "Floral fruity untuk siang."),
    ("Malam", "Evening", "momen", "Setelah matahari terbenam", "Amber spicy untuk malam."),
    ("Setelah Mandi", "After shower", "momen", "Kulit bersih, lembap", "Musk lembut setelah mandi."),
    ("Kantor", "Office", "momen", "Lingkungan kerja", "Powdery musk aman untuk kantor."),
    ("Live Shopping", "Live selling", "momen", "Konten TikTok/Shopee Live", "Citrus cerah cocok untuk live."),
    ("Sesi Foto", "Photoshoot", "momen", "Visual dan branding", "Woody amber memberi kesan premium."),
    ("Hadiah", "Gift", "momen", "Dibeli untuk orang lain", "Floral bouquet sering jadi hadiah."),
    ("Workshop", "Workshop", "momen", "Belajar racik", "Bibit konsentrat dipakai workshop."),
    ("Reseller", "Reseller", "audiens", "Mitra jual kembali", "Bibit B2B menarik reseller."),
    ("Ramah Anggaran", "Budget-friendly", "audiens", "Harga terjangkau (butuh verifikasi)", "Tampilkan hanya produk dengan harga terverifikasi."),
    ("Premium", "Premium", "audiens", "Harga dan positioning tinggi", "Attar oud diposisikan premium."),
]

# Accord: (nama, keluarga, rasio bagian, karakter, momen, maturasi, catatan)
ACCORDS = [
    ("Citrus Pagi", "Citrus Segar", "Bergamot 3 · Lemon 2 · Lavender 2 · White Musk 2 · Cedar 1", "Segar, bersih, ringan", "Pagi, kantor, olahraga", "3–7 hari", "Hindari klaim 'tahan 24 jam' tanpa uji."),
    ("Marbella Air Laut", "Aquatik / Laut", "Marine 3 · Bergamot 2 · Lavender 2 · White Musk 3", "Lapang, segar, bersih", "Pantai, setelah mandi, live", "5–10 hari", "Marine bukan dupa laut; pastikan bahan tersedia."),
    ("Melati Putih", "Floral Putih & Bouquet", "Jasmine 4 · Lily 2 · Pear 1 · White Musk 2 · Cedar 1", "Bunga putih, lembut", "Kencan siang, hadiah", "7–14 hari", "Jasmine kuat; uji dosis agar tidak menusuk."),
    ("Rose Saffron", "Amber / Oriental", "Rose 3 · Saffron 1 · Amber 2 · Musk 2", "Romantis, hangat, mewah", "Malam, foto, hadiah", "14–21 hari", "Saffron mahal; gunakan sebagai aksen."),
    ("Vanilla Cream", "Gourmand", "Vanilla 4 · Tonka 2 · Cream 2 · Musk 1", "Manis krim, nyaman", "Malam, musim hujan", "10–21 hari", "Gourmand mudah berat; seimbangkan dengan musk."),
    ("Coffee Tonka", "Gourmand", "Coffee 3 · Tonka 2 · Vanilla 2 · Cedar 1", "Pahit-manis, energik", "Malam, kerja kreatif", "14–21 hari", "Coffee bisa menguning; cek stabilitas warna."),
    ("Chocolate Almond", "Gourmand", "Chocolate 3 · Almond 2 · Vanilla 2 · Tonka 1", "Manis kacang, dessert", "Kencan, musim hujan", "10–18 hari", "Potensi alergi kacang; cantumkan kehati-hatian."),
    ("Cedar Smoke", "Woody", "Cedar 3 · Woody Accord 2 · Leather 1 · Tonka 2", "Kering, maskulin, hangat", "Malam, meeting", "10–21 hari", "Leather kuat; uji kepekaan kulit."),
    ("Sandalwood Musk", "Woody", "Sandalwood 3 · White Musk 3 · Iris 1 · Amber 1", "Krim, halus, elegan", "Kantor, malam santai", "14–21 hari", "Sandalwood alami mahal; bisa ganti akorda."),
    ("Attar Amber", "Attar & Oud", "Amber 3 · Rose 2 · Musk 2 · Oud 1", "Resin, bunga, tradisional", "Acara keluarga, hadiah", "21–30 hari", "Oud dominan; gunakan sangat sedikit."),
    ("Oud Rose", "Attar & Oud", "Oud 2 · Rose 3 · Saffron 1 · Amber 2", "Gelap, bunga, mewah", "Malam, premium", "21–30 hari", "Tidak untuk pemula; sillage kuat."),
    ("Powdery Iris", "Musk & Powdery", "Iris 3 · Violet 2 · Musk 3 · Cream 1", "Powdery, lembut, nostalgik", "Kantor, setelah mandi", "10–18 hari", "Iris mahal; pakai sebagai aksen powdery."),
    ("White Musk Clean", "Musk & Powdery", "White Musk 4 · Marine 1 · Lily 1 · Cedar 1", "Bersih, dekat kulit", "Setelah mandi, kantor", "5–12 hari", "Cocok sebagai 'parfum pertama'."),
    ("Lavender Herbal", "Aromatic Herbal", "Lavender 3 · Bergamot 2 · Rosemary 1 · Tonka 2", "Herbal, rapi, maskulin", "Kantor, olahraga", "5–12 hari", "Lavender kuat; jangan berlebih."),
    ("Spicy Urban", "Spicy Leather", "Pink Pepper 2 · Leather 2 · Tonka 2 · Amber 2", "Pedas, kulit, urban", "Night out, meeting", "14–21 hari", "Pink pepper bisa menyengat; uji dosis."),
    ("Peach Nectar", "Fruity", "Peach 3 · Pear 2 · Jasmine 2 · Musk 2", "Manis buah, playful", "Hangout, kampus, live", "5–12 hari", "Buah cepat hilang; top up di kulit bila perlu."),
    ("Tropical Juice", "Fruity", "Pineapple 2 · Watermelon 2 · Marine 2 · White Musk 2", "Tropis, cerah", "Pantai, liburan", "3–8 hari", "Cocok untuk konten warna cerah."),
    ("Green Tea", "Citrus Segar", "Green Notes 3 · Bergamot 2 · Neroli 1 · Musk 2", "Hijau, tenang, segar", "Pagi, belajar, kantor", "5–10 hari", "Hindari klaim 'detoks' atau kesehatan."),
    ("Baby Powder", "Musk & Powdery", "Iris 2 · Cream 3 · Vanilla 1 · White Musk 3", "Lembut, nostalgik", "Keluarga, setelah mandi", "7–14 hari", "Jangan ditujukan untuk bayi tanpa uji."),
    ("Laundry Fresh", "Laundry & Clean", "White Musk 3 · Marine 2 · Lavender 2 · Clean Accord 3", "Bersih, pakaian baru", "Cuci pakaian, rumah", "3–7 hari", "Ini untuk laundry, bukan klaim parfum kulit."),
    ("Bergamot Neroli", "Citrus Segar", "Bergamot 3 · Neroli 2 · Orange Blossom 1 · Musk 2", "Bunga jeruk, elegan", "Pagi, kantor, hadiah", "7–14 hari", "Neroli kuat; uji pada kertas terlebih dahulu."),
    ("Amber Vanilla", "Amber / Oriental", "Amber 3 · Vanilla 3 · Tonka 1 · Musk 1", "Hangat, manis, stabil", "Malam, musim hujan", "14–21 hari", "Paling mudah disukai; cocok untuk bundle."),
    ("Nusantara Pandan", "Gourmand", "Vanilla 2 · Cream 3 · Green Notes 2 · Coconut 1", "Krim hijau, lokal", "Hadiah, konten lokal", "7–14 hari", "Bahan 'coconut/pandan' perlu disesuaikan stok."),
    ("Kasturi Gaharu", "Attar & Oud", "Musk 3 · Oud 2 · Amber 2 · Rose 1", "Kasturi, resin, lokal", "Acara, hadiah premium", "21–30 hari", "Gunakan konsentrat terverifikasi."),
]

# Tema: (tema, persona, trigger, keluarga, notes kunci, CTA, format, momen, risiko)
THEMES = [
    ("Parfum Kantor Ringan", "Karyawan 22–40", "Butuh wangi rapi tanpa mengganggu", "Musk & Powdery", "white musk, iris, lavender", "OFFICE", "Reels before/after kerja", "Kantor, meeting", "Jangan klaim bebas alergi."),
    ("Parfum Setelah Mandi", "Semua usia", "Ingin kesan bersih segar", "Musk & Powdery", "white musk, marine, cream", "FRESH", "Story rutinitas mandi", "Pagi, setelah mandi", "Hindari klaim medis."),
    ("Parfum Marbella Air Laut", "Gen Z, 18–30", "Ingin wangi liburan", "Aquatik / Laut", "marine, bergamot, lavender", "MARBELLA", "Reels laut + botol", "Pantai, liburan", "Pakai notes sesuai sumber resmi bila tersedia."),
    ("Wangi Malam Formal", "Profesional 28–45", "Acara malam, foto", "Amber / Oriental", "amber, saffron, vanilla", "NIGHT", "Lookbook malam", "Malam, formal", "Klaim 'premium' harus sesuai harga/stok."),
    ("Hadiah untuk Pasangan", "Pembeli hadiah", "Butuh rekomendasi cepat", "Floral Putih & Bouquet", "rose, jasmine, vanilla", "GIFT", "Card + wrapping", "Kencan, ulang tahun", "Cek stok dan harga sebelum promosi."),
    ("Parfum Pria Urban", "Pria 25–40", "Gaya jaket, night out", "Spicy Leather", "pink pepper, leather, tonka", "URBAN", "OOTD + parfum", "Night out, meeting", "Hindari stereotip gender berlebih."),
    ("Parfum Attar & Oud", "Pembeli attar", "Cari aroma tradisional kuat", "Attar & Oud", "oud, amber, rose", "ATTAR", "Close-up botol/minyak", "Acara keluarga", "Jangan klaim kehalalan tanpa sertifikasi."),
    ("Parfum Laundry Wangi", "Ibu rumah tangga", "Pakaian harus wangi", "Laundry & Clean", "white musk, marine, lavender", "LAUNDRY", "Before/after cucian", "Rumah, laundry", "Ini kategori laundry, bukan parfum kulit."),
    ("Bibit Racik Sendiri", "Reseller, hobbyist", "Mau bikin aroma sendiri", "Bibit / Konsentrat", "bergamot, musk, amber", "RACIK", "Workshop singkat", "Workshop, B2B", "Sertakan petunjuk dilusi dan keamanan."),
    ("Parfum Musim Hujan", "Semua usia", "Cuaca dingin/lembap", "Gourmand", "vanilla, coffee, tonka", "HUJAN", "Suasana hujan + kopi", "Musim hujan", "Tidak ada klaim menghangatkan tubuh."),
    ("Parfum Pantai", "Gen Z, traveler", "Liburan pantai", "Aquatik / Laut", "marine, lotus, cedar", "BEACH", "Vlog liburan", "Pantai, siang", "Gunakan harga terverifikasi untuk CTA."),
    ("Parfum Buah Cerah", "Pelajar, mahasiswa", "Suka manis buah", "Fruity", "pear, peach, raspberry", "FRUITY", "Warna cerah, transisi", "Kampus, hangout", "Manis bukan berarti manis gula; jelaskan notes."),
    ("Parfum Bunga Putih", "Pembeli hadiah", "Suka bunga elegan", "Floral Putih & Bouquet", "jasmine, lily, freesia", "BLOOM", "Flatlay bunga", "Hadiah, foto", "Jangan klaim komposisi resmi brand."),
    ("Signature Scent", "Pembeli setia", "Mau aroma khas", "Amber / Oriental", "amber, musk, sandalwood", "SIGNATURE", "Series '1 parfum 3 momen'", "Malam, harian", "Bantu pilih 2–3 kandidat, bukan klaim unik."),
    ("Parfum Live Shopping", "Penonton TikTok", "Butuh rekomendasi cepat", "Citrus Segar", "bergamot, lemon, musk", "QUOTE", "Live 15 detik per aroma", "Live, siang", "CTA viewer-initiated, bukan auto-DM."),
    ("Parfum Foto & Konten", "Content creator", "Visual harus 'premium'", "Woody", "cedar, sandalwood, amber", "SHOOT", "Behind the scene", "Sesi foto", "Pencahayaan bukan bukti kualitas."),
    ("Parfum Harian Murah", "Pembeli hemat", "Cari nilai baik", "Aromatic Herbal", "lavender, bergamot, musk", "VALUE", "3 aroma attar", "Sehari-hari", "Tampilkan hanya yang Sales Price terisi."),
    ("Parfum Vanila Manis", "Pencinta gourmand", "Ingin manis krim", "Gourmand", "vanilla, tonka, caramel", "VANILLA", "Dessert + parfum", "Malam, hujan", "Gourmand kuat; sarankan dosis kecil."),
    ("Parfum Kopi", "Pecinta kopi", "Aroma kopi nyata", "Gourmand", "coffee, vanilla, tonka", "COFFEE", "Kopi + botol", "Pagi, malam", "Hindari klaim energi/kesehatan."),
    ("Parfum Minimalis", "Pembeli praktis", "Mau satu aroma untuk semua", "Musk & Powdery", "white musk, cedar, violet", "CLEAN", "Satu botol, tiga momen", "Kantor, tidur", "Jangan klaim cocok untuk semua kulit."),
    ("Parfum Keluarga", "Pembeli rumah", "Aroma aman bersama", "Musk & Powdery", "white musk, cream, lavender", "HOME", "Rutinitas keluarga", "Rumah, siang", "Jangan ditujukan untuk bayi tanpa uji."),
    ("Parfum Malam Romantis", "Pembeli kencan", "Ingin kesan dekat", "Floral Putih & Bouquet", "rose, jasmine, vanilla", "DATE", "Candle + parfum", "Kencan malam", "Hindari klaim afrodisiak."),
    ("Workshop Racik Alkaff", "Komunitas, reseller", "Belajar dasar parfum", "Bibit / Konsentrat", "bergamot, jasmine, musk", "WORKSHOP", "Video langkah ringkas", "Workshop", "Sertakan IFRA/keamanan dasar."),
    ("Bundle 3 Momen", "Pembeli hadiah", "Mau variasi", "Citrus Segar", "bergamot, musk, amber", "BUNDLE", "Pagi-siang-malam", "Hadiah", "Cek ketersediaan tiap SKU."),
]

# ---------------------------------------------------------------------------
# Parsing katalog
# ---------------------------------------------------------------------------
def norm_note(value: str) -> str:
    key = value.strip().lower()
    return NOTE_ALIASES.get(key, key)


def canon_family(row: dict) -> str:
    cat = row["Product Category"].lower()
    if "laundry" in cat:
        return "Laundry & Clean"
    if "bahan baku" in cat:
        return "Bibit / Konsentrat"
    raw = FAMILY_RE.search(row["Description"])
    raw = raw.group(1).lower() if raw else ""
    for family, keys in FAMILY_RULES:
        if any(k in raw for k in keys):
            return family
    return "Aromatic Herbal"


FAMILY_RE = re.compile(r"—\s*(.*?)\.\s*Notes:")
NOTES_RE = re.compile(r"Notes:\s*(.*?)\.\s*Karakter:")
LAYER_RE = re.compile(r"(Top|Heart|Base)\s+([^;]+)")
MOMEN_RE = re.compile(r"Cocok dipakai:\s*(.*?)(?:\.\s*Terinspirasi|$)")


def parse_catalog():
    with CATALOG.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    parsed = []
    for row in rows:
        desc = row["Description"]
        notes = defaultdict(list)
        m = NOTES_RE.search(desc)
        if m:
            for layer, part in LAYER_RE.findall(m.group(1)):
                for note in part.split(","):
                    note = norm_note(note)
                    if note:
                        notes[layer].append(note)
        m = MOMEN_RE.search(desc)
        parsed.append({
            "ref": row["Internal Reference"],
            "name": row["Name"],
            "category": row["Product Category"],
            "price": row["Sales Price"].strip(),
            "family": canon_family(row),
            "notes": dict(notes),
            "momen": m.group(1).strip() if m else "",
        })
    return parsed


def note_keys(row):
    """Kunci note unik yang dimiliki suatu produk."""
    return {v for values in row["notes"].values() for v in values}


def pick_refs(parsed, predicate, limit=6, keys=None, family=None):
    """Pilih contoh reference yang relevan.

    Skor: jumlah note kunci yang cocok (lebih penting), kecocokan keluarga,
    lalu harga terverifikasi. Predicate tetap dipakai sebagai filter dasar.
    """
    chosen = []
    for r in parsed:
        if not predicate(r):
            continue
        owned = note_keys(r)
        match = len(owned.intersection(keys)) if keys else 0
        fam_bonus = 3 if family and r["family"] == family else 0
        chosen.append(((-match, -fam_bonus, not bool(r["price"]), r["ref"]), r))
    chosen.sort(key=lambda item: item[0])
    return [r["ref"] for _, r in chosen[:limit]]


def write_csv(name, header, rows):
    with (ROOT / name).open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def main():
    parsed = parse_catalog()
    valid_refs = {r["ref"] for r in parsed}

    note_counts = Counter()
    note_layers = defaultdict(Counter)
    for r in parsed:
        for layer, notes in r["notes"].items():
            for n in notes:
                note_counts[n] += 1
                note_layers[n][layer] += 1

    # 01 keluarga aroma
    fam_rows = []
    for family, meta in FAMILY_META.items():
        refs = pick_refs(parsed, lambda r, f=family: r["family"] == f, family=family)
        fam_rows.append([
            family, meta["deskriptor"], meta["notes"], meta["karakter"], meta["momen"],
            meta["ketahanan"], meta["sillage"], meta["tema"],
            " · ".join(refs) if refs else "(belum ada produk)",
            str(sum(1 for r in parsed if r["family"] == family)),
        ])
    write_csv("01_keluarga_aroma.csv",
              ["Keluarga", "Deskriptor", "Notes Khas", "Karakter", "Momen",
               "Ketahanan Umum", "Sillage", "Tema Konten", "Contoh Internal Reference", "Jumlah Produk"],
              fam_rows)

    # 02 taksonomi notes
    note_rows = []
    for key, meta in NOTE_META.items():
        label, alias, note_family, intensity, longevity, desc, pair = meta
        layers = note_layers.get(key, Counter())
        layer = layers.most_common(1)[0][0] if layers else "Top"
        refs = pick_refs(parsed, lambda r, k=key: k in note_keys(r), keys={key})
        note_rows.append([
            label, key, alias, layer, note_family, intensity, longevity, desc, pair,
            note_counts.get(key, 0), " · ".join(refs) if refs else "(kosakata tambahan)",
        ])
    write_csv("02_taksonomi_notes.csv",
              ["Note", "Kunci", "Alias", "Layer Dominan", "Keluarga Note", "Intensitas (1-5)",
               "Ketahanan", "Deskripsi Aroma", "Pasangan Umum", "Jumlah Produk", "Contoh Internal Reference"],
              note_rows)

    # 03 deskriptor
    write_csv("03_kosakata_deskriptor.csv",
              ["Deskriptor", "English", "Dimensi", "Makna", "Contoh Kalimat"],
              [list(d) for d in DESCRIPTORS])

    # 04 accord
    accord_rows = []
    for nama, family, ratio, character, moment, mature, safety in ACCORDS:
        keys = {norm_note(k) for k in re.findall(r"[A-Za-z][A-Za-z ]+(?=\s*\d)", ratio)}
        refs = pick_refs(parsed, lambda r, ks=keys: bool(note_keys(r).intersection(ks)),
                         keys=keys, family=family)
        accord_rows.append([
            nama, family, ratio, character, moment, mature, safety,
            " · ".join(refs) if refs else "(referensi tema saja)",
            "Edukasi/inspirasi konten; bukan formula produksi.",
        ])
    write_csv("04_resep_accord.csv",
              ["Nama Accord", "Keluarga", "Rasio Bagian (edukatif)", "Karakter", "Momen",
               "Maturasi Saran", "Catatan Keamanan", "Contoh Internal Reference", "Status"],
              accord_rows)

    # 05 tema layanan
    theme_rows = []
    for tema, persona, trigger, family, keys_raw, cta, fmt, moment, risk in THEMES:
        keys = {norm_note(k.strip()) for k in keys_raw.split(",")}
        note_refs = pick_refs(parsed, lambda r, ks=keys: bool(note_keys(r).intersection(ks)),
                              keys=keys, family=family)
        fam_refs = pick_refs(parsed, lambda r, f=family: r["family"] == f, family=family)
        # Tema yang sangat spesifik kategorinya harus memakai produk dari
        # keluarga itu lebih dulu; sisanya baru dilengkapi dari kecocokan notes.
        strict = family in {"Laundry & Clean", "Bibit / Konsentrat", "Attar & Oud"}
        refs = (fam_refs + [r for r in note_refs if r not in fam_refs])[:6] if strict else note_refs
        if not refs:
            refs = fam_refs
        theme_rows.append([
            tema, persona, trigger, family, keys_raw, " · ".join(refs) if refs else "(cek stok)",
            cta, fmt, moment, risk, "Beli/DM dimulai dari pengguna bila dipakai di TikTok LIVE.",
        ])
    write_csv("05_tema_layanan.csv",
              ["Tema", "Persona", "Trigger", "Keluarga", "Notes Kunci", "Contoh Internal Reference",
               "CTA Keyword", "Format Konten", "Momen", "Risiko / Caveat", "Catatan LIVE"],
              theme_rows)

    # 06 bundle JSON untuk aplikasi
    bundle = {
        "sumber": "katalog_parfum_alkaff_odoo.csv",
        "jumlah_produk": len(parsed),
        "keluarga": fam_rows and [dict(zip(["Keluarga","Deskriptor","Notes Khas","Karakter","Momen","Ketahanan Umum","Sillage","Tema Konten","Contoh Internal Reference","Jumlah Produk"], r)) for r in fam_rows],
        "notes": [dict(zip(["Note","Kunci","Alias","Layer Dominan","Keluarga Note","Intensitas","Ketahanan","Deskripsi","Pasangan","Jumlah Produk","Contoh Internal Reference"], r)) for r in note_rows],
        "deskriptor": [dict(zip(["Deskriptor","English","Dimensi","Makna","Contoh Kalimat"], d)) for d in DESCRIPTORS],
        "accord": [dict(zip(["Nama","Keluarga","Rasio","Karakter","Momen","Maturasi","Keamanan","Contoh Internal Reference","Status"], r)) for r in accord_rows],
        "tema": [dict(zip(["Tema","Persona","Trigger","Keluarga","Notes Kunci","Contoh Internal Reference","CTA","Format","Momen","Risiko","Catatan LIVE"], r)) for r in theme_rows],
    }
    (ROOT / "pengetahuan-parfum.json").write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")

    # validasi referensi
    all_refs = set()
    for rows in (fam_rows, note_rows, accord_rows, theme_rows):
        for row in rows:
            for cell in row:
                if isinstance(cell, str):
                    all_refs.update(re.findall(r"\b(?:MCB\d+|LZ\d+|IBC\d+|ALK-[A-Z]-\d+|EXPS\d+|KV\d+)\b", cell))
    invalid = sorted(r for r in all_refs if r not in valid_refs)
    if invalid:
        raise SystemExit("Referensi tidak ditemukan di katalog: " + ", ".join(invalid))

    print(f"Produk: {len(parsed)} | keluarga: {len(fam_rows)} | notes: {len(note_rows)} | "
          f"deskriptor: {len(DESCRIPTORS)} | accord: {len(accord_rows)} | tema: {len(theme_rows)}")
    print("Referensi tervalidasi:", len(all_refs))


if __name__ == "__main__":
    main()
