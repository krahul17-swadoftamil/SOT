from django.contrib import admin
from .models import MenuItem

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'vendor')  # only actual fields
    list_filter = ('vendor',)  # only actual fields
    search_fields = ('name',)  # needed for autocomplete_fields in other inlines
