from functools import wraps
import datetime
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Q, Sum, Count
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .models import Employee, AttendanceRecord, Product, Service, ContactMessage, Notification, Reservation, EmployeeBreak, Order, OrderItem, Payment

# ==============================================================================
# DÉCORATEURS DE SÉCURITÉ ET CONTRÔLE D'ACCÈS PAR RÔLE
# ==============================================================================

def admin_required(view_func):
    """
    Décorateur restreignant l'accès aux pages Administrateur / ERP.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/accounts/login/?next={request.path}")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def employee_required(view_func):
    """
    Décorateur restreignant l'accès à l'Espace Membre Employé / Coiffeur.
    L'administrateur n'a pas accès à cet espace.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/accounts/login/?next={request.path}")
        if request.user.is_staff or request.user.is_superuser or (hasattr(request.user, 'employee_profile') and request.user.employee_profile and request.user.employee_profile.role == 'ADMINISTRATEUR'):
            messages.warning(request, "L'administrateur a uniquement accès au Dashboard Admin ERP.")
            return redirect('dashboard_overview')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def reception_required(view_func):
    """
    Décorateur restreignant l'accès à l'Espace Réception & Caisse / POS.
    L'administrateur n'a pas accès à cet espace.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/accounts/login/?next={request.path}")
        if request.user.is_staff or request.user.is_superuser or (hasattr(request.user, 'employee_profile') and request.user.employee_profile and request.user.employee_profile.role == 'ADMINISTRATEUR'):
            messages.warning(request, "L'administrateur a uniquement accès au Dashboard Admin ERP.")
            return redirect('dashboard_overview')
        return view_func(request, *args, **kwargs)
    return _wrapped_view




# ==============================================================================
# VUES PUBLIQUES (ACCÈS LIBRE SANS CONNEXION)
# ==============================================================================

def frontpage(request):
    """Affiche la page d'accueil avec le Hero banner et la présentation du salon."""
    return render(request, 'core/frontpage.html')  

def contact(request):
    """Traitement du formulaire de contact et affichage de la page Contact."""
    success_msg = None
    # Étape 1 : Si la demande est envoyée via le formulaire (méthode POST)
    if request.method == 'POST':
        # Étape 2 : Récupération des données du formulaire HTML
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip() or "Demande de contact"
        message = request.POST.get('message', '').strip()
        
        # Étape 3 : Validation et enregistrement dans le modèle ContactMessage en BDD
        if name and email and message:
            ContactMessage.objects.create(
                name=name, email=email, phone=phone, subject=subject, message=message
            )
            success_msg = "Votre message a bien été envoyé ! Notre équipe vous répondra dans les plus brefs délais."
            
    # Étape 4 : Rendu du template HTML avec le message de confirmation si présent
    return render(request, 'core/contact.html', {'success_msg': success_msg})

def services(request):
    """Affiche le catalogue des prestations (coupes, barbe, soins) et la liste des coiffeurs."""
    # Étape 1 : Récupère les prestations actives en base de données
    services_list = Service.objects.filter(is_active=True)
    # Étape 2 : Récupère les coiffeurs membres de l'équipe
    employees_list = Employee.objects.filter(is_team_member=True, is_active=True).exclude(role='ADMINISTRATEUR').order_by('first_name')
    # Étape 3 : Injecte les données dans le template services.html
    return render(request, 'core/services.html', {
        'services_list': services_list,
        'employees_list': employees_list
    })  

def equipe(request):
    """Affiche la page de présentation de l'équipe de coiffeurs et barbiers."""
    team_members = Employee.objects.filter(is_team_member=True, is_active=True).exclude(role='ADMINISTRATEUR').order_by('id')
    return render(request, 'core/equipe.html', {'team_members': team_members})

def boutique(request):
    """Affiche la boutique e-commerce avec les produits cosmétiques disponibles."""
    products_list = Product.objects.filter(is_available=True)
    return render(request, 'core/boutique.html', {'products_list': products_list})


# ==========================================
# ERP DASHBOARD VIEWS (STRICT ACCESS CONTROL)
# ==========================================

@admin_required
def dashboard_overview(request):
    today = timezone.now().date()
    team_employees = Employee.objects.filter(is_team_member=True, is_active=True)
    
    total_team = team_employees.count()
    present_count = 0
    pause_count = 0
    repos_count = 0
    absent_count = 0

    for emp in team_employees:
        st = emp.get_current_status()
        if st == 'PRESENT':
            present_count += 1
        elif st == 'PAUSE':
            pause_count += 1
        elif st == 'REPOS':
            repos_count += 1
        else:
            absent_count += 1

    # Dynamic Hours Calculations across team
    hours_today = sum(e.get_hours_worked_today() for e in team_employees)
    hours_week = sum(e.get_hours_worked_this_week() for e in team_employees)
    hours_month = sum(e.get_hours_worked_this_month() for e in team_employees)

    # Formatters
    def fmt_hours(hours):
        h = int(hours)
        m = int(round((hours - h) * 60))
        return f"{h}h {m:02d}m"

    # Module Counters
    total_all_employees = Employee.objects.count()
    total_products = Product.objects.count()
    total_services = Service.objects.count()
    new_messages_count = ContactMessage.objects.filter(status='NEW').count()
    recent_messages = ContactMessage.objects.all()[:5]

    # Daily User Entries for the current week (Lun-Dim)
    start_of_week = today - datetime.timedelta(days=today.weekday())
    daily_user_entries = []
    for i in range(7):
        d = start_of_week + datetime.timedelta(days=i)
        if d <= today:
            cnt = AttendanceRecord.objects.filter(date=d, check_in__isnull=False).values('employee').distinct().count()
        else:
            cnt = 0
        daily_user_entries.append(cnt)

    context = {
        'page_title': 'Dashboard Overview',
        'active_menu': 'dashboard',
        'today_date': today.strftime('%d/%m/%Y'),
        'total_team': total_team,
        'present_count': present_count,
        'pause_count': pause_count,
        'repos_count': repos_count,
        'absent_count': absent_count,
        'hours_today_fmt': fmt_hours(hours_today),
        'hours_week_fmt': fmt_hours(hours_week),
        'hours_month_fmt': fmt_hours(hours_month),
        'total_all_employees': total_all_employees,
        'total_products': total_products,
        'total_services': total_services,
        'new_messages_count': new_messages_count,
        'recent_messages': recent_messages,
        'team_employees': team_employees,
        'daily_user_entries': daily_user_entries,
        'new_orders_count': Order.objects.filter(order_status='NEW').count(),
        'total_orders_count': Order.objects.count(),
    }
    return render(request, 'core/admin/dashboard_overview.html', context)


@admin_required
def dashboard_employees(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        emp_id = request.POST.get('employee_id')
        
        if action == 'create':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            position = request.POST.get('position')
            department = request.POST.get('department', 'Salon')
            role = request.POST.get('role', 'EMPLOYEE')
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            password = request.POST.get('password', '').strip()
            avatar_color = request.POST.get('avatar_color', '#c5a059')
            photo_file = request.FILES.get('photo_file')
            
            if first_name and last_name:
                user_obj = None
                if email and password:
                    username_base = email.split('@')[0].lower() if '@' in email else f"{first_name.lower()}_{last_name.lower()}"
                    username = username_base
                    cnt = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{username_base}{cnt}"
                        cnt += 1
                    
                    user_obj = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name
                    )
                    if role == 'ADMINISTRATEUR':
                        user_obj.is_staff = True
                        user_obj.save()

                if user_obj and hasattr(user_obj, 'employee_profile'):
                    emp = user_obj.employee_profile
                    emp.first_name = first_name
                    emp.last_name = last_name
                    emp.position = position
                    emp.department = department
                    emp.role = role
                    emp.email = email
                    emp.phone = phone
                    emp.avatar_color = avatar_color
                    emp.is_team_member = True
                    emp.is_active = True
                    emp.save()
                else:
                    emp = Employee.objects.create(
                        user=user_obj,
                        first_name=first_name, last_name=last_name, position=position,
                        department=department, role=role, email=email, phone=phone,
                        avatar_color=avatar_color, is_team_member=True, is_active=True
                    )
                if photo_file:
                    from django.core.files.storage import FileSystemStorage
                    import os
                    avatars_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
                    os.makedirs(avatars_dir, exist_ok=True)
                    fs = FileSystemStorage(location=avatars_dir, base_url='/media/avatars/')
                    ext = os.path.splitext(photo_file.name)[1]
                    filename = fs.save(f"emp_{emp.id}_{int(timezone.now().timestamp())}{ext}", photo_file)
                    emp.photo = fs.url(filename)
                    emp.save()

        elif action == 'edit' and emp_id:
            emp = get_object_or_404(Employee, id=emp_id)
            password = request.POST.get('password', '').strip()
            emp.first_name = request.POST.get('first_name', emp.first_name)
            emp.last_name = request.POST.get('last_name', emp.last_name)
            emp.position = request.POST.get('position', emp.position)
            emp.department = request.POST.get('department', emp.department)
            emp.role = request.POST.get('role', emp.role)
            emp.email = request.POST.get('email', emp.email)
            emp.phone = request.POST.get('phone', emp.phone)
            emp.avatar_color = request.POST.get('avatar_color', emp.avatar_color)

            if password:
                if emp.user:
                    emp.user.set_password(password)
                    emp.user.email = emp.email
                    emp.user.first_name = emp.first_name
                    emp.user.last_name = emp.last_name
                    if emp.role == 'ADMINISTRATEUR':
                        emp.user.is_staff = True
                    emp.user.save()
                elif emp.email:
                    username_base = emp.email.split('@')[0].lower() if '@' in emp.email else f"{emp.first_name.lower()}_{emp.last_name.lower()}"
                    username = username_base
                    cnt = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{username_base}{cnt}"
                        cnt += 1
                    u_obj = User.objects.create_user(
                        username=username,
                        email=emp.email,
                        password=password,
                        first_name=emp.first_name,
                        last_name=emp.last_name
                    )
                    if emp.role == 'ADMINISTRATEUR':
                        u_obj.is_staff = True
                        u_obj.save()
                    emp.user = u_obj

            emp.save()

        elif action == 'toggle_active' and emp_id:
            emp = get_object_or_404(Employee, id=emp_id)
            emp.is_active = not emp.is_active
            emp.save()

        elif action == 'toggle_team' and emp_id:
            emp = get_object_or_404(Employee, id=emp_id)
            emp.is_team_member = not emp.is_team_member
            emp.save()

        elif action == 'delete' and emp_id:
            emp = get_object_or_404(Employee, id=emp_id)
            emp.delete()

        return redirect('/dashboard/employees/')

    query = request.GET.get('q', '')
    employees = Employee.objects.filter(is_team_member=True)
    if query:
        employees = employees.filter(
            Q(
                first_name__icontains=query,
                last_name__icontains=query,
                position__icontains=query,
                email__icontains=query,
                _connector=Q.OR,
            )
        )

    context = {
        'page_title': 'Gestion des Employés',
        'active_menu': 'employees',
        'employees': employees,
        'query': query,
    }
    return render(request, 'core/admin/dashboard_employees.html', context)


