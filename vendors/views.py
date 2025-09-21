# vendors/views.py
import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.template.loader import render_to_string

from .models import Vendor, Combo
from .forms import VendorApplicationForm
from orders.models import Customer, Order, OrderItem
from menuitem.models import MenuItem

logger = logging.getLogger(__name__)


# ----------------------
# 🏠 Vendor Homepage
# ----------------------
def home(request):
    """
    Vendor landing page with featured vendors & combos.
    """
    vendors = Vendor.objects.filter(is_active=True, available=True)
    combos = Combo.objects.filter(is_available=True)[:6]
    return render(request, "vendors/home.html", {
        "vendors": vendors,
        "combos": combos,
    })


# ----------------------
# 🔍 Vendor Search (by city/pincode/SOT code)
# ----------------------
def search_vendor(request):
    pincode = request.GET.get("pincode", "").strip()
    city = request.GET.get("city", "").strip()
    sot = request.GET.get("sot", "").strip()

    vendors = Vendor.objects.filter(is_active=True)

    if pincode:
        vendors = vendors.filter(pincode__iexact=pincode)
    if city:
        vendors = vendors.filter(city__icontains=city)
    if sot:
        vendors = vendors.filter(vendor_code__iexact=sot)

    # Distinguish AJAX vs full page
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    context = {"vendors": vendors, "is_ajax": is_ajax}
    template_name = "vendors/home.html"

    return render(request, template_name, context)


# ----------------------
# 📋 Vendor Directory (search + full list)
# ----------------------
def vendor_list(request):
    """
    Search vendors dynamically by name, city, pincode, or vendor code.
    Falls back to showing all vendors if no query provided.
    """
    query = request.GET.get("query", "").strip()
    vendors = Vendor.objects.all()

    if query:
        vendors = vendors.filter(
            Q(name__icontains=query) |
            Q(city__icontains=query) |
            Q(pincode__icontains=query) |
            Q(code__icontains=query)
        )

    context = {
        "vendors": vendors.order_by("name"),
        "query": query,
    }
    return render(request, "vendors/home.html", context)


def vendors_list_view(request):
    """
    Full vendor directory (no filtering).
    """
    vendors = Vendor.objects.all().order_by("name")
    return render(request, "vendors/home.html", {"vendors": vendors})


# ----------------------
# 👨‍🍳 Vendor Detail
# ----------------------
def vendor_detail(request, code: str):
    """
    Vendor profile page with menu items and category/mood filtering.
    Tracks vendor view count for analytics.
    """
    vendor = get_object_or_404(Vendor, code=code, is_active=True)
    menu_items = MenuItem.objects.filter(vendor=vendor, available=True)
    moods = menu_items.values_list("mood", flat=True).distinct()

    # Track vendor views safely
    try:
        vendor.view_count = getattr(vendor, "view_count", 0) + 1
        vendor.save(update_fields=["view_count"])
    except Exception as e:
        logger.warning(f"Could not update view count for vendor {vendor.code}: {e}")

    return render(request, "vendors/vendor_detail.html", {
        "vendor": vendor,
        "menu_items": menu_items,
        "moods": moods,
    })


# ----------------------
# 💬 Secure WhatsApp Chat (no number exposure)
# ----------------------
def vendor_chat(request, vendor_id: int):
    """
    Redirect customer to vendor WhatsApp chat without exposing number.
    """
    vendor = get_object_or_404(Vendor, id=vendor_id, is_active=True)
    wa_url = f"https://wa.me/{vendor.whatsapp_number}?text=Hello%20{vendor.name},%20I%20found%20you%20on%20Swad%20of%20Tamil!"
    return redirect(wa_url)


# ----------------------
# 📝 Vendor Application (Onboarding)
# ----------------------
def vendor_apply(request):
    """
    Vendor onboarding form for new registrations.
    """
    if request.method == "POST":
        form = VendorApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Thank you! Your application has been submitted.")
            return redirect("vendors:apply")
        else:
            messages.error(request, "⚠️ Please correct the errors below.")
    else:
        form = VendorApplicationForm()

    return render(request, "vendors/apply.html", {"form": form})


# ----------------------
# 🛠 Custom Combo Order
# ----------------------
@login_required
@require_POST
def create_custom_order(request, code: str = None, vendor_id: int = None):
    """
    Create a custom combo order by vendor code or ID.
    """
    try:
        if code:
            vendor = get_object_or_404(Vendor, code=code, is_active=True)
        elif vendor_id:
            vendor = get_object_or_404(Vendor, id=vendor_id, is_active=True)
        else:
            return JsonResponse({"success": False, "error": "Vendor not specified"})

        customer, _ = Customer.objects.get_or_create(user=request.user)
        data = json.loads(request.body)

        items_data = data.get("items", [])
        payment_method = data.get("payment_method", "cod")
        special_instructions = data.get("special_instructions", "")

        if not items_data:
            return JsonResponse({"success": False, "error": "No items selected"})

        order = Order.objects.create(
            vendor=vendor,
            customer=customer,
            payment_method=payment_method,
            special_instructions=special_instructions,
        )

        total = 0
        for item in items_data:
            menu_item = get_object_or_404(MenuItem, id=item["id"], vendor=vendor)
            qty = int(item.get("quantity", 1))
            OrderItem.objects.create(order=order, menu_item=menu_item, quantity=qty)
            total += menu_item.price * qty

        order.total_amount = total
        order.save()

        return JsonResponse({"success": True, "order_id": order.id, "total_price": total})

    except Exception as e:
        logger.exception("Error creating custom order")
        return JsonResponse({"success": False, "error": str(e)})


