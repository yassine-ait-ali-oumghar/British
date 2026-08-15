from django.urls import path
from . import views

urlpatterns = [
    # Public Pages
    path('', views.frontpage, name='frontpage'),
    path('contact/', views.contact, name='contact'),
    path('services/', views.services, name='services'),
    path('equipe/', views.equipe, name='equipe'),
    path('boutique/', views.boutique, name='boutique'),

    # Client Booking, Orders & Reservations
    path('reservation/nouvelle/', views.reservation_create, name='reservation_create'),
    path('mes-reservations/', views.client_reservations, name='client_reservations'),
    path('api/available-slots/', views.api_available_slots, name='api_available_slots'),
    path('api/orders/create/', views.api_create_order, name='api_create_order'),

    # Professional ERP Dashboard (Admin Protected)
    path('dashboard/', views.dashboard_overview, name='dashboard_overview'),
    path('dashboard/orders/', views.dashboard_orders, name='dashboard_orders'),
    path('dashboard/reservations/', views.dashboard_reservations, name='dashboard_reservations'),
    path('dashboard/users/', views.dashboard_users, name='dashboard_users'),
    path('dashboard/employees/', views.dashboard_employees, name='dashboard_employees'),
    path('dashboard/products/', views.dashboard_products, name='dashboard_products'),
    path('dashboard/services/', views.dashboard_services, name='dashboard_services'),
    path('dashboard/attendance/', views.dashboard_attendance_log, name='dashboard_attendance_log'),
    path('dashboard/pointage/', views.dashboard_attendance_log, name='dashboard_pointage'),
    path('dashboard/messages/', views.dashboard_messages, name='dashboard_messages'),
    path('dashboard/notifications/', views.dashboard_notifications, name='dashboard_notifications'),
    path('dashboard/performance/', views.dashboard_performance, name='dashboard_performance'),
    path('dashboard/settings/', views.dashboard_settings, name='dashboard_settings'),

    # Actions & Live APIs
    path('dashboard/update-status/', views.update_employee_status, name='update_employee_status'),
    path('dashboard/api/live-stats/', views.api_live_stats, name='api_live_stats'),
    path('dashboard/api/search/', views.api_global_search, name='api_global_search'),
    path('dashboard/api/employee/<int:employee_id>/', views.api_employee_detail, name='api_employee_detail'),

    # Dedicated Employee Interface (Role EMPLOYEE & is_team_member Protected)
    path('employee/dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('employee/pointage/', views.employee_pointage, name='employee_pointage'),
    path('employee/historique/', views.employee_historique, name='employee_historique'),
    path('employee/calendrier/', views.employee_calendrier, name='employee_calendrier'),
    path('employee/profil/', views.employee_profil, name='employee_profil'),
    path('employee/notifications/', views.employee_notifications, name='employee_notifications'),
    path('employee/access-denied/', views.employee_access_denied, name='employee_access_denied'),

    # Employee AJAX APIs
    path('employee/api/clock-action/', views.employee_clock_action, name='employee_clock_action'),
    path('employee/api/live-stats/', views.employee_live_stats, name='employee_live_stats'),
    path('employee/api/calendar-detail/<int:day>/', views.employee_calendar_detail, name='employee_calendar_detail'),

    # Dedicated Receptionist Space (Role RECEPTION & ADMINISTRATEUR Protected)
    path('reception/dashboard/', views.reception_dashboard, name='reception_dashboard'),
    path('reception/planning/', views.reception_planning, name='reception_planning'),
    path('reception/reservations/create/', views.reception_reservation_create, name='reception_reservation_create'),
    path('reception/reservations/<int:pk>/edit/', views.reception_reservation_edit, name='reception_reservation_edit'),
    path('reception/reservations/<int:pk>/arrived/', views.reception_reservation_arrived, name='reception_reservation_arrived'),
    path('reception/reservations/<int:pk>/cancel/', views.reception_reservation_cancel, name='reception_reservation_cancel'),
    path('reception/payments/', views.reception_payments, name='reception_payments'),
    path('reception/orders/', views.reception_orders, name='reception_orders'),
    path('reception/orders/<int:pk>/confirm-pickup/', views.reception_confirm_pickup, name='reception_confirm_pickup'),
    path('reception/clients/', views.reception_clients, name='reception_clients'),
    path('reception/notifications/', views.reception_notifications, name='reception_notifications'),

    # Reception AJAX APIs
    path('reception/api/live-stats/', views.reception_api_live_stats, name='reception_api_live_stats'),
    path('reception/api/check-availability/', views.reception_api_check_availability, name='reception_api_check_availability'),
]