import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'British_Style.settings')
import django
django.setup()

from apps.core.models import Product

def run():
    print("Clearing existing products...")
    Product.objects.all().delete()

    products_data = [
        # ==========================================
        # 1. CHEVEUX & SOINS (HAIR CARE)
        # ==========================================
        {
            'name': 'Olaplex No.3 Hair Perfector',
            'category': 'Cheveux',
            'price': 380,
            'image_url': 'https://images.unsplash.com/photo-1535585209827-a15fcdbc4c2d?auto=format&fit=crop&w=600&q=80',
            'description': 'Soin réparateur avant-shampoing breveté qui répare les liaisons capillaires abîmées.'
        },
        {
            'name': 'Olaplex No.7 Bonding Oil',
            'category': 'Cheveux',
            'price': 390,
            'image_url': 'https://images.unsplash.com/photo-1526947425960-945c6e72858f?auto=format&fit=crop&w=600&q=80',
            'description': 'Huile de coiffage réparatrice ultra-légère, apporte une brillance miroir et protection thermique 232°C.'
        },
        {
            'name': 'Garnier Ultra Doux Masque Huile d\'Argan & Camélia',
            'category': 'Cheveux',
            'price': 90,
            'image_url': 'https://images.unsplash.com/photo-1520340356584-f9917d1eea6f?auto=format&fit=crop&w=600&q=80',
            'description': 'Masque réconfortant aux huiles merveilleuses pour nourrir intensément les cheveux secs.'
        },
        {
            'name': 'L\'Oréal Paris Elseve Extraordinaire Huile de Soin',
            'category': 'Cheveux',
            'price': 140,
            'image_url': 'https://images.unsplash.com/photo-1526947425960-945c6e72858f?auto=format&fit=crop&w=600&q=80',
            'description': 'Soin sublimateur enrichi aux 6 huiles de fleurs rares pour une matière cheveux soyeuse.'
        },
        {
            'name': 'Salvatore Tanino Therapy Treatment (Taninoplastie)',
            'category': 'Cheveux',
            'price': 1100,
            'image_url': 'https://images.unsplash.com/photo-1527799820374-dcf8d9d4a388?auto=format&fit=crop&w=600&q=80',
            'description': 'Soin lissant professionnel Taninoplastie naturelle aux tanins végétaux sans formol.'
        },
        {
            'name': 'Kératine Pure Soin Réparateur Intense',
            'category': 'Cheveux',
            'price': 650,
            'image_url': 'https://images.unsplash.com/photo-1562322140-8baeececf3df?auto=format&fit=crop&w=600&q=80',
            'description': 'Traitement concentré en kératine végétale pour lisser, gainer et réparer la fibre capillaire.'
        },
        {
            'name': 'L\'Oréal Professionnel Absolut Repair Molecular',
            'category': 'Cheveux',
            'price': 420,
            'image_url': 'https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?auto=format&fit=crop&w=600&q=80',
            'description': 'Soin sérum à rincer qui restaure la structure moléculaire des cheveux très abîmés.'
        },
        {
            'name': 'L\'Oréal Professionnel Metal Detox Masque',
            'category': 'Cheveux',
            'price': 450,
            'image_url': 'https://images.unsplash.com/photo-1535585209827-a15fcdbc4c2d?auto=format&fit=crop&w=600&q=80',
            'description': 'Masque protecteur anti-dépôt de métal pour préserver l\'éclat des colorations et balayages.'
        },
        {
            'name': 'Kérastase Elixir Ultime L\'Huile Originale',
            'category': 'Cheveux',
            'price': 590,
            'image_url': 'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=600&q=80',
            'description': 'Huile capillaire sublimatrice rechargeable infusée à l\'huile de camélia sauvage.'
        },
        {
            'name': 'Kérastase Bain Chronologiste',
            'category': 'Cheveux',
            'price': 410,
            'image_url': 'https://images.unsplash.com/photo-1520340356584-f9917d1eea6f?auto=format&fit=crop&w=600&q=80',
            'description': 'Shampoing régénérant jeunesse enrichi en acide hyaluronique, abyssine et vitamine E.'
        },
        {
            'name': 'Pantene Pro-V Huile Réparatrice Soie & Kératine',
            'category': 'Cheveux',
            'price': 110,
            'image_url': 'https://images.unsplash.com/photo-1535585209827-a15fcdbc4c2d?auto=format&fit=crop&w=600&q=80',
            'description': 'Elixir capillaire nourrissant instantané pour sublimer les pointes et éviter les fourches.'
        },
        {
            'name': 'Gisou Honey Infused Hair Oil',
            'category': 'Cheveux',
            'price': 680,
            'image_url': 'https://images.unsplash.com/photo-1601049541289-9b1b7bbbfe19?auto=format&fit=crop&w=600&q=80',
            'description': 'Huile capillaire iconique au miel pur du Jardin Mirsalehi pour hydrater et faire briller.'
        },
        {
            'name': 'Shiseido Fino Premium Touch Hair Mask',
            'category': 'Cheveux',
            'price': 220,
            'image_url': 'https://images.unsplash.com/photo-1631729371254-42c2892f0e6e?auto=format&fit=crop&w=600&q=80',
            'description': 'Masque réparateur japonais culte à la gelée royale pour des cheveux soyeux et doux.'
        },

        # ==========================================
        # 2. VISAGE & SKINCARE (SKINCARE)
        # ==========================================
        {
            'name': 'La Roche-Posay Effaclar Duo+ M Unifiant',
            'category': 'Visage & Skincare',
            'price': 240,
            'image_url': 'https://images.unsplash.com/photo-1571781926291-c477ebfd024b?auto=format&fit=crop&w=600&q=80',
            'description': 'Soin complet anti-imperfections et anti-marques pour peaux à tendance acnéique.'
        },
        {
            'name': 'La Roche-Posay Cicaplast Baume B5+',
            'category': 'Visage & Skincare',
            'price': 160,
            'image_url': 'https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?auto=format&fit=crop&w=600&q=80',
            'description': 'Baume apaisant réparateur multi-indications pour peaux irritées ou fragilisées.'
        },
        {
            'name': 'La Mer Crème de la Mer (30ml)',
            'category': 'Visage & Skincare',
            'price': 2400,
            'image_url': 'https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&w=600&q=80',
            'description': 'Crème régénérante d\'exception infusée au Miracle Broth concentré de mer.'
        },
        {
            'name': 'Medicube Age-R Booster Pro Gel Serum',
            'category': 'Visage & Skincare',
            'price': 490,
            'image_url': 'https://images.unsplash.com/photo-1696497327672-2bdce2e033dd?auto=format&fit=crop&w=600&q=80',
            'description': 'Sérum booster au collagène coréen pour raffermir et illuminer le teint.'
        },
        {
            'name': 'Avène Cicalfate+ Crème Réparatrice',
            'category': 'Visage & Skincare',
            'price': 150,
            'image_url': 'https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?auto=format&fit=crop&w=600&q=80',
            'description': 'Soin apaisant et réparateur riche en eau thermale d\'Avène.'
        },
        {
            'name': 'Anua Heartleaf 77% Soothing Toner',
            'category': 'Visage & Skincare',
            'price': 280,
            'image_url': 'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=600&q=80',
            'description': 'Toner coréen apaisant infusé à 77% d\'extrait de Heartleaf pour calmer les rougeurs.'
        },
        {
            'name': 'Laneige Lip Sleeping Mask Berry',
            'category': 'Visage & Skincare',
            'price': 250,
            'image_url': 'https://images.unsplash.com/photo-1696497327672-2bdce2e033dd?auto=format&fit=crop&w=600&q=80',
            'description': 'Masque de nuit nourrissant pour les lèvres aux extraits de baies sauvages.'
        },
        {
            'name': 'Skin1004 Madagascar Centella Ampoule',
            'category': 'Visage & Skincare',
            'price': 260,
            'image_url': 'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=600&q=80',
            'description': 'Sérum 100% extrait de Centella Asiatica pure pour réparer la barrière cutanée.'
        },
        {
            'name': 'Beauty of Joseon Relief Sun Rice + Probiotics',
            'category': 'Visage & Skincare',
            'price': 230,
            'image_url': 'https://images.unsplash.com/photo-1616394584738-fc6e612e71b9?auto=format&fit=crop&w=600&q=80',
            'description': 'Écran solaire coréen SPF50+ ultra-léger enrichi en extrait de riz et probiotiques.'
        },
        {
            'name': 'Bioderma Sensibio H2O Eau Micellaire (500ml)',
            'category': 'Visage & Skincare',
            'price': 190,
            'image_url': 'https://images.unsplash.com/photo-1571781926291-c477ebfd024b?auto=format&fit=crop&w=600&q=80',
            'description': 'Eau micellaire démaquillante dermatologique référence des peaux sensibles.'
        },

        # ==========================================
        # 3. MAQUILLAGE (MAKEUP)
        # ==========================================
        {
            'name': 'Huda Beauty Easy Bake Loose Powder',
            'category': 'Maquillage',
            'price': 480,
            'image_url': 'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=600&q=80',
            'description': 'Poudre libre fixatrice effet floutant et longue tenue sans transfert.'
        },
        {
            'name': 'Charlotte Tilbury Hollywood Flawless Filter',
            'category': 'Maquillage',
            'price': 590,
            'image_url': 'https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?auto=format&fit=crop&w=600&q=80',
            'description': 'Booster de teint hybride effet filtre illuminateur instantané.'
        },
        {
            'name': 'Charlotte Tilbury Matte Revolution Lipstick (Pillow Talk)',
            'category': 'Maquillage',
            'price': 420,
            'image_url': 'https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=600&q=80',
            'description': 'Rouge à lèvres mat hydratant teinte Nude iconique Pillow Talk.'
        },
        {
            'name': 'Make Up For Ever HD Skin Foundation',
            'category': 'Maquillage',
            'price': 520,
            'image_url': 'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?auto=format&fit=crop&w=600&q=80',
            'description': 'Fond de teint fluide imperceptible couvrance modulable tenue 24h.'
        },
        {
            'name': 'Benefit Benetint Liquid Lip & Cheek Stain',
            'category': 'Maquillage',
            'price': 340,
            'image_url': 'https://images.unsplash.com/photo-1512496015851-a90fb38ba796?auto=format&fit=crop&w=600&q=80',
            'description': 'Eau de teint rosée joues et lèvres effet bonne mine longue durée.'
        },
        {
            'name': 'Dior Beauty Dior Addict Lip Glow Oil',
            'category': 'Maquillage',
            'price': 510,
            'image_url': 'https://images.unsplash.com/photo-1589525231707-f2de2428f59c?auto=format&fit=crop&w=600&q=80',
            'description': 'Huile à lèvres nourrisante et brillante infusée à l\'huile de cerise.'
        },
        {
            'name': 'Rare Beauty Soft Pinch Liquid Blush',
            'category': 'Maquillage',
            'price': 330,
            'image_url': 'https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?auto=format&fit=crop&w=600&q=80',
            'description': 'Blush liquide ultra-pigmenté longue tenue fini radieux par Selena Gomez.'
        },
        {
            'name': 'Too Faced Better Than Sex Mascara',
            'category': 'Maquillage',
            'price': 360,
            'image_url': 'https://images.unsplash.com/photo-1512496015851-a90fb38ba796?auto=format&fit=crop&w=600&q=80',
            'description': 'Mascara volume extrême enrichi en collagène pour un regard déployé.'
        },
        {
            'name': 'YSL Beauty Libre Eau de Parfum (50ml)',
            'category': 'Maquillage',
            'price': 1350,
            'image_url': 'https://images.unsplash.com/photo-1541643600914-78b084683601?auto=format&fit=crop&w=600&q=80',
            'description': 'Parfum iconique Yves Saint Laurent aux notes de lavande florale et fleur d\'oranger.'
        },
        {
            'name': 'NYX Fat Oil Lip Drip',
            'category': 'Maquillage',
            'price': 130,
            'image_url': 'https://images.unsplash.com/photo-1589525231707-f2de2428f59c?auto=format&fit=crop&w=600&q=80',
            'description': 'Gloss huile lèvres ultra-brillant enrichi en huile de framboise et mûre.'
        },
        {
            'name': 'Flormar Silk Matte Liquid Lipstick',
            'category': 'Maquillage',
            'price': 95,
            'image_url': 'https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=600&q=80',
            'description': 'Rouge à lèvres liquide fini mat velours confort extrême.'
        },
        {
            'name': 'Essence Lash Princess False Lash Effect Mascara',
            'category': 'Maquillage',
            'price': 60,
            'image_url': 'https://images.unsplash.com/photo-1512496015851-a90fb38ba796?auto=format&fit=crop&w=600&q=80',
            'description': 'Mascara effet faux-cils spectaculaire volume et longueur.'
        },
        {
            'name': 'Fenty Beauty Gloss Bomb Universal Lip Luminizer',
            'category': 'Maquillage',
            'price': 310,
            'image_url': 'https://images.unsplash.com/photo-1589525231707-f2de2428f59c?auto=format&fit=crop&w=600&q=80',
            'description': 'Gloss universel éclat ultime au beurre de karité par Rihanna.'
        },

        # ==========================================
        # 4. ONGLERIE & VERNIS (NAILS)
        # ==========================================
        {
            'name': 'Vernis Gel UV/LED Construction (Toutes Couleurs)',
            'category': 'Ongles & Vernis',
            'price': 180,
            'image_url': 'https://images.unsplash.com/photo-1632345031435-8727f6897d53?auto=format&fit=crop&w=600&q=80',
            'description': 'Gels de construction et de couleur haute qualité pour extension et modelage ongles.'
        },
        {
            'name': 'BIAB Builder In A Bottle (Nuances Nude & Rose)',
            'category': 'Ongles & Vernis',
            'price': 220,
            'image_url': 'https://images.unsplash.com/photo-1604654894610-df63bc536371?auto=format&fit=crop&w=600&q=80',
            'description': 'Vernis constructeur BIAB gainant et fortifiant pour ongles naturels résistant.'
        },
        {
            'name': 'Vernis Permanent Haute Brilliance (Nuancier Complet)',
            'category': 'Ongles & Vernis',
            'price': 140,
            'image_url': 'https://images.unsplash.com/photo-1553531384-411a247ccd73?auto=format&fit=crop&w=600&q=80',
            'description': 'Vernis permanent professionnel longue tenue 3 à 4 semaines.'
        },
        {
            'name': 'Vernis Semi-Permanent Pro (Palette Toutes Couleurs)',
            'category': 'Ongles & Vernis',
            'price': 120,
            'image_url': 'https://images.unsplash.com/photo-1604654894610-df63bc536371?auto=format&fit=crop&w=600&q=80',
            'description': 'Large gamme de vernis semi-permanents couleurs tendance et séchage UV/LED.'
        },

        # ==========================================
        # 5. COLORATION CHEVEUX (HAIR COLOR)
        # ==========================================
        {
            'name': 'L\'Oréal Professionnel Coloration Inoa / Majirel',
            'category': 'Coloration Cheveux',
            'price': 160,
            'image_url': 'https://images.unsplash.com/photo-1562322140-8baeececf3df?auto=format&fit=crop&w=600&q=80',
            'description': 'Tubes de coloration professionnelle L\'Oréal toutes nuances (Inoa sans ammoniaque & Majirel).'
        },
        {
            'name': 'Inebrya Coloration Crème Professionnelle',
            'category': 'Coloration Cheveux',
            'price': 130,
            'image_url': 'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=600&q=80',
            'description': 'Coloration italienne de prestige enrichie en lin et aloe vera pour une brillance intense.'
        },
        {
            'name': 'Garnier Olia Coloration aux Huiles de Fleurs',
            'category': 'Coloration Cheveux',
            'price': 110,
            'image_url': 'https://images.unsplash.com/photo-1527799820374-dcf8d9d4a388?auto=format&fit=crop&w=600&q=80',
            'description': 'Coloration permanente à domicile sans ammoniaque propulsée par 60% d\'huiles.'
        },
    ]

    count = 0
    for idx, p in enumerate(products_data):
        local_img = f"/static/images/product_{130 + idx}.jpg"
        Product.objects.create(
            name=p['name'],
            category=p['category'],
            price=p['price'],
            is_available=True,
            image_url=local_img,
            description=p['description']
        )
        count += 1

    print(f"Successfully updated {count} real products with local static images.")

if __name__ == '__main__':
    run()
