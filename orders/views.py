# orders/views.py
from decimal import Decimal
import json

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.contrib import messages

from vendors.models import Combo, Vendor
from .models import Order, OrderItem, CustomCombo
from .forms import CheckoutForm   # ✅ FIX: make sure this exists in orders/forms.py
from customers.models import Customer
from menuitem.models import MenuItem
from django.views.decorators.http import require_http_methods


# ======================================================
# Helpers
# ======================================================

def _get_or_create_customer(user):
    """Return or create a Customer profile for a Django User."""
    for attr in ("customer_profile", "customer"):
        cust = getattr(user, attr, None)
        if cust is not None:
            return cust
    customer, _ = Customer.objects.get_or_create(user=user, defaults={"name": user.username})
    return customer


# ======================================================
# Vendor → Order Flow
# ======================================================

@login_required
def create_order(request, vendor_code: str):
    vendor = get_object_or_404(Vendor, vendor_code=vendor_code)
    combos = Combo.objects.filter(vendors=vendor, is_available=True)

    last_orders_qs = (
        OrderItem.objects.filter(combo__vendors=vendor)
        .select_related("order", "combo")[:10]
    )
    last_orders = [
        {
            "customer": o.order.customer.user.username if o.order.customer and o.order.customer.user else "Anonymous",
            "combo": o.combo,
            "quantity": o.quantity,
            "price": getattr(o.combo, "price", 0),
            "total": getattr(o, "total_price", 0),
        }
        for o in last_orders_qs
    ]

    if request.method == "POST":
        customer = _get_or_create_customer(request.user)

        order = Order.objects.create(
            customer=customer,
            vendor=vendor,
            payment_method="cod",
            status="pending",
        )

        added = False
        for combo in combos:
            qty = request.POST.get(f"quantity_{combo.id}")
            if qty and int(qty) > 0:
                OrderItem.objects.create(order=order, combo=combo, quantity=int(qty))
                added = True

        if added:
            order.total_amount = sum(item.total_price for item in order.order_items.all())
            order.save()
            messages.success(request, "✅ Order placed successfully!")
            return redirect("orders:order_detail", order_id=order.id)
        else:
            order.delete()
            messages.warning(request, "⚠️ Please select at least 1 combo.")

    return render(request, "orders/order.html", {"vendor": vendor, "combos": combos, "last_orders": last_orders})


@login_required
@require_POST
def create_custom_order(request, vendor_code: str):
    """AJAX: create an order with custom combo or selected items."""
    try:
        vendor = get_object_or_404(Vendor, vendor_code=vendor_code)
        customer = _get_or_create_customer(request.user)
        data = json.loads(request.body)

        items_data = data.get("items", [])
        custom_combo_id = data.get("custom_combo_id")
        payment_method = data.get("payment_method", "cod")
        special_instructions = data.get("special_instructions", "")

        order = Order.objects.create(
            vendor=vendor,
            customer=customer,
            payment_method=payment_method,
            special_instructions=special_instructions,
        )

        total = Decimal("0.00")
        for item in items_data:
            menu_item = get_object_or_404(MenuItem, id=item["id"], vendor=vendor)
            qty = int(item.get("quantity", 1))
            OrderItem.objects.create(order=order, menu_item=menu_item, quantity=qty)
            total += menu_item.price * qty

        if custom_combo_id:
            custom_combo = get_object_or_404(CustomCombo, id=custom_combo_id)
            order.custom_combo = custom_combo
            total += custom_combo.price
            order.save()

        order.total_amount = total
        order.save()

        return JsonResponse({"success": True, "order_id": order.id, "total_price": float(total)})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


# ======================================================
# Order Pages
# ======================================================

@login_required
def order_summary(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    subtotal = order.order_items.aggregate(subtotal=Sum(F("total_price"))).get("subtotal") or Decimal("0.00")
    delivery_fee = Decimal(str(getattr(order.vendor, "delivery_fee", 0))) if getattr(order, "vendor", None) else Decimal("0.00")
    tax_amount = Decimal(str(getattr(order, "tax_amount", 0) or 0))
    grand_total = subtotal + delivery_fee + tax_amount

    return render(request, "orders/order_summary.html", {
        "order": order,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "tax_amount": tax_amount,
        "grand_total": grand_total,
    })


@login_required
def confirm_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user.customer_profile)
    if request.method == "POST":
        order.status = "confirmed"
        order.save()
        return redirect("orders:order_confirmation", order_id=order.id)
    return render(request, "orders/confirm.html", {"order": order})


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer=request.user.customer_profile)
    return render(request, "orders/confirmation.html", {"order": order})


