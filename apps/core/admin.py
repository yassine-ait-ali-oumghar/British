from django.contrib import admin
from .models import Employee, AttendanceRecord, Product, Service, ContactMessage, Notification, Reservation

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'role', 'position', 'department', 'is_team_member', 'is_active')
    list_filter = ('role', 'department', 'is_team_member', 'is_active')
    search_fields = ('first_name', 'last_name', 'email', 'position')

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'status', 'check_in', 'check_out', 'pause_duration_minutes')
    list_filter = ('status', 'date')
    search_fields = ('employee__first_name', 'employee__last_name')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'duration_minutes', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'category')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('name', 'category')

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'employee', 'service', 'date', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'date', 'employee', 'service')
    search_fields = ('client__username', 'employee__first_name', 'employee__last_name', 'service__name')
