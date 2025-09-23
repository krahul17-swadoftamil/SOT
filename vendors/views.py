# vendors/views.py
import json
import logging
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

from .forms import VendorApplicationForm
from orders.models import Order, OrderItem, OrderTracking, ComboRule
from customers.models import Customer
from menuitem.models import MenuItem, Combo
from vendors.models import Vendor
from .ai_combo import generate_ai_combos   # ✅ external AI logic module

logger = logging.getLogger(__name__)

# ----------------------
# 🏠 Vendor Homepage
# ----------------------
def home(request):
    vendors = Vendor.objects.filter(is_active=True)
    combos = Combo.objects.filter(is_available=True)[:6]
    return render(request, "vendors/home.html", {"vendors": vendors, "combos": combos})


# ----------------------
# 🔍 Vendor Search
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

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    return render(request, "vendors/home.html", {"vendors": vendors, "is_ajax": is_ajax})


# ----------------------
# 📋 Vendor Directory
# ----------------------
def vendor_list(request):
    query = request.GET.get("query", "").strip()
    vendors = Vendor.objects.all()

    if query:
        vendors = vendors.filter(
            Q(name__icontains=query)
            | Q(city__icontains=query)
            | Q(pincode__icontains=query)
            | Q(vendor_code__icontains=query)
        )

    return render(
        request,
        "vendors/home.html",
        {"vendors": vendors.order_by("name"), "query": query},
    )


# ----------------------
# 👨‍🍳 Vendor Detail
# ----------------------
def vendor_detail(request, code: str):
    vendor = get_object_or_404(Vendor, vendor_code=code, is_active=True)
    menu_items = MenuItem.objects.filter(vendor=vendor, is_available=True)
    moods = menu_items.values_list("mood", flat=True).distinct()

    try:
        vendor.view_count = getattr(vendor, "view_count", 0) + 1
        vendor.save(update_fields=["view_count"])
    except Exception as e:
        logger.warning(
            f"Could not update view count for vendor {vendor.vendor_code}: {e}"
        )

    return render(
        request,
        "vendors/vendor_detail.html",
        {"vendor": vendor, "menu_items": menu_items, "moods": moods},
    )


# ----------------------
# 💬 WhatsApp Chat
# ----------------------
def vendor_chat(request, vendor_id: int):
    vendor = get_object_or_404(Vendor, id=vendor_id, is_active=True)
    wa_url = (
        f"https://wa.me/{vendor.whatsapp_number}?"
        f"text=Hello%20{vendor.name},%20I%20found%20you%20on%20Swad%20of%20Tamil!"
    )
    return redirect(wa_url)


# ----------------------
# 📝 Vendor Application
# ----------------------
def vendor_apply(request):
    if request.method == "POST":
        form = VendorApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Thank you! Your application has been submitted.")
            return redirect("vendors:vendor_apply")
        messages.error(request, "⚠️ Please correct the errors below.")
    else:
        form = VendorApplicationForm()
    return render(request, "vendors/apply.html", {"form": form})


# ----------------------
# 🛠 Custom Combo Order
# ----------------------
@csrf_exempt
@login_required
def create_custom_order(request, code):
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "message": "Only POST requests allowed"}, status=405
        )

    try:
        data = json.loads(request.body.decode("utf-8"))

        vendor = get_object_or_404(Vendor, vendor_code=code, is_active=True)
        customer = get_object_or_404(Customer, user=request.user)

        order = Order.objects.create(
            customer=customer,
            vendor=vendor,
            delivery_name=data.get("delivery_name", ""),
            delivery_phone=data.get("delivery_phone", ""),
            delivery_address=data.get("delivery_address", ""),
            pincode=data.get("pincode", ""),
            payment_method=data.get("payment_method", "cod"),
            status="placed",
        )

        items = data.get("items", [])
        subtotal = Decimal("0.00")

        for item_data in items:
            menu_item = get_object_or_404(MenuItem, id=item_data["id"], vendor=vendor)
            qty = int(item_data.get("quantity", 1))
            price = menu_item.price
            line_total = price * qty

            OrderItem.objects.create(
                order=order, menu_item=menu_item, quantity=qty, price=price
            )
            subtotal += line_total

        discount_total = Decimal("0.00")
        for rule in ComboRule.objects.filter(menu_item__vendor=vendor, is_active=True):
            qty = sum(
                oi.quantity
                for oi in order.order_items.all()
                if oi.menu_item == rule.menu_item
            )
            if qty >= rule.min_quantity:
                discount = (subtotal * rule.discount_percentage) / Decimal("100")
                discount_total += discount

        order.subtotal = subtotal
        order.tax_amount = subtotal * Decimal("0.05")
        order.delivery_fee = Decimal("20.00") if subtotal < 200 else Decimal("0.00")
        order.total_price = subtotal + order.tax_amount + order.delivery_fee - discount_total
        order.save()

        OrderTracking.objects.create(order=order, status="placed")

        return JsonResponse({
            "success": True,
            "order_id": order.id,
            "subtotal": float(order.subtotal),
            "tax": float(order.tax_amount),
            "delivery_fee": float(order.delivery_fee),
            "discount": float(discount_total),
            "total": float(order.total_price),
        })

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON body"}, status=400)
    except Exception as e:
        logger.error(f"Order creation failed: {e}", exc_info=True)
        return JsonResponse({"success": False, "message": str(e)}, status=500)