@admin_required
def dashboard_users(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        emp_id = request.POST.get('employee_id')
        user_id = request.POST.get('user_id')

        if action in ['add_to_team', 'edit_user_team']:
            target_emp = None
            if emp_id:
                target_emp = get_object_or_404(Employee, id=emp_id)
            elif user_id:
                target_user = get_object_or_404(User, id=user_id)
                target_emp = getattr(target_user, 'employee_profile', None)
                if not target_emp:
                    target_emp = Employee.objects.create(
                        user=target_user,
                        first_name=target_user.first_name or target_user.username,
                        last_name=target_user.last_name or "",
                        email=target_user.email or ""
                    )

            if target_emp:
                first_name = request.POST.get('first_name', '').strip()
                last_name = request.POST.get('last_name', '').strip()
                position = request.POST.get('position', '').strip() or 'Employé'
                department = request.POST.get('department', '').strip() or 'Salon'
                role = request.POST.get('role', 'EMPLOYEE')
                avatar_color = request.POST.get('avatar_color', '').strip()
                phone = request.POST.get('phone', '').strip()
                email = request.POST.get('email', '').strip()

                if first_name:
                    target_emp.first_name = first_name
                    if target_emp.user:
                        target_emp.user.first_name = first_name
                if last_name is not None:
                    target_emp.last_name = last_name
                    if target_emp.user:
                        target_emp.user.last_name = last_name
                if email:
                    target_emp.email = email
                    if target_emp.user:
                        target_emp.user.email = email
                if target_emp.user:
                    target_emp.user.save()

                target_emp.position = position
                target_emp.department = department
                target_emp.role = role
                
                photo_file = request.FILES.get('photo_file')
                if photo_file:
                    from django.core.files.storage import FileSystemStorage
                    import os
                    avatars_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
                    os.makedirs(avatars_dir, exist_ok=True)
                    fs = FileSystemStorage(location=avatars_dir, base_url='/media/avatars/')
                    ext = os.path.splitext(photo_file.name)[1]
                    filename = fs.save(f"emp_{target_emp.id}_{int(timezone.now().timestamp())}{ext}", photo_file)
                    target_emp.photo = fs.url(filename)
                
                if phone:
                    target_emp.phone = phone
                if avatar_color:
                    target_emp.avatar_color = avatar_color

                target_emp.is_team_member = True
                target_emp.is_active = True
                target_emp.save()

                password = request.POST.get('password', '').strip()
                if password:
                    if target_emp.user:
                        target_emp.user.set_password(password)
                        target_emp.user.save()
                    elif email:
                        username_base = email.split('@')[0].lower() if '@' in email else f"{first_name.lower()}_{last_name.lower()}"
                        username = username_base
                        cnt = 1
                        while User.objects.filter(username=username).exists():
                            username = f"{username_base}{cnt}"
                            cnt += 1
                        u_obj = User.objects.create_user(
                            username=username,
                            email=email,
                            password=password,
                            first_name=first_name or target_emp.first_name,
                            last_name=last_name or target_emp.last_name
                        )
                        if role == 'ADMINISTRATEUR':
                            u_obj.is_staff = True
                            u_obj.save()
                        target_emp.user = u_obj

                if role == 'ADMINISTRATEUR' and target_emp.user:
                    target_emp.user.is_staff = True
                    target_emp.user.save()

        elif action == 'remove_from_team' and emp_id:
            target_emp = get_object_or_404(Employee, id=emp_id)
            target_emp.is_team_member = False
            target_emp.role = 'USER'
            target_emp.save()

        elif action == 'delete_user' and emp_id:
            target_emp = get_object_or_404(Employee, id=emp_id)
            if target_emp.user:
                if target_emp.user != request.user and not target_emp.user.is_superuser:
                    target_emp.user.delete()
            else:
                target_emp.delete()

        return redirect('/dashboard/users/')

    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', 'all')

    users_without_profile = User.objects.filter(employee_profile__isnull=True)
    for u in users_without_profile:
        Employee.objects.create(
            user=u,
            first_name=u.first_name or u.username,
            last_name=u.last_name or "",
            email=u.email or "",
            role='ADMINISTRATEUR' if (u.is_staff or u.is_superuser) else 'USER',
            position="Administrateur ERP" if (u.is_staff or u.is_superuser) else "Utilisateur",
            department="Direction" if (u.is_staff or u.is_superuser) else "Général",
            is_team_member=False,
            is_active=True
        )

    all_employees = Employee.objects.select_related('user').all().order_by('-created_at')

    if query:
        all_employees = all_employees.filter(
            Q(
                first_name__icontains=query,
                last_name__icontains=query,
                email__icontains=query,
                user__username__icontains=query,
                position__icontains=query,
                _connector=Q.OR,
            )
        )

    if status_filter == 'users':
        all_employees = all_employees.filter(is_team_member=False)
    elif status_filter == 'team':
        all_employees = all_employees.filter(is_team_member=True)

    total_users_count = Employee.objects.count()
    simple_users_count = Employee.objects.filter(is_team_member=False).count()
    team_members_count = Employee.objects.filter(is_team_member=True).count()

    context = {
        'page_title': 'Gestion des Utilisateurs',
        'active_menu': 'users',
        'employees_list': all_employees,
        'query': query,
        'status_filter': status_filter,
        'total_users_count': total_users_count,
        'simple_users_count': simple_users_count,
        'team_members_count': team_members_count,
    }
    return render(request, 'core/admin/dashboard_users.html', context)


@admin_required
def dashboard_products(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        prod_id = request.POST.get('product_id')

        if action == 'create':
            name = request.POST.get('name')
            category = request.POST.get('category')
            price = request.POST.get('price', 0)
            stock = request.POST.get('stock', 0)
            is_available = request.POST.get('is_available') == 'on'
            image_url = request.POST.get('image_url', '').strip()
            description = request.POST.get('description', '')
            image_file = request.FILES.get('image_file')

            if image_file:
                from django.core.files.storage import FileSystemStorage
                import os
                products_dir = os.path.join(settings.MEDIA_ROOT, 'products')
                os.makedirs(products_dir, exist_ok=True)
                fs = FileSystemStorage(location=products_dir, base_url='/media/products/')
                ext = os.path.splitext(image_file.name)[1]
                filename = fs.save(f"prod_{int(timezone.now().timestamp())}_{random.randint(100,999)}{ext}", image_file)
                image_url = fs.url(filename)

            if name and price:
                Product.objects.create(
                    name=name, category=category, price=price, stock=stock,
                    is_available=is_available, image_url=image_url, description=description
                )

        elif action == 'edit' and prod_id:
            prod = get_object_or_404(Product, id=prod_id)
            prod.name = request.POST.get('name', prod.name)
            prod.category = request.POST.get('category', prod.category)
            prod.price = request.POST.get('price', prod.price)
            prod.stock = request.POST.get('stock', prod.stock)
            prod.is_available = request.POST.get('is_available') == 'on'
            image_url_input = request.POST.get('image_url', '').strip()
            if image_url_input:
                prod.image_url = image_url_input
            prod.description = request.POST.get('description', prod.description)

            image_file = request.FILES.get('image_file')
            if image_file:
                from django.core.files.storage import FileSystemStorage
                import os
                products_dir = os.path.join(settings.MEDIA_ROOT, 'products')
                os.makedirs(products_dir, exist_ok=True)
                fs = FileSystemStorage(location=products_dir, base_url='/media/products/')
                ext = os.path.splitext(image_file.name)[1]
                filename = fs.save(f"prod_{prod.id}_{int(timezone.now().timestamp())}{ext}", image_file)
                prod.image_url = fs.url(filename)

            prod.save()

        elif action == 'toggle_available' and prod_id:
            prod = get_object_or_404(Product, id=prod_id)
            prod.is_available = not prod.is_available
            prod.save()

        elif action == 'delete' and prod_id:
            prod = get_object_or_404(Product, id=prod_id)
            prod.delete()

        return redirect('/dashboard/products/')

    products = Product.objects.all()
    context = {
        'page_title': 'Gestion des Produits',
        'active_menu': 'products',
        'products': products,
    }
    return render(request, 'core/admin/dashboard_products.html', context)


@admin_required
def dashboard_services(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        serv_id = request.POST.get('service_id')

        if action == 'create':
            name = request.POST.get('name')
            category = request.POST.get('category')
            price = request.POST.get('price', 0)
            duration_minutes = request.POST.get('duration_minutes', 30)
            is_active = request.POST.get('is_active') == 'on'
            image_url = request.POST.get('image_url', '')
            description = request.POST.get('description', '')

            if name and price:
                Service.objects.create(
                    name=name, category=category, price=price, duration_minutes=duration_minutes,
                    is_active=is_active, image_url=image_url, description=description
                )

        elif action == 'edit' and serv_id:
            serv = get_object_or_404(Service, id=serv_id)
            serv.name = request.POST.get('name', serv.name)
            serv.category = request.POST.get('category', serv.category)
            serv.price = request.POST.get('price', serv.price)
            serv.duration_minutes = request.POST.get('duration_minutes', serv.duration_minutes)
            serv.is_active = request.POST.get('is_active') == 'on'
            serv.image_url = request.POST.get('image_url', serv.image_url)
            serv.description = request.POST.get('description', serv.description)
            serv.save()

        elif action == 'toggle_active' and serv_id:
            serv = get_object_or_404(Service, id=serv_id)
            serv.is_active = not serv.is_active
            serv.save()

        elif action == 'delete' and serv_id:
            serv = get_object_or_404(Service, id=serv_id)
            serv.delete()

        return redirect('/dashboard/services/')

    services_list = Service.objects.all()
    context = {
        'page_title': 'Gestion des Services',
        'active_menu': 'services',
        'services': services_list,
    }
    return render(request, 'core/admin/dashboard_services.html', context)


@admin_required
def dashboard_attendance_log(request):
    period = request.GET.get('period', 'today')
    emp_id = request.GET.get('employee_id', 'all')
    today = timezone.now().date()

    records = AttendanceRecord.objects.select_related('employee').all()

    if period == 'today':
        records = records.filter(date=today)
    elif period == 'week':
        start_of_week = today - datetime.timedelta(days=today.weekday())
        records = records.filter(date__gte=start_of_week, date__lte=today)
    elif period == 'month':
        start_of_month = today.replace(day=1)
        records = records.filter(date__gte=start_of_month, date__lte=today)

    if emp_id != 'all':
        records = records.filter(employee_id=emp_id)

    total_hours_sum = sum(r.calculate_hours_worked() for r in records)
    total_overtime_sum = sum(r.overtime_hours for r in records)
    total_lateness_count = sum(1 for r in records if r.is_late)

    employees = Employee.objects.filter(is_team_member=True)

    context = {
        'page_title': 'Gestion du Pointage & Historique',
        'active_menu': 'attendance',
        'records': records,
        'employees': employees,
        'period': period,
        'selected_emp_id': emp_id,
        'total_hours_sum': f"{int(total_hours_sum)}h {int(round((total_hours_sum - int(total_hours_sum)) * 60)):02d}m",
        'total_overtime_sum': f"{total_overtime_sum:.1f}h",
        'total_lateness_count': total_lateness_count,
    }
    return render(request, 'core/admin/dashboard_attendance.html', context)


@admin_required
def dashboard_messages(request):
    if request.method == 'POST':
        msg_id = request.POST.get('message_id')
        action = request.POST.get('action')
        msg = get_object_or_404(ContactMessage, id=msg_id)

        if action == 'mark_read':
            msg.status = 'READ'
            msg.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'new_status': 'READ'})
        elif action == 'mark_processed':
            msg.status = 'PROCESSED'
            msg.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success', 'new_status': 'PROCESSED'})
        elif action == 'delete':
            msg.delete()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success'})

        return redirect('/dashboard/messages/')

    status_filter = request.GET.get('status', 'all')
    messages_qs = ContactMessage.objects.all()
    if status_filter != 'all':
        messages_qs = messages_qs.filter(status=status_filter.upper())

    context = {
        'page_title': 'Messages de Contact',
        'active_menu': 'messages',
        'messages': messages_qs,
        'status_filter': status_filter,
    }
    return render(request, 'core/admin/dashboard_messages.html', context)


@admin_required
def dashboard_performance(request):
    team_employees = Employee.objects.filter(is_team_member=True, is_active=True)
    perf_data = []

    for emp in team_employees:
        score_info = emp.get_performance_score()
        perf_data.append({
            'employee': emp,
            'attendance_rate': emp.get_attendance_rate(),
            'lateness_count': emp.get_lateness_count(),
            'hours_today': emp.get_hours_worked_today_formatted(),
            'hours_week': emp.get_hours_worked_this_week_formatted(),
            'hours_month': emp.get_hours_worked_this_month_formatted(),
            'performance': score_info,
        })

    context = {
        'page_title': 'Évaluation & Performance de l\'Équipe',
        'active_menu': 'performance',
        'perf_data': perf_data,
    }
    return render(request, 'core/admin/dashboard_performance.html', context)


@admin_required
def dashboard_settings(request):
    context = {
        'page_title': 'Paramètres Système ERP',
        'active_menu': 'settings',
    }
    return render(request, 'core/admin/dashboard_settings.html', context)


@admin_required
def dashboard_notifications(request):
    msg = None
    msg_type = 'success'

    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        if action == 'create':
            title = request.POST.get('title', '').strip()
            message = request.POST.get('message', '').strip()
            notif_type = request.POST.get('type', 'ANNOUNCEMENT')
            employee_id = request.POST.get('employee_id')

            if title and message:
                target_emp = None
                if employee_id and employee_id != 'all':
                    target_emp = Employee.objects.filter(id=employee_id).first()

                Notification.objects.create(
                    title=title,
                    message=message,
                    type=notif_type,
                    employee=target_emp
                )
                msg = "Notification publiée avec succès à l'attention des employés !"
            else:
                msg = "Veuillez remplir le titre et le message de la notification."
                msg_type = 'danger'

        elif action == 'delete':
            notif_id = request.POST.get('notification_id')
            if notif_id:
                Notification.objects.filter(id=notif_id).delete()
                msg = "Notification supprimée avec succès."

    notifications = Notification.objects.select_related('employee').all().order_by('-created_at')
    team_employees = Employee.objects.filter(is_team_member=True, is_active=True).order_by('first_name')

    total_count = notifications.count()
    announcement_count = notifications.filter(type='ANNOUNCEMENT').count()
    admin_count = notifications.filter(type='ADMIN').count()
    schedule_count = notifications.filter(type='SCHEDULE').count()

    context = {
        'page_title': 'Notifications & Annonces d\'Équipe',
        'active_menu': 'notifications',
        'notifications': notifications,
        'team_employees': team_employees,
        'total_count': total_count,
        'announcement_count': announcement_count,
        'admin_count': admin_count,
        'schedule_count': schedule_count,
        'msg': msg,
        'msg_type': msg_type,
    }
    return render(request, 'core/admin/dashboard_notifications.html', context)


@admin_required
def update_employee_status(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        new_status = request.POST.get('status')
        
        employee = get_object_or_404(Employee, id=employee_id)
        now_dt = timezone.localtime(timezone.now())
        today = now_dt.date()
        now_time = now_dt.time()
        
        record, created = AttendanceRecord.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={'status': new_status}
        )

        if new_status == 'PRESENT':
            if not record.check_in:
                record.check_in = now_time
            record.status = 'PRESENT'
        elif new_status == 'PAUSE':
            if not record.check_in:
                record.check_in = now_time
            record.status = 'PAUSE'
        elif new_status == 'CHECK_OUT':
            record.check_out = now_time
            record.status = 'PRESENT'
        elif new_status == 'REPOS':
            record.status = 'REPOS'
            record.check_in = None
            record.check_out = None
        elif new_status == 'ABSENT':
            record.status = 'ABSENT'
            record.check_in = None
            record.check_out = None

        record.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'new_status': record.status, 'new_status_display': record.get_status_display()})
            
    return redirect(request.META.get('HTTP_REFERER', '/dashboard/'))


# ==========================================
# AJAX LIVE STATS & GLOBAL SEARCH ENDPOINTS
# ==========================================

@admin_required
def api_live_stats(request):
    team_employees = Employee.objects.filter(is_team_member=True, is_active=True)
    present_count = sum(1 for e in team_employees if e.get_current_status() == 'PRESENT')
    pause_count = sum(1 for e in team_employees if e.get_current_status() == 'PAUSE')
    repos_count = sum(1 for e in team_employees if e.get_current_status() == 'REPOS')
    absent_count = sum(1 for e in team_employees if e.get_current_status() == 'ABSENT')
    
    hours_today = sum(e.get_hours_worked_today() for e in team_employees)

    def fmt_hours(hours):
        h = int(hours)
        m = int(round((hours - h) * 60))
        return f"{h}h {m:02d}m"

    data = {
        'total_team': team_employees.count(),
        'present_count': present_count,
        'pause_count': pause_count,
        'repos_count': repos_count,
        'absent_count': absent_count,
        'hours_today_fmt': fmt_hours(hours_today),
    }
    return JsonResponse(data)


