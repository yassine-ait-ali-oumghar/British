import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'British_Style.settings')
django.setup()

from apps.core.models import Service, Reservation

def run():
    print("Clearing old services...")
    # Delete reservations if any (though currently 0)
    Reservation.objects.all().delete()
    Service.objects.all().delete()

    services_data = [
        # --- ONGLERIE ---
        {
            'name': 'Pose Vernis',
            'category': 'Onglerie',
            'price': 50,
            'duration_minutes': 20,
            'description': 'Pose de vernis classique sur ongles mains ou pieds.'
        },
        {
            'name': 'Pose Permanente',
            'category': 'Onglerie',
            'price': 130,
            'duration_minutes': 40,
            'description': 'Pose de vernis semi-permanent tenue longue durée.'
        },
        {
            'name': 'Manucure',
            'category': 'Onglerie',
            'price': 70,
            'duration_minutes': 30,
            'description': 'Soin complet des mains, nettoyage des cuticules et limage des ongles.'
        },
        {
            'name': 'Pédicure',
            'category': 'Onglerie',
            'price': 130,
            'duration_minutes': 45,
            'description': 'Soin esthétique complet des pieds et beautés des ongles.'
        },
        {
            'name': 'Pédicure Médicale (ongle incarné)',
            'category': 'Onglerie',
            'price': 150,
            'duration_minutes': 45,
            'description': 'Soin spécialisé pour traiter les ongles incarnés et soulager l\'inconfort.'
        },
        {
            'name': 'Manucure SPA',
            'category': 'Onglerie',
            'price': 150,
            'duration_minutes': 45,
            'description': 'Soin nourrissant et relaxant des mains avec gommage, masque et massage.'
        },
        {
            'name': 'Pédicure SPA',
            'category': 'Onglerie',
            'price': 200,
            'duration_minutes': 60,
            'description': 'Soin d\'exception complet des pieds avec gommage, masque et bain relaxant (200 à 300 DH).'
        },
        {
            'name': 'French Normal',
            'category': 'Onglerie',
            'price': 10,
            'duration_minutes': 10,
            'description': 'Finition French classique (supplément +10 DH).'
        },
        {
            'name': 'French Permanent',
            'category': 'Onglerie',
            'price': 20,
            'duration_minutes': 15,
            'description': 'Finition French semi-permanente (supplément +20 DH).'
        },
        {
            'name': 'Faux Ongles',
            'category': 'Onglerie',
            'price': 140,
            'duration_minutes': 60,
            'description': 'Pose de faux ongles esthétique et soignée.'
        },
        {
            'name': 'Gel / Résine',
            'category': 'Onglerie',
            'price': 400,
            'duration_minutes': 90,
            'description': 'Pose complète d\'ongles en Gel ou Résine haute tenue.'
        },
        {
            'name': 'Remplissage',
            'category': 'Onglerie',
            'price': 250,
            'duration_minutes': 60,
            'description': 'Entretien et remplissage pour ongles en Gel ou Résine.'
        },
        {
            'name': 'Baby Boomer Gel',
            'category': 'Onglerie',
            'price': 500,
            'duration_minutes': 90,
            'description': 'Dégradé d\'élégance naturel Baby Boomer réalisé en gel.'
        },
        {
            'name': 'Baby Boomer Permanente',
            'category': 'Onglerie',
            'price': 200,
            'duration_minutes': 45,
            'description': 'Effet Baby Boomer semi-permanent chic et raffiné.'
        },

        # --- COIFFURE ---
        {
            'name': 'Brushing',
            'category': 'Coiffure',
            'price': 40,
            'duration_minutes': 30,
            'description': 'Mise en forme et brushing professionnel (40 à 60 DH selon longueur).'
        },
        {
            'name': 'Brushing + Extension',
            'category': 'Coiffure',
            'price': 70,
            'duration_minutes': 45,
            'description': 'Brushing spécifique sur cheveux avec rajouts / extensions (70 à 100 DH).'
        },
        {
            'name': 'Touching',
            'category': 'Coiffure',
            'price': 40,
            'duration_minutes': 20,
            'description': 'Retouche et rafraîchissement rapide du coiffage.'
        },
        {
            'name': 'Babyliss',
            'category': 'Coiffure',
            'price': 80,
            'duration_minutes': 45,
            'description': 'Création de boucles et ondulations glamour au fer Babyliss (80 à 100 DH).'
        },
        {
            'name': 'Coupe',
            'category': 'Coiffure',
            'price': 80,
            'duration_minutes': 30,
            'description': 'Coupe sur mesure selon votre morphologie et vos envies.'
        },
        {
            'name': 'Pointes',
            'category': 'Coiffure',
            'price': 30,
            'duration_minutes': 15,
            'description': 'Égalisation et entretien des pointes abîmées.'
        },
        {
            'name': 'Shampoing Colorant',
            'category': 'Coiffure',
            'price': 100,
            'duration_minutes': 45,
            'description': 'Shampoing repigmentant pour raviver les reflets (100 à 200 DH).'
        },
        {
            'name': 'Racines Ammoniaque',
            'category': 'Coiffure',
            'price': 150,
            'duration_minutes': 45,
            'description': 'Application de coloration racines avec formule classique.'
        },
        {
            'name': 'Pose Coloration',
            'category': 'Coiffure',
            'price': 100,
            'duration_minutes': 45,
            'description': 'Prestation de pose de coloration capillaire.'
        },
        {
            'name': 'Coloration Perla',
            'category': 'Coiffure',
            'price': 250,
            'duration_minutes': 60,
            'description': 'Coloration brillance Perla (250 à 350 DH).'
        },
        {
            'name': 'Coloration Inoa',
            'category': 'Coiffure',
            'price': 400,
            'duration_minutes': 60,
            'description': 'Coloration d\'exception Inoa sans ammoniaque au confort optimal.'
        },
        {
            'name': 'Racines Inoa',
            'category': 'Coiffure',
            'price': 250,
            'duration_minutes': 45,
            'description': 'Retouche racines avec la gamme sans ammoniaque Inoa.'
        },
        {
            'name': 'Mèches / Balayage / Ombré',
            'category': 'Coiffure',
            'price': 500,
            'duration_minutes': 120,
            'description': 'Éclaircissement sur mesure, balayage ou ombre hair lumineux (500 à 700 DH).'
        },
        {
            'name': 'Coiffure',
            'category': 'Coiffure',
            'price': 200,
            'duration_minutes': 60,
            'description': 'Coiffure élaborée de soirée, chignon ou événement (200 à 500 DH).'
        },
        {
            'name': 'Protéine',
            'category': 'Coiffure',
            'price': 800,
            'duration_minutes': 120,
            'description': 'Soin profond à la protéine pour lisser et réparer la fibre capillaire (800 à 1000 DH).'
        },
        {
            'name': 'Extension',
            'category': 'Coiffure',
            'price': 2000,
            'duration_minutes': 180,
            'description': 'Pose d\'extensions de cheveux naturelles sur mesure (2000 à 6000 DH).'
        },
        {
            'name': 'Pose Anneaux',
            'category': 'Coiffure',
            'price': 300,
            'duration_minutes': 60,
            'description': 'Pose technique d\'extensions à anneaux (micro-rings).'
        },
        {
            'name': 'Rinçage après Racines',
            'category': 'Coiffure',
            'price': 50,
            'duration_minutes': 15,
            'description': 'Rinçage et soin traitant spécifique post-coloration (+50 DH).'
        },

        # --- ESTHÉTIQUE ---
        {
            'name': 'Duvet',
            'category': 'Esthétique',
            'price': 20,
            'duration_minutes': 10,
            'description': 'Épilation douce du duvet de la lèvre supérieure.'
        },
        {
            'name': 'Sourcils',
            'category': 'Esthétique',
            'price': 20,
            'duration_minutes': 15,
            'description': 'Épilation et redessin de la ligne des sourcils.'
        },
        {
            'name': 'Menton',
            'category': 'Esthétique',
            'price': 10,
            'duration_minutes': 10,
            'description': 'Épilation cire zone menton.'
        },
        {
            'name': 'Visage',
            'category': 'Esthétique',
            'price': 60,
            'duration_minutes': 25,
            'description': 'Épilation complète des zones du visage.'
        },
        {
            'name': 'Teinte Sourcils',
            'category': 'Esthétique',
            'price': 20,
            'duration_minutes': 15,
            'description': 'Teinture des sourcils pour intensifier le regard.'
        },
        {
            'name': 'Aisselles',
            'category': 'Esthétique',
            'price': 30,
            'duration_minutes': 15,
            'description': 'Épilation douce de la zone aisselles.'
        },
        {
            'name': 'Avant Bras',
            'category': 'Esthétique',
            'price': 40,
            'duration_minutes': 20,
            'description': 'Épilation à la cire des avant-bras.'
        },
        {
            'name': 'Bras',
            'category': 'Esthétique',
            'price': 60,
            'duration_minutes': 30,
            'description': 'Épilation complète des bras.'
        },
        {
            'name': 'Maillot Bords',
            'category': 'Esthétique',
            'price': 60,
            'duration_minutes': 20,
            'description': 'Épilation du contour du maillot.'
        },
        {
            'name': 'Maillot Intégrale',
            'category': 'Esthétique',
            'price': 100,
            'duration_minutes': 30,
            'description': 'Épilation intégrale de la zone maillot.'
        },
        {
            'name': 'Demi Jambes',
            'category': 'Esthétique',
            'price': 60,
            'duration_minutes': 25,
            'description': 'Épilation demi-jambes (mollets ou cuisses).'
        },
        {
            'name': 'Jambes Entières',
            'category': 'Esthétique',
            'price': 100,
            'duration_minutes': 40,
            'description': 'Épilation complète des jambes.'
        },
        {
            'name': 'Épilation Complète sans Bras',
            'category': 'Esthétique',
            'price': 220,
            'duration_minutes': 60,
            'description': 'Forfait épilation corps complet (jambes + maillot + aisselles) hors bras.'
        },
        {
            'name': 'Épilation Complète plus Bras',
            'category': 'Esthétique',
            'price': 280,
            'duration_minutes': 75,
            'description': 'Forfait épilation corps complet avec bras inclus.'
        },
        {
            'name': 'Make Up',
            'category': 'Esthétique',
            'price': 400,
            'duration_minutes': 60,
            'description': 'Maquillage professionnel sur mesure (200 à 400 DH).'
        },
        {
            'name': 'Faux Cils',
            'category': 'Esthétique',
            'price': 120,
            'duration_minutes': 30,
            'description': 'Pose de faux cils à frange ou en bouquets.'
        },
        {
            'name': 'Faux Cils en Soie',
            'category': 'Esthétique',
            'price': 350,
            'duration_minutes': 60,
            'description': 'Pose d\'extensions de cils effet naturel en soie (350 à 450 DH).'
        },
        {
            'name': 'Microblading',
            'category': 'Esthétique',
            'price': 1200,
            'duration_minutes': 90,
            'description': 'Technique de maquillage semi-permanent des sourcils effet poil par poil.'
        },
        {
            'name': 'Soins de Visage',
            'category': 'Esthétique',
            'price': 300,
            'duration_minutes': 60,
            'description': 'Soin du visage nettoyant, hydratant et revitalisant (300 à 400 DH).'
        },
    ]

    count = 0
    for s in services_data:
        Service.objects.create(
            name=s['name'],
            category=s['category'],
            price=s['price'],
            duration_minutes=s['duration_minutes'],
            description=s['description'],
            is_active=True
        )
        count += 1

    print(f"Successfully created {count} services in the database.")

if __name__ == '__main__':
    run()
