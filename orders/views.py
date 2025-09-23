import json
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, F
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from vendors.models import Vendor
from customers.models import Customer
from menuitem.models import MenuItem
from .models import Order, OrderItem, OrderTracking, CustomCombo, ComboRule
from .forms import CheckoutForm


# ======================================================
# Vendor Search
# ======================================================
def vendor_search(request):
    query_pincode = request.GET.get("pincode")
    query_city = request.GET.get("city")
    query_sot = request.GET.get("sot_code")

    vendors = Vendor.objects.all()

    if query_pincode:
        vendors = vendors.filter(pincode__icontains=query_pincode)
    if query_city:
        vendors = vendors.filter(city__icontains=query_city)
    if query_sot:
        vendors = vendors.filter(sot_code__icontains=query_sot)

    return render(request, "vendors/vendor_list.html", {"vendors": vendors})


# ======================================================
# Helpers
# ======================================================
def _get_or_create_customer(user):
    """Return or create a Customer object linked to the logged-in user."""
    if not user.is_authenticated:
        return None
    customer, _ = Customer.objects.get_or_create(
        user=user,
        defaults={"name": user.get_username()}
    )
    return customer


def _send_sms(mobile, text):
    """Dummy SMS sender (replace with real SMS API)."""
    print(f"📱 Sending SMS to {mobile}: {text}")


def _send_order_confirmation(customer, order):
    """Send email + SMS order confirmation."""
    customer_name = customer.user.first_name or customer.user.username
    subject = f"Order #{order.id} Confirmation"
    message = (
        f"Hello {customer_name},\n\n"
        f"Thank you for your order #{order.id}!\n"
        f"Status: {order.status}\n"
        f"Total: ₹{order.total_price:.2f}\n\n"
        "We’ll notify you once it’s out for delivery.\n\n"
        "— Swad of Tamil"
    )

    # Email
    recipient = [customer.user.email] if customer.user.email else []
    if recipient:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient, fail_silently=False)

    # SMS
    if customer.mobile:
        sms_message = (
            f"Hi {customer_name}, your order #{order.id} is {order.status}. "
            f"Total: ₹{order.total_price:.2f}. Thank you for choosing Swad of Tamil!"
        )
        _send_sms(customer.mobile, sms_message)


# ======================================================
# Order Placement
# ======================================================
@login_required
@csrf_exempt   # remove if CSRF token is already sent via JS
def place_order(request, combo_id):
    """Place an order from a CustomCombo."""
    combo = get_object_or_404(CustomCombo, id=combo_id)
    customer = _get_or_create_customer(request.user)

    if request.method != "POST":
        return render(request, "orders/order_summary.html", {"combo": combo})

    # 1) Validate combo rules
    errors = combo.validate_requirements()
    if errors:
        messages.error(request, "⚠️ Combo not valid: " + ", ".join(errors))
        return redirect("combo_builder")

    # 2) Global ComboRule validation
    for rule in ComboRule.objects.all():
        item = combo.items.filter(menu_item=rule.menu_item).first()
        qty = item.quantity if item else 0
        if qty < rule.min_quantity:
            messages.error(
                request,
                f"'{rule.menu_item.name}' requires at least {rule.min_quantity} item(s)."
            )
            return redirect("combo_builder")

    # 3) Create order & items
    try:
        with transaction.atomic():
            order = Order.objects.create(
                customer=customer,
                vendor=combo.vendor,
                status="pending",
                subtotal=Decimal("0.00"),
                delivery_fee=Decimal("0.00"),
                tax_amount=Decimal("0.00"),
                total_price=Decimal("0.00"),
            )

            subtotal = Decimal("0.00")

            for citem in combo.items.select_related("menu_item").all():
                menu_item = citem.menu_item
                unit_price = getattr(menu_item, "price", Decimal("0.00")) or Decimal("0.00")
                qty = citem.quantity or 1

                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    combo=None,
                    custom_combo=combo,
                    quantity=qty,
                    price=unit_price,
                )

                subtotal += (unit_price * qty)

            # Final totals
            order.subtotal = subtotal
            order.total_price = subtotal + order.delivery_fee + order.tax_amount
            order.save()
    except Exception as exc:
        messages.error(request, "Failed to place order: " + str(exc))
        return redirect("combo_builder")

    messages.success(request, "Order placed successfully ✅")
    return redirect("orders:payment_page", pk=order.pk)

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "orders/order_detail.html", {"order": order})


