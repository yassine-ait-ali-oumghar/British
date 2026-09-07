# ==============================================================================
# MODÈLES DE DONNÉES DE L'APPLICATION BRITISH STYLE (ORM DJANGO / POSTGRESQL)
# ==============================================================================
# Ce fichier définit la structure de la base de données relationnelle.
# Il contient les 10 entités clés du projet ainsi que la logique métier de bas niveau
# (calculs d'heures de travail, calculs de présence, génération des scores de performance, etc.).
# ==============================================================================

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver

# Liste des rôles d'accès au système
ROLE_CHOICES = [
    ('EMPLOYEE', 'Employé'),
    ('RECEPTION', 'Réceptionniste'),
    ('ADMINISTRATEUR', 'Administrateur'),
]

# Liste des postes prédéfinis
POSITION_CHOICES = [
    ('Coiffure', 'Coiffure'),
    ('Esthétique', 'Esthétique'),
    ('Onglerie', 'Onglerie'),
    ('Réceptionniste', 'Réceptionniste'),
    ('Master', 'Master'),
]

# Liste des départements prédéfinis
DEPARTMENT_CHOICES = [
    ('Coiffure', 'Coiffure'),
    ('Esthétique', 'Esthétique'),
    ('Onglerie', 'Onglerie'),
    ('Accueil', 'Accueil'),
    ('Salon Master', 'Salon Master'),
]

