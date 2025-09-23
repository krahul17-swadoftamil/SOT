from django.contrib import admin
from .models import Vendor, ComboItem, ComboVendor, VendorApplication
from menuitem.models import Combo   # ✅ use the real Combo

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
# Combo Admin (real model from menuitem)
# ----------------------
@admin.register(Combo)
class ComboAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "get_vendors")   # ✅ show vendors via helper
    list_filter = ("vendors", "is_available")         # ✅ use vendors (M2M)
    search_fields = ("name", "description")
    ordering = ("name",)
    list_editable = ("price",)
    inlines = [ComboItemInline, ComboVendorInline]

    # custom method to display vendors in list
    def get_vendors(self, obj):
        return ", ".join([v.name for v in obj.vendors.all()])
    get_vendors.short_description = "Vendors"

# ----------------------
# ComboItem Admin
# ----------------------
@admin.register(ComboItem)
class ComboItemAdmin(admin.ModelAdmin):
    list_display = ("combo", "menu_item", "quantity")
    list_filter = ("combo", "menu_item")
    search_fields = ("combo__name", "menu_item__name")
    autocomplete_fields = ["combo", "menu_item"]
