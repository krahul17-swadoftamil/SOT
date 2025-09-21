from django.contrib import admin
from .models import Vendor, Combo, ComboItem, ComboVendor
from .models import VendorApplication


# ----------------------
# Inline: Vendor–Combo relation (through model)
# ----------------------
class ComboVendorInline(admin.TabularInline):
    model = ComboVendor
    extra = 1
    autocomplete_fields = ["vendor", "combo"]


# ----------------------
# Inline: ComboItem inside Combo
# ----------------------
class ComboItemInline(admin.TabularInline):
    model = ComboItem
    extra = 1
    fields = ("menu_item", "quantity")
    autocomplete_fields = ["menu_item"]


# ----------------------
# Vendor Admin
# ----------------------
@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("vendor_code", "name", "city", "available", "is_active", "items_count")
    list_filter = ("available", "is_active", "city")
    search_fields = ("vendor_code", "name", "owner_name", "city")
    readonly_fields = ("vendor_code",)

@admin.register(VendorApplication)
class VendorApplicationAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "mobile", "city", "created_at")
    search_fields = ("name","email","mobile","city")
    list_filter = ("created_at",) 


# ----------------------
# Combo Admin
# ----------------------
@admin.register(Combo)
class ComboAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "is_available", "created_at")
    list_filter = ("is_available",)
    search_fields = ("name", "description")
    ordering = ("name",)
    list_editable = ("price", "is_available")
    inlines = [ComboItemInline, ComboVendorInline]


# ----------------------
# ComboItem Admin
# ----------------------
@admin.register(ComboItem)
class ComboItemAdmin(admin.ModelAdmin):
    list_display = ("combo", "menu_item", "quantity")
    list_filter = ("combo", "menu_item")
    search_fields = ("combo__name", "menu_item__name")
    autocomplete_fields = ["combo", "menu_item"]
