# ==============================================================================
# ROUTAGE ET CARTOGRAPHIE DES URLS DE L'APPLICATION CORE
# ==============================================================================
# Ce fichier fait le lien entre chaque adresse URL (parcours navigateur ou API)
# et la fonction de Vue correspondante dans views.py.
# ==============================================================================

from django.urls import path
from . import views

urlpatterns = [
    # --------------------------------------------------------------------------
    # 1. VITRINE PUBLIQUE (Accès libre sans connexion)
    # --------------------------------------------------------------------------
    path('', views.frontpage, name='frontpage'),            # Page d'accueil
    path('contact/', views.contact, name='contact'),        # Formulaire de contact
    path('services/', views.services, name='services'),    # Grille des prestations & tarifs
    path('equipe/', views.equipe, name='equipe'),          # Présentation des coiffeurs / barbiers
    path('boutique/', views.boutique, name='boutique'),    # Catalogue e-commerce & Panier

    # --------------------------------------------------------------------------
    # 2. RÉSERVATIONS CLIENTS & COMMANDES BOUTIQUE
    # --------------------------------------------------------------------------
    path('reservation/nouvelle/', views.reservation_create, name='reservation_create'), # Enregistrer un RDV
    path('mes-reservations/', views.client_reservations, name='client_reservations'),   # Historique du client
    path('api/available-slots/', views.api_available_slots, name='api_available_slots'), # API créneaux libres (AJAX)
    path('api/orders/create/', views.api_create_order, name='api_create_order'),         # API création commande (AJAX)

    # --------------------------------------------------------------------------
    # 3. TABLEAU DE BORD ADMINISTRATEUR / ERP (Accès @admin_required)
    # --------------------------------------------------------------------------
    path('dashboard/', views.dashboard_overview, name='dashboard_overview'),            # Vue d'ensemble & Stats
    path('dashboard/orders/', views.dashboard_orders, name='dashboard_orders'),        # Commandes boutique
    path('dashboard/reservations/', views.dashboard_reservations, name='dashboard_reservations'), # Tous les RDV
    path('dashboard/users/', views.dashboard_users, name='dashboard_users'),            # Comptes clients
    path('dashboard/employees/', views.dashboard_employees, name='dashboard_employees'),# Gestion du personnel
    path('dashboard/products/', views.dashboard_products, name='dashboard_products'),  # Gestion du stock boutique
    path('dashboard/services/', views.dashboard_services, name='dashboard_services'),  # Tarifs des prestations
    path('dashboard/attendance/', views.dashboard_attendance_log, name='dashboard_attendance_log'), # Registre des pointages
    path('dashboard/pointage/', views.dashboard_attendance_log, name='dashboard_pointage'),
    path('dashboard/messages/', views.dashboard_messages, name='dashboard_messages'),  # Messages formulaire contact
    path('dashboard/notifications/', views.dashboard_notifications, name='dashboard_notifications'), # Alerts
    path('dashboard/performance/', views.dashboard_performance, name='dashboard_performance'), # Graphiques & Scores
    path('dashboard/settings/', views.dashboard_settings, name='dashboard_settings'),   # Paramètres généraux

    # APIs Administrateur
    path('dashboard/update-status/', views.update_employee_status, name='update_employee_status'),
    path('dashboard/api/live-stats/', views.api_live_stats, name='api_live_stats'),     # Stats live ERP
    path('dashboard/api/search/', views.api_global_search, name='api_global_search'),   # Recherche globale
    path('dashboard/api/employee/<int:employee_id>/', views.api_employee_detail, name='api_employee_detail'),

    # --------------------------------------------------------------------------
    # 4. ESPACE MEMBRE EMPLOYE / COIFFEUR (Accès @employee_required)
    # --------------------------------------------------------------------------
    path('employee/dashboard/', views.employee_dashboard, name='employee_dashboard'),   # Chrono & RDV du jour
    path('employee/pointage/', views.employee_pointage, name='employee_pointage'),      # Interface de pointage
    path('employee/historique/', views.employee_historique, name='employee_historique'),# Bilan d'heures mensuel
    path('employee/calendrier/', views.employee_calendrier, name='employee_calendrier'),# Planning interactif
    path('employee/profil/', views.employee_profil, name='employee_profil'),            # Profil personnel
    path('employee/notifications/', views.employee_notifications, name='employee_notifications'),
    path('employee/access-denied/', views.employee_access_denied, name='employee_access_denied'), # Page de refus

    # APIs Employé (AJAX)
    path('employee/api/clock-action/', views.employee_clock_action, name='employee_clock_action'), # Action pointage
    path('employee/api/live-stats/', views.employee_live_stats, name='employee_live_stats'),     # Chrono temps réel
    path('employee/api/calendar-detail/<int:day>/', views.employee_calendar_detail, name='employee_calendar_detail'),

    # --------------------------------------------------------------------------
    # 5. ESPACE RÉCEPTIONNISTE & CAISSE POS (Accès @reception_required)
    # --------------------------------------------------------------------------
    path('reception/dashboard/', views.reception_dashboard, name='reception_dashboard'),# Accueil des clients du jour
    path('reception/planning/', views.reception_planning, name='reception_planning'),   # Grille horaire salon
    path('reception/reservations/create/', views.reception_reservation_create, name='reception_reservation_create'),
    path('reception/reservations/<int:pk>/edit/', views.reception_reservation_edit, name='reception_reservation_edit'),
    path('reception/reservations/<int:pk>/arrived/', views.reception_reservation_arrived, name='reception_reservation_arrived'),
    path('reception/reservations/<int:pk>/cancel/', views.reception_reservation_cancel, name='reception_reservation_cancel'),
    path('reception/payments/', views.reception_payments, name='reception_payments'),   # Caisse & Encaissement
    path('reception/orders/', views.reception_orders, name='reception_orders'),         # Retrait commandes boutique
    path('reception/orders/<int:pk>/confirm-pickup/', views.reception_confirm_pickup, name='reception_confirm_pickup'),
    path('reception/clients/', views.reception_clients, name='reception_clients'),       # Fichier clients
    path('reception/notifications/', views.reception_notifications, name='reception_notifications'),

    # APIs Réception (AJAX)
    path('reception/api/live-stats/', views.reception_api_live_stats, name='reception_api_live_stats'),
    path('reception/api/check-availability/', views.reception_api_check_availability, name='reception_api_check_availability'),
]