@login_required
def orders_list(request):
    if request.user.is_staff:
        orders = Order.objects.all().order_by("-id")
    else:
        customer = get_object_or_404(Customer, user=request.user)
        orders = Order.objects.filter(customer=customer).order_by("-id")
    return render(request, "orders/list.html", {"orders": orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer__user=request.user)
    return render(request, "orders/order.html", {"order": order})


# ======================================================
# Cart System
# ======================================================

@login_required
def add_to_cart(request, combo_id):
    combo = get_object_or_404(Combo, id=combo_id)
    cart = request.session.get("cart", {})
    cart.setdefault(str(combo_id), {"title": combo.name, "price": float(combo.price), "quantity": 0})
    cart[str(combo_id)]["quantity"] += 1
    request.session["cart"] = cart
    messages.success(request, f"{combo.name} added to cart ✅")
    return redirect("orders:view_cart")


@login_required
def view_cart(request):
    cart = request.session.get("cart", {})
    total = sum(item["price"] * item["quantity"] for item in cart.values())
    return render(request, "orders/cart.html", {"cart": cart, "total": total})


@login_required
def update_cart(request, combo_id):
    if request.method == "POST":
        action = request.POST.get("action")
        cart = request.session.get("cart", {})
        if str(combo_id) in cart:
            if action == "increase":
                cart[str(combo_id)]["quantity"] += 1
            elif action == "decrease":
                cart[str(combo_id)]["quantity"] -= 1
                if cart[str(combo_id)]["quantity"] <= 0:
                    del cart[str(combo_id)]
        request.session["cart"] = cart
        request.session.modified = True
    return redirect("orders:view_cart")


@login_required
def remove_from_cart(request, combo_id):
    cart = request.session.get("cart", {})
    if str(combo_id) in cart:
        del cart[str(combo_id)]
        request.session["cart"] = cart
        request.session.modified = True
    return redirect("orders:view_cart")


@login_required
def checkout(request):
    """Handle checkout: convert cart session data into a confirmed Order and send emails."""
    cart = request.session.get("cart", {})

    # ✅ Check if cart is empty
    if not cart:
        messages.warning(request, "Your cart is empty ❌")
        return redirect("orders:view_cart")

    # ✅ Ensure customer profile exists
    customer, _ = Customer.objects.get_or_create(user=request.user)

    # 🛒 Create a new order
    order = Order.objects.create(customer=customer, vendor=None)

    order_items_summary = []
    total = 0

    # ➕ Add each cart item to the order
    for combo_id, item in cart.items():
        combo = get_object_or_404(Combo, id=combo_id)
        quantity = item.get("quantity", 1)
        order_item = OrderItem.objects.create(
            order=order,
            combo=combo,
            quantity=quantity,
        )
        line_total = order_item.total_price
        total += line_total
        order_items_summary.append(f"{combo.name} × {quantity} = ₹{line_total}")

    # ✅ Recalculate order total
    order.total_price = total
    order.save()

    # 🧹 Clear session cart after checkout
    request.session["cart"] = {}
    request.session.modified = True

    # -----------------------
    # 📧 EMAIL: Admin
    # -----------------------
    admin_subject = f"🆕 New Order #{order.id} from {customer.user.username}"
    admin_message = (
        f"Customer: {customer.user.username}\n"
        f"Email: {customer.user.email}\n"
        f"Order ID: {order.id}\n\n"
        "Items:\n" + "\n".join(order_items_summary) +
        f"\n\nTotal: ₹{order.total_price}\n"
        f"Payment: {order.payment_method}\n"
    )
    send_mail(
        admin_subject,
        admin_message,
        settings.DEFAULT_FROM_EMAIL,
        ["foodsorder@gmail.com"],  # Admin email
    )

    # -----------------------
    # 📧 EMAIL: Customer
    # -----------------------
    customer_subject = f"✅ Your Order #{order.id} is Confirmed"
    customer_message = (
        f"Hello {customer.user.username},\n\n"
        f"Thank you for ordering with Street Kitchen!\n\n"
        "Here are your order details:\n"
        + "\n".join(order_items_summary) +
        f"\n\nTotal: ₹{order.total_price}\n"
        f"Payment: {order.payment_method}\n"
        f"Order ID: {order.id}\n\n"
        "We will notify you when your food is on the way 🚀🍴\n\n"
        "— Team Street Kitchen"
    )
    if customer.user.email:
        send_mail(
            customer_subject,
            customer_message,
            settings.DEFAULT_FROM_EMAIL,
            [customer.user.email],  # Customer email
        )

    # ✅ Notify in UI
    messages.success(request, f"Order #{order.id} placed successfully ✅")
    return redirect("orders:order_summary", order_id=order.id)


# ======================================================
# Tracking
# ======================================================

@login_required
def track_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "orders/track_order.html", {"order": order})