@admin_required
def api_global_search(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'results': []})

    results = []

    # Search Employees
    for emp in Employee.objects.filter(
        Q(first_name__icontains=q, last_name__icontains=q, position__icontains=q, _connector=Q.OR)
    ):
        results.append({
            'type': 'Employé',
            'title': emp.full_name,
            'subtitle': emp.position,
            'url': '/dashboard/employees/'
        })

    # Search Products
    for p in Product.objects.filter(Q(name__icontains=q, category__icontains=q, _connector=Q.OR)):
        results.append({
            'type': 'Produit',
            'title': p.name,
            'subtitle': f"{p.price} DH",
            'url': '/dashboard/products/'
        })

    # Search Services
    for s in Service.objects.filter(Q(name__icontains=q, category__icontains=q, _connector=Q.OR)):
        results.append({
            'type': 'Service',
            'title': s.name,
            'subtitle': f"{s.price} DH - {s.duration_minutes} min",
            'url': '/dashboard/services/'
        })

    # Search Contact Messages
    for m in ContactMessage.objects.filter(
        Q(name__icontains=q, subject__icontains=q, email__icontains=q, _connector=Q.OR)
    ):
        results.append({
            'type': 'Message',
            'title': m.subject,
            'subtitle': f"De: {m.name} ({m.email})",
            'url': '/dashboard/messages/'
        })

    return JsonResponse({'results': results[:10]})


@admin_required
def api_employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    today = timezone.now().date()
    rec = employee.get_today_record()
    
    start_of_week = today - datetime.timedelta(days=today.weekday())
    day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    weekly_history = []
    
    for i in range(7):
        d = start_of_week + datetime.timedelta(days=i)
        r = employee.attendance_records.filter(date=d).first()
        weekly_history.append({
            'date': d.strftime('%d/%m/%Y'),
            'day_name': day_names[i],
            'is_today': (d == today),
            'status': r.status if r else ('-' if d > today else 'ABSENT'),
            'status_display': r.get_status_display() if r else ('-' if d > today else 'Absent'),
            'check_in': r.check_in.strftime('%H:%M') if (r and r.check_in) else '-',
            'check_out': r.check_out.strftime('%H:%M') if (r and r.check_out) else ('En cours' if (r and r.status in ['PRESENT', 'PAUSE'] and d == today) else '-'),
            'hours_worked': r.hours_worked_formatted if r else '0h 00m'
        })

    data = {
        'id': employee.id,
        'first_name': employee.first_name,
        'last_name': employee.last_name,
        'full_name': employee.full_name,
        'position': employee.position,
        'role_display': employee.get_role_display(),
        'email': employee.email or '',
        'phone': employee.phone or '',
        'avatar_color': employee.avatar_color,
        'current_status': employee.get_current_status(),
        'current_status_display': employee.get_current_status_display(),
        'check_in': rec.check_in.strftime('%H:%M') if (rec and rec.check_in) else '-',
        'check_out': rec.check_out.strftime('%H:%M') if (rec and rec.check_out) else ('En cours' if (rec and rec.status in ['PRESENT', 'PAUSE']) else '-'),
        'hours_worked_today': employee.get_hours_worked_today_formatted(),
        'hours_worked_this_week': employee.get_hours_worked_this_week_formatted(),
        'weekly_history': weekly_history,
    }
    return JsonResponse(data)


# ==========================================
# DEDICATED EMPLOYEE DASHBOARD VIEWS & APIS
# ==========================================

def get_employee_reservations_qs(emp):
    emp_filter = (
        Q(employee=emp) |
        Q(notes__icontains=f"Expert: {emp.user.username}") |
        Q(notes__icontains=f"Expert: {emp.full_name}") |
        Q(notes__icontains=f"Expert principal: {emp.user.username}") |
        Q(notes__icontains=f"Expert principal: {emp.full_name}")
    )
    return Reservation.objects.filter(emp_filter).distinct()


def employee_access_denied(request):
    return render(request, 'core/employee/access_denied.html', {
        'message': "Vous n'avez pas encore été ajouté à l'équipe par un administrateur."
    })


@employee_required
def employee_dashboard(request):
    emp = request.user.employee_profile
    pos = (emp.position or '').lower()
    is_reception = emp.role == 'RECEPTION' or 'réception' in pos or 'reception' in pos
    if is_reception:
        return redirect('reception_dashboard')

    today = timezone.now().date()
    msg = None
    msg_type = 'success'


    # POST Action Handlers
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_reservation_status':
            res_id = request.POST.get('reservation_id')
            new_status = request.POST.get('status')
            if res_id and new_status:
                res = get_employee_reservations_qs(emp).filter(id=res_id).first()
                if res:
                    res.set_status_for_employee(emp, new_status)
                    msg = f"Statut de votre prestation mis à jour : {res.get_status_display_for_employee(emp)}."

        elif action == 'add_break':
            start_str = request.POST.get('start_time')
            end_str = request.POST.get('end_time')
            title = request.POST.get('title', 'Pause déjeuner').strip() or 'Pause'
            date_str = request.POST.get('date', today.strftime('%Y-%m-%d'))
            try:
                b_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                b_start = datetime.datetime.strptime(start_str, '%H:%M').time()
                b_end = datetime.datetime.strptime(end_str, '%H:%M').time()
                if b_end <= b_start:
                    msg = "L'heure de fin de pause doit être supérieure à l'heure de début."
                    msg_type = 'danger'
                else:
                    EmployeeBreak.objects.create(
                        employee=emp,
                        date=b_date,
                        start_time=b_start,
                        end_time=b_end,
                        title=title
                    )
                    msg = f"Pause '{title}' ({start_str} → {end_str}) enregistrée."
            except ValueError:
                msg = "Créneau de pause invalide."
                msg_type = 'danger'

        elif action == 'delete_break':
            break_id = request.POST.get('break_id')
            if break_id:
                EmployeeBreak.objects.filter(id=break_id, employee=emp).delete()
                msg = "Pause supprimée."

    today_rec = emp.get_today_record()
    current_status = emp.get_current_status()
    
    # Personal statistics calculations
    hours_today = emp.get_hours_worked_today_formatted()
    hours_week = emp.get_hours_worked_this_week_formatted()
    hours_month = emp.get_hours_worked_this_month_formatted()
    pause_today = emp.get_pause_time_today_formatted()
    days_present = emp.get_days_present_this_month()
    days_rest = emp.get_days_rest_this_month()
    lateness_count = emp.get_lateness_count()
    overtime_month = emp.get_overtime_hours_this_month_formatted()

    recent_records = emp.attendance_records.order_by('-date')[:5]
    is_reception_or_admin = (emp.role in ['RECEPTION', 'RECEPTIONNISTE', 'ADMINISTRATEUR']) or request.user.is_superuser
    if is_reception_or_admin:
        unread_notifications_count = Notification.objects.filter(
            Q(employee=emp) | Q(employee__isnull=True), is_read=False
        ).count()
    else:
        unread_notifications_count = Notification.objects.filter(
            (
                Q(employee=emp) |
                (
                    Q(employee__isnull=True) &
                    ~Q(type='ORDER') &
                    ~Q(title__icontains='Commande') &
                    ~Q(title__icontains='Retrait') &
                    ~Q(title__icontains='Encaissement') &
                    ~Q(title__icontains='Absente') &
                    ~Q(title__icontains='No-Show') &
                    ~Q(title__icontains='Annul')
                )
            ),
            is_read=False
        ).count()

    # Daily Schedule Timeline (09:00 to 19:00)
    selected_date_str = request.GET.get('date', today.strftime('%Y-%m-%d'))
    try:
        schedule_date = datetime.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        schedule_date = today

    today_reservations = get_employee_reservations_qs(emp).filter(
        date=schedule_date
    ).select_related('service', 'client').order_by('start_time')

    pending_reservations = get_employee_reservations_qs(emp).filter(
        status='PENDING', date__gte=today
    ).select_related('service', 'client').order_by('date', 'start_time')

    today_breaks = EmployeeBreak.objects.filter(
        employee=emp, date=schedule_date
    ).order_by('start_time')

    # Timeline Slots Generation (09:00 -> 20:00)
    timeline_slots = []
    start_hour = 9
    end_hour = 20
    dummy_date = datetime.date(2000, 1, 1)

    curr_time_dt = datetime.datetime.combine(dummy_date, datetime.time(start_hour, 0))
    end_time_dt = datetime.datetime.combine(dummy_date, datetime.time(end_hour, 0))

    while curr_time_dt < end_time_dt:
        t_start = curr_time_dt.time()
        t_end = (curr_time_dt + datetime.timedelta(minutes=30)).time()
        slot_label = t_start.strftime('%H:%M')

        # Check matching reservation or break for this employee using sequential service windows
        res_found = None
        emp_services = []
        emp_window_label = ""

        for res in today_reservations:
            if res.status in ['CANCELLED', 'NO_SHOW']:
                continue

            windows = res.get_employee_service_time_windows(emp)
            for win in windows:
                if win.get('status') in ['NO_SHOW', 'CANCELLED']:
                    continue
                if win['start_time'] < t_end and win['end_time'] > t_start:
                    res_found = res
                    emp_services.append(win['service_name'])
                    emp_window_label = f"{win['start_time'].strftime('%H:%M')} → {win['end_time'].strftime('%H:%M')}"
                    break
            if res_found:
                break

        break_found = None
        if not res_found:
            for brk in today_breaks:
                if brk.start_time < t_end and brk.end_time > t_start:
                    break_found = brk
                    break

        emp_status = res_found.get_status_for_employee(emp) if res_found else None
        emp_status_display = res_found.get_status_display_for_employee(emp) if res_found else None

        timeline_slots.append({
            'time_label': slot_label,
            'start_time': t_start,
            'end_time': t_end,
            'reservation': res_found,
            'emp_services': emp_services,
            'emp_window_label': emp_window_label,
            'emp_status': emp_status,
            'emp_status_display': emp_status_display,
            'break': break_found,
            'is_available': res_found is None and break_found is None
        })

        curr_time_dt += datetime.timedelta(minutes=30)

    context = {
        'page_title': 'Mon Tableau de Bord & Planning',
        'active_menu': 'dashboard',
        'employee': emp,
        'today_rec': today_rec,
        'current_status': current_status,
        'current_status_display': emp.get_current_status_display(),
        'hours_today': hours_today,
        'hours_week': hours_week,
        'hours_month': hours_month,
        'pause_today': pause_today,
        'days_present': days_present,
        'days_rest': days_rest,
        'lateness_count': lateness_count,
        'overtime_month': overtime_month,
        'recent_records': recent_records,
        'unread_notifications_count': unread_notifications_count,
        'schedule_date': schedule_date,
        'schedule_date_str': schedule_date.strftime('%Y-%m-%d'),
        'today_reservations': today_reservations,
        'pending_reservations': pending_reservations,
        'today_breaks': today_breaks,
        'timeline_slots': timeline_slots,
        'msg': msg,
        'msg_type': msg_type,
    }
    return render(request, 'core/employee/dashboard.html', context)


@employee_required
def employee_pointage(request):
    emp = request.user.employee_profile
    today_rec = emp.get_today_record()
    current_status = emp.get_current_status()
    pos = (emp.position or '').lower()
    is_reception = emp.role in ['RECEPTION', 'RECEPTIONNISTE'] or 'réception' in pos or 'reception' in pos
    
    context = {
        'page_title': 'Mon Pointage',
        'active_menu': 'pointage',
        'employee': emp,
        'today_rec': today_rec,
        'current_status': current_status,
        'current_status_display': emp.get_current_status_display(),
        'hours_today': emp.get_hours_worked_today_formatted(),
        'pause_today': emp.get_pause_time_today_formatted(),
        'base_template': 'core/reception/reception_base.html' if is_reception else 'core/employee/employee_base.html',
    }
    return render(request, 'core/employee/pointage.html', context)


@employee_required
def employee_historique(request):
    emp = request.user.employee_profile
    period = request.GET.get('period', 'month')
    today = timezone.now().date()
    records = emp.attendance_records.all()
    pos = (emp.position or '').lower()
    is_reception = emp.role in ['RECEPTION', 'RECEPTIONNISTE'] or 'réception' in pos or 'reception' in pos

    if period == 'today':
        records = records.filter(date=today)
    elif period == 'week':
        start_of_week = today - datetime.timedelta(days=today.weekday())
        records = records.filter(date__gte=start_of_week, date__lte=today)
    elif period == 'month':
        start_of_month = today.replace(day=1)
        records = records.filter(date__gte=start_of_month, date__lte=today)
    elif period == 'custom':
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date and end_date:
            records = records.filter(date__gte=start_date, date__lte=end_date)

    context = {
        'page_title': 'Mon Historique de Pointage',
        'active_menu': 'historique',
        'records': records,
        'period': period,
        'start_date': request.GET.get('start_date', ''),
        'end_date': request.GET.get('end_date', ''),
        'base_template': 'core/reception/reception_base.html' if is_reception else 'core/employee/employee_base.html',
    }
    return render(request, 'core/employee/historique.html', context)


@employee_required
def employee_calendrier(request):
    emp = request.user.employee_profile
    today = timezone.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    pos = (emp.position or '').lower()
    is_reception = emp.role in ['RECEPTION', 'RECEPTIONNISTE'] or 'réception' in pos or 'reception' in pos

    import calendar
    cal = calendar.monthcalendar(year, month)
    
    month_records = emp.attendance_records.filter(date__year=year, date__month=month)
    records_dict = {r.date.day: r for r in month_records}

    month_reservations = get_employee_reservations_qs(emp).filter(date__year=year, date__month=month).select_related('service', 'client').order_by('start_time')
    reservations_by_day = {}
    for res in month_reservations:
        day_num = res.date.day
        if day_num not in reservations_by_day:
            reservations_by_day[day_num] = []
        reservations_by_day[day_num].append(res)

    month_names = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

    context = {
        'page_title': 'Mon Planning & Calendrier',
        'active_menu': 'calendrier',
        'current_year': year,
        'current_month': month,
        'month_name': month_names[month],
        'today': today,
        'calendar_matrix': cal,
        'records_dict': records_dict,
        'reservations_by_day': reservations_by_day,
        'base_template': 'core/reception/reception_base.html' if is_reception else 'core/employee/employee_base.html',
    }
    return render(request, 'core/employee/calendrier.html', context)