# ----------------------
# ⚡ Quick Order
# ----------------------
@login_required
def quick_order(request, code: str):
    vendor = get_object_or_404(Vendor, vendor_code=code, is_active=True)
    customer, _ = Customer.objects.get_or_create(user=request.user)

    combo = Combo.objects.filter(vendors=vendor, is_available=True).first()
    if not combo:
        messages.error(request, "No combos available for quick order.")
        return redirect("vendors:vendor_detail", code=vendor.vendor_code)

    order = Order.objects.create(
        vendor=vendor,
        customer=customer,
        payment_method="cod",
        special_instructions="Quick order placed",
        total_price=combo.price,
    )
    OrderItem.objects.create(order=order, combo=combo, quantity=1, price=combo.price)

    messages.success(request, f"Quick order placed for {combo.name}")
    return redirect("orders:order_detail", order_id=order.id)


# ----------------------
# 📬 Contact Form
# ----------------------
@require_POST
def contact_submit(request):
    logger.info(
        f"Contact Form: {request.POST.get('name')} ({request.POST.get('email')}): {request.POST.get('message')}"
    )
    messages.success(request, "✅ Your message has been sent!")
    return redirect("vendors:home")


# ----------------------
# 💳 Checkout & Success
# ----------------------
@login_required
def checkout(request, order_id: int):
    order = get_object_or_404(Order, pk=order_id, customer__user=request.user)
    return render(request, "vendors/checkout.html", {"order": order})


@login_required
def order_success(request, order_id: int):
    order = get_object_or_404(Order, pk=order_id, customer__user=request.user)
    return render(request, "vendors/order_success.html", {"order": order})


# ----------------------
# 🧩 Combo Builder & Detail
# ----------------------
def combo_builder(request, vendor_id=None, vendor_code=None):
    if vendor_id is not None:
        vendor = get_object_or_404(Vendor, id=vendor_id, is_active=True)
    elif vendor_code:
        vendor = get_object_or_404(
            Vendor, vendor_code__iexact=vendor_code, is_active=True
        )
    else:
        raise Http404("Vendor not specified")

    items_qs = MenuItem.objects.filter(vendor=vendor, is_available=True)
    combo_rules = ComboRule.objects.filter(
        menu_item__vendor=vendor, is_active=True
    ).select_related("menu_item")

    categories = list(items_qs.values_list("category", flat=True).distinct())
    categories = [c for c in categories if c]
    categories.sort()

    ai_combos = generate_ai_combos(vendor, max_combos=5)  # ✅ integrated AI logic

    return render(
        request,
        "vendors/combo_builder.html",
        {
            "vendor": vendor,
            "items": items_qs,
            "categories": categories,
            "combo_rules": combo_rules,
            "ai_combos": ai_combos,
        },
    )


def combo_detail(request, pk: int):
    combo = get_object_or_404(Combo, pk=pk, is_available=True)
    return render(request, "vendors/combo_detail.html", {"combo": combo})


# ----------------------
# 📦 Vendor Items API
# ----------------------
@require_GET
def vendor_items_api(request, vendor_code):
    vendor = get_object_or_404(Vendor, vendor_code__iexact=vendor_code, is_active=True)
    qs = vendor.menu_items.filter(is_available=True)

    payload = [
        {
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "price": float(item.price),
            "is_available": item.is_available,
        }
        for item in qs
    ]

    return JsonResponse({"items": payload})