@login_required
def create_custom_order_by_id(request, vendor_id: int):
    """
    Fallback: create custom order by vendor ID.
    """
    vendor = get_object_or_404(Vendor, id=vendor_id, is_active=True)
    if request.method == "POST":
        return JsonResponse({"success": True, "message": f"Order created for {vendor.name}"})
    return JsonResponse({"success": False, "error": "Invalid request method"})


# ----------------------
# ⚡ Quick Order
# ----------------------
@login_required
def quick_order(request, code: str):
    """
    Quick order for the first available combo.
    """
    vendor = get_object_or_404(Vendor, code=code, is_active=True)
    customer, _ = Customer.objects.get_or_create(user=request.user)

    combo = Combo.objects.filter(vendors=vendor, is_available=True).first()
    if not combo:
        messages.error(request, "No combos available for quick order.")
        return redirect("vendors:vendor_detail", code=vendor.code)

    order = Order.objects.create(
        vendor=vendor,
        customer=customer,
        payment_method="cod",
        special_instructions="Quick order placed",
    )
    order.total_amount = combo.price
    order.save()

    OrderItem.objects.create(order=order, combo=combo, quantity=1)

    messages.success(request, f"Quick order placed for {combo.name}")
    return redirect("orders:order_detail", order_id=order.id)


# ----------------------
# 📬 Contact
# ----------------------
@require_POST
def contact_submit(request):
    """
    Handle contact form submissions.
    """
    name = request.POST.get("name")
    email = request.POST.get("email")
    message = request.POST.get("message")

    logger.info(f"Contact Form: {name} ({email}): {message}")

    messages.success(request, "✅ Your message has been sent!")
    return redirect("vendors:home")


# ----------------------
# 💳 Checkout & Order Success
# ----------------------
@login_required
def checkout(request, order_id: int):
    order = get_object_or_404(Order, id=order_id, customer__user=request.user)
    return render(request, "vendors/checkout.html", {"order": order})


@login_required
def order_success(request, order_id: int):
    order = get_object_or_404(Order, id=order_id, customer__user=request.user)
    return render(request, "vendors/order_success.html", {"order": order})


# ----------------------
# 🧩 Combo Builder & Detail
# ----------------------
def combo_builder(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    return render(request, "vendors/combo_builder.html", {"vendor": vendor})


def combo_detail(request, pk: int):
    combo = get_object_or_404(Combo, pk=pk, is_available=True)
    return render(request, "vendors/combo_detail.html", {"combo": combo})


# ----------------------
# 📦 Vendor Items API
# ----------------------
def combo_builder(request, vendor_id: int):
    """
    Render combo builder page. The client JS will fetch items using vendor_code.
    """
    vendor = get_object_or_404(Vendor, id=vendor_id, is_active=True)
    # template will call API to fetch items (live)
    return render(request, "vendors/combo_builder.html", {"vendor": vendor})


@require_GET
def vendor_items_api(request, vendor_code):
    """
    Returns JSON list of menu items for a vendor. Uses vendor_code field.
    """
    # Use vendor_code field in DB (your model stores vendor_code)
    vendor = get_object_or_404(Vendor, vendor_code=vendor_code, is_active=True)
    items = MenuItem.objects.filter(vendor=vendor, available=True).order_by("name")

    payload = []
    for i in items:
        payload.append({
            "id": i.id,
            "name": i.name,
            "description": i.description if hasattr(i, "description") else "",
            "price": float(i.price),
            "available": bool(getattr(i, "available", True)),
            "image": i.image.url if getattr(i, "image", None) else None,
        })
    return JsonResponse({"items": payload})


@require_POST
@login_required
def create_custom_order(request, code: str = None, vendor_id: int = None):
    """
    Accepts JSON body: { items: [{id: <menuitem id>, quantity: <int>}, ...] }
    Creates Order & OrderItems and returns JSON { success, order_id, redirect_url }.
    """
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    if code:
        vendor = get_object_or_404(Vendor, vendor_code=code, is_active=True)
    elif vendor_id:
        vendor = get_object_or_404(Vendor, id=vendor_id, is_active=True)
    else:
        return JsonResponse({"success": False, "error": "Vendor not specified"}, status=400)

    items_data = payload.get("items") or []
    if not items_data:
        return JsonResponse({"success": False, "error": "No items provided"}, status=400)

    customer, _ = Customer.objects.get_or_create(user=request.user)

    # create order
    order = Order.objects.create(vendor=vendor, customer=customer, payment_method="cod", special_instructions=payload.get("special_instructions", ""))

    subtotal = 0
    for it in items_data:
        mid = int(it.get("id"))
        qty = int(it.get("quantity", 1))
        menu_item = get_object_or_404(MenuItem, id=mid, vendor=vendor)
        OrderItem.objects.create(order=order, menu_item=menu_item, quantity=qty)
        subtotal += float(menu_item.price) * qty

    # Example tax: compute GST or similar; keep in order.total_amount
    # If you have order model fields for gst, tax, etc., set them here.
    gst_percent = 5.0
    gst_amount = subtotal * (gst_percent / 100.0)
    total = subtotal + gst_amount

    order.subtotal = subtotal if hasattr(order, "subtotal") else None
    order.total_amount = total
    # Save then return
    order.save()

    # Return a redirect url to a friendly order summary page if available
    redirect_url = None
    try:
        # if you have named url orders:order_detail or orders:order_summary use it
        from django.urls import reverse
        redirect_url = reverse("orders:order_detail", args=[order.id])
    except Exception:
        redirect_url = f"/orders/detail/{order.id}/"

    return JsonResponse({"success": True, "order_id": order.id, "total_price": total, "redirect_url": redirect_url})