@employee_required
def employee_profil(request):
    emp = request.user.employee_profile
    user = request.user
    msg = None
    msg_type = 'success'
    pos = (emp.position or '').lower()
    is_reception = emp.role in ['RECEPTION', 'RECEPTIONNISTE'] or 'réception' in pos or 'reception' in pos

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_info':
            phone = request.POST.get('phone', '').strip()
            photo_file = request.FILES.get('photo_file')
            emp.phone = phone
            if photo_file:
                from django.core.files.storage import FileSystemStorage
                import os
                avatars_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
                os.makedirs(avatars_dir, exist_ok=True)
                fs = FileSystemStorage(location=avatars_dir, base_url='/media/avatars/')
                ext = os.path.splitext(photo_file.name)[1]
                filename = fs.save(f"emp_{emp.id}_{int(timezone.now().timestamp())}{ext}", photo_file)
                emp.photo = fs.url(filename)
            emp.save()
            msg = "Vos informations (téléphone/photo) ont été mises à jour."

        elif action == 'change_password':
            old_password = request.POST.get('old_password', '')
            new_password1 = request.POST.get('new_password1', '')
            new_password2 = request.POST.get('new_password2', '')

            if not user.check_password(old_password):
                msg = "L'ancien mot de passe est incorrect."
                msg_type = 'danger'
            elif new_password1 != new_password2:
                msg = "Les nouveaux mots de passe ne correspondent pas."
                msg_type = 'danger'
            elif len(new_password1) < 6:
                msg = "Le nouveau mot de passe doit contenir au moins 6 caractères."
                msg_type = 'danger'
            else:
                user.set_password(new_password1)
                user.save()
                update_session_auth_hash(request, user)
                msg = "Votre mot de passe a été modifié avec succès."

    context = {
        'page_title': 'Mon Profil Employé',
        'active_menu': 'profil',
        'employee': emp,
        'msg': msg,
        'msg_type': msg_type,
        'base_template': 'core/reception/reception_base.html' if is_reception else 'core/employee/employee_base.html',
    }
    return render(request, 'core/employee/profil.html', context)


@employee_required
def employee_notifications(request):
    emp = request.user.employee_profile
    pos = (emp.position or '').lower()
    is_reception = emp.role in ['RECEPTION', 'RECEPTIONNISTE'] or 'réception' in pos or 'reception' in pos
    is_reception_or_admin = (emp.role in ['RECEPTION', 'RECEPTIONNISTE', 'ADMINISTRATEUR']) or request.user.is_superuser
    if is_reception_or_admin:
        notif_qs = Notification.objects.filter(Q(employee=emp) | Q(employee__isnull=True))
    else:
        notif_qs = Notification.objects.filter(
            Q(employee=emp) |
            (
                Q(employee__isnull=True) &
                ~Q(type='ORDER') &
                ~Q(title__icontains='Commande') &
                ~Q(title__icontains='Retrait') &
                ~Q(title__icontains='Encaissement') &
                ~Q(title__icontains='Absente') &
                ~Q(title__icontains='No-Show') &
                ~Q(title__icontains='Annul')
            )
        )

    if request.method == 'POST':
        notif_id = request.POST.get('notification_id')
        if notif_id:
            notif = notif_qs.filter(id=notif_id).first()
            if notif:
                notif.is_read = True
                notif.save()
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success'})

    notifications = notif_qs.order_by('-created_at')

    context = {
        'page_title': 'Mes Notifications',
        'active_menu': 'notifications',
        'notifications': notifications,
        'base_template': 'core/reception/reception_base.html' if is_reception else 'core/employee/employee_base.html',
    }
    return render(request, 'core/employee/notifications.html', context)


@employee_required
@require_POST
def employee_clock_action(request):
    emp = request.user.employee_profile
    action = request.POST.get('action')
    now_dt = timezone.localtime(timezone.now())
    today = now_dt.date()
    now_time = now_dt.time()

    record, created = AttendanceRecord.objects.get_or_create(
        employee=emp,
        date=today,
        defaults={'status': 'ABSENT'}
    )

    success = False
    message = ""

    if action == 'CHECK_IN':
        if record.check_in is not None:
            message = "Vous avez déjà pointé votre entrée pour aujourd'hui."
        else:
            record.check_in = now_time
            record.status = 'PRESENT'
            record.save()
            success = True
            message = f"Entrée enregistrée avec succès à {now_time.strftime('%H:%M')}."

    elif action == 'START_PAUSE':
        if record.check_in is None:
            message = "Vous devez d'abord pointer votre entrée avant de démarrer une pause."
        elif record.check_out is not None:
            message = "Votre journée est déjà terminée."
        elif record.status == 'PAUSE' or record.pause_start is not None:
            message = "Vous êtes déjà en pause (pauses consécutives non autorisées)."
        else:
            record.status = 'PAUSE'
            record.pause_start = now_time
            record.save()
            success = True
            message = f"Pause démarrée à {now_time.strftime('%H:%M')}."

    elif action == 'END_PAUSE':
        if record.status != 'PAUSE':
            message = "Vous n'êtes pas actuellement en pause."
        else:
            record.status = 'PRESENT'
            record.pause_end = now_time
            if record.pause_start:
                dummy = datetime.date(2000, 1, 1)
                dt_start = datetime.datetime.combine(dummy, record.pause_start)
                dt_end = datetime.datetime.combine(dummy, now_time)
                if dt_end < dt_start:
                    dt_end += datetime.timedelta(days=1)
                diff = dt_end - dt_start
                mins = max(1, int(diff.total_seconds() / 60))
                record.pause_duration_minutes += mins
                record.pause_start = None
            record.save()
            success = True
            message = "Pause terminée. Bon retour au travail !"

    elif action == 'CHECK_OUT':
        if record.check_in is None:
            message = "Vous n'avez pas encore pointé l'entrée."
        elif record.status == 'PAUSE':
            message = "Veuillez d'abord terminer votre pause avant de pointer la sortie."
        elif record.check_out is not None:
            message = "Vous avez déjà pointé votre sortie pour aujourd'hui."
        else:
            record.check_out = now_time
            record.status = 'PRESENT'
            record.save()
            success = True
            message = f"Sortie enregistrée à {now_time.strftime('%H:%M')}. Votre journée est terminée !"

    stats = {
        'current_status': emp.get_current_status(),
        'current_status_display': emp.get_current_status_display(),
        'hours_today': emp.get_hours_worked_today_formatted(),
        'hours_week': emp.get_hours_worked_this_week_formatted(),
        'hours_month': emp.get_hours_worked_this_month_formatted(),
        'pause_today': emp.get_pause_time_today_formatted(),
        'days_present': emp.get_days_present_this_month(),
        'days_rest': emp.get_days_rest_this_month(),
        'lateness_count': emp.get_lateness_count(),
        'overtime_month': emp.get_overtime_hours_this_month_formatted(),
        'check_in': record.check_in.strftime('%H:%M') if record.check_in else None,
        'check_out': record.check_out.strftime('%H:%M') if record.check_out else None,
        'is_day_finished': record.check_out is not None,
    }

    return JsonResponse({
        'success': success,
        'message': message,
        'stats': stats,
    })


@employee_required
def employee_live_stats(request):
    emp = request.user.employee_profile
    rec = emp.get_today_record()
    data = {
        'current_status': emp.get_current_status(),
        'current_status_display': emp.get_current_status_display(),
        'hours_today': emp.get_hours_worked_today_formatted(),
        'hours_week': emp.get_hours_worked_this_week_formatted(),
        'hours_month': emp.get_hours_worked_this_month_formatted(),
        'pause_today': emp.get_pause_time_today_formatted(),
        'days_present': emp.get_days_present_this_month(),
        'days_rest': emp.get_days_rest_this_month(),
        'lateness_count': emp.get_lateness_count(),
        'overtime_month': emp.get_overtime_hours_this_month_formatted(),
        'check_in': rec.check_in.strftime('%H:%M') if (rec and rec.check_in) else '-',
        'check_out': rec.check_out.strftime('%H:%M') if (rec and rec.check_out) else '-',
        'is_day_finished': rec.check_out is not None if rec else False,
    }
    return JsonResponse(data)


@employee_required
def employee_calendar_detail(request, day):
    emp = request.user.employee_profile
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    
    try:
        query_date = datetime.date(year, month, int(day))
    except ValueError:
        return JsonResponse({'error': 'Invalid date'}, status=400)

    rec = emp.attendance_records.filter(date=query_date).first()
    res_qs = get_employee_reservations_qs(emp).filter(date=query_date).select_related('service', 'client').order_by('start_time')
    
    reservations_list = []
    status_choices_dict = dict(Reservation.STATUS_CHOICES)
    dummy_d = datetime.date(2000, 1, 1)

    for r in res_qs:
        client_name = f"{r.client.first_name} {r.client.last_name}".strip() or r.client.username
        windows = r.get_employee_service_time_windows(emp)
        if windows:
            for win in windows:
                dt1 = datetime.datetime.combine(dummy_d, win['start_time'])
                dt2 = datetime.datetime.combine(dummy_d, win['end_time'])
                dur_min = int((dt2 - dt1).total_seconds() / 60)
                win_st = win.get('status') or r.status
                win_st_display = status_choices_dict.get(win_st, r.get_status_display())
                
                reservations_list.append({
                    'id': r.id,
                    'service_name': win['service_name'],
                    'client_name': client_name,
                    'start_time': win['start_time'].strftime('%H:%M'),
                    'end_time': win['end_time'].strftime('%H:%M'),
                    'duration': f"{dur_min} min",
                    'status': win_st,
                    'status_display': win_st_display,
                    'notes': r.notes or 'Aucune'
                })
        else:
            reservations_list.append({
                'id': r.id,
                'service_name': r.service.name,
                'client_name': client_name,
                'start_time': r.start_time.strftime('%H:%M'),
                'end_time': r.end_time.strftime('%H:%M'),
                'duration': f"{r.duration_minutes} min",
                'status': r.status,
                'status_display': r.get_status_display(),
                'notes': r.notes or 'Aucune'
            })

    attendance_data = None
    if rec:
        attendance_data = {
            'status': rec.status,
            'status_display': rec.get_status_display(),
            'check_in': rec.check_in.strftime('%H:%M') if rec.check_in else '-',
            'check_out': rec.check_out.strftime('%H:%M') if rec.check_out else '-',
            'pause_start': rec.pause_start.strftime('%H:%M') if rec.pause_start else '-',
            'pause_end': rec.pause_end.strftime('%H:%M') if rec.pause_end else '-',
            'pause_minutes': f"{rec.pause_duration_minutes} min",
            'hours_worked': rec.hours_worked_formatted,
            'notes': rec.notes or 'Aucune note'
        }
    else:
        is_past = query_date < timezone.now().date()
        attendance_data = {
            'status': 'ABSENT' if is_past else 'NOT_STARTED',
            'status_display': 'Absent' if is_past else 'Non commencé',
            'check_in': '-',
            'check_out': '-',
            'pause_start': '-',
            'pause_end': '-',
            'pause_minutes': '0 min',
            'hours_worked': '0h 00m',
            'notes': '-'
        }

    return JsonResponse({
        'date': query_date.strftime('%d/%m/%Y'),
        'attendance': attendance_data,
        'reservations': reservations_list
    })


# ==========================================
# SERVICE RESERVATION & AVAILABILITY ENGINE
# ==========================================

def api_available_slots(request):
    service_id = request.GET.get('service_id')
    service_ids_raw = request.GET.get('service_ids')
    employee_id = request.GET.get('employee_id')
    date_str = request.GET.get('date')

    if not employee_id or not date_str:
        return JsonResponse({'error': 'Paramètres manquants'}, status=400)

    try:
        employee = Employee.objects.get(id=employee_id, is_team_member=True, is_active=True)
        booking_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()

        s_ids = []
        if service_ids_raw:
            s_ids = [int(x) for x in service_ids_raw.split(',') if x.strip().isdigit()]
        elif service_id:
            s_ids = [int(service_id)]

        if not s_ids:
            return JsonResponse({'error': 'Aucun service sélectionné'}, status=400)

        selected_services = list(Service.objects.filter(id__in=s_ids, is_active=True))
        if not selected_services:
            return JsonResponse({'error': 'Service introuvable'}, status=400)

        duration = sum(s.duration_minutes for s in selected_services)

    except (ObjectDoesNotExist, ValueError):
        return JsonResponse({'error': 'Données invalides'}, status=400)

    now_dt = timezone.localtime(timezone.now())
    today = now_dt.date()
    now_time = now_dt.time()

    # Check Attendance Record for booking_date
    att_record = employee.attendance_records.filter(date=booking_date).first()

    # If marked ABSENT or REPOS, no slots available
    if att_record and att_record.status in ['ABSENT', 'REPOS']:
        status_display = "absent(e)" if att_record.status == 'ABSENT' else "en repos"
        return JsonResponse({
            'employee_id': employee.id,
            'employee_name': employee.full_name,
            'date': date_str,
            'duration_minutes': duration,
            'total_price': sum(float(s.price) for s in selected_services),
            'available_slots': [],
            'notice': f"{employee.full_name} est {status_display} le {booking_date.strftime('%d/%m/%Y')}."
        })

    # Default real-life working hours: Mon-Sat 09:00 to 20:00, Sun 10:00 to 18:00
    if booking_date.weekday() == 6:  # Dimanche
        start_work = datetime.time(10, 0)
        end_work = datetime.time(18, 0)
    else:
        start_work = datetime.time(9, 0)
        end_work = datetime.time(20, 0)

    # If employee checked in on that date, start slots from check_in
    if att_record and att_record.check_in:
        ci = att_record.check_in
        if ci.minute == 0:
            start_work = ci
        elif ci.minute <= 30:
            start_work = datetime.time(ci.hour, 30)
        else:
            start_work = datetime.time((ci.hour + 1) % 24, 0)

    existing_reservations = Reservation.objects.filter(
        employee=employee,
        date=booking_date
    ).exclude(status__in=['CANCELLED', 'NO_SHOW'])

    existing_breaks = EmployeeBreak.objects.filter(
        employee=employee,
        date=booking_date
    )

    available_slots = []

    # Generate 30-min candidate slots
    current_dt = datetime.datetime.combine(booking_date, start_work)
    end_dt = datetime.datetime.combine(booking_date, end_work)

    while current_dt + datetime.timedelta(minutes=duration) <= end_dt:
        slot_start = current_dt.time()
        slot_end = (current_dt + datetime.timedelta(minutes=duration)).time()

        # Filter past slots for today
        is_past = (booking_date < today) or (booking_date == today and slot_start <= now_time)

        if not is_past:
            # Overlap check (reservations + breaks)
            has_overlap = False
            for res in existing_reservations:
                if res.start_time < slot_end and res.end_time > slot_start:
                    has_overlap = True
                    break
            
            if not has_overlap:
                for brk in existing_breaks:
                    if brk.start_time < slot_end and brk.end_time > slot_start:
                        has_overlap = True
                        break

            if not has_overlap:
                available_slots.append({
                    'start': slot_start.strftime('%H:%M'),
                    'end': slot_end.strftime('%H:%M'),
                    'display': f"{slot_start.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}"
                })

        current_dt += datetime.timedelta(minutes=30)

    return JsonResponse({
        'employee_id': employee.id,
        'employee_name': employee.full_name,
        'date': date_str,
        'duration_minutes': duration,
        'total_price': sum(float(s.price) for s in selected_services),
        'available_slots': available_slots
    })