class Employee(models.Model):
    """
    Modèle du profil Employé / Coiffeur / Membre du personnel.
    Rattaché à un compte utilisateur Django (User) par une relation OneToOne.
    Contient la logique de calcul d'heures, de présence et de performance.
    """
    objects = models.Manager()
    attendance_records: models.Manager
    notifications: models.Manager
    reservations: models.Manager
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='employee_profile')
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    position = models.CharField(max_length=100, verbose_name="Poste")
    department = models.CharField(max_length=100, default="Salon", verbose_name="Département")
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='USER', verbose_name="Rôle Métier")
    is_team_member = models.BooleanField(default=False, verbose_name="Membre de l'Équipe (Statistiques)")
    is_active = models.BooleanField(default=True, verbose_name="Compte Actif")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    photo = models.CharField(max_length=500, blank=True, null=True, verbose_name="Photo de Profil")
    avatar_color = models.CharField(max_length=20, default="#c5a059", verbose_name="Couleur Avatar")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"

    @property
    def full_name(self):
        """Retourne le nom complet (Prénom + Nom) de l'employé."""
        return f"{self.first_name} {self.last_name}"

    def get_today_record(self):
        """Récupère l'enregistrement de pointage (AttendanceRecord) de la journée en cours."""
        # 1. Obtient la date d'aujourd'hui dans le fuseau horaire local (Casablanca)
        today = timezone.localtime(timezone.now()).date()
        # 2. Cherche en BDD le pointage correspondant à cet employé et cette date
        return self.attendance_records.filter(date=today).first()

    def get_current_status(self):
        """Renvoie le statut brut actuel ('PRESENT', 'PAUSE', 'REPOS', 'ABSENT')."""
        # 1. Récupère le pointage du jour
        record = self.get_today_record()
        # 2. Si un pointage existe, renvoie son statut, sinon renvoie 'ABSENT'
        if record:
            return record.status
        return 'ABSENT'

    def get_current_status_display(self):
        """Renvoie le statut du jour au format lisible ('Présent', 'En pause', etc.)."""
        record = self.get_today_record()
        if record:
            return record.get_status_display()
        return 'Absent'

    def get_hours_worked_today(self):
        """Calcule le nombre d'heures décimales effectuées aujourd'hui."""
        # 1. Récupère le pointage du jour
        record = self.get_today_record()
        # 2. Si le pointage existe, appelle la méthode de calcul d'heures nettes
        if record:
            return record.calculate_hours_worked()
        return 0.0

    def get_hours_worked_today_formatted(self):
        """Convertit le temps de travail du jour au format lisible 'Xh YYm'."""
        # 1. Récupère le total d'heures décimal (ex: 7.5)
        hours = self.get_hours_worked_today()
        # 2. Extrait la partie entière (heures) et calcule les minutes restantes
        h = int(hours)
        m = int(round((hours - h) * 60))
        # 3. Formate le résultat en texte (ex: '7h 30m')
        return f"{h}h {m:02d}m"

    def get_hours_worked_this_week(self):
        """Calcule le total cumulé d'heures travaillées depuis le début de la semaine (Lundi)."""
        # 1. Obtient la date du jour
        today = timezone.now().date()
        # 2. Calcule la date du Lundi (début de semaine) et du Dimanche (fin de semaine)
        start_of_week = today - datetime.timedelta(days=today.weekday())
        end_of_week = start_of_week + datetime.timedelta(days=6)
        
        # 3. Filtre tous les pointages compris entre le Lundi et le Dimanche
        records = self.attendance_records.filter(date__gte=start_of_week, date__lte=end_of_week)
        # 4. Additionne les heures travaillées de chaque jour
        total_hours = sum(r.calculate_hours_worked() for r in records)
        return total_hours

    def get_hours_worked_this_week_formatted(self):
        """Formate le total des heures de la semaine au format 'Xh YYm'."""
        hours = self.get_hours_worked_this_week()
        h = int(hours)
        m = int(round((hours - h) * 60))
        return f"{h}h {m:02d}m"

    def get_hours_worked_this_month(self):
        """Calcule le total d'heures effectuées depuis le 1er du mois en cours."""
        # 1. Date du jour et 1er jour du mois
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        # 2. Récupère les pointages du mois et fait la somme des heures nettes
        records = self.attendance_records.filter(date__gte=start_of_month, date__lte=today)
        total_hours = sum(r.calculate_hours_worked() for r in records)
        return total_hours

    def get_hours_worked_this_month_formatted(self):
        """Formate le total des heures du mois au format 'Xh YYm'."""
        hours = float(self.get_hours_worked_this_month() or 0)
        h = int(hours)
        m = int(round((hours - h) * 60))
        return f"{h}h {m:02d}m"

    def get_pause_time_today_formatted(self):
        """Formate le temps total de pause de la journée."""
        record = self.get_today_record()
        if record:
            p_min = record.pause_duration_minutes
            h = p_min // 60
            m = p_min % 60
            return f"{h}h {m:02d}m" if h > 0 else f"{m} min"
        return "0 min"

    def get_days_present_this_month(self):
        """Compte le nombre de jours où l'employé a été présent ce mois-ci."""
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        return self.attendance_records.filter(date__gte=start_of_month, date__lte=today, status__in=['PRESENT', 'PAUSE']).count()

    def get_days_rest_this_month(self):
        """Compte le nombre de jours de repos pris ce mois-ci."""
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        return self.attendance_records.filter(date__gte=start_of_month, date__lte=today, status='REPOS').count()

    def get_overtime_hours_this_month(self):
        """Calcule le total d'heures supplémentaires accumulées ce mois-ci."""
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        records = self.attendance_records.filter(date__gte=start_of_month, date__lte=today)
        total_overtime = sum(r.overtime_hours for r in records)
        return total_overtime

    def get_overtime_hours_this_month_formatted(self):
        """Formate les heures supplémentaires du mois au format 'Xh YYm'."""
        ot = self.get_overtime_hours_this_month()
        h = int(ot)
        m = int(round((ot - h) * 60))
        return f"{h}h {m:02d}m"

    def get_attendance_rate(self):
        """Calcule le taux de présence mensuel en pourcentage (ex: 95%)."""
        # 1. Définit l'intervalle de jours écoulés dans le mois
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        total_days = (today - start_of_month).days + 1
        # 2. Compte le nombre de jours ouvrables hors dimanche
        work_days = max(1, sum(1 for d in range(total_days) if (start_of_month + datetime.timedelta(days=d)).weekday() < 6))
        # 3. Compte les jours de présence effective
        present_records = self.attendance_records.filter(date__gte=start_of_month, status__in=['PRESENT', 'PAUSE']).count()
        # 4. Ratio entre jours présent et jours ouvrables
        rate = round((present_records / work_days) * 100)
        return min(100, max(0, rate))

    def get_lateness_count(self):
        today = timezone.now().date()
        start_of_month = today.replace(day=1)
        records = self.attendance_records.filter(date__gte=start_of_month, check_in__gt=datetime.time(9, 15))
        return records.count()

    def get_performance_score(self):
        rate = self.get_attendance_rate()
        lateness = self.get_lateness_count()
        score = max(50, rate - (lateness * 5))
        stars = round(score / 20, 1)
        return {
            'percentage': score,
            'stars': stars,
            'star_count': int(stars),
            'has_half_star': (stars - int(stars)) >= 0.5
        }


