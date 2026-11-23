from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "buyer", "producer", "quantity", "total_price", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("product__name", "buyer__username", "producer__username")
    readonly_fields = ("unit_price", "total_price", "created_at", "updated_at")
