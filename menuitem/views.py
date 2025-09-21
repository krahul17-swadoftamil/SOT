# menuitem/views.py
from django.shortcuts import render, get_object_or_404
from .models import MenuItem
from vendors.models import Vendor

# List all menu items for a vendor
def menu_list(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    items = MenuItem.objects.filter(vendor=vendor, is_available=True).order_by("category", "name")
    return render(request, "menuitem/menu_list.html", {
        "vendor": vendor,
        "items": items
    })

# Detail view for single menu item (optional)
def menu_detail(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    return render(request, "menuitem/menu_detail.html", {"item": item})

def combo_detail(request, combo_id):
    combo = get_object_or_404(Combo, id=combo_id)
    return render(request, "combo_detail.html", {"combo": combo})
