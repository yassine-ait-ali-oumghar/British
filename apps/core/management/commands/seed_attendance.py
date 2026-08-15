import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from apps.core.models import Employee, AttendanceRecord, Product, Service, ContactMessage, Notification

class Command(BaseCommand):
    help = "Alimente la base de données ERP avec des employés, pointages, produits, services, notifications et utilisateurs."

    def handle(self, *args, **options):
        self.stdout.write("Génération des données ERP...")

        # 1. Employees & Team
        employees_data = [
            {"first_name": "Arthur", "last_name": "Pendleton", "position": "Master Barber", "department": "Salon Master", "role": "ADMINISTRATEUR", "is_team_member": True, "email": "a.pendleton@britishstyle.co.uk", "phone": "+33 6 12 34 56 78", "avatar_color": "#c5a059", "username": "admin_arthur"},
            {"first_name": "Victoria", "last_name": "Sterling", "position": "Styliste Visagiste", "department": "Coiffure", "role": "MANAGER", "is_team_member": True, "email": "v.sterling@britishstyle.co.uk", "phone": "+33 6 23 45 67 89", "avatar_color": "#2c3e50", "username": "victoria"},
            {"first_name": "Charles", "last_name": "Wellington", "position": "Barber Senior", "department": "Salon", "role": "EMPLOYEE", "is_team_member": True, "email": "c.wellington@britishstyle.co.uk", "phone": "+33 6 34 56 78 90", "avatar_color": "#16a085", "username": "charles"},
            {"first_name": "Elizabeth", "last_name": "Kingsley", "position": "Esthéticienne Head", "department": "Esthétique", "role": "RESPONSABLE", "is_team_member": True, "email": "e.kingsley@britishstyle.co.uk", "phone": "+33 6 45 67 89 01", "avatar_color": "#8e44ad", "username": "elizabeth"},
            {"first_name": "George", "last_name": "Windsor", "position": "Réceptionniste / Hôte", "department": "Accueil", "role": "VENDEUR", "is_team_member": True, "email": "g.windsor@britishstyle.co.uk", "phone": "+33 6 56 78 90 12", "avatar_color": "#d35400", "username": "george"},
            {"first_name": "Charlotte", "last_name": "Kensington", "position": "Coloriste d'Élite", "department": "Coiffure", "role": "EMPLOYEE", "is_team_member": True, "email": "c.kensington@britishstyle.co.uk", "phone": "+33 6 67 89 01 23", "avatar_color": "#27ae60", "username": "charlotte"},
            {"first_name": "James", "last_name": "Bond", "position": "Logistique & Stock", "department": "Réserve", "role": "LOGISTIQUE", "is_team_member": False, "email": "j.bond@britishstyle.co.uk", "phone": "+33 6 77 88 99 00", "avatar_color": "#000000", "username": "james_bond"},
        ]

        employees = []
        for emp_data in employees_data:
            username = emp_data.pop("username")
            email = emp_data["email"]

            # Create or get Django User
            user, u_created = User.objects.get_or_create(username=username, defaults={"email": email, "first_name": emp_data["first_name"], "last_name": emp_data["last_name"]})
            if u_created:
                user.set_password("password123")
                if emp_data["role"] == "ADMINISTRATEUR":
                    user.is_staff = True
                    user.is_superuser = True
                user.save()

            emp, created = Employee.objects.get_or_create(
                email=email,
                defaults={**emp_data, "user": user}
            )
            if not created:
                for key, value in emp_data.items():
                    setattr(emp, key, value)
                emp.user = user
                emp.save()
            employees.append(emp)

        # 2. Attendance Records
        today = timezone.now().date()
        start_of_week = today - datetime.timedelta(days=today.weekday())

        weekly_schedules = {
            "Arthur Pendleton": [
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(9, 0), None, "PRESENT", 30),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 45),
                (datetime.time(10, 0), datetime.time(18, 0), "PRESENT", 60),
            ],
            "Victoria Sterling": [
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(9, 0), None, "PAUSE", 45),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 45),
                (datetime.time(10, 0), datetime.time(18, 0), "PRESENT", 60),
            ],
            "Charles Wellington": [
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(9, 0), None, "PRESENT", 0),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(10, 0), datetime.time(18, 0), "PRESENT", 60),
            ],
            "Elizabeth Kingsley": [
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(10, 0), datetime.time(18, 0), "PRESENT", 60),
            ],
            "George Windsor": [
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 45),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 45),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 0),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 45),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 45),
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 45),
                (datetime.time(10, 0), datetime.time(18, 0), "PRESENT", 45),
            ],
            "Charlotte Kensington": [
                (datetime.time(9, 0), datetime.time(20, 0), "PRESENT", 60),
                (datetime.time(9, 0), datetime.time(17, 30), "PRESENT", 60),
                (None, None, "ABSENT", 0),
                (datetime.time(9, 0), datetime.time(17, 30), "PRESENT", 60),
                (datetime.time(9, 0), datetime.time(17, 30), "PRESENT", 60),
                (datetime.time(9, 0), datetime.time(15, 0), "PRESENT", 30),
                (None, None, "REPOS", 0),
            ],
        }

        for emp in employees:
            if not emp.is_team_member:
                continue
            name = emp.full_name
            schedules = weekly_schedules.get(name, [])
            for day_idx, (cin, cout, status, pause_min) in enumerate(schedules):
                record_date = start_of_week + datetime.timedelta(days=day_idx)
                if record_date > today:
                    continue
                actual_cout = cout
                if record_date == today and status in ["PRESENT", "PAUSE"] and cout is None:
                    actual_cout = None

                AttendanceRecord.objects.update_or_create(
                    employee=emp,
                    date=record_date,
                    defaults={
                        "status": status,
                        "check_in": cin,
                        "check_out": actual_cout,
                        "pause_duration_minutes": pause_min,
                        "notes": "Pointage régulier" if status == "PRESENT" else ("Congé / Repos hebdomadaire" if status == "REPOS" else "")
                    }
                )

        # 3. Products Seed
        products_data = [
            {"name": "Huile à Barbe Royal Gold", "category": "Barbe", "price": 34.90, "stock": 25, "is_available": True, "description": "Nourrit en profondeur la barbe avec un fini satiné d'exception."},
            {"name": "Shampooing Fortifiant Keratin", "category": "Cheveux", "price": 28.50, "stock": 40, "is_available": True, "description": "Formule enrichie en kératine et huiles précieuses."},
            {"name": "Cire Coiffante Mat Prestige", "category": "Coiffage", "price": 22.00, "stock": 15, "is_available": True, "description": "Tenue forte naturelle sans résidu."},
            {"name": "Coffret Soin Visage Gentleman", "category": "Coffrets", "price": 89.00, "stock": 8, "is_available": True, "description": "Ensemble nettoyant, sérum hydratant et baume après-rasage."},
            {"name": "Sérum Anti-Âge Luxis", "category": "Soins Visage", "price": 65.00, "stock": 0, "is_available": False, "description": "Sérum régénérant d'exception aux actifs précieux."},
        ]
        for pdata in products_data:
            Product.objects.get_or_create(name=pdata["name"], defaults=pdata)

        # 4. Services Seed
        services_data = [
            {"name": "Coupe & Coiffage Signature", "category": "Coiffure", "price": 45.00, "duration_minutes": 45, "is_active": True, "description": "Coupe sur-mesure avec shampooing et massage crânien."},
            {"name": "Taille de Barbe & Serviette Chaude", "category": "Barbier", "price": 35.00, "duration_minutes": 30, "is_active": True, "description": "Rasage à l'ancienne avec soin apaisant aux huiles essentielles."},
            {"name": "Rituel Soin du Visage Éclat", "category": "Esthétique", "price": 75.00, "duration_minutes": 60, "is_active": True, "description": "Nettoyage profond, gommage doux et masque régénérant."},
            {"name": "Coloration Prestige Gloss", "category": "Coloration", "price": 60.00, "duration_minutes": 60, "is_active": True, "description": "Coloration nuance par nuance sans ammoniaque."},
        ]
        for sdata in services_data:
            Service.objects.get_or_create(name=sdata["name"], defaults=sdata)

        # 5. Contact Messages Seed
        messages_data = [
            {"name": "Jean-Pierre Dupont", "email": "jp.dupont@gmail.com", "phone": "0611223344", "subject": "Demande de rendez-vous groupe", "message": "Bonjour, nous souhaiterions privatiser le salon pour un mariage le mois prochain.", "status": "NEW"},
            {"name": "Sophie Martin", "email": "s.martin@yahoo.fr", "phone": "0655667788", "subject": "Renseignements coffrets produits", "message": "Proposez-vous la livraison à domicile pour les coffrets cadeaux ?", "status": "READ"},
            {"name": "Alexandre Moreau", "email": "alex.m@outlook.com", "phone": "0699001122", "subject": "Avis prestation Barbier", "message": "Excellent service d'Arthur ! Je reviendrai régulièrement.", "status": "PROCESSED"},
        ]
        for mdata in messages_data:
            ContactMessage.objects.get_or_create(email=mdata["email"], subject=mdata["subject"], defaults=mdata)

        # 6. Notifications Seed
        notifications_data = [
            {"title": "Mise à jour des horaires d'ouverture", "message": "Le salon fermera exceptionnellement à 17h00 ce vendredi pour réunion d'équipe.", "type": "ANNOUNCEMENT"},
            {"title": "Note d'information Administration", "message": "Pensez à bien valider votre sortie à la fin de chaque journée de travail.", "type": "ADMIN"},
            {"title": "Changement de Planning Semaine Prochaine", "message": "Le planning de la semaine prochaine est en ligne dans votre calendrier.", "type": "SCHEDULE"},
        ]
        for ndata in notifications_data:
            Notification.objects.get_or_create(title=ndata["title"], defaults=ndata)

        self.stdout.write(self.style.SUCCESS("Succès: Base de données ERP alimentée avec succès !"))