@login_required
def payment_page(request, pk):
    """Payment selection page."""
    customer = _get_or_create_customer(request.user)
    order = get_object_or_404(Order, pk=pk, customer=customer)

    if request.method == "POST":
        method = request.POST.get("payment_method")

        if method == "cod":
            order.status = "confirmed"
            order.save()
            messages.success(request, "✅ Order confirmed! Pay Cash on Delivery.")
        elif method == "upi":
            messages.info(request, "📲 Redirecting to UPI app...")
        elif method == "card":
            messages.info(request, "💳 Redirecting to card gateway...")

        return redirect("orders:order_summary", order_id=order.pk)

    return render(request, "orders/payment.html", {"order": order})


# ======================================================
# Order Views
# ======================================================
@login_required
def order_list(request):
    customer = _get_or_create_customer(request.user)
    orders = Order.objects.filter(customer=customer).order_by("-created_at")
    return render(request, "orders/order_list.html", {"orders": orders})


@login_required
def order_summary(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    subtotal = sum((item.price * item.quantity) for item in order.order_items.all())
    delivery_fee = 30
    tax_rate = Decimal("0.05")
    tax_amount = round(subtotal * tax_rate, 2)
    grand_total = subtotal + delivery_fee + tax_amount

    context = {
        "order": order,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "tax_amount": tax_amount,
        "grand_total": grand_total,
    }
    return render(request, "orders/order_summary.html", context)


@login_required
def confirm_order(request, order_id):
    customer = _get_or_create_customer(request.user)
    order = get_object_or_404(Order, pk=order_id, customer=customer)

    if request.method == "POST":
        order.status = "confirmed"
        order.save()
        OrderTracking.objects.create(order=order, status="confirmed")
    return redirect("orders:order_summary", order_id=order.id)


@login_required
def order_success(request, order_id):
    customer = _get_or_create_customer(request.user)
    order = get_object_or_404(Order, pk=order_id, customer=customer)
    return render(request, "orders/order_success.html", {"order": order})


# ======================================================
# Tracking
# ======================================================
@login_required
def track_order(request, order_id):
    customer = _get_or_create_customer(request.user)
    order = get_object_or_404(Order, pk=order_id, customer=customer)
    return render(request, "orders/track_order.html", {"order": order})


@login_required
def track_status_api(request, order_id):
    customer = _get_or_create_customer(request.user)
    order = get_object_or_404(Order, pk=order_id, customer=customer)

    logs = order.tracking_logs.order_by("timestamp").values("status", "timestamp")

    eta_seconds = 600 if order.status in ["pending", "confirmed"] else None
    driver = {"name": "Ravi Kumar", "phone": "+91-9876543210"} if order.status == "dispatched" else None

    return JsonResponse({
        "order_id": order.id,
        "status": order.status,
        "eta_seconds": eta_seconds,
        "driver": driver,
        "logs": list(logs),
        "last_updated": getattr(order, "updated_at", None).strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(order, "updated_at") else None,
    })


@login_required
def order_tracking_status(request, order_id):
    customer = _get_or_create_customer(request.user)
    order = get_object_or_404(Order, pk=order_id, customer=customer)
    logs = order.tracking_logs.order_by("-timestamp")

    return render(request, "orders/order_tracking_status.html", {
        "order": order,
        "logs": logs,
    })