class AttendanceRecord(models.Model):
    objects = models.Manager()
    STATUS_CHOICES = [
        ('PRESENT', 'Présent'),
        ('PAUSE', 'En pause'),
        ('REPOS', 'En repos'),
        ('ABSENT', 'Absent'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records', verbose_name="Employé")
    date = models.DateField(default=timezone.now, verbose_name="Date")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PRESENT', verbose_name="Statut")
    check_in = models.TimeField(null=True, blank=True, verbose_name="Heure d'arrivée")
    check_out = models.TimeField(null=True, blank=True, verbose_name="Heure de départ")
    pause_start = models.TimeField(null=True, blank=True, verbose_name="Début de pause")
    pause_end = models.TimeField(null=True, blank=True, verbose_name="Fin de pause")
    pause_duration_minutes = models.IntegerField(default=0, verbose_name="Durée pause (min)")
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Pointage"
        verbose_name_plural = "Pointages"
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.get_status_display()})"

    def calculate_hours_worked(self):
        """Calcul net des heures effectuées dans la journée après déduction des pauses."""
        # Étape 1 : Si l'employé est absent, en repos ou n'a pas pointé d'arrivée -> 0 heure
        if self.status in ['ABSENT', 'REPOS'] or not self.check_in:
            return 0.0
        
        # Étape 2 : Si l'heure de départ n'est pas encore saisie (journée en cours)
        end_time = self.check_out
        if not end_time:
            now_dt = timezone.localtime(timezone.now())
            # Si c'est aujourd'hui, on prend l'heure actuelle comme fin provisoire
            if self.date == now_dt.date():
                end_time = now_dt.time()
            else:
                return 0.0

        # Étape 3 : Conversion des TimeField en datetime pour permettre la soustraction
        dummy_date = datetime.date(2000, 1, 1)
        dt_in = datetime.datetime.combine(dummy_date, self.check_in)
        dt_out = datetime.datetime.combine(dummy_date, end_time)

        # Étape 4 : Gestion du travail de nuit (si le départ a lieu après minuit)
        if dt_out < dt_in:
            dt_out += datetime.timedelta(days=1)

        # Étape 5 : Calcul de la différence nette en secondes, conversion en heures et déduction des pauses
        diff = dt_out - dt_in
        hours = diff.total_seconds() / 3600.0 - (self.pause_duration_minutes / 60.0)
        return max(0.0, hours)

    @property
    def hours_worked_formatted(self):
        """Formatage lisible du temps de travail (ex: '8h 15m')."""
        hours = self.calculate_hours_worked()
        h = int(hours)
        m = int(round((hours - h) * 60))
        return f"{h}h {m:02d}m"

    @property
    def is_late(self):
        if self.check_in and self.check_in > datetime.time(9, 15):
            return True
        return False

    @property
    def lateness_minutes(self):
        if self.check_in and self.check_in > datetime.time(9, 15):
            dummy_date = datetime.date(2000, 1, 1)
            dt_in = datetime.datetime.combine(dummy_date, self.check_in)
            dt_std = datetime.datetime.combine(dummy_date, datetime.time(9, 0))
            return int((dt_in - dt_std).total_seconds() // 60)
        return 0

    @property
    def overtime_hours(self):
        worked = self.calculate_hours_worked()
        if worked > 8.0:
            return round(worked - 8.0, 2)
        return 0.0


class Product(models.Model):
    objects = models.Manager()
    name = models.CharField(max_length=200, verbose_name="Nom du produit")
    category = models.CharField(max_length=100, verbose_name="Catégorie")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix (DH)")
    stock = models.IntegerField(default=0, verbose_name="Stock")
    is_available = models.BooleanField(default=True, verbose_name="Disponible")
    image_url = models.CharField(max_length=500, blank=True, verbose_name="URL Image")
    shades = models.JSONField(default=list, blank=True, verbose_name="Nuances / Couleurs")
    description = models.TextField(blank=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.price} DH)"


class Service(models.Model):
    objects = models.Manager()
    name = models.CharField(max_length=200, verbose_name="Nom du service")
    category = models.CharField(max_length=100, verbose_name="Catégorie")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix (DH)")
    duration_minutes = models.IntegerField(default=30, verbose_name="Durée (minutes)")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    image_url = models.CharField(max_length=500, blank=True, verbose_name="URL Image")
    description = models.TextField(blank=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.duration_minutes} min - {self.price} DH)"


class ContactMessage(models.Model):
    objects = models.Manager()
    STATUS_CHOICES = [
        ('NEW', 'Nouveau'),
        ('READ', 'Lu'),
        ('PROCESSED', 'Traité'),
    ]

    name = models.CharField(max_length=100, verbose_name="Nom complet")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Téléphone")
    subject = models.CharField(max_length=200, verbose_name="Sujet")
    message = models.TextField(verbose_name="Message")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW', verbose_name="Statut")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'envoi")

    class Meta:
        verbose_name = "Message Contact"
        verbose_name_plural = "Messages Contact"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject} ({self.get_status_display()})"


