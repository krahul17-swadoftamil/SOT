from django.contrib import admin
from .models import Order, OrderItem, CustomCombo, CustomComboItem


# ----------------------
# Inline for CustomComboItem
# ----------------------
class CustomComboItemInline(admin.TabularInline):
    model = CustomComboItem
    extra = 1
    autocomplete_fields = ['menu_item']


# ----------------------
# CustomCombo Admin
# ----------------------
@admin.register(CustomCombo)
class CustomComboAdmin(admin.ModelAdmin):
    list_display = ("title", "get_customer_name", "get_vendor_name", "mood", "price", "created_at")
    list_filter = ("mood", "vendor")
    search_fields = ("title", "customer__username", "vendor__name")
    ordering = ("-created_at",)
    inlines = [CustomComboItemInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.calculate_price()

    def get_customer_name(self, obj):
        return obj.customer.username if obj.customer else "-"
    get_customer_name.short_description = "Customer"

    def get_vendor_name(self, obj):
        return obj.vendor.name if obj.vendor else "-"
    get_vendor_name.short_description = "Vendor"


# ----------------------
# CustomComboItem Admin
# ----------------------
@admin.register(CustomComboItem)
class CustomComboItemAdmin(admin.ModelAdmin):
    list_display = ("combo", "menu_item", "quantity")
    list_filter = ("combo", "menu_item")
    search_fields = ("combo__title", "menu_item__name")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("combo", "custom_combo", "menu_item", "quantity", "addons", "display_total_price")
    readonly_fields = ("display_total_price",)

    def display_total_price(self, obj):
        return obj.total_price
    display_total_price.short_description = "Total Price"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "vendor", "status", "payment_method", "total_price", "created_at")
    list_filter = ("status", "payment_method", "vendor", "created_at")
    search_fields = ("id", "customer__user__username", "vendor__name")
    inlines = [OrderItemInline]
