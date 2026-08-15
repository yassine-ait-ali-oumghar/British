# British Style

A Django 6.0.7 web application with two custom apps — `core` and `vendor`.

---

## Project Structure

```
British_Style/
├── manage.py                    # Django CLI entry point
├── British_Style/               # Project configuration package
│   ├── __init__.py
│   ├── settings.py              # Django settings (DB, apps, middleware, etc.)
│   ├── urls.py                  # Root URL configuration
│   ├── wsgi.py                  # WSGI application for deployment
│   └── asgi.py                  # ASGI application for async deployment
├── apps/                        # Custom Django applications
│   ├── core/                    # Core app — public pages
│   │   ├── __init__.py
│   │   ├── apps.py              # AppConfig: CoreConfig
│   │   ├── views.py             # View functions (frontpage, contact)
│   │   ├── urls.py              # URL patterns for core
│   │   ├── models.py            # (empty — no models yet)
│   │   ├── admin.py             # (empty — no admin registration yet)
│   │   ├── tests.py             # (empty — no tests yet)
│   │   └── templates/
│   │       └── core/
│   │           ├── base.html       # Base template (Bootstrap 5 + footer)
│   │           ├── frontpage.html  # Home page
│   │           └── contact.html    # Contact page
│   └── vendor/                  # Vendor app — vendor management
│       ├── __init__.py
│       ├── apps.py              # AppConfig: VendorConfig
│       ├── models.py            # Vendor model
│       ├── admin.py             # Vendor registered in admin
│       ├── views.py             # (empty — no views yet)
│       ├── tests.py             # (empty — no tests yet)
│       └── migrations/
│           └── 0001_initial.py  # Initial migration for Vendor model
└── static/
    └── styles/
        └── main.css             # Custom footer styles
```

---

## File-by-File Documentation

### 1. `manage.py`

**Purpose:** Standard Django CLI entry point. Sets `DJANGO_SETTINGS_MODULE` to `British_Style.settings` and calls `execute_from_command_line`.

**Key code:**
```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'British_Style.settings')
execute_from_command_line(sys.argv)
```

---

### 2. `British_Style/settings.py`

**Purpose:** Main Django settings file.

**Key configuration:**
| Setting | Value |
|---|---|
| `SECRET_KEY` | `django-insecure-#o=p6!qmt2@0%^^ri(cccr9!c$scp0i0dsr!6@ey9m+ryxm6(0` |
| `DEBUG` | `True` |
| `ALLOWED_HOSTS` | `[]` (empty — development only) |
| `INSTALLED_APPS` | Default Django apps + `apps.core`, `apps.vendor` |
| `DATABASES` | SQLite (`db.sqlite3`) |
| `STATIC_URL` | `static/` |
| `STATICFILES_DIRS` | `[BASE_DIR / 'static']` |

**Templates:** Uses Django template backend with `APP_DIRS=True` (looks for `templates/` inside each app).

---

### 3. `British_Style/urls.py`

**Purpose:** Root URL configuration.

**URL patterns:**
| Path | Target |
|---|---|
| `admin/` | Django admin site |
| `""` (root) | `apps.core.urls` |

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
]
```

---

### 4. `British_Style/wsgi.py`

**Purpose:** WSGI entry point for production deployment (Gunicorn, uWSGI, etc.).

```python
application = get_wsgi_application()
```

---

### 5. `British_Style/asgi.py`

**Purpose:** ASGI entry point for async deployment (Daphne, Uvicorn, etc.).

```python
application = get_asgi_application()
```

---

### 6. `apps/core/apps.py`

**Purpose:** App configuration for the `core` app.

```python
class CoreConfig(AppConfig):
    name = 'apps.core'
```

---

### 7. `apps/core/views.py`

**Purpose:** View functions for public pages.

| Function | Template | URL name |
|---|---|---|
| `frontpage(request)` | `core/frontpage.html` | — |
| `contact(request)` | `core/contact.html` | — |

```python
def frontpage(request):
    return render(request, 'core/frontpage.html')

