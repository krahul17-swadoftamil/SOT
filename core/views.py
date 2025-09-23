# core/views.py
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .forms import ContactForm
from vendors.models import Vendor
from menuitem.models import Combo
from menuitem.models import MenuItem
from orders.models import Order
from .forms import ContactForm

logger = logging.getLogger(__name__)


# ----------------------
# Homepage
# ----------------------
def home(request):
    """
    Homepage: search, featured vendors, premium combos & contact form.
    """
    contact_form = ContactForm()

    featured_vendors = Vendor.objects.filter(is_active=True, available=True).order_by("-id")[:5]
    premium_combos = (
        Combo.objects.filter(is_available=True)
        .prefetch_related("vendors")
        .order_by("-created_at")[:10]
    )

    return render(request, "core/home.html", {
        "contact_form": contact_form,
        "featured_vendors": featured_vendors,
        "combos": premium_combos,
    })


# ----------------------
# Static Info Pages
# ----------------------
def about_us(request):
    return render(request, "core/about.html")


def brand_story(request):
    """Premium brand story page."""
    return render(request, "core/brand_story.html")


def mission(request):
    """Premium mission page."""
    return render(request, "core/mission.html")


def products(request):
    """Our products page."""
    return render(request, "core/products.html")


# ----------------------
# Contact Views
# ----------------------
def contact_view(request):
    """Display and process contact form."""
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()
            logger.info(f"📩 New contact message from {contact.name} <{contact.email}>")
            messages.success(request, "✅ Thank you! Your message has been sent.")
            return redirect("core:contact_view")
        else:
            messages.error(request, "⚠️ Please correct the errors below.")
    else:
        form = ContactForm()

    return render(request, "core/contact.html", {"contact_form": form})


# ----------------------
# Vendor Search & Listing
# ----------------------
def search_vendor(request):
    query = request.GET.get("query", "").strip()

    vendors = Vendor.objects.filter(
        Q(pincode__icontains=query) |
        Q(city__icontains=query) |
        Q(name__icontains=query) |
        Q(vendor_code__icontains=query),
        is_active=True
    )

    return render(request, "vendors/home.html", {
        "vendors": vendors,  # ✅ match template
        "query": query,
    })


def vendors_by_pincode(request, code=None):
    """List vendors filtered by exact pincode."""
    pincode = code or request.GET.get("pincode", "").strip()

    vendors = Vendor.objects.filter(pincode=pincode, is_active=True) if pincode else Vendor.objects.none()

    paginator = Paginator(vendors, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "vendors/vendors_list.html", {
        "vendors": page_obj,
        "pincode": pincode,
        "page_obj": page_obj,
    })


# ----------------------
# Vendor Detail & Orders
# ----------------------
def vendor_detail(request, code: str):
    """Vendor detail page using vendor_code (e.g., SOT001)."""
    vendor = get_object_or_404(Vendor, vendor_code=code, is_active=True)
    menu_items = MenuItem.objects.filter(vendor=vendor, available=True)
    moods = menu_items.values_list("mood", flat=True).distinct()

    # Track view count (optional field)
    if hasattr(vendor, "view_count"):
        try:
            vendor.view_count += 1
            vendor.save(update_fields=["view_count"])
        except Exception as e:
            logger.error(f"Failed to update view count for vendor {vendor.vendor_code}: {str(e)}")

    return render(request, "vendors/vendor_detail.html", {
        "vendor": vendor,
        "menu_items": menu_items,
        "moods": moods,
    })


def create_order(request, code: str):
    """Order creation page for a vendor (combo-based)."""
    vendor = get_object_or_404(Vendor, vendor_code=code, is_active=True)
    combos = Combo.objects.filter(vendors=vendor, is_available=True)

    # Fetch last 10 orders for history
    last_orders_qs = Order.objects.filter(vendor=vendor).order_by("-created_at")[:10]
    last_orders = [{
        "customer_name": o.customer_name,
        "customer_mobile": o.customer_mobile,
        "combo": o.combo,
        "quantity": o.quantity,
        "price": o.combo.price,
        "total": o.quantity * o.combo.price,
    } for o in last_orders_qs]

    if request.method == "POST":
        placed = False
        for combo in combos:
            qty = request.POST.get(f"quantity_{combo.id}")
            if qty and int(qty) > 0:
                Order.objects.create(
                    vendor=vendor,
                    combo=combo,
                    quantity=int(qty),
                    customer_name="Anonymous",   # TODO: Replace with form field
                    customer_mobile="0000000000" # TODO: Replace with form field
                )
                placed = True

        if placed:
            messages.success(request, "✅ Order placed successfully!")
        else:
            messages.warning(request, "⚠️ Please select at least one combo.")

        return redirect(request.path_info)

    return render(request, "orders/order.html", {
        "vendor": vendor,
        "combos": combos,
        "last_orders": last_orders,
    })


# ----------------------
# AJAX / API Endpoints
# ----------------------
def ajax_search_vendor(request):
    """Live search API for vendors (autocomplete)."""
    query = request.GET.get("q", "").strip()
    vendors = Vendor.objects.filter(
        Q(name__icontains=query) |
        Q(city__icontains=query) |
        Q(pincode__icontains=query),
        is_active=True
    )[:10] if query else Vendor.objects.none()

    results = [{
        "id": v.id,
        "code": v.vendor_code,
        "name": v.name,
        "city": v.city,
        "pincode": getattr(v, "pincode", ""),
        "mobile": getattr(v, "mobile", ""),
        "image": v.image.url if v.image else "",
    } for v in vendors]

    return JsonResponse({"vendors": results})


@csrf_exempt
def track_vendor_click(request, code: str):
    """Track vendor card clicks for analytics."""
    vendor = get_object_or_404(Vendor, vendor_code=code, is_active=True)
    if hasattr(vendor, "click_count"):
        try:
            vendor.click_count += 1
            vendor.save(update_fields=["click_count"])
        except Exception as e:
            logger.error(f"Error tracking click for vendor {code}: {str(e)}")
    return JsonResponse({"status": "success"})


# ----------------------
# Admin / Dashboard
# ----------------------
def vendor_dashboard(request):
    """Simple vendor dashboard for admins."""
    vendors = Vendor.objects.filter(is_active=True).order_by("-id")
    total_vendors = vendors.count()
    active_vendors = vendors.filter(available=True).count()

    paginator = Paginator(vendors, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "vendors/vendor_dashboard.html", {
        "vendors": page_obj,
        "total_vendors": total_vendors,
        "active_vendors": active_vendors,
    })


# ----------------------
# Utilities
# ----------------------
def filter_vendors(query=None, pincode=None, city=None):
    """Reusable vendor filter function."""
    filters = Q(is_active=True)
    if query:
        filters &= Q(name__icontains=query)
    if pincode:
        filters &= Q(pincode__icontains=pincode)
    if city:
        filters &= Q(city__icontains=city)
    return Vendor.objects.filter(filters)

def menu(request):
    # build context for menu page (replace with your actual menu logic)
    context = {
        "menu_items": []  # populate from your MenuItem model
    }
    return render(request, "core/menu.html", context)