class Notification(models.Model):
    objects = models.Manager()
    TYPE_CHOICES = [
        ('ANNOUNCEMENT', 'Annonce'),
        ('ADMIN', 'Message de l\'administration'),
        ('SCHEDULE', 'Changement de planning'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications', verbose_name="Employé (Vide = Tous)")
    title = models.CharField(max_length=200, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='ANNOUNCEMENT', verbose_name="Type")
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']

    def __str__(self):
        target = self.employee.full_name if self.employee else "Tous"
        return f"[{self.get_type_display()}] {self.title} -> {target}"


class EmployeeBreak(models.Model):
    objects = models.Manager()
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='breaks', verbose_name="Employé")
    date = models.DateField(default=timezone.now, verbose_name="Date")
    start_time = models.TimeField(verbose_name="Heure de début")
    end_time = models.TimeField(verbose_name="Heure de fin")
    title = models.CharField(max_length=100, default="Pause déjeuner", verbose_name="Libellé de la pause")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pause Employé"
        verbose_name_plural = "Pauses Employés"
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"Pause {self.employee.full_name} ({self.date} {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"


class Reservation(models.Model):
    objects = models.Manager()
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('CONFIRMED', 'Confirmé'),
        ('ARRIVED', 'Cliente arrivée'),
        ('IN_PROGRESS', 'Soin en cours'),
        ('COMPLETED', 'Terminé'),
        ('CANCELLED', 'Annulé'),
        ('NO_SHOW', 'Cliente absente'),
    ]

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations', verbose_name="Client")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='reservations', verbose_name="Employé")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='reservations', verbose_name="Service")
    date = models.DateField(verbose_name="Date de réservation")
    start_time = models.TimeField(verbose_name="Heure de début")
    end_time = models.TimeField(verbose_name="Heure de fin")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Statut")
    arrival_time = models.DateTimeField(null=True, blank=True, verbose_name="Heure d'arrivée de la cliente")
    cancellation_reason = models.CharField(max_length=255, blank=True, null=True, verbose_name="Motif d'annulation")
    notes = models.TextField(blank=True, verbose_name="Notes / Demande particulière")
    rating = models.IntegerField(null=True, blank=True, verbose_name="Évaluation (1-5)")
    review_comment = models.TextField(blank=True, verbose_name="Commentaire d'évaluation")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"Réservation #{self.id} - {self.client.username} avec {self.employee.full_name} ({self.date} {self.start_time.strftime('%H:%M')})"

    @property
    def duration_minutes(self):
        if self.start_time and self.end_time:
            dummy_date = datetime.date(2000, 1, 1)
            dt_start = datetime.datetime.combine(dummy_date, self.start_time)
            dt_end = datetime.datetime.combine(dummy_date, self.end_time)
            return int((dt_end - dt_start).total_seconds() / 60)
        return 0

    @property
    def multi_services_breakdown(self):
        if not self.notes or "[Formule Multi-Prestations:" not in self.notes:
            return []
        
        import re
        match = re.search(r"\[Formule Multi-Prestations:\s*(.*?)(?:\s*\|\s*Total:|\s*\])", self.notes)
        if not match:
            return []
        
        raw_items = match.group(1).split('+')
        items = []
        for item in raw_items:
            item_str = item.strip()
            if not item_str:
                continue
            exp_match = re.search(r"^(.*?)\s*\(Expert(?: principal)?: ([^)]+)\)", item_str)
            if exp_match:
                items.append({
                    'service_name': exp_match.group(1).strip(),
                    'expert_name': exp_match.group(2).strip()
                })
            else:
                items.append({
                    'service_name': item_str,
                    'expert_name': self.employee.full_name
                })
        return items

    @property
    def experts_display(self):
        breakdown = self.multi_services_breakdown
        if not breakdown:
            return self.employee.full_name
        experts = []
        for item in breakdown:
            exp = item.get('expert_name')
            if exp and exp not in experts:
                experts.append(exp)
        if experts:
            return ", ".join(experts)
        return self.employee.full_name

    @property
    def user_custom_notes(self):
        if not self.notes:
            return ""
        import re
        cleaned = self.notes
        cleaned = re.sub(r"\[Formule Multi-Prestations:.*?\]", "", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"\[ExpertStatuses:.*?\]", "", cleaned, flags=re.DOTALL).strip()
        return cleaned

    def get_status_for_expert_name(self, exp_name):
        if self.status == 'CANCELLED':
            return 'CANCELLED'
        if not self.notes or "[ExpertStatuses:" not in self.notes:
            return self.status
        
        import re
        exp_clean = (exp_name or '').strip().lower()
        
        match = re.search(r"\[ExpertStatuses:\s*(.*?)\]", self.notes)
        if match:
            pairs = match.group(1).split(',')
            for pair in pairs:
                if '=' in pair:
                    k, v = pair.split('=', 1)
                    k_clean = k.strip().lower()
                    if k_clean == exp_clean:
                        return v.strip()
        return self.status

    def get_status_for_employee(self, emp):
        if self.status == 'CANCELLED':
            return 'CANCELLED'
        if not self.notes or "[ExpertStatuses:" not in self.notes:
            return self.status
        
        import re
        emp_username = emp.user.username.strip().lower()
        emp_fullname = emp.full_name.strip().lower()
        
        match = re.search(r"\[ExpertStatuses:\s*(.*?)\]", self.notes)
        if match:
            pairs = match.group(1).split(',')
            for pair in pairs:
                if '=' in pair:
                    k, v = pair.split('=', 1)
                    k_clean = k.strip().lower()
                    if k_clean == emp_username or k_clean == emp_fullname:
                        return v.strip()
        return self.status

    def get_status_display_for_employee(self, emp):
        st = self.get_status_for_employee(emp)
        return self.format_status_display(st)

    def set_status_for_employee(self, emp, new_status):
        import re
        emp_key = emp.user.username.strip()
        
        statuses = {}
        # Pre-fill all experts from breakdown with default or existing status
        for item in self.multi_services_breakdown:
            exp = item.get('expert_name', '').strip()
            if exp:
                statuses[exp] = self.get_status_for_expert_name(exp)

        if not statuses:
            statuses[emp_key] = new_status
        else:
            statuses[emp_key] = new_status

        # Read existing ExpertStatuses if any
        if self.notes and "[ExpertStatuses:" in self.notes:
            match = re.search(r"\[ExpertStatuses:\s*(.*?)\]", self.notes)
            if match:
                pairs = match.group(1).split(',')
                for pair in pairs:
                    if '=' in pair:
                        k, v = pair.split('=', 1)
                        statuses[k.strip()] = v.strip()
                statuses[emp_key] = new_status

        status_str = ", ".join([f"{k}={v}" for k, v in statuses.items()])
        status_tag = f"[ExpertStatuses: {status_str}]"

        if self.notes and "[ExpertStatuses:" in self.notes:
            self.notes = re.sub(r"\[ExpertStatuses:.*?\]", status_tag, self.notes)
        else:
            self.notes = f"{self.notes}\n{status_tag}".strip() if self.notes else status_tag

        # Update overall reservation status dynamically based on all experts' statuses
        all_vals = list(statuses.values())
        if any(v == 'COMPLETED' for v in all_vals):
            self.status = 'COMPLETED'
        elif any(v == 'IN_PROGRESS' for v in all_vals):
            self.status = 'IN_PROGRESS'
        elif any(v == 'ARRIVED' for v in all_vals):
            self.status = 'ARRIVED'
        elif all(v == 'CANCELLED' for v in all_vals):
            self.status = 'CANCELLED'
        elif all(v == 'NO_SHOW' for v in all_vals):
            self.status = 'NO_SHOW'
        elif any(v == 'CONFIRMED' for v in all_vals):
            self.status = 'CONFIRMED'
        else:
            self.status = new_status

        if new_status == 'NO_SHOW':
            from apps.core.models import Notification
            client_name = f"{self.client.first_name or self.client.username} {self.client.last_name}".strip()
            Notification.objects.create(
                title="🚨 Cliente Absente Signalée (No-Show)",
                message=f"La cliente {client_name} a été signalée absente par {emp.full_name} pour la réservation #{self.id} ({self.service.name}) du {self.date.strftime('%d/%m/%Y')} de {self.start_time.strftime('%H:%M')} à {self.end_time.strftime('%H:%M')}. Expert(s) : {self.experts_display}.",
                employee=None
            )

        self.save()

    def format_status_display(self, status_code):
        mapping = {
            'PENDING': '🟡 En attente',
            'CONFIRMED': '🔵 Confirmé',
            'ARRIVED': '🟣 Cliente arrivée',
            'IN_PROGRESS': '🟠 Soin en cours',
            'COMPLETED': '🟢 Terminé',
            'CANCELLED': '🔴 Annulé',
            'NO_SHOW': '⚫ Cliente absente'
        }
        return mapping.get(status_code, status_code)

    def get_services_for_employee(self, emp):
        breakdown = self.multi_services_breakdown
        if not breakdown:
            if self.employee == emp:
                return [self.service.name]
            return []
        
        emp_name = emp.full_name.strip().lower()
        emp_username = emp.user.username.strip().lower()
        
        matching_services = []
        for item in breakdown:
            exp = item.get('expert_name', '').strip().lower()
            if exp == emp_name or exp == emp_username:
                matching_services.append(item.get('service_name'))
        
        if not matching_services and self.employee == emp:
            matching_services.append(self.service.name)
            
        return matching_services

    def get_employee_service_time_windows(self, emp):
        emp_name = emp.full_name.strip().lower()
        emp_username = emp.user.username.strip().lower()
        emp_st = self.get_status_for_employee(emp)
        
        breakdown = self.multi_services_breakdown
        if not breakdown:
            if self.employee == emp:
                return [{
                    'service_name': self.service.name,
                    'start_time': self.start_time,
                    'end_time': self.end_time,
                    'status': emp_st
                }]
            return []

        dummy_date = datetime.date(2000, 1, 1)
        curr_dt = datetime.datetime.combine(dummy_date, self.start_time)
        
        emp_windows = []
        for item in breakdown:
            serv_name = item.get('service_name')
            exp = item.get('expert_name', '').strip().lower()
            
            serv_obj = Service.objects.filter(name__iexact=serv_name).first()
            dur = serv_obj.duration_minutes if serv_obj else 30
            
            s_start = curr_dt.time()
            curr_dt = curr_dt + datetime.timedelta(minutes=dur)
            s_end = curr_dt.time()
            
            if exp == emp_name or exp == emp_username:
                st = self.get_status_for_expert_name(exp)
                emp_windows.append({
                    'service_name': serv_name,
                    'start_time': s_start,
                    'end_time': s_end,
                    'status': st
                })
                
        if not emp_windows and self.employee == emp:
            emp_windows.append({
                'service_name': self.service.name,
                'start_time': self.start_time,
                'end_time': self.end_time,
                'status': emp_st
            })
            
        return emp_windows

    @property
    def multi_services_breakdown_with_times(self):
        breakdown = self.multi_services_breakdown
        if not breakdown:
            return []

        dummy_date = datetime.date(2000, 1, 1)
        curr_dt = datetime.datetime.combine(dummy_date, self.start_time)
        
        items = []
        for item in breakdown:
            serv_name = item.get('service_name')
            exp_name = item.get('expert_name')
            
            serv_obj = Service.objects.filter(name__iexact=serv_name).first()
            dur = serv_obj.duration_minutes if serv_obj else 30
            
            s_start = curr_dt.time()
            curr_dt = curr_dt + datetime.timedelta(minutes=dur)
            s_end = curr_dt.time()
            
            st = self.get_status_for_expert_name(exp_name)
            
            items.append({
                'service_name': serv_name,
                'expert_name': exp_name,
                'start_time': s_start.strftime('%H:%M'),
                'end_time': s_end.strftime('%H:%M'),
                'status': st,
                'status_display': self.format_status_display(st)
            })
            
        return items

    @property
    def get_service_windows_breakdown(self):
        breakdown = self.multi_services_breakdown
        dummy_date = datetime.date(2000, 1, 1)

        from django.db.models import Q
        from apps.core.models import Employee, Service

        if not breakdown:
            return [{
                'id': self.id,
                'reservation': self,
                'service_name': self.service.name,
                'service_category': self.service.category,
                'service_obj': self.service,
                'employee': self.employee,
                'expert_name': self.employee.full_name,
                'start_time': self.start_time,
                'end_time': self.end_time,
                'duration_minutes': self.duration_minutes,
                'status': self.status,
                'status_display': self.get_status_display(),
                'is_paid': self.is_paid,
            }]

        curr_dt = datetime.datetime.combine(dummy_date, self.start_time)
        items = []

        for item in breakdown:
            serv_name = item.get('service_name')
            exp_name = (item.get('expert_name') or '').strip()

            serv_obj = Service.objects.filter(name__iexact=serv_name).first() or self.service
            dur = serv_obj.duration_minutes if serv_obj else 30

            s_start = curr_dt.time()
            curr_dt = curr_dt + datetime.timedelta(minutes=dur)
            s_end = curr_dt.time()

            emp_obj = None
            if exp_name:
                emp_obj = Employee.objects.filter(
                    Q(user__username__iexact=exp_name) |
                    Q(first_name__iexact=exp_name) |
                    Q(last_name__iexact=exp_name)
                ).first()
                if not emp_obj:
                    for e in Employee.objects.filter(is_team_member=True):
                        if e.full_name.strip().lower() == exp_name.lower():
                            emp_obj = e
                            break
            if not emp_obj:
                emp_obj = self.employee

            st = self.get_status_for_expert_name(exp_name)

            items.append({
                'id': self.id,
                'reservation': self,
                'service_name': serv_name,
                'service_category': serv_obj.category if serv_obj else self.service.category,
                'service_obj': serv_obj,
                'employee': emp_obj,
                'expert_name': exp_name or emp_obj.full_name,
                'start_time': s_start,
                'end_time': s_end,
                'duration_minutes': dur,
                'status': st,
                'status_display': self.format_status_display(st),
                'is_paid': self.is_paid,
            })

        return items

    def clean(self):
        super().clean()
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError("L'heure de fin doit être postérieure à l'heure de début.")

            if self.status not in ['CANCELLED', 'NO_SHOW'] and self.employee_id and self.date:
                overlapping = Reservation.objects.filter(
                    employee=self.employee,
                    date=self.date,
                    start_time__lt=self.end_time,
                    end_time__gt=self.start_time
                ).exclude(status__in=['CANCELLED', 'NO_SHOW'])

                if self.pk:
                    overlapping = overlapping.exclude(pk=self.pk)

                if overlapping.exists():
                    raise ValidationError(f"L'employé {self.employee.full_name} n'est pas disponible sur le créneau {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')} le {self.date.strftime('%d/%m/%Y')}.")

                # Also check overlapping EmployeeBreak
                break_overlap = EmployeeBreak.objects.filter(
                    employee=self.employee,
                    date=self.date,
                    start_time__lt=self.end_time,
                    end_time__gt=self.start_time
                )
                if break_overlap.exists():
                    b = break_overlap.first()
                    raise ValidationError(f"L'employé {self.employee.full_name} est en pause ({b.title}: {b.start_time.strftime('%H:%M')} - {b.end_time.strftime('%H:%M')}) le {self.date.strftime('%d/%m/%Y')}.")

    @property
    def is_paid(self):
        return self.payments.filter(status='PAID').exists()

    @property
    def paid_payment(self):
        return self.payments.filter(status='PAID').first()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_employee_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'employee_profile'):
        first_name = instance.first_name or instance.username
        last_name = instance.last_name or ""
        if instance.is_staff or instance.is_superuser:
            role = 'ADMINISTRATEUR'
            is_team_member = False
            position = "Administrateur ERP"
            department = "Direction"
        else:
            role = 'USER'
            is_team_member = False
            position = "Utilisateur"
            department = "Général"
        Employee.objects.create(
            user=instance,
            first_name=first_name,
            last_name=last_name,
            email=instance.email or "",
            role=role,
            position=position,
            department=department,
            is_team_member=is_team_member,
            is_active=True
        )


