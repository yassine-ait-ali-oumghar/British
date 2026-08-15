import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'British_Style.settings')
django.setup()

from apps.core.models import Product

def run():
    shades_data = {
        # --- COLORATIONS ---
        "L'Oréal Professionnel Coloration Inoa / Majirel": [
            {"name": "Noir Profond 1.0", "hex": "#1B1B1B"},
            {"name": "Brun Châtain 4.0", "hex": "#4A2E2B"},
            {"name": "Châtain Clair 5.0", "hex": "#6A4035"},
            {"name": "Blond Cendré 7.1", "hex": "#A88D67"},
            {"name": "Blond Doré 8.3", "hex": "#D1B26F"}
        ],
        "Inebrya Coloration Crème Professionnelle": [
            {"name": "Châtain Marron 4.3", "hex": "#5C3A21"},
            {"name": "Chocolat Intense 5.35", "hex": "#4E2F1D"},
            {"name": "Blond Suédois 10.0", "hex": "#E8D8B0"},
            {"name": "Rouge Acajou 6.66", "hex": "#8B1E1E"}
        ],
        "Garnier Olia Coloration aux Huiles de Fleurs": [
            {"name": "Noir Pur 1.0", "hex": "#121212"},
            {"name": "Châtain Chocolat 5.3", "hex": "#54332B"},
            {"name": "Miel Cendré 8.13", "hex": "#C9A769"},
            {"name": "Rouge Intense 6.60", "hex": "#9E1B1B"}
        ],

        # --- ONGLERIE & VERNIS ---
        "Vernis Gel UV/LED Construction (Toutes Couleurs)": [
            {"name": "Clear Translucide", "hex": "#F0F4F8"},
            {"name": "Cover Nude", "hex": "#E5B9A8"},
            {"name": "Milky White", "hex": "#FDFBF7"},
            {"name": "Soft Pink", "hex": "#F4C2C2"}
        ],
        "BIAB Builder In A Bottle (Nuances Nude & Rose)": [
            {"name": "Teddy Nude", "hex": "#D7B19D"},
            {"name": "Dolly Pink", "hex": "#ECA1B5"},
            {"name": "Milky White", "hex": "#F5F5F0"},
            {"name": "Lady Top Coat", "hex": "#FFE4E1"}
        ],
        "Vernis Permanent Haute Brilliance (Nuancier Complet)": [
            {"name": "Rose Poudré", "hex": "#F4C2C2"},
            {"name": "Rouge Cerise", "hex": "#990000"},
            {"name": "Prune Sombre", "hex": "#4A0E2E"},
            {"name": "Coral d'Été", "hex": "#FF6F61"}
        ],
        "Vernis Semi-Permanent Pro (Palette Toutes Couleurs)": [
            {"name": "Rouge Passion", "hex": "#B22222"},
            {"name": "Nude Rosé", "hex": "#E8C5C8"},
            {"name": "French Blanc", "hex": "#FFFFFF"},
            {"name": "Noir Pailleté", "hex": "#222222"},
            {"name": "Bordeaux Profond", "hex": "#58111A"}
        ],

        # --- MAQUILLAGE & LÈVRES ---
        "Flormar Silk Matte Liquid Lipstick": [
            {"name": "Terracotta 012", "hex": "#C86A4B"},
            {"name": "Rose Nuance 005", "hex": "#D88B97"},
            {"name": "Rouge Mat 001", "hex": "#A31D24"}
        ],
        "Charlotte Tilbury Matte Revolution Lipstick (Pillow Talk)": [
            {"name": "Pillow Talk Original", "hex": "#C08081"},
            {"name": "Pillow Talk Medium", "hex": "#A25F60"},
            {"name": "Pillow Talk Intense", "hex": "#7E3F42"}
        ],
        "Rare Beauty Soft Pinch Liquid Blush": [
            {"name": "Hope (Nude Mauve)", "hex": "#C38B8B"},
            {"name": "Happy (Dewy Pink)", "hex": "#F497AC"},
            {"name": "Joy (Peach)", "hex": "#F08D70"}
        ],
        "Dior Beauty Dior Addict Lip Glow Oil": [
            {"name": "001 Pink", "hex": "#FFB6C1"},
            {"name": "012 Rosewood", "hex": "#C87D7E"},
            {"name": "015 Cherry", "hex": "#D22B2B"}
        ],
        "Fenty Beauty Gloss Bomb Universal Lip Luminizer": [
            {"name": "Fenty Glow", "hex": "#B87352"},
            {"name": "Fussy Pink", "hex": "#E4A7B5"},
            {"name": "Glass Slipper", "hex": "#FFFFFF"}
        ],
        "Benefit Benetint Liquid Lip & Cheek Stain": [
            {"name": "Benetint Rose", "hex": "#CE2029"},
            {"name": "ChaCha Tint Mango", "hex": "#FF6F59"},
            {"name": "Flora Tint Spiced Rose", "hex": "#A3485E"}
        ]
    }

    count = 0
    for name, shades in shades_data.items():
        prods = Product.objects.filter(name=name)
        for p in prods:
            p.shades = shades
            p.save()
            count += 1
            print(f"[OK] Added {len(shades)} shades for {p.name}")

    print(f"\nDone! Updated shades for {count} products in PostgreSQL.")

if __name__ == '__main__':
    run()
