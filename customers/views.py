# customers/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Customer


@login_required
def customer_profile(request):
    """Show logged-in customer's profile."""
    customer = get_object_or_404(Customer, user=request.user)
    return render(request, "customers/profile.html", {"customer": customer})


@login_required
def customer_list(request):
    """Admin/staff can see all customers (basic example)."""
    if not request.user.is_staff:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    
    customers = Customer.objects.all().values("id", "user__username", "mobile", "city", "pincode", "created_at")
    return JsonResponse(list(customers), safe=False)


@login_required
def customer_detail(request, pk):
    """Fetch single customer detail by ID."""
    customer = get_object_or_404(Customer, pk=pk)
    data = {
        "id": customer.id,
        "username": customer.user.username,
        "mobile": customer.mobile,
        "city": customer.city,
        "pincode": customer.pincode,
        "address": customer.address,
        "created_at": customer.created_at,
    }
    return JsonResponse(data)