def contact(request):
    return render(request, 'core/contact.html')
```

---

### 8. `apps/core/urls.py`

**Purpose:** URL routing for the `core` app.

| Path | View | Name |
|---|---|---|
| `""` (root) | `frontpage` | `frontpage` |
| `contact/` | `contact` | `contact` |

```python
urlpatterns = [
    path('', views.frontpage, name='frontpage'),
    path('contact/', views.contact, name='contact'),
]
```

---

### 9. `apps/core/models.py`

Currently empty — no database models defined yet.

```python
from django.db import models
# Create your models here.
```

---

### 10. `apps/core/admin.py`

Currently empty — no admin registrations yet.

```python
from django.contrib import admin
# Register your models here.
```

---

### 11. `apps/core/templates/core/base.html`

**Purpose:** Base HTML template — all other pages extend this.

**Features:**
- Bootstrap 5.3 CSS (CDN)
- Responsive navbar with:
  - Brand logo ("Navbar")
  - Home link
  - Dropdown menu
  - Contact link (links to `contact` URL)
  - Search form
- Main content block (`{% block content %}`)
- Dark footer with:
  - 4-column grid (Brand, Product, Resources, Company)
  - Social media icons (Twitter, GitHub, LinkedIn)
  - Copyright notice
- Bootstrap 5.3 JS bundle (includes Popper)

**Blocks available for child templates:**
- `{% block title %}` — page title (default: "British Style")
- `{% block content %}` — main content area

**Navbar code example:**
```html
<a class="nav-link active" href="{% url 'contact' %}">contact</a>
```

**Footer classes (styled in `main.css`):**
- `.footer-dark` — overall footer container
- `.footer-dark__main-grid` — 4-column responsive grid
- `.footer-dark__brand` — brand logo + description
- `.footer-dark__heading` — section headings
- `.footer-dark__links` — link lists
- `.footer-dark__bottom` — copyright + social row
- `.footer-dark__social` — social icon nav

---

### 12. `apps/core/templates/core/frontpage.html`

**Purpose:** Home page. Extends `base.html`.

```html
{% extends 'core/base.html' %}
{% block content %}
<h1>Welcome to the Front Page</h1>
{% endblock %}
```

---

### 13. `apps/core/templates/core/contact.html`

**Purpose:** Contact page. Extends `base.html`, overrides `title` and `content`.

```html
{% extends "core/base.html" %}
{% block title %}Contact Us{% endblock %}
{% block content %}
    <h1>Contact Us</h1>
{% endblock %}
```

---

### 14. `apps/vendor/apps.py`

**Purpose:** App configuration for the `vendor` app.

```python
class VendorConfig(AppConfig):
    name = 'apps.vendor'
```

> **Note:** The `name` must match the dotted Python path to the app. Since `vendor` lives inside the `apps` package, it must be `'apps.vendor'` (not `'vendor'`).

---

### 15. `apps/vendor/models.py`

**Purpose:** Database model for vendors.

**Vendor model fields:**
| Field | Type | Details |
|---|---|---|
| `name` | `CharField(max_length=255)` | Vendor name |
| `created_at` | `DateTimeField(auto_now_add=True)` | Auto-set on creation |
| `created_by` | `OneToOneField(User)` | Links to Django auth User, `on_delete=CASCADE` |

**Meta:**
```python
class Meta:
    ordering = ['name']
```

**String representation:**
```python
def __str__(self):
    return self.name
```

---

### 16. `apps/vendor/admin.py`

**Purpose:** Register the Vendor model in Django admin.

```python
from django.contrib import admin
from .models import Vendor

