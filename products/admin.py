from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "producer", "category", "price", "unit", "quantity", "location", "is_available", "created_at")
    list_filter = ("category", "is_available", "location")
    search_fields = ("name", "producer__username", "location")
    list_editable = ("is_available",)