class Order(models.Model):
    objects = models.Manager()
    items: models.Manager

    DELIVERY_CHOICES = [
        ('DELIVERY', 'Livraison à domicile'),
        ('CLICK_COLLECT', 'Click & Collect'),
    ]

    PAYMENT_MODE_CHOICES = [
        ('COD', 'Paiement à la livraison'),
        ('CARD', 'Carte bancaire'),
        ('STORE', 'Paiement au retrait'),
    ]

    ORDER_STATUS_CHOICES = [
        ('NEW', 'Nouvelle'),
        ('CONFIRMED', 'Confirmée'),
        ('PREPARING', 'En préparation'),
        ('READY_FOR_PICKUP', 'Prête au retrait'),
        ('RETRIEVED', 'Retirée'),
        ('SHIPPED', 'Expédiée'),
        ('DELIVERING', 'En livraison'),
        ('DELIVERED', 'Livrée'),
        ('CANCELLED', 'Annulée'),
    ]

    CLICK_COLLECT_STATUS_CHOICES = [
        ('NEW', 'Nouvelle'),
        ('CONFIRMED', 'Confirmée'),
        ('PREPARING', 'En préparation'),
        ('READY_FOR_PICKUP', 'Prête au retrait'),
        ('RETRIEVED', 'Retirée'),
        ('CANCELLED', 'Annulée'),
    ]

    DELIVERY_STATUS_CHOICES = [
        ('NEW', 'Nouvelle'),
        ('CONFIRMED', 'Confirmée'),
        ('PREPARING', 'En préparation'),
        ('SHIPPED', 'Expédiée'),
        ('DELIVERING', 'En livraison'),
        ('DELIVERED', 'Livrée'),
        ('CANCELLED', 'Annulée'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('PAID', 'Payé'),
        ('FAILED', 'Échoué'),
        ('REFUNDED', 'Remboursé'),
        ('CANCELLED', 'Annulée'),
    ]

    client = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name="Client")
    client_name = models.CharField(max_length=150, verbose_name="Nom du client")
    client_phone = models.CharField(max_length=30, verbose_name="Téléphone")
    client_email = models.EmailField(blank=True, verbose_name="Email")
    shipping_address = models.TextField(blank=True, verbose_name="Adresse de livraison")
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Sous-total (DH)")
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Frais de livraison (DH)")
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Total Général (DH)")
    
    delivery_mode = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='DELIVERY', verbose_name="Mode de livraison")
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, default='COD', verbose_name="Mode de paiement")
    
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='NEW', verbose_name="Statut commande")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING', verbose_name="Statut paiement")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de commande")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-created_at']

    def __str__(self):
        return f"Commande #{self.id} - {self.client_name} ({self.total} DH)"


