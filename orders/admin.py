# orders/admin.py
from django.contrib import admin
from .models import Order, OrderItem, CustomCombo, CustomComboItem, ComboRule


# ======================================================
# Inline for CustomComboItem
# ======================================================
class CustomComboItemInline(admin.TabularInline):
    model = CustomComboItem
    extra = 1
    autocomplete_fields = ["menu_item"]


# ======================================================
# CustomCombo Admin
# ======================================================
@admin.register(CustomCombo)
class CustomComboAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "get_customer_name", "get_vendor_name", "created_at")
    list_filter = ("created_at", "vendor")
    search_fields = (
        "title",
        "vendor__name",
        "customer__name",
        "customer__user__username",
    )
    ordering = ("-created_at",)
    inlines = [CustomComboItemInline]

    def get_customer_name(self, obj):
        customer = getattr(obj, "customer", None)
        if not customer:
            return "-"
        if getattr(customer, "user", None):
            return (
                customer.user.get_full_name()
                or customer.user.username
                or customer.user.email
            )
        return customer.name or str(customer)
    get_customer_name.short_description = "Customer"

    def get_vendor_name(self, obj):
        return obj.vendor.name if obj.vendor else "-"
    get_vendor_name.short_description = "Vendor"


# ======================================================
# ComboRule Admin
# ======================================================
@admin.register(ComboRule)
class ComboRuleAdmin(admin.ModelAdmin):
    list_display = ("menu_item", "min_quantity")
    search_fields = ("menu_item__name",)


# ======================================================
# OrderItem Admin
# ======================================================
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "get_order_id",
        "get_customer_name",
        "display_item_name",
        "quantity",
        "price",
        "created_at",
    )
    list_filter = ("combo", "custom_combo", "menu_item", "created_at")
    search_fields = (
        "order__id",
        "order__customer__name",
        "order__customer__user__username",
        "combo__name",
        "custom_combo__title",
        "menu_item__name",
    )
    autocomplete_fields = ["order", "combo", "custom_combo", "menu_item"]
    ordering = ("-created_at",)

    def get_order_id(self, obj):
        return obj.order.id if obj.order else "-"
    get_order_id.short_description = "Order ID"

    def get_customer_name(self, obj):
        customer = obj.order.customer if obj.order else None
        if not customer:
            return "-"
        if getattr(customer, "user", None):
            return (
                customer.user.get_full_name()
                or customer.user.username
                or customer.user.email
            )
        return customer.name or str(customer)
    get_customer_name.short_description = "Customer"

    def display_item_name(self, obj):
        if obj.menu_item:
            return obj.menu_item.name
        elif obj.combo:
            return obj.combo.name
        elif obj.custom_combo:
            return obj.custom_combo.title
        return "(no item)"
    display_item_name.short_description = "Item"


# ======================================================
# Inline for OrderItem inside Order
# ======================================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ["combo", "custom_combo", "menu_item"]
    fields = ("combo", "custom_combo", "menu_item", "quantity", "display_price")
    readonly_fields = ("display_price",)

    def display_price(self, obj):
        return f"₹{obj.price:.2f}" if obj.price else "-"
    display_price.short_description = "Price"


# ======================================================
# Order Admin
# ======================================================
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "get_customer_name",
        "get_vendor_name",
        "status",
        "payment_method",
        "total_price",
        "get_item_count",
        "created_at",
    )
    list_filter = ("status", "payment_method", "vendor", "created_at")
    search_fields = ("id", "customer__name", "customer__user__username", "vendor__name")
    ordering = ("-created_at",)
    inlines = [OrderItemInline]
    readonly_fields = ("total_price",)

    def get_customer_name(self, obj):
        customer = obj.customer
        if not customer:
            return "-"
        if getattr(customer, "user", None):
            return (
                customer.user.get_full_name()
                or customer.user.username
                or customer.user.email
            )
        return customer.name or str(customer)
    get_customer_name.short_description = "Customer"

    def get_vendor_name(self, obj):
        return obj.vendor.name if obj.vendor else "-"
    get_vendor_name.short_description = "Vendor"

    def get_item_count(self, obj):
        return obj.order_items.count()
    get_item_count.short_description = "Items"

    # Bulk actions
    actions = ["mark_confirmed", "mark_delivered", "mark_cancelled"]

    def mark_confirmed(self, request, queryset):
        queryset.update(status="confirmed")
    mark_confirmed.short_description = "Mark selected orders as Confirmed"

    def mark_delivered(self, request, queryset):
        queryset.update(status="delivered")
    mark_delivered.short_description = "Mark selected orders as Delivered"

    def mark_cancelled(self, request, queryset):
        queryset.update(status="cancelled")
    mark_cancelled.short_description = "Mark selected orders as Cancelled"