@login_required
def reservation_create(request):
    services = Service.objects.filter(is_active=True).order_by('category', 'name')
    employees = Employee.objects.filter(is_team_member=True, is_active=True).exclude(role='ADMINISTRATEUR').order_by('first_name')
    
    selected_service_id = request.GET.get('service_id')
    selected_employee_id = request.GET.get('employee_id')
    selected_date = request.GET.get('date', timezone.now().strftime('%Y-%m-%d'))
    
    msg = None
    msg_type = 'success'

    if request.method == 'POST':
        service_id = request.POST.get('service_id')
        additional_service_ids = request.POST.get('additional_service_ids', '')
        employee_id = request.POST.get('employee_id')
        date_str = request.POST.get('date')
        time_str = request.POST.get('start_time')
        user_notes = request.POST.get('notes', '').strip()

        try:
            primary_service = Service.objects.get(id=service_id, is_active=True)
            employee = Employee.objects.get(id=employee_id, is_team_member=True, is_active=True)
            res_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            res_start = datetime.datetime.strptime(time_str, '%H:%M').time()
            
            extra_ids = [int(x) for x in additional_service_ids.split(',') if x.strip().isdigit() and int(x) != primary_service.id]
            extra_services = list(Service.objects.filter(id__in=extra_ids, is_active=True))

            all_services = [primary_service] + extra_services
            total_duration = sum(s.duration_minutes for s in all_services)
            total_price = sum(s.price for s in all_services)

            dummy_date = datetime.date(2000, 1, 1)
            dt_start = datetime.datetime.combine(dummy_date, res_start)
            dt_end = dt_start + datetime.timedelta(minutes=total_duration)
            res_end = dt_end.time()

            notes_content = user_notes
            if extra_services:
                extra_details = []
                expert_status_pairs = [f"{employee.user.username}=PENDING"]
                for extra_s in extra_services:
                    extra_emp_id = request.POST.get(f'extra_employee_{extra_s.id}')
                    extra_emp = Employee.objects.filter(id=extra_emp_id).first() if extra_emp_id else None
                    if extra_emp:
                        extra_details.append(f"{extra_s.name} (Expert: {extra_emp.full_name})")
                        expert_status_pairs.append(f"{extra_emp.user.username}=PENDING")
                    else:
                        extra_details.append(extra_s.name)
                
                combo_info = f"[Formule Multi-Prestations: {primary_service.name} (Expert principal: {employee.full_name}) + {' + '.join(extra_details)} | Total: {total_price:.0f} DH, {total_duration} min]"
                status_info = f"[ExpertStatuses: {', '.join(expert_status_pairs)}]"
                notes_content = f"{combo_info}\n{status_info}\n{user_notes}".strip()

            reservation = Reservation(
                client=request.user,
                employee=employee,
                service=primary_service,
                date=res_date,
                start_time=res_start,
                end_time=res_end,
                status='PENDING',
                notes=notes_content
            )
            reservation.full_clean()
            reservation.save()

            return redirect('client_reservations')

        except (ObjectDoesNotExist, ValueError):
            msg = "Informations de réservation invalides."
            msg_type = 'danger'
        except ValidationError as e:
            msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            msg_type = 'danger'

    context = {
        'page_title': 'Réserver un Service',
        'services': services,
        'employees': employees,
        'selected_service_id': selected_service_id,
        'selected_employee_id': selected_employee_id,
        'selected_date': selected_date,
        'msg': msg,
        'msg_type': msg_type,
    }
    return render(request, 'core/services.html', context)


@login_required
def client_reservations(request):
    msg = None
    msg_type = 'success'

    if request.method == 'POST':
        action = request.POST.get('action')
        res_id = request.POST.get('reservation_id')
        
        if action == 'cancel' and res_id:
            reservation = get_object_or_404(Reservation, id=res_id, client=request.user)
            if reservation.status in ['PENDING', 'CONFIRMED']:
                reservation.status = 'CANCELLED'
                reservation.save()
                msg = "Votre réservation a été annulée. Le créneau est à nouveau disponible."
            else:
                msg = "Cette réservation ne peut plus être annulée."
                msg_type = 'danger'

        elif action == 'reschedule' and res_id:
            reservation = get_object_or_404(Reservation, id=res_id, client=request.user)
            if reservation.status in ['PENDING', 'CONFIRMED']:
                new_date_str = request.POST.get('new_date')
                new_time_str = request.POST.get('new_start_time')
                new_emp_id = request.POST.get('new_employee_id')
                try:
                    new_date = datetime.datetime.strptime(new_date_str, '%Y-%m-%d').date()
                    new_start = datetime.datetime.strptime(new_time_str, '%H:%M').time()
                    new_emp = Employee.objects.get(id=new_emp_id, is_team_member=True, is_active=True)
                    
                    duration = reservation.duration_minutes or reservation.service.duration_minutes
                    dummy_date = datetime.date(2000, 1, 1)
                    dt_start = datetime.datetime.combine(dummy_date, new_start)
                    dt_end = dt_start + datetime.timedelta(minutes=duration)
                    new_end = dt_end.time()

                    reservation.date = new_date
                    reservation.start_time = new_start
                    reservation.end_time = new_end
                    reservation.employee = new_emp
                    reservation.full_clean()
                    reservation.save()
                    msg = f"Votre rendez-vous #{reservation.id} a été reprogrammé au {new_date.strftime('%d/%m/%Y')} à {new_time_str} avec {new_emp.full_name}."
                except (ValueError, ObjectDoesNotExist):
                    msg = "Paramètres de modification invalides."
                    msg_type = 'danger'
                except ValidationError as e:
                    msg = e.messages[0] if hasattr(e, 'messages') else str(e)
                    msg_type = 'danger'
            else:
                msg = "Impossible de modifier ce rendez-vous dans son statut actuel."
                msg_type = 'danger'

        elif action == 'rate_service' and res_id:
            reservation = get_object_or_404(Reservation, id=res_id, client=request.user)
            if reservation.status == 'COMPLETED':
                rating_val = request.POST.get('rating')
                comment = request.POST.get('review_comment', '').strip()
                if rating_val and rating_val.isdigit():
                    reservation.rating = min(5, max(1, int(rating_val)))
                    reservation.review_comment = comment
                    reservation.save()
                    msg = "Merci pour votre évaluation ! Votre avis a bien été pris en compte."
                else:
                    msg = "Veuillez attribuer une note entre 1 et 5 étoiles."
                    msg_type = 'danger'

    all_reservations = Reservation.objects.filter(client=request.user).select_related('service', 'employee').order_by('-date', '-start_time')
    
    upcoming_reservations = [r for r in all_reservations if r.status in ['PENDING', 'CONFIRMED', 'ARRIVED', 'IN_PROGRESS']]
    completed_reservations = [r for r in all_reservations if r.status == 'COMPLETED']
    cancelled_reservations = [r for r in all_reservations if r.status in ['CANCELLED', 'NO_SHOW']]

    all_employees = Employee.objects.filter(is_team_member=True, is_active=True).exclude(role='ADMINISTRATEUR').order_by('first_name')

    # Fetch User Orders for Client Portal
    user_orders = Order.objects.filter(
        Q(client=request.user) | Q(client_email=request.user.email, client_email__gt='')
    ).prefetch_related('items').distinct().order_by('-created_at')

    context = {
        'page_title': 'Mes Réservations & Commandes',
        'all_reservations': all_reservations,
        'upcoming_reservations': upcoming_reservations,
        'completed_reservations': completed_reservations,
        'cancelled_reservations': cancelled_reservations,
        'all_employees': all_employees,
        'user_orders': user_orders,
        'msg': msg,
        'msg_type': msg_type,
    }
    return render(request, 'core/client_reservations.html', context)


@reception_required
def dashboard_reservations(request):
    msg = ""
    msg_type = "info"
    if request.method == 'POST':
        action = request.POST.get('action')
        res_id = request.POST.get('reservation_id')
        new_status = request.POST.get('status')
        
        if action == 'update_status' and res_id and new_status:
            res = get_object_or_404(Reservation, id=res_id)
            res.status = new_status
            res.save()
            msg = f"Statut de la réservation #{res.id} mis à jour : {res.get_status_display()}."

    reservations = Reservation.objects.select_related('client', 'employee', 'service').all()

    employee_id = request.GET.get('employee_id')
    date_filter = request.GET.get('date')
    service_id = request.GET.get('service_id')
    status_filter = request.GET.get('status')

    if employee_id:
        reservations = reservations.filter(employee_id=employee_id)
    if date_filter:
        reservations = reservations.filter(date=date_filter)
    if service_id:
        reservations = reservations.filter(service_id=service_id)
    if status_filter:
        reservations = reservations.filter(status=status_filter)

    total_count = Reservation.objects.count()
    pending_count = Reservation.objects.filter(status='PENDING').count()
    confirmed_count = Reservation.objects.filter(status='CONFIRMED').count()
    arrived_count = Reservation.objects.filter(status='ARRIVED').count()
    in_progress_count = Reservation.objects.filter(status='IN_PROGRESS').count()
    completed_count = Reservation.objects.filter(status='COMPLETED').count()
    cancelled_count = Reservation.objects.filter(status='CANCELLED').count()
    no_show_count = Reservation.objects.filter(status='NO_SHOW').count()

    team_employees = Employee.objects.filter(is_team_member=True, is_active=True).order_by('first_name')
    services = Service.objects.filter(is_active=True).order_by('name')

    emp = getattr(request.user, 'employee_profile', None)
    emp_role = emp.role if emp else ''
    base_template = 'core/admin/admin_base.html' if (request.user.is_superuser or emp_role == 'ADMINISTRATEUR') else 'core/employee/employee_base.html'

    no_show_reservations = Reservation.objects.filter(
        Q(status='NO_SHOW') | Q(notes__icontains='NO_SHOW')
    ).select_related('service', 'client', 'employee').distinct().order_by('-date', '-start_time')[:10]

    from django.db.models import Sum
    paid_revenue = Payment.objects.filter(
        reservation__isnull=False, status='PAID'
    ).exclude(
        status='REFUNDED'
    ).exclude(
        reservation__status__in=['CANCELLED', 'NO_SHOW']
    ).aggregate(Sum('amount'))['amount__sum'] or 0.0
    pending_payments_count = Reservation.objects.exclude(status__in=['CANCELLED', 'NO_SHOW']).exclude(payments__status='PAID').count()

    context = {
        'page_title': 'Gestion des Réservations',
        'active_menu': 'reservations',
        'base_template': base_template,
        'reservations': reservations,
        'team_employees': team_employees,
        'services': services,
        'total_count': total_count,
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        'arrived_count': arrived_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'no_show_count': no_show_count,
        'paid_revenue': round(float(paid_revenue), 2),
        'pending_payments_count': pending_payments_count,
        'no_show_reservations': no_show_reservations,
        'selected_employee_id': employee_id,
        'selected_date': date_filter,
        'selected_service_id': service_id,
        'selected_status': status_filter,
        'msg': msg,
        'msg_type': msg_type,
    }
    return render(request, 'core/admin/dashboard_reservations.html', context)


