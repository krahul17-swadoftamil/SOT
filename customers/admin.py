from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "get_username", "name", "phone", "email", "city", "pincode", "created_at")
    search_fields = ("user__username", "name", "phone", "email", "city", "pincode")
    list_filter = ("city", "pincode", "created_at")

    def get_username(self, obj):
        return obj.user.username if obj.user else "-"
    get_username.short_description = "Username"