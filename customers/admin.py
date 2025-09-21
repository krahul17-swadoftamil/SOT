from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("get_username", "mobile", "city", "pincode", "created_at")
    search_fields = ("user__username", "mobile", "city", "pincode")

    def get_username(self, obj):
        return obj.user.username if obj.user else "-"
    get_username.short_description = "Username"