def password_reset_code(request):
    step = 'send_code'

    if request.GET.get('reset_email') == '1':
        if 'reset_otp' in request.session:
            del request.session['reset_otp']
        return redirect('account_reset_password')

    email = ''

    def find_user_by_email_or_username(value):
        search_val = value.strip().lower()
        if not search_val:
            return None
        return User.objects.filter(
            Q(email__iexact=search_val) | Q(username__iexact=search_val)
        ).first()

    def send_reset_code(request, user):
        if not user.email:
            messages.error(
                request,
                "Ce compte n'a pas d'adresse email. Contactez le support pour réinitialiser votre mot de passe.",
            )
            return None

        code = f"{random.randint(100000, 999999)}"
        request.session['reset_otp'] = {
            'code': code,
            'user_id': user.id,
            'email': user.email,
        }

        try:
            send_mail(
                subject="Votre code de vérification - British Style",
                message=(
                    f"Bonjour {user.first_name or user.username},\n\n"
                    f"Votre code de vérification pour réinitialiser votre mot de passe est : {code}\n\n"
                    "Ce code est valable pour la réinitialisation de votre compte."
                ),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'British Style <noreply@britishstyle.com>'),
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception:
            messages.error(
                request,
                "Impossible d'envoyer l'email. Vérifiez la configuration Gmail dans le fichier .env (EMAIL_HOST_USER et EMAIL_HOST_PASSWORD).",
            )
            return None

        messages.success(request, f"Un code de vérification a été envoyé à {user.email}.")
        return user.email

    if request.method == 'GET' and request.GET.get('email'):
        param_email = request.GET.get('email', '').strip()
        user = find_user_by_email_or_username(param_email)

        if user:
            sent_to = send_reset_code(request, user)
            if sent_to:
                step = 'verify_code'
                email = sent_to
            else:
                email = param_email
                step = 'send_code'
        else:
            messages.error(request, f"Aucun compte trouvé avec l'email ou le nom d'utilisateur '{param_email}'.")
            email = param_email
            step = 'send_code'

    elif 'reset_otp' in request.session:
        email = request.session['reset_otp'].get('email', '')
        step = 'verify_code'

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'send_code':
            raw_input = request.POST.get('email', '').strip()
            user = find_user_by_email_or_username(raw_input)

            if user:
                sent_to = send_reset_code(request, user)
                if sent_to:
                    step = 'verify_code'
                    email = sent_to
                else:
                    email = raw_input
                    step = 'send_code'
            else:
                messages.error(request, "Aucun compte trouvé avec cet email ou nom d'utilisateur.")
                step = 'send_code'
                email = raw_input

        elif action == 'verify_code':
            user_code = request.POST.get('code', '').strip().replace(' ', '')
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')

            otp_data = request.session.get('reset_otp')
            if not otp_data:
                messages.error(request, "Session expirée. Veuillez demander un nouveau code.")
                return redirect('account_reset_password')

            expected_code = str(otp_data.get('code'))
            user_id = otp_data.get('user_id')
            email = otp_data.get('email', '')

            if user_code != expected_code:
                messages.error(request, "Code de vérification incorrect. Veuillez réessayer.")
                step = 'verify_code'
            elif len(password1) < 6:
                messages.error(request, "Le mot de passe doit contenir au moins 6 caractères.")
                step = 'verify_code'
            elif password1 != password2:
                messages.error(request, "Les mots de passe ne correspondent pas.")
                step = 'verify_code'
            else:
                try:
                    user = User.objects.get(id=user_id)
                    user.set_password(password1)
                    user.save()
                    if 'reset_otp' in request.session:
                        del request.session['reset_otp']
                    messages.success(request, "Votre mot de passe a été réinitialisé avec succès ! Vous pouvez maintenant vous connecter.")
                    return redirect('account_login')
                except User.DoesNotExist:
                    messages.error(request, "Utilisateur non trouvé.")
                    step = 'send_code'

    return render(request, 'account/password_reset.html', {
        'step': step,
        'email': email,
    })


import json

@require_POST
def api_create_order(request):
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Format de requête invalide.'}, status=400)

    cart_items = data.get('cart', [])
    if not cart_items:
        return JsonResponse({'error': 'Votre panier est vide.'}, status=400)

    client_name = data.get('name', '').strip()
    client_phone = data.get('phone', '').strip()
    client_address = data.get('address', '').strip()
    client_email = data.get('email', '').strip()

    clean_phone_digits = ''.join(c for c in client_phone if c.isdigit())

    if not client_name:
        return JsonResponse({'error': 'Le nom est obligatoire.'}, status=400)

    if len(clean_phone_digits) != 10:
        return JsonResponse({'error': 'Le numéro de téléphone est obligatoire et doit comporter exactement 10 chiffres (ex: 0612345678).'}, status=400)

    raw_delivery_mode = data.get('delivery_mode', 'delivery')  # 'delivery' or 'collect'
    raw_payment_mode = data.get('payment_mode', 'cod')        # 'cod', 'card', 'store'

    # Map frontend keys to DB values
    delivery_mode = 'DELIVERY' if raw_delivery_mode == 'delivery' else 'CLICK_COLLECT'

    if raw_payment_mode == 'card':
        payment_mode = 'CARD'
    elif raw_payment_mode == 'store':
        payment_mode = 'STORE'
    else:
        payment_mode = 'COD'

    # Ensure address is provided if DELIVERY
    if delivery_mode == 'DELIVERY' and not client_address:
        return JsonResponse({'error': "L'adresse de livraison est requise pour la livraison à domicile."}, status=400)

    # Server-Side Price & Shipping Recalculation (Authoritative)
    calculated_subtotal = 0.0
    order_items_data = []

    for item in cart_items:
        name = item.get('name', '')
        unit_price = float(item.get('unitPrice', 0))
        quantity = int(item.get('quantity', 1))
        variant = item.get('variant', '')

        # Try matching DB product for authoritative price
        db_product = Product.objects.filter(name__iexact=name.strip()).first()
        if db_product:
            unit_price = float(db_product.price)

        if quantity < 1:
            quantity = 1

        item_subtotal = unit_price * quantity
        calculated_subtotal += item_subtotal

        order_items_data.append({
            'product': db_product,
            'product_name': name,
            'product_price': unit_price,
            'quantity': quantity,
            'variant': variant,
            'subtotal': item_subtotal,
        })

    # Shipping fee calculation (Server authoritative: +10 DH for DELIVERY, 0 DH for CLICK_COLLECT)
    shipping_fee = 10.0 if delivery_mode == 'DELIVERY' else 0.0
    total = calculated_subtotal + shipping_fee

    # Initial status logic
    payment_status = 'PAID' if payment_mode == 'CARD' else 'PENDING'
    order_status = 'NEW'

    client_user = request.user if request.user.is_authenticated else None

    # Create Order
    order = Order.objects.create(
        client=client_user,
        client_name=client_name,
        client_phone=client_phone,
        client_email=client_email or (client_user.email if client_user else ''),
        shipping_address=client_address,
        subtotal=calculated_subtotal,
        shipping_fee=shipping_fee,
        total=total,
        delivery_mode=delivery_mode,
        payment_mode=payment_mode,
        order_status=order_status,
        payment_status=payment_status,
    )

    # Create OrderItems
    for item_data in order_items_data:
        OrderItem.objects.create(
            order=order,
            product=item_data['product'],
            product_name=item_data['product_name'],
            product_price=item_data['product_price'],
            quantity=item_data['quantity'],
            variant=item_data['variant'],
            subtotal=item_data['subtotal'],
        )

    # Automatic Caisse / Payment Entry for Online Card Payments
    if payment_status == 'PAID':
        Payment.objects.create(
            client=client_user,
            order=order,
            amount=total,
            payment_method='CARD' if payment_mode == 'CARD' else 'CASH',
            payment_type='BOUTIQUE',
            status='PAID',
            notes=f"Paiement automatique en ligne par carte pour la commande #{order.id}"
        )

    return JsonResponse({
        'success': True,
        'order_id': order.id,
        'message': f"Merci {order.client_name} ! Votre commande #{order.id} a été enregistrée avec succès.",
        'total': float(order.total),
    })


@admin_required
def dashboard_orders(request):
    msg = None
    msg_type = 'success'

    emp = getattr(request.user, 'employee_profile', None)
    emp_role = emp.role if emp else ''
    is_admin_role = request.user.is_superuser or emp_role == 'ADMINISTRATEUR'
    can_perform_actions = True

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_order_status = request.POST.get('order_status')
        new_payment_status = request.POST.get('payment_status')

        order = get_object_or_404(Order, id=order_id)
        if new_order_status and new_order_status in dict(Order.ORDER_STATUS_CHOICES):
            order.order_status = new_order_status
        if new_payment_status and new_payment_status in dict(Order.PAYMENT_STATUS_CHOICES):
            order.payment_status = new_payment_status
            if new_payment_status == 'PAID' and not order.payments.filter(status='PAID').exists():
                Payment.objects.create(
                    client=order.client,
                    order=order,
                    amount=order.total,
                    payment_method='CASH',
                    payment_type='BOUTIQUE',
                    status='PAID',
                    receptionist=request.user,
                    notes=f"Paiement validé depuis la gestion des commandes #{order.id}"
                )
            elif new_payment_status in ['CANCELLED', 'REFUNDED']:
                order.order_status = 'CANCELLED'
                order.payments.filter(status='PAID').update(status='REFUNDED')
        order.save()
        msg = f"Statuts de la commande #{order.id} mis à jour avec succès (Commande: {order.get_order_status_display()} | Paiement: {order.get_payment_status_display()})."

    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('order_status', '')
    payment_filter = request.GET.get('payment_status', '')

    orders_qs = Order.objects.prefetch_related('items').all().order_by('-created_at')

    if search_query:
        orders_qs = orders_qs.filter(
            Q(id__icontains=search_query) |
            Q(client_name__icontains=search_query) |
            Q(client_phone__icontains=search_query) |
            Q(client_email__icontains=search_query)
        )

    if status_filter:
        orders_qs = orders_qs.filter(order_status=status_filter)

    if payment_filter:
        orders_qs = orders_qs.filter(payment_status=payment_filter)

    # Metrics
    all_orders = Order.objects.all()
    total_orders_count = all_orders.count()
    total_revenue = all_orders.filter(payment_status='PAID').exclude(order_status='CANCELLED').exclude(payment_status__in=['CANCELLED', 'REFUNDED']).aggregate(Sum('total'))['total__sum'] or 0.0
    new_orders_count = all_orders.filter(order_status='NEW').count()
    pending_payments_count = all_orders.filter(payment_status='PENDING').count()

    base_template = 'core/admin/admin_base.html' if (request.user.is_superuser or emp_role == 'ADMINISTRATEUR') else 'core/employee/employee_base.html'

    context = {
        'page_title': 'Gestion des Commandes',
        'active_menu': 'orders',
        'base_template': base_template,
        'orders': orders_qs,
        'search_query': search_query,
        'status_filter': status_filter,
        'payment_filter': payment_filter,
        'total_orders_count': total_orders_count,
        'total_revenue': round(float(total_revenue), 2),
        'new_orders_count': new_orders_count,
        'pending_payments_count': pending_payments_count,
        'order_status_choices': Order.ORDER_STATUS_CHOICES,
        'payment_status_choices': Order.PAYMENT_STATUS_CHOICES,
        'can_perform_actions': can_perform_actions,
        'is_admin_role': is_admin_role,
        'msg': msg,
        'msg_type': msg_type,
    }
    return render(request, 'core/admin/dashboard_orders.html', context)


# ==========================================
# RECEPTIONIST SPACE VIEWS (ESPACE RÉCEPTIONNISTE)
# ==========================================

def check_employee_availability(employee, date_obj, start_time_obj, end_time_obj, exclude_reservation_id=None):
    att = employee.attendance_records.filter(date=date_obj).first()
    if att and att.status in ['ABSENT', 'REPOS']:
        status_disp = "absent(e)" if att.status == 'ABSENT' else "en repos"
        return False, f"L'employé(e) {employee.full_name} est {status_disp} le {date_obj.strftime('%d/%m/%Y')}."

    res_qs = Reservation.objects.filter(
        employee=employee,
        date=date_obj,
        start_time__lt=end_time_obj,
        end_time__gt=start_time_obj
    ).exclude(status__in=['CANCELLED', 'NO_SHOW'])

    if exclude_reservation_id:
        res_qs = res_qs.exclude(pk=exclude_reservation_id)

    if res_qs.exists():
        r = res_qs.first()
        return False, f"L'employé(e) {employee.full_name} a déjà un rendez-vous ({r.service.name}) de {r.start_time.strftime('%H:%M')} à {r.end_time.strftime('%H:%M')}."

    break_qs = EmployeeBreak.objects.filter(
        employee=employee,
        date=date_obj,
        start_time__lt=end_time_obj,
        end_time__gt=start_time_obj
    )
    if break_qs.exists():
        b = break_qs.first()
        return False, f"L'employé(e) {employee.full_name} est en pause ({b.title}) de {b.start_time.strftime('%H:%M')} à {b.end_time.strftime('%H:%M')}."

    return True, "Disponible"


@reception_required
def reception_dashboard(request):
    today = timezone.now().date()
    
    # 1. Real-time statistics
    today_reservations_qs = Reservation.objects.filter(date=today)
    today_reservations_count = today_reservations_qs.count()
    pending_reservations_count = today_reservations_qs.filter(status='PENDING').count()
    expected_clients_count = today_reservations_qs.filter(status__in=['PENDING', 'CONFIRMED', 'ARRIVED', 'IN_PROGRESS']).count()
    
    today_payments_total = Payment.objects.filter(created_at__date=today, status='PAID').aggregate(Sum('amount'))['amount__sum'] or 0.00
    click_collect_pending_count = Order.objects.filter(
        delivery_mode='CLICK_COLLECT',
        order_status__in=['NEW', 'CONFIRMED', 'PREPARING', 'READY_FOR_PICKUP']
    ).count()

    # Timeline schedule for today
    schedule_reservations = today_reservations_qs.select_related('client', 'employee', 'service').order_by('start_time')
    
    # Preload choices and data for modals & filters
    all_employees = Employee.objects.filter(is_team_member=True, is_active=True).order_by('first_name')
    all_services = Service.objects.filter(is_active=True).order_by('category', 'name')
    all_clients = User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username')
    
    recent_notifications = Notification.objects.filter(
        Q(employee__isnull=True) | Q(employee__role='RECEPTION')
    ).order_by('-created_at')[:10]

    context = {
        'page_title': 'Tableau de Bord Réception',
        'active_menu': 'dashboard',
        'today_date': today,
        'today_reservations_count': today_reservations_count,
        'pending_reservations_count': pending_reservations_count,
        'expected_clients_count': expected_clients_count,
        'today_payments_total': round(float(today_payments_total), 2),
        'click_collect_pending_count': click_collect_pending_count,
        'schedule_reservations': schedule_reservations,
        'all_employees': all_employees,
        'all_services': all_services,
        'all_clients': all_clients,
        'recent_notifications': recent_notifications,
    }
    return render(request, 'core/reception/dashboard.html', context)