# ----------------------
# 🤖 AI Combo Suggestions API
# ----------------------
@require_GET
def ai_combo_suggestions(request, vendor_code):
    vendor = get_object_or_404(Vendor, vendor_code__iexact=vendor_code, is_active=True)

    mood = request.GET.get("mood", "balanced").lower()
    profile = request.GET.get("profile", "normal").lower()   # 👈 new: health profile selector

    # ✅ Nutrition DB (per serving)
    NUTRITION = {
        "idli": {"cal": 58, "protein": 2, "carbs": 12, "fat": 0.4, "fiber": 0.7},   # per 1 idli (~50g)
        "sambar": {"cal": 100, "protein": 5, "carbs": 12, "fat": 3, "fiber": 3},    # per 100 ml
        "coconut chutney": {"cal": 80, "protein": 1, "carbs": 4, "fat": 7, "fiber": 2},
        "peanut chutney": {"cal": 90, "protein": 4, "carbs": 5, "fat": 7, "fiber": 2},
        "onion-tomato chutney": {"cal": 50, "protein": 1, "carbs": 8, "fat": 1, "fiber": 2},
    }

    # ✅ Base combos (fallback / moods)
    hardcoded = {
        "light breakfast": [
            {"name": "Idli", "qty": 2},
            {"name": "Sambar", "qty": 1},
            {"name": "Coconut Chutney", "qty": 1},
        ],
        "family dinner": [
            {"name": "Idli", "qty": 6},
            {"name": "Sambar", "qty": 2},
            {"name": "Coconut Chutney", "qty": 1},
            {"name": "Onion-Tomato Chutney", "qty": 1},
        ],
        "quick snack": [
            {"name": "Idli", "qty": 1},
            {"name": "Sambar", "qty": 1},
        ],
    }

    items = hardcoded.get(mood, [{"name": "Idli", "qty": 4}, {"name": "Sambar", "qty": 1}])

    # ✅ Apply health profile adjustments
    if profile == "diabetic":
        for i in items:
            if i["name"].lower() == "idli":
                i["qty"] = max(1, i["qty"] - 2)   # reduce carbs
        items.append({"name": "Peanut Chutney", "qty": 1})   # add protein/fat for satiety

    elif profile == "weight loss":
        for i in items:
            if i["name"].lower() == "idli":
                i["qty"] = max(1, i["qty"] - 1)   # portion control
        items.append({"name": "Onion-Tomato Chutney", "qty": 1})  # fiber boost

    elif profile == "high protein":
        items.append({"name": "Peanut Chutney", "qty": 2})   # protein boost

    # ✅ Nutrition + Price calculation
    nutrition = {"cal": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}
    subtotal = 0

    for i in items:
        name = i["name"].lower()
        qty = i["qty"]

        nutri = NUTRITION.get(name, {"cal": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0})
        for k in nutrition:
            nutrition[k] += nutri[k] * qty

        # ✅ Price comes from DB
        db_item = vendor.menu_items.filter(name__iexact=i["name"]).first()
        if db_item:
            subtotal += float(db_item.price) * qty
            i["price"] = float(db_item.price)
        else:
            i["price"] = 0

    gst = round(subtotal * 0.05, 2)
    delivery = 20 if subtotal < 200 else 0
    total = subtotal + gst + delivery

    # ✅ Personalized health tip
    if profile == "diabetic":
        tip = "🍀 Diabetic Tip: Controlled carbs, extra protein for stable sugar."
    elif profile == "weight loss":
        tip = "🔥 Weight Loss Tip: Smaller idli portion, more fiber helps satiety."
    elif profile == "high protein":
        tip = "💪 High Protein Tip: Peanut chutney boosts protein for muscle health."
    else:
        tip = "🥗 Balanced Diet: Great mix of carbs, protein, and fiber."

    return JsonResponse({
        "success": True,
        "vendor": vendor.vendor_code,
        "mood": mood,
        "profile": profile,
        "items": items,
        "nutrition": nutrition,
        "subtotal": subtotal,
        "gst": gst,
        "delivery": delivery,
        "total": total,
        "tip": tip,
    })