admin.site.register(Vendor)
```

This makes the `Vendor` model visible and editable at `/admin/`.

---

### 17. `apps/vendor/views.py`

Currently empty — no view functions defined yet.

```python
from django.shortcuts import render
# Create your views here.
```

---

### 18. `apps/vendor/migrations/0001_initial.py`

**Purpose:** Initial database migration for the Vendor model.

Created via `python manage.py makemigrations vendor`. Creates the `vendor_vendor` table with columns:
- `id` (auto-increment primary key)
- `name` (varchar 255)
- `created_at` (datetime)
- `created_by_id` (foreign key to `auth_user`)

---

### 19. `static/styles/main.css`

**Purpose:** Custom styles — primarily the dark footer layout.

**Key CSS classes:**

| Class | Purpose |
|---|---|
| `.footer-dark` | Dark background (`#121212`), light text (`#a0a0a0`), padding |
| `.footer-dark__main-grid` | CSS Grid — 1 column on mobile, 2 on tablet, 4 on desktop |
| `.footer-dark__brand .logo` | SVG logo sizing |
| `.footer-dark__heading` | White, bold headings |
| `.footer-dark__links a` | Link styling with hover effect |
| `.footer-dark__bottom` | Top border separator |
| `.footer-dark__social ul` | Horizontal flexbox for social icons |

**Responsive breakpoints:**
- `768px` — 2-column grid, social icons right-aligned
- `992px` — 4-column grid, bottom row uses flexbox (space-between)

**Layout helpers:**
```css
html, body { height: 100%; }
body { display: flex; flex-direction: column; min-height: 100vh; }
main { flex: 1 0 auto; }
```

---

## Authentication & Google OAuth (django-allauth)

The project uses `django-allauth` for email-based authentication and Google OAuth 2.0 single sign-on.

### Google OAuth Configuration (`settings.py`)

```python
INSTALLED_APPS = [
    ...
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

SITE_ID = 1

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': '1787044947-8oo9r1tfau5h2k46ird4a1n5jk65n0mn.apps.googleusercontent.com',
            'secret': 'GOCSPX-...',
            'key': ''
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PKCE_ENABLED': True,
    }
}
```

### URL Routes (`urls.py`)

- `http://127.0.0.1:8000/accounts/login/` — Custom Login Page with Google OAuth
- `http://127.0.0.1:8000/accounts/signup/` — Custom Sign Up Page
- `http://127.0.0.1:8000/accounts/logout/` — Sign Out Route
- `http://127.0.0.1:8000/accounts/google/login/` — Google OAuth Trigger Route
- `http://127.0.0.1:8000/accounts/google/login/callback/` — Google OAuth Callback URI

### Custom Templates (`apps/core/templates/account/`)

- `login.html`: Luxury custom login template with a **"Continuer avec Google"** button and email login form.
- `signup.html`: Luxury custom sign-up template with Google registration and email registration form.

---

## Layout & Header Alignment Fixes

To prevent fixed top navigation header (`#main-header`) overlap:
- Added `style="padding-top: 140px !important;"` to `.services-section`, `.team-section`, `.boutique-hero`, and `.contact-container` across `services.html`, `equipe.html`, `boutique.html`, and `contact.html`.
- Updated corresponding CSS files (`services.css`, `equipe.css`, `boutique.css`).

---

## Running the Project

```bash
# Activate the virtual environment
venv\Scripts\Activate.ps1

# Apply database migrations
python manage.py migrate

# Start the development server
python manage.py runserver
```

Then visit:
- `http://127.0.0.1:8000/` — Home page
- `http://127.0.0.1:8000/services/` — Services page
- `http://127.0.0.1:8000/boutique/` — Boutique page
- `http://127.0.0.1:8000/contact/` — Contact page
- `http://127.0.0.1:8000/accounts/login/` — Google OAuth / Allauth Login Page

---

## Technology Stack

| Component | Version / Library |
|---|---|
| Python | 3.14 |
| Django | 6.0.7 |
| Authentication | `django-allauth`, Google OAuth 2.0 |
| OAuth Dependencies | `requests`, `pyjwt`, `cryptography` |
| Database | SQLite3 |
| Frontend | Bootstrap 5.3 |
| Template Engine | Django Templates |

Email : admin@britishstyle.com
Nom d'utilisateur : admin
Mot de passe : admin123
---