@reception_required
def reception_planning(request):
    today = timezone.now().date()
    date_str = request.GET.get('date', today.strftime('%Y-%m-%d'))
    try:
        query_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        query_date = today

    employee_id = request.GET.get('employee_id', '')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')

    res_qs = Reservation.objects.filter(date=query_date).select_related('client', 'employee', 'service').order_by('start_time')

    if employee_id:
        res_qs = res_qs.filter(employee_id=employee_id)
    if category_filter:
        res_qs = res_qs.filter(service__category__icontains=category_filter)
    if status_filter:
        res_qs = res_qs.filter(status=status_filter)

    all_employees = Employee.objects.filter(is_team_member=True, is_active=True).order_by('first_name')
    all_services = Service.objects.filter(is_active=True).order_by('category', 'name')
    all_clients = User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username')

    context = {
        'page_title': 'Planning du Jour',
        'active_menu': 'planning',
        'query_date': query_date,
        'query_date_str': query_date.strftime('%Y-%m-%d'),
        'reservations': res_qs,
        'employee_id': employee_id,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'all_employees': all_employees,
        'all_services': all_services,
        'all_clients': all_clients,
        'status_choices': Reservation.STATUS_CHOICES,
    }
    return render(request, 'core/reception/planning.html', context)


@reception_required
def reception_reservation_create(request):
    if request.method == 'POST':
        client_id = request.POST.get('client_id')
        service_id = request.POST.get('service_id')
        employee_id = request.POST.get('employee_id')
        date_str = request.POST.get('date')
        time_str = request.POST.get('start_time')
        notes = request.POST.get('notes', '').strip()

        if not all([client_id, service_id, employee_id, date_str, time_str]):
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return redirect(request.META.get('HTTP_REFERER', 'reception_dashboard'))

        try:
            client = User.objects.get(id=client_id)
            service = Service.objects.get(id=service_id)
            employee = Employee.objects.get(id=employee_id)
            res_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            start_t = datetime.datetime.strptime(time_str, '%H:%M').time()
        except (User.DoesNotExist, Service.DoesNotExist, Employee.DoesNotExist, ValueError) as e:
            messages.error(request, f"Données de réservation invalides: {e}")
            return redirect(request.META.get('HTTP_REFERER', 'reception_dashboard'))

        dummy_d = datetime.date(2000, 1, 1)
        dt_start = datetime.datetime.combine(dummy_d, start_t)
        dt_end = dt_start + datetime.timedelta(minutes=service.duration_minutes)
        end_t = dt_end.time()

        is_avail, avail_reason = check_employee_availability(employee, res_date, start_t, end_t)
        if not is_avail:
            messages.error(request, f"❌ Impossible de réserver : {avail_reason}")
            return redirect(request.META.get('HTTP_REFERER', 'reception_dashboard'))

        res = Reservation.objects.create(
            client=client,
            employee=employee,
            service=service,
            date=res_date,
            start_time=start_t,
            end_time=end_t,
            status='CONFIRMED',
            notes=notes
        )

        Notification.objects.create(
            title="📅 Nouveau Rendez-vous Créé",
            message=f"Rendez-vous #{res.id} créé par la Réception pour {client.get_full_name() or client.username} ({service.name}) avec {employee.full_name} le {res_date.strftime('%d/%m/%Y')} à {start_t.strftime('%H:%M')}.",
            employee=employee
        )

        messages.success(request, f"✅ Rendez-vous #{res.id} enregistré avec succès pour {client.get_full_name() or client.username} !")
        return redirect(request.META.get('HTTP_REFERER', 'reception_dashboard'))

    return redirect('reception_dashboard')


@reception_required
def reception_reservation_edit(request, pk):
    res = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        service_id = request.POST.get('service_id')
        employee_id = request.POST.get('employee_id')
        date_str = request.POST.get('date')
        time_str = request.POST.get('start_time')
        status = request.POST.get('status')
        notes = request.POST.get('notes', '').strip()

        try:
            service = Service.objects.get(id=service_id) if service_id else res.service
            employee = Employee.objects.get(id=employee_id) if employee_id else res.employee
            res_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else res.date
            start_t = datetime.datetime.strptime(time_str, '%H:%M').time() if time_str else res.start_time
        except (Service.DoesNotExist, Employee.DoesNotExist, ValueError) as e:
            messages.error(request, f"Données de modification invalides : {e}")
            return redirect(request.META.get('HTTP_REFERER', 'reception_planning'))

        dummy_d = datetime.date(2000, 1, 1)
        dt_start = datetime.datetime.combine(dummy_d, start_t)
        dt_end = dt_start + datetime.timedelta(minutes=service.duration_minutes)
        end_t = dt_end.time()

        if status not in ['CANCELLED', 'NO_SHOW']:
            is_avail, avail_reason = check_employee_availability(employee, res_date, start_t, end_t, exclude_reservation_id=res.id)
            if not is_avail:
                messages.error(request, f"❌ Modification impossible : {avail_reason}")
                return redirect(request.META.get('HTTP_REFERER', 'reception_planning'))

        res.service = service
        res.employee = employee
        res.date = res_date
        res.start_time = start_t
        res.end_time = end_t
        if status and status in dict(Reservation.STATUS_CHOICES):
            res.status = status
        res.notes = notes
        res.save()

        messages.success(request, f"Modifications enregistrées pour le rendez-vous #{res.id}.")
        return redirect(request.META.get('HTTP_REFERER', 'reception_planning'))

    return redirect('reception_planning')


@reception_required
def reception_reservation_arrived(request, pk):
    res = get_object_or_404(Reservation, pk=pk)
    now_dt = timezone.localtime(timezone.now())
    
    res.arrival_time = now_dt
    res.status = 'ARRIVED'
    res.save()

    client_name = f"{res.client.first_name} {res.client.last_name}".strip() or res.client.username
    time_formatted = now_dt.strftime('%H:%M')

    # Send Notification to assigned Employee
    Notification.objects.create(
        title="🟢 Cliente Arrivée en Réception",
        message=f"Votre cliente {client_name} est arrivée en réception à {time_formatted} pour la prestation {res.service.name} (RDV #{res.id}).",
        employee=res.employee
    )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"🟢 Cliente {client_name} arrivée à {time_formatted}",
            'arrival_time': time_formatted,
            'status': res.status,
            'status_display': res.get_status_display()
        })

    messages.success(request, f"🟢 Cliente {client_name} marquée comme arrivée à {time_formatted}.")
    return redirect(request.META.get('HTTP_REFERER', 'reception_dashboard'))


@reception_required
def reception_reservation_cancel(request, pk):
    res = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('cancellation_reason', 'Autre').strip()
        custom_note = request.POST.get('cancellation_note', '').strip()
        
        full_reason = f"{reason} - {custom_note}".strip(' -')
        res.status = 'CANCELLED'
        res.cancellation_reason = full_reason
        if custom_note:
            res.notes = f"{res.notes}\n[Annulation: {full_reason}]".strip()
        res.save()

        Notification.objects.create(
            title="🔴 Rendez-vous Annulé",
            message=f"Le rendez-vous #{res.id} de {res.client.get_full_name() or res.client.username} ({res.service.name}) a été annulé par la Réception. Motif : {full_reason}.",
            employee=res.employee
        )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Rendez-vous annulé et créneau libéré.'})

        messages.info(request, f"🔴 Rendez-vous #{res.id} annulé. Le créneau est à nouveau disponible.")
        return redirect(request.META.get('HTTP_REFERER', 'reception_planning'))

    return redirect('reception_planning')


