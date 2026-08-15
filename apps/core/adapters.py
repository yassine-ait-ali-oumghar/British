from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from apps.core.models import Employee

User = get_user_model()

class CustomAccountAdapter(DefaultAccountAdapter):
    def clean_username(self, username, shallow=False):
        cleaned_username = super().clean_username(username, shallow=False)
        if cleaned_username and User.objects.filter(username__iexact=cleaned_username).exists():
            raise ValidationError("Ce nom d'utilisateur est déjà utilisé. Veuillez en choisir un autre.")
        return cleaned_username

    def clean_email(self, email):
        cleaned_email = super().clean_email(email)
        if cleaned_email and User.objects.filter(email__iexact=cleaned_email).exists():
            raise ValidationError("Un compte avec cette adresse email existe déjà.")
        return cleaned_email

    def save_user(self, request, user, form, commit=True):
        username = user.username or (form.cleaned_data.get('username') if (hasattr(form, 'cleaned_data') and form.cleaned_data) else None)
        if username:
            base_username = username
            counter = 1
            qs = User.objects.filter(username__iexact=username)
            if user.pk:
                qs = qs.exclude(pk=user.pk)
            while qs.exists():
                username = f"{base_username}{counter}"
                counter += 1
                qs = User.objects.filter(username__iexact=username)
                if user.pk:
                    qs = qs.exclude(pk=user.pk)

            user.username = username
            if hasattr(form, 'cleaned_data') and form.cleaned_data is not None:
                form.cleaned_data['username'] = username
            if hasattr(form, 'user') and form.user:
                form.user.username = username

        phone = request.POST.get('phone', '').strip()
        saved_user = super().save_user(request, user, form, commit=commit)
        if saved_user.username != username:
            saved_user.username = username
            saved_user.save()

        if phone:
            emp = getattr(saved_user, 'employee_profile', None)
            if emp:
                emp.phone = phone
                emp.save()
            else:
                Employee.objects.create(
                    user=saved_user,
                    first_name=saved_user.first_name or saved_user.username,
                    email=saved_user.email or '',
                    phone=phone,
                    role='USER',
                    position='Utilisateur',
                    department='Général',
                    is_team_member=False,
                    is_active=True
                )
        return saved_user

    def get_login_redirect_url(self, request):
        user = request.user
        if user.is_authenticated:
            if not hasattr(user, 'employee_profile') or not user.employee_profile:
                first_name = user.first_name or user.username
                last_name = user.last_name or ""
                if user.is_staff or user.is_superuser:
                    role = 'ADMINISTRATEUR'
                    is_team = True
                    position = "Administrateur ERP"
                    department = "Direction"
                else:
                    role = 'USER'
                    is_team = False
                    position = "Utilisateur"
                    department = "Général"
                Employee.objects.get_or_create(
                    user=user,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': user.email or '',
                        'role': role,
                        'position': position,
                        'department': department,
                        'is_team_member': is_team,
                        'is_active': True
                    }
                )
            
            emp = user.employee_profile
            pos = (emp.position or '').lower()
            is_reception = emp.role == 'RECEPTION' or 'réception' in pos or 'reception' in pos
            if is_reception:
                return '/reception/dashboard/'
            if user.is_staff or user.is_superuser or emp.role == 'ADMINISTRATEUR':
                return '/dashboard/'
            if emp.is_team_member and emp.is_active and emp.role != 'USER':
                return '/employee/dashboard/'
            return '/'
        return '/'


    def get_signup_redirect_url(self, request):
        return self.get_login_redirect_url(request)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if not user.username:
            email = (data.get('email') or user.email or '').strip()
            base_username = email.split('@')[0] if email else 'user'
            username = base_username
            counter = 1
            while User.objects.filter(username__iexact=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            user.username = username
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        if not hasattr(user, 'employee_profile') or not user.employee_profile:
            first_name = user.first_name or user.username
            last_name = user.last_name or ""
            Employee.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': user.email or '',
                    'role': 'USER',
                    'position': 'Utilisateur',
                    'department': 'Général',
                    'is_team_member': False,
                    'is_active': True,
                },
            )
        return user

    def get_connect_redirect_url(self, request, socialaccount):
        account_adapter = CustomAccountAdapter(request)
        return account_adapter.get_login_redirect_url(request)

    def get_login_redirect_url(self, request):
        account_adapter = CustomAccountAdapter(request)
        return account_adapter.get_login_redirect_url(request)

    def get_signup_redirect_url(self, request):
        return self.get_login_redirect_url(request)




