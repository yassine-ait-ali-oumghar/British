from django.urls import path
from . import views

urlpatterns = [
    path('become_vendor/', views.become_vendor, name='become_vendor'),
    path('vendor_admin/', views.vendor_admin, name='vendor_admin')
]