class OrderItem(models.Model):
    objects = models.Manager()
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Commande")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Produit")
    product_name = models.CharField(max_length=200, verbose_name="Nom du produit")
    product_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire (DH)")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantité")
    variant = models.CharField(max_length=100, blank=True, verbose_name="Nuance / Variante")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Sous-total (DH)")

    class Meta:
        verbose_name = "Article de commande"
        verbose_name_plural = "Articles de commande"

    def __str__(self):
        return f"{self.quantity}x {self.product_name} ({self.subtotal} DH)"


class Payment(models.Model):
    objects = models.Manager()
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Espèces 💵'),
        ('CARD', 'Carte bancaire 💳'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'En attente 🟡'),
        ('PAID', 'Payé 🟢'),
        ('REFUNDED', 'Remboursé 🔴'),
    ]
    PAYMENT_TYPE_CHOICES = [
        ('SERVICE', '💇 Service'),
        ('BOUTIQUE', '🛍️ Boutique'),
        ('AUTRE', '🏪 Autre'),
    ]
    client = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments', verbose_name="Cliente")
    reservation = models.ForeignKey(Reservation, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments', verbose_name="Réservation")
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments', verbose_name="Commande")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant (DH)")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='CASH', verbose_name="Moyen de paiement")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='SERVICE', verbose_name="Type de paiement")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PAID', verbose_name="Statut")
    notes = models.TextField(blank=True, verbose_name="Notes")
    receptionist = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_payments', verbose_name="Réceptionniste ayant encaissé")
    refunded_at = models.DateTimeField(null=True, blank=True, verbose_name="Date du remboursement")
    refund_reason = models.TextField(blank=True, verbose_name="Raison du remboursement")
    refunded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='refunded_payments', verbose_name="Remboursé par")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Date et heure du paiement")

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-created_at']

    def __str__(self):
        return f"Paiement #{self.id} - {self.amount} DH ({self.get_payment_method_display()}) - {self.get_status_display()}"

    @property
    def reference_code(self):
        return f"#PAY-{self.id:05d}"

    @property
    def origin_info(self):
        if self.reservation:
            return {
                'code': 'SERVICE',
                'label': 'Service',
                'icon': 'bi-scissors',
                'badge_class': 'bg-purple bg-opacity-10 text-dark border-purple fw-bold',
                'display': '💇 Service'
            }
        elif self.order:
            if self.order.delivery_mode == 'CLICK_COLLECT':
                return {
                    'code': 'CLICK_COLLECT',
                    'label': 'Click & Collect',
                    'icon': 'bi-shop',
                    'badge_class': 'bg-info bg-opacity-10 text-dark border-info fw-bold',
                    'display': '🏪 Click & Collect'
                }
            else:
                return {
                    'code': 'LIVRAISON',
                    'label': 'Livraison',
                    'icon': 'bi-truck',
                    'badge_class': 'bg-primary bg-opacity-10 text-dark border-primary fw-bold',
                    'display': '📦 Livraison'
                }
        else:
            if self.payment_type == 'BOUTIQUE':
                return {
                    'code': 'BOUTIQUE',
                    'label': 'Boutique',
                    'icon': 'bi-bag',
                    'badge_class': 'bg-warning bg-opacity-10 text-dark border-warning fw-bold',
                    'display': '🛍️ Boutique'
                }
            elif self.payment_type == 'SERVICE':
                return {
                    'code': 'SERVICE',
                    'label': 'Service',
                    'icon': 'bi-scissors',
                    'badge_class': 'bg-purple bg-opacity-10 text-dark border-purple fw-bold',
                    'display': '💇 Service'
                }
            else:
                return {
                    'code': 'DIRECT',
                    'label': 'Encaissement direct',
                    'icon': 'bi-cash-stack',
                    'badge_class': 'bg-secondary bg-opacity-10 text-dark border-secondary fw-bold',
                    'display': '🏪 Encaissement direct'
                }

    @property
    def service_or_product_display(self):
        if self.reservation:
            return self.reservation.service.name
        elif self.order:
            items = list(self.order.items.all())
            if items:
                return ", ".join([f"{item.quantity}x {item.product_name}" for item in items])
            return f"Commande Boutique #{self.order.id}"
        elif self.notes:
            return self.notes.split('\n')[0]
        return "Encaissement libre"

    @property
    def client_display_name(self):
        if self.client:
            full = f"{self.client.first_name} {self.client.last_name}".strip()
            return full if full else self.client.username
        elif self.order and self.order.client_name:
            return self.order.client_name
        return "Cliente de passage"

    @property
    def receptionist_display_name(self):
        if self.receptionist:
            full = f"{self.receptionist.first_name} {self.receptionist.last_name}".strip()
            return full if full else self.receptionist.username
        return "Réception Salon"