@reception_required
def reception_payments(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # 1. Action: Remboursement (Refund)
        if action == 'refund':
            payment_id = request.POST.get('payment_id')
            refund_reason = request.POST.get('refund_reason', '').strip()
            if not payment_id:
                messages.error(request, "Paiement non spécifié pour le remboursement.")
                return redirect('reception_payments')
            
            payment = get_object_or_404(Payment, id=payment_id)
            if payment.status == 'REFUNDED':
                messages.warning(request, f"Le paiement {payment.reference_code} est déjà remboursé.")
                return redirect('reception_payments')
            
            payment.status = 'REFUNDED'
            payment.refunded_at = timezone.now()
            payment.refund_reason = refund_reason or "Remboursement client par la réception"
            payment.refunded_by = request.user
            payment.save()

            if payment.order:
                payment.order.payment_status = 'REFUNDED'
                payment.order.order_status = 'CANCELLED'
                payment.order.save()

            Notification.objects.create(
                title=f"💸 Remboursement Effectué ({payment.reference_code})",
                message=f"Le paiement {payment.reference_code} de {payment.amount:.2f} DH a été remboursé par {request.user.username}.\nMotif: {payment.refund_reason}",
                type='ADMIN',
                employee=None
            )

            messages.success(request, f"🔴 Remboursement du paiement {payment.reference_code} de {payment.amount:.2f} DH enregistré avec succès.")
            return redirect('reception_payments')

        # 2. Action: Encaissement lié à un Rendez-vous (pay_reservation)
        elif action == 'pay_reservation' or request.POST.get('reservation_id'):
            reservation_id = request.POST.get('reservation_id')
            amount_str = request.POST.get('amount')
            payment_method = request.POST.get('payment_method', 'CASH')
            notes = request.POST.get('notes', '').strip()

            if not reservation_id:
                messages.error(request, "Veuillez sélectionner un rendez-vous à encaisser.")
                return redirect('reception_payments')

            reservation = get_object_or_404(Reservation, id=reservation_id)

            # Prevent duplicate payment
            if reservation.is_paid:
                messages.warning(request, f"Le rendez-vous #{reservation.id} ({reservation.service.name}) est déjà marqué comme payé.")
                return redirect('reception_payments')

            try:
                amount = float(amount_str) if amount_str else float(reservation.service.price)
            except ValueError:
                amount = float(reservation.service.price)

            payment = Payment.objects.create(
                client=reservation.client,
                reservation=reservation,
                amount=amount,
                payment_method=payment_method,
                payment_type='SERVICE',
                status='PAID',
                receptionist=request.user,
                notes=notes or f"Encaissement Soin {reservation.service.name}"
            )

            messages.success(request, f"🟢 Encaissement {payment.reference_code} de {amount:.2f} DH enregistré pour le RDV #{reservation.id} ({reservation.service.name}) !")
            return redirect('reception_payments')

        # 3. Action: Encaissement d'une Commande Boutique (pay_order)
        elif action == 'pay_order' or (request.POST.get('order_id') and not request.POST.get('reservation_id')):
            order_id = request.POST.get('order_id')
            amount_str = request.POST.get('amount')
            payment_method = request.POST.get('payment_method', 'CASH')
            notes = request.POST.get('notes', '').strip()
            mark_retrieved = request.POST.get('mark_retrieved') in ['true', '1', 'on']

            if not order_id:
                messages.error(request, "Veuillez sélectionner une commande à encaisser.")
                return redirect('reception_payments')

            order = get_object_or_404(Order, id=order_id)

            # Prevent duplicate payment
            if order.payment_status == 'PAID':
                messages.warning(request, f"La commande #{order.id} est déjà enregistrée comme payée.")
                return redirect('reception_payments')

            try:
                amount = float(amount_str) if amount_str else float(order.total)
            except ValueError:
                amount = float(order.total)

            payment = Payment.objects.create(
                client=order.client,
                order=order,
                amount=amount,
                payment_method=payment_method,
                payment_type='BOUTIQUE',
                status='PAID',
                receptionist=request.user,
                notes=notes or f"Encaissement commande #{order.id} ({order.get_delivery_mode_display()})"
            )

            order.payment_status = 'PAID'
            if mark_retrieved or order.delivery_mode == 'CLICK_COLLECT':
                order.order_status = 'RETRIEVED'
            elif order.delivery_mode == 'DELIVERY' and order.order_status == 'DELIVERING':
                order.order_status = 'DELIVERED'
            order.save()

            messages.success(request, f"🛍️ Encaissement {payment.reference_code} de {amount:.2f} DH enregistré pour la commande #{order.id} (Payé 🟢).")
            return redirect('reception_payments')

        # 4. Action: Encaissement Direct (Nouvel Encaissement libre)
        else:
            client_id = request.POST.get('client_id')
            amount_str = request.POST.get('amount')
            payment_method = request.POST.get('payment_method', 'CASH')
            payment_type = request.POST.get('payment_type', 'SERVICE')
            description = request.POST.get('description', '').strip()
            notes = request.POST.get('notes', '').strip()
            status = request.POST.get('status', 'PAID')

            if not amount_str:
                messages.error(request, "Veuillez préciser le montant de l'encaissement.")
                return redirect('reception_payments')

            try:
                amount = float(amount_str)
                client = User.objects.get(id=client_id) if client_id else None
            except (ValueError, User.DoesNotExist) as e:
                messages.error(request, f"Erreur de saisie : {e}")
                return redirect('reception_payments')

            full_notes = f"{description}\n{notes}".strip() if description else notes

            payment = Payment.objects.create(
                client=client,
                amount=amount,
                payment_method=payment_method,
                payment_type=payment_type,
                status=status,
                receptionist=request.user,
                notes=full_notes
            )

            messages.success(request, f"💵 Encaissement direct {payment.reference_code} de {amount:.2f} DH enregistré avec succès.")
            return redirect('reception_payments')

    # GET Request Processing
    search_query = request.GET.get('q', '').strip()
    date_filter = request.GET.get('date', '').strip()
    client_filter = request.GET.get('client_id', '').strip()
    method_filter = request.GET.get('method', '').strip()
    status_filter = request.GET.get('status', '').strip()
    origin_filter = request.GET.get('origin', '').strip()
    service_filter = request.GET.get('service_id', '').strip()

    payments_qs = Payment.objects.select_related(
        'client', 'reservation', 'reservation__service', 'order', 'receptionist'
    ).all().order_by('-created_at')

    # Apply Search & Filters
    if search_query:
        q_num = search_query.replace('#PAY-', '').replace('PAY-', '').replace('#', '').strip()
        search_filter = (
            Q(client__first_name__icontains=search_query) |
            Q(client__last_name__icontains=search_query) |
            Q(client__username__icontains=search_query) |
            Q(order__client_name__icontains=search_query) |
            Q(order__client_phone__icontains=search_query) |
            Q(notes__icontains=search_query) |
            Q(reservation__service__name__icontains=search_query)
        )
        if q_num.isdigit():
            search_filter |= Q(id=int(q_num)) | Q(order_id=int(q_num)) | Q(reservation_id=int(q_num))
        payments_qs = payments_qs.filter(search_filter)

    if date_filter:
        try:
            filter_dt = datetime.datetime.strptime(date_filter, '%Y-%m-%d').date()
            payments_qs = payments_qs.filter(created_at__date=filter_dt)
        except ValueError:
            pass

    if client_filter:
        payments_qs = payments_qs.filter(client_id=client_filter)

    if method_filter:
        payments_qs = payments_qs.filter(payment_method=method_filter)

    if status_filter:
        payments_qs = payments_qs.filter(status=status_filter)

    if service_filter:
        payments_qs = payments_qs.filter(reservation__service_id=service_filter)

    if origin_filter:
        if origin_filter == 'SERVICE':
            payments_qs = payments_qs.filter(Q(reservation__isnull=False) | Q(payment_type='SERVICE'))
        elif origin_filter == 'CLICK_COLLECT':
            payments_qs = payments_qs.filter(order__delivery_mode='CLICK_COLLECT')
        elif origin_filter == 'LIVRAISON':
            payments_qs = payments_qs.filter(order__delivery_mode='DELIVERY')
        elif origin_filter == 'BOUTIQUE':
            payments_qs = payments_qs.filter(Q(order__isnull=False) | Q(payment_type='BOUTIQUE'))
        elif origin_filter == 'DIRECT':
            payments_qs = payments_qs.filter(reservation__isnull=True, order__isnull=True, payment_type='AUTRE')

    # Calculate Cash Dashboard Metrics in real-time
    today = timezone.localtime(timezone.now()).date()
    
    today_paid_qs = Payment.objects.filter(created_at__date=today, status='PAID')
    month_paid_qs = Payment.objects.filter(created_at__year=today.year, created_at__month=today.month, status='PAID')

    total_today = today_paid_qs.aggregate(Sum('amount'))['amount__sum'] or 0.00
    total_month = month_paid_qs.aggregate(Sum('amount'))['amount__sum'] or 0.00

    services_today = today_paid_qs.filter(Q(reservation__isnull=False) | Q(payment_type='SERVICE')).aggregate(Sum('amount'))['amount__sum'] or 0.00
    boutique_today = today_paid_qs.filter(Q(order__isnull=False) | Q(payment_type='BOUTIQUE')).aggregate(Sum('amount'))['amount__sum'] or 0.00

    cash_today = today_paid_qs.filter(payment_method='CASH').aggregate(Sum('amount'))['amount__sum'] or 0.00
    card_today = today_paid_qs.filter(payment_method='CARD').aggregate(Sum('amount'))['amount__sum'] or 0.00
    digital_today = today_paid_qs.filter(payment_method='DIGITAL').aggregate(Sum('amount'))['amount__sum'] or 0.00

    # Data for Modals
    all_clients = User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username')
    all_services = Service.objects.filter(is_active=True).order_by('category', 'name')
    
    service_categories = Service.objects.filter(is_active=True).values_list('category', flat=True).distinct()

    # Unpaid reservations available for payment
    unpaid_reservations = Reservation.objects.filter(
        status__in=['ARRIVED', 'IN_PROGRESS', 'COMPLETED', 'CONFIRMED']
    ).exclude(payments__status='PAID').select_related('client', 'employee', 'service').order_by('-date', '-start_time')[:40]

    # Unpaid orders available for payment
    unpaid_orders = Order.objects.filter(
        payment_status='PENDING'
    ).prefetch_related('items', 'client').order_by('-created_at')[:40]

    context = {
        'page_title': 'Gestion des Paiements & Caisse',
        'active_menu': 'payments',
        'payments': payments_qs,
        'search_query': search_query,
        'date_filter': date_filter,
        'client_filter': client_filter,
        'method_filter': method_filter,
        'status_filter': status_filter,
        'origin_filter': origin_filter,
        'service_filter': service_filter,
        
        # Cash Dashboard Stats
        'total_today': round(float(total_today), 2),
        'total_month': round(float(total_month), 2),
        'services_today': round(float(services_today), 2),
        'boutique_today': round(float(boutique_today), 2),
        'cash_today': round(float(cash_today), 2),
        'card_today': round(float(card_today), 2),
        'digital_today': round(float(digital_today), 2),

        # Selection datasets
        'all_clients': all_clients,
        'all_services': all_services,
        'service_categories': service_categories,
        'pending_reservations': unpaid_reservations,
        'pending_orders': unpaid_orders,
        
        # Choice tuples
        'payment_methods': Payment.PAYMENT_METHOD_CHOICES,
        'payment_statuses': Payment.STATUS_CHOICES,
        'payment_types': Payment.PAYMENT_TYPE_CHOICES,
    }
    return render(request, 'core/reception/payments.html', context)


@reception_required
def reception_orders(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_order_status':
            order_id = request.POST.get('order_id')
            new_status = request.POST.get('new_status')
            if order_id and new_status:
                order = get_object_or_404(Order, id=order_id)
                order.order_status = new_status
                
                # Auto-confirm payment if marked as DELIVERED or RETRIEVED
                if new_status in ['DELIVERED', 'RETRIEVED'] and order.payment_status == 'PENDING':
                    order.payment_status = 'PAID'
                    Payment.objects.create(
                        client=order.client,
                        order=order,
                        amount=order.total,
                        payment_method='CASH',
                        payment_type='BOUTIQUE',
                        status='PAID',
                        receptionist=request.user,
                        notes=f"Encaissement automatique livraison/retrait commande #{order.id}"
                    )
                    messages.success(request, f"🟢 Commande #{order.id} marquée comme {order.get_order_status_display()} et paiement de {order.total:.2f} DH enregistré !")
                else:
                    messages.success(request, f"Statut de la commande #{order.id} mis à jour : {order.get_order_status_display()}")
                
                order.save()
                return redirect(request.META.get('HTTP_REFERER', 'reception_orders'))

    search_query = request.GET.get('q', '').strip()
    delivery_filter = request.GET.get('delivery_mode', '')
    status_filter = request.GET.get('order_status', '')

    orders_qs = Order.objects.prefetch_related('items', 'client').all().order_by('-created_at')

    if search_query:
        orders_qs = orders_qs.filter(
            Q(id__icontains=search_query) |
            Q(client_name__icontains=search_query) |
            Q(client_phone__icontains=search_query) |
            Q(client_email__icontains=search_query)
        )

    if delivery_filter:
        orders_qs = orders_qs.filter(delivery_mode=delivery_filter)

    if status_filter:
        orders_qs = orders_qs.filter(order_status=status_filter)

    click_collect_orders = orders_qs.filter(delivery_mode='CLICK_COLLECT')
    delivery_orders = orders_qs.filter(delivery_mode='DELIVERY')

    context = {
        'page_title': 'Boutique & Click & Collect',
        'active_menu': 'orders',
        'click_collect_orders': click_collect_orders,
        'delivery_orders': delivery_orders,
        'search_query': search_query,
        'delivery_filter': delivery_filter,
        'status_filter': status_filter,
        'order_status_choices': Order.ORDER_STATUS_CHOICES,
        'click_collect_status_choices': Order.CLICK_COLLECT_STATUS_CHOICES,
        'delivery_status_choices': Order.DELIVERY_STATUS_CHOICES,
        'payment_methods': Payment.PAYMENT_METHOD_CHOICES,
    }
    return render(request, 'core/reception/orders.html', context)


@reception_required
def reception_confirm_pickup(request, pk):
    order = get_object_or_404(Order, pk=pk, delivery_mode='CLICK_COLLECT')
    order.order_status = 'RETRIEVED'
    
    payment_method = request.POST.get('payment_method', 'CASH')
    
    if order.payment_status == 'PENDING':
        order.payment_status = 'PAID'
        Payment.objects.create(
            client=order.client,
            order=order,
            amount=order.total,
            payment_method=payment_method,
            payment_type='BOUTIQUE',
            status='PAID',
            receptionist=request.user,
            notes=f"Paiement au retrait Click & Collect #{order.id}"
        )

    order.save()

    Notification.objects.create(
        title="📦 Commande Retirée",
        message=f"La commande Click & Collect #{order.id} a été marquée comme retirée par {order.client_name} en Réception.",
        type='ORDER',
        employee=None
    )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': f'Commande #{order.id} marquée comme Retirée.'})

    messages.success(request, f"📦 Commande Click & Collect #{order.id} confirmée retirée et encaissée ({order.total:.2f} DH) !")
    return redirect(request.META.get('HTTP_REFERER', 'reception_orders'))



@reception_required
def reception_clients(request):
    search_query = request.GET.get('q', '').strip()
    selected_client_id = request.GET.get('client_id')

    clients_qs = User.objects.filter(is_active=True).order_by('first_name', 'last_name')

    if search_query:
        clients_qs = clients_qs.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(employee_profile__phone__icontains=search_query)
        )

    selected_client = None
    upcoming_reservations = []
    past_reservations = []
    client_orders = []
    client_payments = []
    booked_services_summary = []

    if selected_client_id:
        selected_client = get_object_or_404(User, pk=selected_client_id)
        today = timezone.now().date()
        
        upcoming_reservations = Reservation.objects.filter(client=selected_client, date__gte=today).select_related('service', 'employee').order_by('date', 'start_time')
        past_reservations = Reservation.objects.filter(client=selected_client, date__lt=today).select_related('service', 'employee').order_by('-date')
        client_orders = Order.objects.filter(client=selected_client).prefetch_related('items').order_by('-created_at')
        client_payments = Payment.objects.filter(client=selected_client).order_by('-created_at')

        # Collect distinct booked services
        service_ids = Reservation.objects.filter(client=selected_client).values_list('service_id', flat=True).distinct()
        booked_services_summary = Service.objects.filter(id__in=service_ids)

    context = {
        'page_title': 'Gestion des Clientes',
        'active_menu': 'clients',
        'clients': clients_qs,
        'search_query': search_query,
        'selected_client': selected_client,
        'upcoming_reservations': upcoming_reservations,
        'past_reservations': past_reservations,
        'client_orders': client_orders,
        'client_payments': client_payments,
        'booked_services_summary': booked_services_summary,
    }
    return render(request, 'core/reception/clients.html', context)


@reception_required
def reception_notifications(request):
    if request.method == 'POST' and request.POST.get('action') == 'mark_all_read':
        Notification.objects.filter(Q(employee__isnull=True) | Q(employee__role='RECEPTION')).update(is_read=True)
        messages.success(request, "Toutes les notifications ont été marquées comme lues.")
        return redirect('reception_notifications')

    notifications = Notification.objects.filter(
        Q(employee__isnull=True) | Q(employee__role='RECEPTION')
    ).order_by('-created_at')

    context = {
        'page_title': 'Centre de Notifications Réception',
        'active_menu': 'notifications',
        'notifications': notifications,
    }
    return render(request, 'core/reception/notifications.html', context)


@reception_required
def reception_api_live_stats(request):
    today = timezone.now().date()
    today_reservations_qs = Reservation.objects.filter(date=today)
    
    today_reservations_count = today_reservations_qs.count()
    pending_reservations_count = today_reservations_qs.filter(status='PENDING').count()
    expected_clients_count = today_reservations_qs.filter(status__in=['PENDING', 'CONFIRMED', 'ARRIVED', 'IN_PROGRESS']).count()
    today_payments_total = Payment.objects.filter(created_at__date=today, status='PAID').aggregate(Sum('amount'))['amount__sum'] or 0.00
    click_collect_pending_count = Order.objects.filter(
        delivery_mode='CLICK_COLLECT',
        order_status__in=['NEW', 'CONFIRMED', 'PREPARING', 'READY_FOR_PICKUP']
    ).count()

    unread_notifications = Notification.objects.filter(
        (Q(employee__isnull=True) | Q(employee__role='RECEPTION')),
        is_read=False
    ).count()

    return JsonResponse({
        'today_reservations_count': today_reservations_count,
        'pending_reservations_count': pending_reservations_count,
        'expected_clients_count': expected_clients_count,
        'today_payments_total': f"{today_payments_total:.2f} DH",
        'click_collect_pending_count': click_collect_pending_count,
        'unread_notifications': unread_notifications,
    })


@reception_required
def reception_api_check_availability(request):
    employee_id = request.GET.get('employee_id')
    date_str = request.GET.get('date')
    start_time_str = request.GET.get('start_time')
    duration_str = request.GET.get('duration_minutes', '30')
    exclude_id = request.GET.get('exclude_reservation_id')

    if not all([employee_id, date_str, start_time_str]):
        return JsonResponse({'available': False, 'message': 'Paramètres manquants.'}, status=400)

    try:
        employee = Employee.objects.get(id=employee_id)
        res_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        start_t = datetime.datetime.strptime(start_time_str, '%H:%M').time()
        duration = int(duration_str)
    except (Employee.DoesNotExist, ValueError) as e:
        return JsonResponse({'available': False, 'message': f'Données invalides: {e}'}, status=400)

    dummy_d = datetime.date(2000, 1, 1)
    dt_start = datetime.datetime.combine(dummy_d, start_t)
    dt_end = dt_start + datetime.timedelta(minutes=duration)
    end_t = dt_end.time()

    is_avail, reason = check_employee_availability(
        employee, res_date, start_t, end_t,
        exclude_reservation_id=int(exclude_id) if exclude_id and exclude_id.isdigit() else None
    )

    return JsonResponse({
        'available': is_avail,
        'message': reason
    })