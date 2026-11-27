#!/usr/bin/env python3
"""Bangun basis pengetahuan parfum dari katalog Alkaff.

Membaca:  ../katalog-alkaff-odoo/katalog_parfum_alkaff_odoo.csv
Menulis:  file CSV + JSON di direktori ini.

Data yang dihasilkan bersifat **edukatif dan komersial-ringan**: taksonomi,
deskriptor, ide accord, tema layanan, frasa sensorik, dan pagar klaim. Bukan
komposisi resmi pabrik, bukan formula produksi, bukan positioning merek lain,
dan bukan klaim kosmetik/obat.
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
    "mawar": "rose",
    "kopi": "coffee",
    "gula": "sugar",
    "safron": "saffron",
    "marine notes": "marine",
    "notes laut": "marine",
    "almond pahit": "almond",
    "amalfi lemon": "lemon",
    "clean musk": "white musk",
    "cocoa": "chocolate",
    "woody notes": "woody accord",
    "floral notes": "floral accord",
    "green": "green notes",
    "leafy green": "green notes",
    "prairie oud": "oud",
    # Dari riset 01_perbendaharaan_aroma.md (2026-11-27).
    "kenanga": "ylang ylang",
    "akar wangi": "vetiver",
    "olibanum": "frankincense",
    "dupa": "incense",
    "bunga lawang": "star anise",
    "muguet": "lily of the valley",
    "kamboja": "frangipani",
    "ara": "fig",
    "jambu biji": "guava",
    "kacang hazel": "hazelnut",
    "kelapa": "coconut",
    "udara ozon": "ozone",
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
    "acacia": ("Acacia", "akasia", "Floral", 3, "4–6 jam", "Bunga kuning manis-lembut, sedikit madu", "Rose, bergamot, musk"),
    "airy notes": ("Airy Notes", "notes lapang", "Aquatic", 2, "2–4 jam", "Ringan dan transparan, mudah menguap", "Marine, white musk, citrus"),
    "ambergris": ("Ambergris", "ambergris", "Amber", 5, "12–16 jam", "Resin laut hangat, asin-manis, langka", "Amber, oud, marine"),
    "amberwood": ("Amberwood", "kayu amber", "Amber", 4, "10–14 jam", "Kayu hangat ke resin, modern", "Ambroxan, cedar, vanilla"),
    "ambroxan": ("Ambroxan", "ambroksan", "Amber", 4, "10–14 jam", "Amber bersih, dekat kulit, penambah proyeksi", "Bergamot, musk, amberwood"),
    "bamboo": ("Bamboo", "bambu", "Green", 2, "3–5 jam", "Hijau segar, renyah, ringan", "Green tea, lotus, musk"),
    "bay leaf": ("Bay Leaf", "daun salam", "Herbal", 3, "4–6 jam", "Herbal kering, sedikit pedas", "Bergamot, cedar, cardamom"),
    "benzoin": ("Benzoin", "benzoin", "Amber", 4, "8–12 jam", "Balsam manis, vanila-resin", "Vanilla, tonka, amber"),
    "birch": ("Birch", "kayu birch", "Woody", 3, "6–9 jam", "Kayu kering, sedikit asap", "Leather, cedar, tonka"),
    "black pepper": ("Black Pepper", "lada hitam", "Spice", 3, "4–6 jam", "Pedas tajam, hangat, maskulin", "Bergamot, leather, cedar"),
    "blackcurrant": ("Blackcurrant", "blackcurrant", "Fruity", 3, "3–5 jam", "Berry hitam asam-manis, tajam", "Rose, vanilla, musk"),
    "blood orange": ("Blood Orange", "jeruk darah", "Citrus", 3, "2–3 jam", "Jeruk merah manis-asam, sedikit berry", "Neroli, bergamot, musk"),
    "butter": ("Butter", "mentega", "Gourmand", 2, "4–6 jam", "Krim kaya, lembut, sedikit asin", "Vanilla, cream, caramel"),
    "cempaka": ("Cempaka", "cempaka", "Floral", 3, "4–7 jam", "Bunga champaca manis-krim, khas Asia", "Rose, sandalwood, musk"),
    "cherry": ("Cherry", "ceri", "Fruity", 3, "3–5 jam", "Manis buah merah gelap, sedikit almond", "Almond, vanilla, rose"),
    "cherry blossom": ("Cherry Blossom", "bunga sakura", "Floral", 2, "3–5 jam", "Bunga merah muda lembut, ringan", "Pear, musk, jasmine"),
    "citronella": ("Citronella", "serai wangi", "Citrus", 2, "2–4 jam", "Jeruk-herbal, segar, menenangkan", "Lemongrass, lime, musk"),
    "citrus": ("Citrus Accord", "akorda jeruk", "Citrus", 3, "2–4 jam", "Kesan jeruk campuran, cerah", "Bergamot, lemon, neroli"),
    "cognac": ("Cognac", "kognak", "Gourmand", 4, "7–10 jam", "Anggur hangat, oak, sedikit manis", "Tonka, vanilla, leather"),
    "cyclamen": ("Cyclamen", "siklamen", "Floral", 2, "3–5 jam", "Bunga hijau-merah muda, segar", "Violet, green notes, musk"),
    "driftwood": ("Driftwood", "kayu hanyut", "Woody", 3, "6–9 jam", "Kayu kering terpapar laut", "Marine, cedar, white musk"),
    "fir": ("Fir", "fir", "Woody", 3, "5–8 jam", "Jarum pinus hijau, hutan dingin", "Bergamot, oakmoss, cedar"),
    "fir resin": ("Fir Resin", "resin fir", "Amber", 4, "8–12 jam", "Resin pinus hangat, balsam", "Amber, benzoin, cedar"),
    "grape": ("Grape", "anggur", "Fruity", 2, "2–4 jam", "Manis buah anggur, ringan", "Rose, musk, vanilla"),
    "grapefruit": ("Grapefruit", "jeruk bali", "Citrus", 3, "2–3 jam", "Pahit-manis cerah, lebih tajam dari lemon", "Bergamot, marine, musk"),
    "green apple": ("Green Apple", "apel hijau", "Fruity", 3, "2–3 jam", "Asam renyah, lebih tajam dari apel merah", "Cinnamon, cedar, vanilla"),
    "green tea": ("Green Tea", "teh hijau", "Green", 2, "3–5 jam", "Daun teh segar, tenang, sedikit pahit", "Bergamot, lotus, musk"),
    "heliotrope": ("Heliotrope", "heliotrop", "Floral", 3, "5–8 jam", "Bunga ungu powdery, vanila-almond", "Vanilla, iris, almond"),
    "juicy fruits": ("Juicy Fruits", "campuran buah berair", "Fruity", 2, "2–4 jam", "Buah segar berair, manis cerah", "Marine, pear, musk"),
    "lemongrass": ("Lemongrass", "serai", "Herbal", 3, "3–5 jam", "Segar tajam, sitrus-herbal", "Ginger, lime, musk"),
    "matcha": ("Matcha", "matcha", "Green", 2, "3–5 jam", "Teh hijau bubuk, creamy, sedikit pahit", "Cream, vanilla, green notes"),
    "milk": ("Milk", "susu", "Gourmand", 2, "4–6 jam", "Lembut, susu, nyaman", "Vanilla, iris, caramel"),
    "mint": ("Mint", "mint", "Herbal", 3, "3–5 jam", "Dingin, hijau, menyegarkan", "Lime, marine, lavender"),
    "oak": ("Oak", "oak", "Woody", 4, "8–12 jam", "Kayu oak kering, sedikit anggur", "Cognac, leather, amber"),
    "orchid": ("Orchid", "anggrek", "Floral", 2, "4–6 jam", "Bunga eksotis lembut, sedikit vanila", "Jasmine, vanilla, musk"),
    "pepper": ("Pepper", "lada", "Spice", 3, "4–6 jam", "Pedas umum, hangat, tajam", "Bergamot, leather, cedar"),
    "rosewood": ("Rosewood", "kayu mawar", "Woody", 3, "6–9 jam", "Kayu merah muda, bunga, halus", "Rose, sandalwood, musk"),
    "sakura": ("Sakura", "sakura", "Floral", 2, "3–5 jam", "Bunga ceri Jepang, manis lembut", "Pear, jasmine, musk"),
    "sea salt": ("Sea Salt", "garam laut", "Aquatic", 2, "3–5 jam", "Asin segar, seperti angin pantai", "Marine, bergamot, driftwood"),
    "tuberose": ("Tuberose", "tuberosa", "Floral", 5, "8–12 jam", "Bunga putih sangat kuat, krim, manis", "Jasmine, vanilla, musk"),
    "violet leaf": ("Violet Leaf", "daun ungu", "Green", 3, "4–6 jam", "Hijau-keras, sedikit powdery", "Iris, violet, green notes"),
    "white wood": ("White Wood", "kayu putih", "Woody", 3, "6–9 jam", "Kayu bersih, ringan, ke krim", "White musk, sandalwood, amber"),
    # Entri riset 01_perbendaharaan_aroma.md, akses 2026-11-27. Angka
    # intensitas/ketahanan adalah heuristik edukatif, bukan uji produk.
    "ylang ylang": ("Ylang-Ylang", "kenanga, cananga", "Floral", 5, "8–12 jam (gambaran)", "Bunga krim manis, buah, hijau-powdery; kuat", "Jasmine, sandalwood, vanilla"),
    "petitgrain": ("Petitgrain", "daun jeruk pahit", "Citrus", 3, "3–5 jam (gambaran)", "Sitrus hijau kering, lebih pahit dari neroli", "Lavender, neroli, musk"),
    "palmarosa": ("Palmarosa", "rumput mawar India", "Floral", 3, "4–6 jam (gambaran)", "Mawar ringan dengan sisi sitrus", "Rose, lemongrass, cedar"),
    "stephanotis": ("Stephanotis", "bunga pengantin Madagaskar", "Floral", 3, "4–6 jam (gambaran)", "Bunga putih kecil, manis-lembut", "Jasmine, lily, white musk"),
    "vetiver": ("Vetiver", "akar wangi", "Woody", 4, "8–12 jam (gambaran)", "Akar kering, tanah, kayu; Jawa lebih berasap", "Bergamot, cedar, black pepper"),
    "galbanum": ("Galbanum", "resin hijau pahit", "Green", 5, "6–9 jam (gambaran)", "Hijau menyengat, pinus, earthy; dosis kecil", "Bergamot, oakmoss, hyacinth"),
    "frankincense": ("Frankincense", "olibanum, dupa", "Amber", 4, "8–12 jam (gambaran)", "Resin sitrus-pedas lalu hangat balsamik", "Labdanum, myrrh, sandalwood"),
    "labdanum": ("Labdanum", "resin cistus", "Amber", 4, "8–12 jam (gambaran)", "Ambery hangat, woody, kulit, sedikit animalik", "Benzoin, oakmoss, vanilla"),
    "opoponax": ("Opoponax", "sweet myrrh", "Amber", 4, "8–12 jam (gambaran)", "Resin manis-berasap, powdery, karamel pahit", "Labdanum, benzoin, vanilla"),
    "elemi": ("Elemi", "resin pucat", "Amber", 3, "5–8 jam (gambaran)", "Balsam-pedas, hampir lemony, segar", "Frankincense, cedar, bergamot"),
    "incense": ("Incense", "kesan dupa", "Amber", 4, "8–12 jam (gambaran)", "Kesan bakaran kayu/resin/rempah, bukan satu bahan", "Frankincense, labdanum, oakmoss"),
    "coumarin": ("Coumarin", "jerami kering", "Gourmand", 3, "6–9 jam (gambaran)", "Manis jerami, milky, tonka-like; cek IFRA", "Lavender, tonka, bergamot"),
    "star anise": ("Star Anise", "bunga lawang", "Spice", 4, "6–9 jam (gambaran)", "Manis licorice, aniseed, pedas hangat", "Cardamom, petitgrain, cedar"),
    "licorice": ("Licorice", "akar manis", "Gourmand", 3, "6–9 jam (gambaran)", "Aniseed-karamel, manis akar; hindari klaim kesehatan", "Tonka, cedar, vanilla"),
    "gardenia": ("Gardenia", "gardenia", "Floral", 5, "8–12 jam (gambaran)", "Bunga putih sangat kuat, krim, sedikit hijau", "Jasmine, tuberose, cream"),
    "magnolia": ("Magnolia", "magnolia", "Floral", 3, "5–8 jam (gambaran)", "Bunga putih krim-manis dengan tepi segar", "Lily, pear, musk"),
    "hyacinth": ("Hyacinth", "hiasin", "Floral", 5, "6–10 jam (gambaran)", "Hijau saat kuncup, sangat kuat saat mekar", "Narcissus, lily of the valley, green notes"),
    "narcissus": ("Narcissus", "narsis", "Floral", 5, "6–10 jam (gambaran)", "Kaya, hijau, heady; kuat di ruang tertutup", "Hyacinth, jasmine, violet"),
    "lily of the valley": ("Lily of the Valley", "muguet", "Floral", 4, "5–8 jam (gambaran)", "Hijau-manis, hampir pedas, hint lemon", "Rose, magnolia, green notes"),
    "lilac": ("Lilac", "lilac", "Floral", 3, "4–7 jam (gambaran)", "Powdery-lembut, jasmine-like, almond-mawar", "Violet, rose, iris"),
    "carnation": ("Carnation", "anyelir", "Floral", 4, "6–9 jam (gambaran)", "Bunga cengkeh-pedas hangat, vintage", "Clove, rose, cinnamon"),
    "boronia": ("Boronia", "boronia", "Floral", 3, "4–7 jam (gambaran)", "Raspberi, aprikot, violet, freesia", "Pear, raspberry, freesia"),
    "frangipani": ("Frangipani", "kamboja", "Floral", 4, "8–12 jam (gambaran)", "Bunga tropis krim-peachy, kuat di malam", "Coconut, tiare, ylang ylang"),
    "tiare": ("Tiaré", "tiare Tahiti", "Floral", 4, "6–10 jam (gambaran)", "Bunga putih manis khas monoi", "Coconut, frangipani, vanilla"),
    "honeysuckle": ("Honeysuckle", "kamandingan", "Floral", 3, "5–8 jam (gambaran)", "Nectar manis seperti jasmine dengan vanilla", "Jasmine, orange blossom, musk"),
    "osmanthus": ("Osmanthus", "bunga osmanthus", "Floral", 3, "5–8 jam (gambaran)", "Aprikot kering, madu, sedikit rempah", "Black tea, pear, honey"),
    "bluebell": ("Bluebell", "bluebell", "Floral", 2, "3–5 jam (gambaran)", "Kabut bunga hijau cerah, musim semi", "Green notes, hyacinth, musk"),
    "guaiac wood": ("Guaiac Wood", "palo santo", "Woody", 4, "8–12 jam (gambaran)", "Kayu berat birch-tar, karet, tembakau", "Leather, birch, tonka"),
    "juniper": ("Juniper", "juniper", "Herbal", 3, "4–7 jam (gambaran)", "Getah pinus segar, pahit, seperti gin", "Cypress, lime, vetiver"),
    "fig": ("Fig", "ara", "Fruity", 3, "4–7 jam (gambaran)", "Daun pahit-sejuk + buah manis-krim", "Coconut, green notes, musk"),
    "guava": ("Guava", "jambu biji", "Fruity", 2, "3–5 jam (gambaran)", "Tropis manis-juicy, kadang sedikit pahit", "Lime, pineapple, marine"),
    "hazelnut": ("Hazelnut", "kacang hazel", "Gourmand", 3, "6–9 jam (gambaran)", "Kacang panggang buttery; kehati-hatian alergi", "Chocolate, praline, vanilla"),
    "coconut": ("Coconut", "kelapa", "Gourmand", 3, "5–9 jam (gambaran)", "Tropis, nutty, vanili-susu (perlu verifikasi)", "Tiare, frangipani, fig"),
    "yuzu": ("Yuzu", "yuzu", "Citrus", 3, "2–4 jam (gambaran)", "Sitrus manis-sangat pahit, grapefruit-hijau", "Bergamot, neroli, petitgrain"),
    "marshmallow": ("Marshmallow", "marshmallow", "Gourmand", 2, "4–7 jam (gambaran)", "Gula powdery ringan, kadang toasted", "Vanilla, cream, heliotrope"),
    "ozone": ("Ozone", "udara ozon", "Aquatic", 2, "2–4 jam (gambaran)", "Udara bersih setelah hujan, bukan dupa laut", "Marine, white musk, clean accord"),
    "amaryllis": ("Amaryllis", "amaryllis", "Floral", 2, "3–5 jam (gambaran)", "Bunga samar antara mawar dan nektarin", "Pear, rose, freesia"),
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
    ("Asin", "Salty", "karakter", "Seperti garam atau angin laut", "Sea salt memberi kesan asin segar."),
    ("Berair", "Juicy", "tekstur", "Buah segar mengandung air", "Juicy fruits terasa berair di top note."),
    ("Krim Kocok", "Whipped", "tekstur", "Busa lembut seperti krim kocok", "Whipped cream cocok untuk gourmand ringan."),
    ("Maduan", "Honeyed", "karakter", "Manis seperti madu, lengket lembut", "Orange blossom punya sisi maduan."),
    ("Balsamik", "Balsamic", "karakter", "Resin manis hangat", "Benzoin memberi kesan balsamik."),
    ("Herbal", "Herbal", "karakter", "Daun kering, rempah hijau", "Lavender dan rosemary terasa herbal."),
    ("Hijau Daun", "Leafy", "karakter", "Daun segar belum kering", "Violet leaf memberi kesan hijau daun."),
    ("Pinus", "Piney", "karakter", "Jarum konifer, hutan dingin", "Fir mengingatkan pada hutan pinus."),
    ("Kayu Krim", "Woody Creamy", "tekstur", "Kayu halus berlapis krim", "Sandalwood terasa kayu krim."),
    ("Kayu Kering", "Dry Woody", "tekstur", "Kayu tanpa manis, serat kering", "Cedar dan oak memberi kayu kering."),
    ("Kulit Halus", "Soft Leather", "tekstur", "Kulit tidak tajam, lebih lembut", "Leather tonka terasa kulit halus."),
    ("Bunga Krim", "Creamy Floral", "karakter", "Bunga lembut berlapis krim", "Tuberose memberi bunga krim yang kuat."),
    ("Bunga Powdery", "Powdery Floral", "karakter", "Bunga berbedak halus", "Heliotrope memadukan bunga dan powdery."),
    ("Buah Berry", "Berry", "karakter", "Berry merah/hitam asam-manis", "Blackcurrant memberi kesan berry."),
    ("Ceri", "Cherry", "karakter", "Buah ceri manis gelap", "Cherry almond cocok untuk gourmand buah."),
    ("Teh", "Tea", "karakter", "Daun teh segar, sedikit pahit", "Matcha memberi kesan teh creamy."),
    ("Susu", "Milky", "tekstur", "Susu lembut, bukan gula", "Milk melembutkan vanilla."),
    ("Alkohol Hangat", "Boozy", "karakter", "Aroma minuman keras hangat", "Cognac memberi kesan boozy pada amber."),
    ("Lokal", "Local-inspired", "tema", "Terinspirasi bahan atau momen Indonesia", "Cempaka cocok untuk tema lokal."),
    ("Musim Semi", "Spring", "musim", "Segar bunga untuk cuaca transisi", "Sakura cocok untuk musim semi."),
    ("Musim Gugur", "Autumn", "musim", "Hangat kayu dan rempah", "Oak cognac cocok untuk musim gugur."),
    ("Fotogenik", "Photogenic", "tema", "Menonjol di kamera dan pencahayaan", "Amber wood fotogenik untuk sesi foto."),
    ("Restock", "Restock", "momen", "Pembelian ulang rutin", "White musk mudah di-restock."),
]

# Riset 03_karakter_marketing.md (2026-11-27), §3. Kalimat pendek 2–8 kata
# untuk copywriter overlay/LIVE. Ini gambaran sensorik/suasana, BUKAN klaim
# komposisi, performa, efek tubuh, atau arketipe resmi/persona demografi.
SENSORIAL_PHRASES = [
    (1, "Quiet Luxurian", "Kain linen tersetrika rapi", "BARU", "—"),
    (2, "Quiet Luxurian", "Cahaya jendela sore", "BARU", "—"),
    (3, "Quiet Luxurian", "Kayu halus tanpa riuh", "BARU", "Kayu, Kayu Krim"),
    (4, "Quiet Luxurian", "Lipatan kemeja bersih", "BARU", "Bersih"),
    (5, "Quiet Luxurian", "Ruang kerja sunyi", "BARU", "Tenang"),
    (6, "Quiet Luxurian", "Sentuhan akhir yang pelan", "BARU", "—"),
    (7, "Quiet Luxurian", "Elegan tanpa perlu sorotan", "BARU", "Mewah"),
    (8, "Modern Romantic", "Kelopak setelah hujan", "BARU", "—"),
    (9, "Modern Romantic", "Mawar dengan embun pagi", "BARU", "Berbunga"),
    (10, "Modern Romantic", "Pelukan kain katun", "BARU", "Krim"),
    (11, "Modern Romantic", "Manis vanila yang lembut", "BARU", "Manis, Krim"),
    (12, "Modern Romantic", "Surat yang belum dikirim", "BARU", "Romantis"),
    (13, "Modern Romantic", "Sore di taman kota", "BARU", "—"),
    (14, "Modern Romantic", "Bunga putih di meja", "BARU", "Berbunga, Bunga Krim"),
    (15, "Night Strategist", "Meja rapat lampu redup", "BARU", "Formal"),
    (16, "Night Strategist", "Rapat yang sudah siap", "BARU", "Formal"),
    (17, "Night Strategist", "Jaket sebelum keluar", "BARU", "—"),
    (18, "Night Strategist", "Langkah di trotoar malam", "BARU", "Malam"),
    (19, "Night Strategist", "Kata yang dipikirkan dulu", "BARU", "—"),
    (20, "Night Strategist", "Bayangan di dinding kantor", "BARU", "Kantor"),
    (21, "Night Strategist", "Selesai sebelum besok pagi", "BARU", "—"),
    (22, "Playful Gourmand", "Sendok karamel hangat", "BARU", "Manis"),
    (23, "Playful Gourmand", "Kue dari oven kecil", "BARU", "Manis"),
    (24, "Playful Gourmand", "Gula tabur di atas", "BARU", "Manis"),
    (25, "Playful Gourmand", "Tawa setelah kopi", "BARU", "Nostalgik"),
    (26, "Playful Gourmand", "Busa susu manis", "BARU", "Susu, Krim Kocok"),
    (27, "Playful Gourmand", "Ceri di ujung lidah", "BARU", "Ceri"),
    (28, "Playful Gourmand", "Main-main di dapur", "BARU", "—"),
    (29, "Clean Minimalist", "Kain setelah dijemur", "BARU", "Bersih"),
    (30, "Clean Minimalist", "Sabun di tangan bersih", "BARU", "Bersih"),
    (31, "Clean Minimalist", "Satu botol untuk harian", "BARU", "Santai, Minimalis"),
    (32, "Clean Minimalist", "Rak yang tidak penuh", "BARU", "Minimalis"),
    (33, "Clean Minimalist", "Pagi tanpa banyak pilihan", "BARU", "Pagi"),
    (34, "Clean Minimalist", "Hembusan tipis di leher", "BARU", "Dekat Kulit, Ringan"),
    (35, "Clean Minimalist", "Putih yang tidak berisik", "BARU", "Minimalis"),
    (36, "Heritage Keeper", "Resin yang disimpan lama", "BARU", "Resin"),
    (37, "Heritage Keeper", "Cerita dari lemari kayu", "BARU", "Kayu, Nostalgik"),
    (38, "Heritage Keeper", "Sore di rumah lama", "BARU", "Nostalgik"),
    (39, "Heritage Keeper", "Mawar dan damar berdampingan", "BARU", "Resin, Berbunga"),
    (40, "Heritage Keeper", "Kain songket di acara keluarga", "BARU", "Lokal"),
    (41, "Heritage Keeper", "Warisan yang dipakai lagi", "BARU", "Nostalgik"),
    (42, "Heritage Keeper", "Aroma attar yang dikenal", "BARU", "Mewah"),
    (43, "Explorer", "Peta di saku jaket", "BARU", "—"),
    (44, "Explorer", "Pintu yang belum dibuka", "BARU", "—"),
    (45, "Explorer", "Angin dari kota baru", "BARU", "Lapang"),
    (46, "Explorer", "Rasa penasaran di perjalanan", "BARU", "—"),
    (47, "Explorer", "Aroma yang sulit ditebak", "BARU", "Dramatis"),
    (48, "Explorer", "Jalan masuk ke hutan", "BARU", "Hijau Daun, Pinus"),
    (49, "Explorer", "Kembali dengan cerita baru", "BARU", "—"),
    (50, "Soft Rebel", "Aturan yang dilipat kecil", "BARU", "—"),
    (51, "Soft Rebel", "Warna yang sengaja beda", "BARU", "Dramatis"),
    (52, "Soft Rebel", "Senyum di balik jaket", "BARU", "—"),
    (53, "Soft Rebel", "Langkah yang tidak searah", "BARU", "—"),
    (54, "Soft Rebel", "Lada di ujung manis", "BARU", "Pedas, Segar-Manis"),
    (55, "Soft Rebel", "Nada yang tidak ikut arus", "BARU", "—"),
    (56, "Soft Rebel", "Gelap yang tetap ramah", "BARU", "Hangat"),
    (57, "Ritualist", "Cangkir teh masih hangat", "BARU", "Teh"),
    (58, "Ritualist", "Tiga napas sebelum mulai", "BARU", "Tenang"),
    (59, "Ritualist", "Lampu kecil di sudut", "BARU", "Tenang"),
    (60, "Ritualist", "Halaman yang dibuka pelan", "BARU", "—"),
    (61, "Ritualist", "Rangkaian pagi yang sama", "BARU", "Pagi"),
    (62, "Ritualist", "Daun kering dalam cangkir", "BARU", "Teh, Herbal"),
    (63, "Ritualist", "Jeda antara dua rapat", "BARU", "Kantor"),
    (64, "Collector", "Rak yang bertambah satu", "BARU", "Restock"),
    (65, "Collector", "Botol kecil untuk dicoba", "BARU", "Workshop"),
    (66, "Collector", "Catatan di kertas kecil", "BARU", "—"),
    (67, "Collector", "Sampel yang disimpan rapi", "BARU", "Workshop"),
    (68, "Collector", "Satu lagi yang berbeda", "BARU", "—"),
    (69, "Collector", "Koleksi yang ikut bertumbuh", "BARU", "Restock"),
    (70, "Collector", "Cukup untuk hari ini", "BARU", "—"),
]

# Riset 03_karakter_marketing.md (2026-11-27), §4. Pagar klaim untuk
# narasi LIVE/theater. Kolom dasar memakai kode sumber S5–S16 pada laporan;
# status verifikasi disalin apa adanya, bukan klaim produk Alkaff.
CLAIM_GUARDS = [
    ("Tahan 24 jam / seharian penuh / 12 jam tanpa top up",
     "Tanpa bukti; angka harus dari uji yang relevan dengan produk",
     "Coba di kulit Anda dan amati sendiri; cocok untuk rutinitas panjang tanpa angka",
     "S6 https://eur-lex.europa.eu/eli/reg/2013/655/oj/eng; S9 https://www.ftc.gov/legal-library/browse/ftc-policy-statement-regarding-advertising-substantiation",
     "2026-11-27", "Terverifikasi (primer)"),
    ("Bebas alergi / hypoallergenic / alergy tested / tidak mungkin gatal",
     "Dilarang/tanpa jaminan",
     "Coba sedikit lebih dulu; lihat daftar bahan pada kemasan",
     "S7 https://www.fda.gov/cosmetics/cosmetics-labeling-claims/hypoallergenic-cosmetics; S5 https://ifrafragrance.org/about-fragrance/this-is-a-fragrance-2",
     "2026-11-27", "Terverifikasi (primer + editorial)"),
    ("Afrodisiak / memicu hasrat / pasangan pasti jatuh cinta",
     "Dilarang sebagai efek tubuh/pikiran",
     "Aroma bunga yang terasa personal; pilihan untuk malam yang rapi",
     "S8 https://www.fda.gov/cosmetics/cosmetic-products/aromatherapy; S10 https://ads.tiktok.com/resources/help/article/tiktok-ads-policy-misleading-and-false-content",
     "2026-11-27", "Terverifikasi (primer + platform)"),
    ("Menghangatkan tubuh / mendinginkan suhu tubuh / menurunkan demam",
     "Dilarang; masuk klaim fungsi tubuh/obat",
     "Kesan resin hangat di hidung; sejuk kaca sebagai gambaran aroma",
     "S8 https://www.fda.gov/cosmetics/cosmetic-products/aromatherapy",
     "2026-11-27", "Terverifikasi (primer)"),
    ("Halal tanpa sertifikat / attar halal hanya karena tradisi",
     "Dilarang tanpa penunjukan resmi",
     "Aroma tradisional berbasis attar; status sertifikasi dicek pada dokumen produk",
     "S13 https://bpjph.halal.go.id/read/penyesuaian-penahapan-kewajiban-sertifikasi-halal-diatur-dalam-pp-40-tahun-2026-begini-rinciannya; S14 https://jdih.halal.go.id/api/jdih/pdf?path=jdih%2Fdokumen%2F1792631903741_salinan_-_370.2026._pedoman_pelaksanaan_sjph_kosmetik.pdf",
     "2026-11-27", "Terverifikasi (primer; S14 cuplikan PDF)"),
    ("BPOM / disetujui BPOM / lolos uji pemerintah tanpa nomor",
     "Dilarang; otoritas tidak memberi stempel klaim produk",
     "Informasi Produk dan nomor notifikasi ditampilkan apa adanya; bila kosong, jangan disebut",
     "S12 https://standar-otskk.pom.go.id/berita/siaran-pers-nomor-hm-01-1-2-05-25-104-tanggal-15-mei-2025; S6 https://eur-lex.europa.eu/eli/reg/2013/655/oj/eng",
     "2026-11-27", "Terverifikasi (primer)"),
    ("Harga resmi / harga brand / promo resmi tanpa sumber",
     "Dilarang tanpa sumber; platform melarang info harga tidak konsisten",
     "Harga dan stok dicek pada katalog/toko resmi saat LIVE; tidak menyebut angka",
     "S10 https://ads.tiktok.com/resources/help/article/tiktok-ads-policy-misleading-and-false-content",
     "2026-11-27", "Terverifikasi (platform) + prinsip internal"),
    ("Bersertifikat IFRA tanpa dokumen pembuat campuran wewangian",
     "Tanpa bukti; jangan menyiratkan stempel IFRA",
     "Dapat diminta: dokumen kesesuaian dari pembuat campuran wewangian, bila tersedia",
     "S5 https://ifrafragrance.org/about-fragrance/this-is-a-fragrance-2",
     "2026-11-27", "Terverifikasi (editorial)"),
    ("Detoks / melancarkan peredaran darah / mengatasi stres / menyembuhkan insomnia",
     "Dilarang; klaim terapi/obat",
     "Suasana lembut, tidak mengganggu; ritual teh yang sederhana",
     "S8 https://www.fda.gov/cosmetics/cosmetic-products/aromatherapy",
     "2026-11-27", "Terverifikasi (primer)"),
    ("100% natural / chemical-free / non-toxic / organik tanpa dokumen",
     "Dilarang/menyesatkan; istilah pemasaran tanpa definisi ketat",
     "Terinspirasi bunga dan kayu; perpaduan note alami dan molekul wewangian",
     "S5 https://ifrafragrance.org/about-fragrance/this-is-a-fragrance-2; S6 https://eur-lex.europa.eu/eli/reg/2013/655/oj/eng",
     "2026-11-27", "Terverifikasi (editorial + primer)"),
    ("Paling wangi / No. 1 di TikTok / terbaik di dunia",
     "Dilarang sebagai istilah absolut",
     "Salah satu opsi yang sering dipilih untuk malam; cocok untuk yang suka amber",
     "S10 https://ads.tiktok.com/resources/help/article/tiktok-ads-policy-misleading-and-false-content; S6 https://eur-lex.europa.eu/eli/reg/2013/655/oj/eng",
     "2026-11-27", "Terverifikasi (platform + primer)"),
    ("Cocok untuk semua kulit / aman untuk bayi / aman untuk ibu hamil",
     "Dilarang/tanpa bukti; sensitivitas individu berbeda",
     "Coba dalam jumlah kecil sesuai petunjuk penggunaan; konsultasikan bila ada kekhawatiran",
     "S7 https://www.fda.gov/cosmetics/cosmetics-labeling-claims/hypoallergenic-cosmetics; S5 https://ifrafragrance.org/about-fragrance/this-is-a-fragrance-2",
     "2026-11-27", "Terverifikasi (primer + editorial)"),
    ("EDP pasti lebih tahan dari EDT / ekstrak 30% pasti lebih kuat",
     "Tanpa bukti; jangan menjanjikan performa dari label saja",
     "Bandingkan pada kulit Anda; sebutkan label konsentrasi apa adanya",
     "S6 https://eur-lex.europa.eu/eli/reg/2013/655/oj/eng",
     "2026-11-27", "Terverifikasi (primer) + prinsip internal"),
    ("Komposisi persis brand X / dupe identik / formula resmi pabrik",
     "Dilarang tanpa data resmi",
     "Terinspirasi keluarga aroma; daftar note bersifat edukatif",
     "S6 https://eur-lex.europa.eu/eli/reg/2013/655/oj/eng; S9 https://www.ftc.gov/legal-library/browse/ftc-policy-statement-regarding-advertising-substantiation",
     "2026-11-27", "Terverifikasi (primer)"),
    ("Sebelum/sesudah dengan filter / warna botol membuktikan mutu",
     "Dilarang; menyesatkan secara visual",
     "Tampilkan kartu notes dan kondisi pencahayaan apa adanya",
     "S10 https://ads.tiktok.com/resources/help/article/tiktok-ads-policy-misleading-and-false-content; S11 https://www.tiktok.com/community-guidelines/en/integrity-authenticity",
     "2026-11-27", "Terverifikasi (platform)"),
    ("Auto-DM dari komentar LIVE / DM massal / interaksi otomatis",
     "Dilarang oleh alur platform",
     "Penonton mengetik keyword; balasan dikirim dalam jalur DM yang sah",
     "S11 https://www.tiktok.com/community-guidelines/en/integrity-authenticity; S16 dokumentasi internal LIVE",
     "2026-11-27", "Terverifikasi (platform) + prinsip internal"),
    ("Aroma menenangkan pikiran / membuat tidur lebih nyenyak",
     "Dilarang sebagai klaim terapi",
     "Suasana lembut, tidak mengganggu; cocok untuk rutinitas malam",
     "S8 https://www.fda.gov/cosmetics/cosmetic-products/aromatherapy",
     "2026-11-27", "Terverifikasi (primer)"),
    ("Gratis / diskon / angka stok atau ketersediaan belum dicek",
     "Dilarang bila tidak cocok dengan katalog",
     "CTA diarahkan ke pengecekan katalog; tidak menyebut angka",
     "S10 https://ads.tiktok.com/resources/help/article/tiktok-ads-policy-misleading-and-false-content",
     "2026-11-27", "Terverifikasi (platform) + prinsip internal"),
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
    ("Sakura Pear", "Floral Putih & Bouquet", "Sakura 3 · Pear 2 · Jasmine 2 · White Musk 2", "Bunga lembut, manis ringan", "Hadiah, siang, foto", "5–12 hari", "Cek ketersediaan referensi sakura."),
    ("Cempaka Sandal", "Floral Putih & Bouquet", "Cempaka 3 · Sandalwood 2 · Rose 1 · Musk 2", "Bunga Asia, krim, hangat", "Hadiah, malam santai", "10–18 hari", "Cempaka kuat; uji dosis."),
    ("Ambergris Marine", "Amber / Oriental", "Ambergris 2 · Marine 3 · Bergamot 2 · White Musk 2", "Laut hangat, asin-manis", "Pantai, malam", "14–21 hari", "Ambergris langka; pakai akorda bila perlu."),
    ("Ambroxan Clean", "Musk & Powdery", "Ambroxan 3 · White Musk 3 · Bergamot 2 · Cedar 1", "Bersih, proyeksi modern", "Kantor, live", "10–18 hari", "Ambroxan kuat; hindari overdosage."),
    ("Blackcurrant Rose", "Fruity", "Blackcurrant 3 · Rose 2 · Vanilla 2 · Musk 2", "Berry-asam, bunga, manis", "Kencan, siang", "7–14 hari", "Berry bisa menguning; cek stabilitas."),
    ("Cherry Almond", "Gourmand", "Cherry 3 · Almond 2 · Vanilla 2 · Tonka 1", "Ceri kacang, dessert", "Malam, hujan", "10–18 hari", "Almond: perhatikan risiko alergi."),
    ("Green Tea Matcha", "Citrus Segar", "Green Tea 2 · Matcha 2 · Bergamot 2 · Cream 2", "Teh hijau krim, tenang", "Pagi, belajar", "5–12 hari", "Jangan klaim detoks."),
    ("Lemongrass Mint", "Aromatic Herbal", "Lemongrass 3 · Mint 2 · Lime 2 · Musk 2", "Segar tajam, herbal dingin", "Olahraga, siang", "4–10 hari", "Mint tajam; uji kepekaan kulit."),
    ("Oak Cognac", "Woody", "Oak 3 · Cognac 2 · Tonka 2 · Leather 1", "Kayu anggur hangat", "Malam, formal", "14–21 hari", "Cognac bisa kuat; seimbangkan."),
    ("Fir Resin", "Amber / Oriental", "Fir 3 · Fir Resin 2 · Amber 2 · Cedar 2", "Hutan resin, hangat", "Musim hujan, malam", "14–21 hari", "Resin lengket; cek stabilitas."),
    ("Sea Salt Driftwood", "Aquatik / Laut", "Sea Salt 2 · Driftwood 3 · Marine 2 · White Musk 2", "Asin, kayu hanyut", "Pantai, liburan", "7–14 hari", "Garam menarik lembap; simpan kering."),
    ("Tuberose Cream", "Floral Putih & Bouquet", "Tuberose 3 · Cream 2 · Jasmine 1 · Musk 2", "Bunga putih krim kuat", "Malam, foto", "14–21 hari", "Tuberose sangat kuat; dosis kecil."),
    ("Violet Leaf Iris", "Musk & Powdery", "Violet Leaf 3 · Iris 2 · Violet 2 · White Musk 2", "Hijau powdery elegan", "Kantor, siang", "10–18 hari", "Iris mahal; pakai sebagai aksen."),
    ("Grapefruit Neroli", "Citrus Segar", "Grapefruit 3 · Neroli 2 · Blood Orange 2 · Musk 2", "Jeruk pahit-manis, bunga", "Pagi, kantor", "5–12 hari", "Citrus cepat hilang; sarankan top up."),
    ("Bamboo Lotus", "Aquatik / Laut", "Bamboo 3 · Lotus 2 · Green Tea 2 · White Musk 2", "Hijau-air tenang", "Siang, santai", "5–12 hari", "Hindari klaim kesehatan."),
    ("Heliotrope Milk", "Gourmand", "Heliotrope 3 · Milk 2 · Vanilla 2 · Almond 1", "Bunga powdery susu", "Malam, musim hujan", "10–18 hari", "Perhatikan alergi susu/kacang."),
    # Riset 01_perbendaharaan_aroma.md (2026-11-27). Tanpa rasio/dosis:
    # kolom ketiga adalah daftar kesan, bukan resep produksi.
    ("Chypre Labdanum", "Woody", "Labdanum + Bergamot + Oakmoss + Patchouli (tanpa rasio)", "Segar-kering, hangat, klasik", "Malam, formal, signature", "Tidak ditentukan", "Gambaran keluarga; bukan komposisi resmi."),
    ("Fougere Coumarin", "Aromatic Herbal", "Lavender + Geranium + Oakmoss + Coumarin (tanpa rasio)", "Herbal, jerami-manis, rapi", "Kantor, harian", "Tidak ditentukan", "Coumarin: cek batas IFRA sebelum produksi."),
    ("Ambre Resin", "Amber / Oriental", "Labdanum + Benzoin + Vanilla (tanpa rasio)", "Resin hangat-manis, krim", "Malam, musim hujan, hadiah", "Tidak ditentukan", "Gambaran keluarga; bukan formula produksi."),
    ("Galbanum Green Spark", "Citrus Segar", "Galbanum + Bergamot + Oakmoss (tanpa rasio)", "Hijau pahit menyengat, chypre kering", "Siang, workshop hijau", "Tidak ditentukan", "Galbanum kuat; uji dosis."),
    ("Vetiver Citrus Pepper", "Woody", "Vetiver + Bergamot + Black Pepper (tanpa rasio)", "Kayu tanah kering, sitrus, lada", "Kantor, siang", "Tidak ditentukan", "Perlu verifikasi ahli; bukan uji lab."),
    ("Incense Resin Noir", "Amber / Oriental", "Frankincense + Labdanum + Elemi (tanpa rasio)", "Dupa kayu-resin, drydown ambery", "Malam, acara, tradisi", "Tidak ditentukan", "Jangan disamakan dengan satu bahan tunggal."),
    ("Tiare Coconut Solar", "Floral Putih & Bouquet", "Tiare + Coconut + Vanilla (tanpa rasio)", "Bunga putih manis, monoi", "Pantai, liburan, after-bath", "Tidak ditentukan", "Coconut perlu verifikasi; bukan klaim produk."),
    ("Frangipani Tropical Night", "Floral Putih & Bouquet", "Frangipani + Coconut + Fig (tanpa rasio)", "Kamboja krim-peachy, tropis", "Malam tropis, liburan", "Tidak ditentukan", "Sillage kuat; sarankan tes."),
    ("Ylang Jasmine Solar", "Floral Putih & Bouquet", "Ylang-Ylang + Jasmine + Sandalwood (tanpa rasio)", "Bunga krim berat, floral surya", "Malam, hadiah", "Tidak ditentukan", "Ylang dominan; dosis kecil."),
    ("Muguet Green Spring", "Floral Putih & Bouquet", "Lily of the Valley + Green Notes + Lemon (tanpa rasio)", "Bunga hijau-manis, udara semi", "Siang, hadiah", "Tidak ditentukan", "Muguet umumnya direkonstruksi."),
    ("Ozonic Rain Air", "Aquatik / Laut", "Ozone + Marine + White Musk (tanpa rasio)", "Udara basah bersih, transparan", "Setelah hujan, laundry, live", "Tidak ditentukan", "Bukan dupa laut asin."),
    ("Guaiac Smoke Leather", "Woody", "Guaiac Wood + Leather + Tonka (tanpa rasio)", "Kayu berasap, kulit, tembakau", "Malam, jaket, foto", "Tidak ditentukan", "Perlu verifikasi ahli; pakai aksen."),
    ("Juniper Pine Aromatic", "Aromatic Herbal", "Juniper + Fir + Lime (tanpa rasio)", "Getah pinus segar, pahit, gin", "Siang, olahraga", "Tidak ditentukan", "Dosis kecil."),
    ("Licorice Wood Gourmand", "Gourmand", "Licorice + Cedar + Tonka (tanpa rasio)", "Aniseed-karamel dengan kayu", "Malam, musim hujan", "Tidak ditentukan", "Hindari klaim kesehatan."),
    ("Marshmallow Vanilla Cloud", "Gourmand", "Marshmallow + Vanilla + Cream (tanpa rasio)", "Busa gula powdery, vanili krim", "Malam, dessert", "Tidak ditentukan", "Jangan ditujukan untuk bayi tanpa uji."),
    ("Fig Coconut Shade", "Fruity", "Fig + Coconut + Green Notes (tanpa rasio)", "Daun ara sejuk, buah manis, kelapa", "Siang, konten teduh", "Tidak ditentukan", "Coconut perlu verifikasi."),
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
    ("Parfum Sakura", "Pembeli hadiah", "Suka bunga lembut", "Floral Putih & Bouquet", "sakura, pear, jasmine", "SAKURA", "Flatlay bunga merah muda", "Hadiah, foto", "Cek stok sakura."),
    ("Parfum Cempaka Lokal", "Pembeli lokal", "Cari aroma Nusantara", "Floral Putih & Bouquet", "cempaka, sandalwood, rose", "CEMPAKA", "Konten bunga lokal", "Hadiah, malam", "Jangan klaim asal-usul tanpa data."),
    ("Parfum Laut Asin", "Traveler", "Ingin kesan pantai nyata", "Aquatik / Laut", "sea salt, driftwood, marine", "GARAM", "Vlog pantai", "Pantai", "Garam bukan klaim mineral kesehatan."),
    ("Parfum Amber Modern", "Profesional 25–40", "Ingin elegan tidak berat", "Musk & Powdery", "ambroxan, white musk, cedar", "AMBER", "Lookbook minimal", "Kantor, malam", "Ambroxan kuat; dosis kecil."),
    ("Parfum Berry Manis", "Gen Z", "Suka buah beri", "Fruity", "blackcurrant, rose, vanilla", "BERRY", "Warna ungu cerah", "Siang, kampus", "Stabilitas warna perlu dicek."),
    ("Parfum Ceri Almond", "Pencinta dessert", "Manis kacang buah", "Gourmand", "cherry, almond, vanilla", "CHERRY", "Dessert flatlay", "Malam", "Perhatikan alergi kacang."),
    ("Parfum Teh Hijau", "Pembeli tenang", "Ingin aroma ringan", "Citrus Segar", "green tea, matcha, bergamot", "TEH", "Ritual teh", "Pagi, belajar", "Hindari klaim detoks."),
    ("Parfum Serai Segar", "Pembeli aktif", "Butuh segar tajam", "Aromatic Herbal", "lemongrass, mint, lime", "SERAI", "Olahraga", "Siang, gym", "Mint bisa menyengat."),
    ("Parfum Kayu Oak", "Pria formal", "Kayu hangat anggur", "Woody", "oak, cognac, tonka", "OAK", "Meeting malam", "Formal", "Jangan klaim usia tanpa bukti."),
    ("Parfum Hutan Pinus", "Pecinta alam", "Aroma hutan dingin", "Amber / Oriental", "fir, fir resin, amber", "PINUS", "Camping, hujan", "Musim hujan", "Resin lengket; simpan baik."),
    ("Parfum Tuberose", "Pembeli berani", "Bunga kuat", "Floral Putih & Bouquet", "tuberose, cream, jasmine", "TUBEROSE", "Close-up bunga", "Malam, foto", "Sillage kuat; sarankan tes."),
    ("Parfum Violet Powdery", "Kantoran", "Elegan powdery", "Musk & Powdery", "violet leaf, iris, musk", "VIOLET", "Flatlay ungu", "Kantor", "Iris mahal; cek harga."),
    ("Parfum Grapefruit", "Pembeli segar", "Jeruk pahit-manis", "Citrus Segar", "grapefruit, neroli, blood orange", "GRAPEFRUIT", "Citrus slice", "Pagi", "Cepat hilang; top up."),
    ("Parfum Bambu Lotus", "Pembeli tenang", "Hijau-air minimalis", "Aquatik / Laut", "bamboo, lotus, green tea", "BAMBU", "Konten zen", "Siang", "Hindari klaim meditasi/kesehatan."),
    ("Parfum Heliotrope Susu", "Pencinta manis lembut", "Bunga powdery", "Gourmand", "heliotrope, milk, vanilla", "HELIOTROPE", "Dessert susu", "Malam", "Alergi susu/kacang; cantumkan."),
    ("Parfum Fotogenik", "Content creator", "Butuh visual premium", "Amber / Oriental", "amberwood, ambroxan, musk", "SHOOT", "Behind the scene", "Sesi foto", "Pencahayaan bukan bukti kualitas."),
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

    # 06 frasa sensorik dari riset 03 (bukan klaim, bukan komposisi resmi)
    phrase_rows = [
        [str(no), archetype, phrase, status, similar,
         "Gambaran sensorik/suasana; bukan komposisi, performa, atau efek tubuh.",
         "research/03_karakter_marketing.md", "2026-11-27"]
        for no, archetype, phrase, status, similar in SENSORIAL_PHRASES
    ]
    write_csv("06_frasa_sensorik.csv",
              ["#", "Arketipe (alat bercerita)", "Frasa", "Status", "Mirip Deskriptor",
               "Batasan", "Sumber", "Tanggal Akses"],
              phrase_rows)

    # 07 pagar klaim dari riset 03 (aturan, bukan janji produk)
    guard_rows = [
        [risky, status, safe, basis, access, verification,
         "Diterapkan pada narasi overlay/LIVE; bukan bukti mutu produk Alkaff."]
        for risky, status, safe, basis, access, verification in CLAIM_GUARDS
    ]
    write_csv("07_pagar_klaim.csv",
              ["Klaim Berisiko", "Status", "Alternatif Aman", "Dasar / URL Sumber",
               "Tanggal Akses", "Status Verifikasi", "Batasan"],
              guard_rows)

    # 08 bundle JSON untuk aplikasi
    bundle = {
        "sumber": "katalog_parfum_alkaff_odoo.csv",
        "jumlah_produk": len(parsed),
        "keluarga": fam_rows and [dict(zip(["Keluarga","Deskriptor","Notes Khas","Karakter","Momen","Ketahanan Umum","Sillage","Tema Konten","Contoh Internal Reference","Jumlah Produk"], r)) for r in fam_rows],
        "notes": [dict(zip(["Note","Kunci","Alias","Layer Dominan","Keluarga Note","Intensitas","Ketahanan","Deskripsi","Pasangan","Jumlah Produk","Contoh Internal Reference"], r)) for r in note_rows],
        "deskriptor": [dict(zip(["Deskriptor","English","Dimensi","Makna","Contoh Kalimat"], d)) for d in DESCRIPTORS],
        "accord": [dict(zip(["Nama","Keluarga","Rasio","Karakter","Momen","Maturasi","Keamanan","Contoh Internal Reference","Status"], r)) for r in accord_rows],
        "tema": [dict(zip(["Tema","Persona","Trigger","Keluarga","Notes Kunci","Contoh Internal Reference","CTA","Format","Momen","Risiko","Catatan LIVE"], r)) for r in theme_rows],
        "frasa": [dict(zip(["#","Arketipe","Frasa","Status","Mirip Deskriptor","Batasan","Sumber","Tanggal Akses"], r)) for r in phrase_rows],
        "pagarKlaim": [dict(zip(["Klaim Berisiko","Status","Alternatif Aman","Dasar","Tanggal Akses","Status Verifikasi","Batasan"], r)) for r in guard_rows],
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
          f"deskriptor: {len(DESCRIPTORS)} | accord: {len(accord_rows)} | tema: {len(theme_rows)} | "
          f"frasa: {len(phrase_rows)} | pagar klaim: {len(guard_rows)}")
    print("Referensi tervalidasi:", len(all_refs))


if __name__ == "__main__":
    main()
