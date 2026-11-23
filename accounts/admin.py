from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import BuyerProfile, ProducerProfile, TransporterProfile, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "role", "city", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active", "city")
    search_fields = ("username", "email", "first_name", "last_name", "phone")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Informations AgriConnect", {"fields": ("role", "phone", "address", "city", "is_verified")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Informations AgriConnect", {"fields": ("role", "phone", "address", "city")}),
    )


@admin.register(ProducerProfile)
class ProducerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "farm_name")
    search_fields = ("user__username", "farm_name")


@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "company_name", "business_type")
    search_fields = ("user__username", "company_name")


@admin.register(TransporterProfile)
class TransporterProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "company_name", "vehicle_type", "coverage_area")
    search_fields = ("user__username", "company_name", "coverage_area")