@login_required
def track_status_api(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer__user=request.user)
    eta_seconds = 600 if order.status in ["placed", "preparing", "on_the_way"] else None
    driver = {"name": "Ravi Kumar", "phone": "+91-9876543210"} if order.status == "on_the_way" else None
    activity = [f"Order placed at {order.created_at.strftime('%H:%M %p')}"]
    if getattr(order, "updated_at", None):
        activity.append(f"Status changed to {order.get_status_display()} at {order.updated_at.strftime('%H:%M %p')}")
    return JsonResponse({
        "status": order.status,
        "status_display": order.get_status_display(),
        "eta_seconds": eta_seconds,
        "driver": driver,
        "last_updated": order.updated_at.strftime("%Y-%m-%d %H:%M:%S") if getattr(order, "updated_at", None) else None,
        "activity": activity,
    })


# ======================================================
# Cart View (DB-backed cart for premium mode)
# ======================================================

@login_required
def cart_view(request):
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to view your cart.")
        return redirect("customers:login")
    customer = request.user.customer_profile
    cart = Order.objects.filter(customer=customer, status="cart").first()
    context = {
        "cart": cart,
        "total": cart.get_subtotal() if cart else 0,
        "order": cart,
        "customer": customer,
        "packs": Combo.objects.filter(vendor=customer.vendor) if customer.vendor else [],
        "empty_cart_url": "/orders/empty/",
    }
    return render(request, "orders/cart.html", context)


@login_required
def empty_cart(request):
    if not request.user.is_authenticated:
        messages.error(request, "You need to log in to empty your cart.")
        return redirect("customers:login")
    cart = Order.objects.filter(customer=request.user.customer_profile, status="cart").first()
    if cart:
        cart.order_items.all().delete()
        messages.success(request, "🗑 Your cart has been emptied.")
    else:
        messages.warning(request, "No active cart found.")
    return redirect("orders:cart")

@login_required
def combo_builder(request, code: str):
    """Premium combo builder page for a given vendor."""
    vendor = get_object_or_404(Vendor, vendor_code=code)
    menu_items = MenuItem.objects.filter(vendor=vendor, available=True)

    return render(request, "orders/combo_builder.html", {
        "vendor": vendor,
        "menu_items": menu_items,
    })

def order_final(request, order_id):
    order = get_object_or_404(Order, id=order_id, customer__user=request.user)

    # Customer details
    customer_name = order.customer.user.username
    customer_email = order.customer.user.email

    # Send Email Confirmation
    try:
        send_mail(
            subject=f"Swad of Tamil - Order #{order.id} Confirmation",
            message=(
                f"Dear {customer_name},\n\n"
                f"Your order #{order.id} has been placed successfully.\n"
                f"Total: ₹{order.total_price}\n\n"
                f"Thank you for choosing Swad of Tamil! 🍴"
            ),
            from_email="no-reply@swadoftamil.com",
            recipient_list=[customer_email],
            fail_silently=True,
        )
        messages.success(request, "✅ Order placed successfully! A confirmation email has been sent.")
    except Exception as e:
        messages.error(request, f"⚠️ Order placed but email could not be sent. ({e})")

    return render(request, "orders/order_final.html", {"order": order})

