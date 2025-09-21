# core/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import ContactMessage, QuickMenu, Pincode, VendorAnalytics, FeaturedCombo





# ----------------------
# QuickMenu Admin
# ----------------------
@admin.register(QuickMenu)
class QuickMenuAdmin(admin.ModelAdmin):
    list_display = ("display_name", "vendor", "combo", "is_active", "highlight_preview", "created_at")
    list_filter = ("is_active", "vendor", "created_at")
    search_fields = ("display_name", "vendor__name", "combo__name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    def highlight_preview(self, obj):
        """Display a small color box for highlight_color."""
        return format_html(
            '<div style="width: 50px; height: 20px; background:{}; border-radius:4px; border:1px solid #ccc;"></div>',
            obj.highlight_color or "#ffffff"
        )
    highlight_preview.short_description = "Highlight Color"


# ----------------------
# Pincode Admin
# ----------------------
@admin.register(Pincode)
class PincodeAdmin(admin.ModelAdmin):
    list_display = ("code", "city", "is_active")
    list_filter = ("is_active", "city")
    search_fields = ("code", "city")
    ordering = ("code",)


# ----------------------
# Vendor Analytics Admin
# ----------------------
@admin.register(VendorAnalytics)
class VendorAnalyticsAdmin(admin.ModelAdmin):
    list_display = ("vendor", "total_views", "total_clicks", "total_orders", "updated_at")
    search_fields = ("vendor__name", "vendor__code")
    readonly_fields = ("total_views", "total_clicks", "total_orders", "created_at", "updated_at")
    ordering = ("-updated_at",)
    date_hierarchy = "updated_at"


# ----------------------
# Featured Combo Admin
# ----------------------
@admin.register(FeaturedCombo)
class FeaturedComboAdmin(admin.ModelAdmin):
    list_display = ("combo", "vendor", "title", "is_active", "highlight_preview", "created_at")
    list_filter = ("is_active", "vendor", "created_at")
    search_fields = ("combo__name", "vendor__name", "title")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    def highlight_preview(self, obj):
        """Show a small box with the selected highlight color."""
        return format_html(
            '<div style="width: 50px; height: 20px; background:{}; border-radius:4px; border:1px solid #ccc;"></div>',
            obj.highlight_color or "#ffffff"
        )
    highlight_preview.short_description = "Highlight Color"


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "mobile",
        "email",
        "enquiry_type",
        "subscribe",
        "created_at",
    )
    list_filter = ("enquiry_type", "subscribe", "created_at")
    search_fields = ("name", "mobile", "email", "message")
    ordering = ("-created_at",)

    # Read-only fields (prevent accidental edits)
    readonly_fields = ("created_at",)

    # Group fields in the form layout
    fieldsets = (
        ("👤 Contact Info", {
            "fields": ("name", "mobile", "email")
        }),
        ("📩 Message Details", {
            "fields": ("enquiry_type", "message", "subscribe")
        }),
        ("🕒 Metadata", {
            "fields": ("created_at",),
            "classes": ("collapse",),  # collapsed by default
        }),
    )

    # Optional: highlight new messages
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by("-created_at")