def create_custom_order(request, vendor_code):
    """
    Expects JSON: items list + customer info
    Returns JSON: { success: true, order_id: id, redirect_url: "/orders/confirmation/<id>/" }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    # validate vendor
    vendor = get_object_or_404(Vendor, vendor_code=vendor_code)

    # basic required fields
    customer_name = (data.get("customer_name") or "").strip()
    customer_phone = (data.get("customer_phone") or "").strip()
    items = data.get("items") or []
    if not customer_name or not customer_phone:
        return JsonResponse({"success": False, "error": "Name and phone are required"}, status=400)
    if not items:
        return JsonResponse({"success": False, "error": "Cart is empty"}, status=400)

    # optional fields
    customer_email = data.get("customer_email")
    delivery_address = data.get("delivery_address")
    pincode = data.get("pincode")
    preferences = data.get("preferences")
    gst_percent = Decimal(data.get("gst_percent", 5.0))

    # create order + items in transaction
    with transaction.atomic():
        order = Order.objects.create(
            vendor=vendor,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            delivery_address=delivery_address,
            pincode=pincode,
            preferences=preferences,
            gst_percent=gst_percent,
            payment_method=data.get("payment_method", "Cash on Delivery"),
        )

        subtotal = Decimal("0.00")
        for entry in items:
            try:
                menu_id = int(entry.get("id"))
                qty = int(entry.get("quantity", 0))
            except Exception:
                transaction.set_rollback(True)
                return JsonResponse({"success": False, "error": "Invalid item format"}, status=400)
            if qty <= 0:
                continue

            menu_item = get_object_or_404(MenuItem, id=menu_id, vendor=vendor)
            unit_price = Decimal(menu_item.price)
            line_total = (unit_price * qty).quantize(Decimal("0.01"))
            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                name=menu_item.name,
                unit_price=unit_price,
                quantity=qty,
                line_total=line_total,
            )
            subtotal += line_total

        # compute gst & totals
        gst_amount = (subtotal * (gst_percent / Decimal("100.0"))).quantize(Decimal("0.01"))
        total = (subtotal + gst_amount).quantize(Decimal("0.01"))

        order.subtotal = subtotal
        order.gst_amount = gst_amount
        order.total_price = total
        order.save(update_fields=["subtotal", "gst_amount", "total_price"])

    # send emails (safe fallback - settings must be configured)
    try:
        send_order_emails(order.id)
    except Exception as exc:
        # log but do not fail the order
        # import logging; logger = logging.getLogger(__name__); logger.exception(exc)
        pass

    # success
    return JsonResponse({
        "success": True,
        "order_id": order.id,
        "redirect_url": "/orders/confirmation/{}/".format(order.id)
    }, status=201)


def send_order_emails(order_id):
    """
    Helper to send email to customer and vendor. Adjust content / templates as needed.
    """
    from django.template.loader import render_to_string
    order = Order.objects.select_related("vendor").prefetch_related("items").get(pk=order_id)
    subject_customer = f"Order #{order.id} — Swad of Tamil"
    subject_vendor = f"New Order #{order.id} received"

    # customer email content (HTML/text)
    customer_body = render_to_string("orders/email_customer.txt", {"order": order})
    vendor_body = render_to_string("orders/email_vendor.txt", {"order": order})

    # send to customer if email provided
    if order.customer_email:
        send_mail(subject_customer, customer_body, settings.DEFAULT_FROM_EMAIL, [order.customer_email], fail_silently=True)

    # send to vendor (if vendor email set)
    if getattr(order.vendor, "email", None):
        send_mail(subject_vendor, vendor_body, settings.DEFAULT_FROM_EMAIL, [order.vendor.email], fail_silently=True)


@require_http_methods(["GET"])
def order_confirmation(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("items__menu_item"), pk=order_id)
    return render(request, "orders/order_confirmation.html", {"order": order})

def order_list(request):
    """Show all orders for the logged-in customer"""
    orders = Order.objects.filter(customer__user=request.user).order_by("-created_at")
    return render(request, "orders/order_list.html", {"orders": orders})
