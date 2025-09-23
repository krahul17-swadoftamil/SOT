# orders/models.py
from django.db import models
from django.utils import timezone
from decimal import Decimal   # 👈 added
from vendors.models import Vendor
from menuitem.models import Combo, MenuItem
from customers.models import Customer


# ======================================================
# Base Timestamp Model
# ======================================================
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ======================================================
# Custom Combo (user-built or AI-suggested combos)
# ======================================================
class CustomCombo(TimeStampedModel):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="custom_combos")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def validate_requirements(self):
        """Check if this combo meets all required rules."""
        rules = ComboRule.objects.filter(is_active=True)
        errors = []

        for rule in rules:
            item = self.items.filter(menu_item=rule.menu_item).first()
            qty = item.quantity if item else 0
            if qty < rule.min_quantity:
                errors.append(
                    f"{rule.menu_item.name} requires at least {rule.min_quantity}, but got {qty}."
                )

        return errors

    def calculate_total(self):
        """Sum price of all items in this combo."""
        total = Decimal("0.00")
        for item in self.items.all():
            if item.menu_item and item.menu_item.price:
                total += item.menu_item.price * item.quantity
        return total

    def __str__(self):
        return self.title or f"CustomCombo #{self.pk}"


class CustomComboItem(models.Model):
    custom_combo = models.ForeignKey(
        CustomCombo,
        on_delete=models.CASCADE,
        related_name="items",
        null=True,
        blank=True,
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="order_customcomboitems",  # ✅ unique
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.menu_item.name if self.menu_item else 'Item'} ×{self.quantity}"


# ======================================================
# Orders
# ======================================================
class Order(TimeStampedModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending", "Pending"),
        ("placed", "Placed"),
        ("confirmed", "Confirmed"),
        ("dispatched", "Dispatched"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_CHOICES = [
        ("cod", "Cash on Delivery"),
        ("online", "Online Payment"),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="orders"
    )
    vendor = models.ForeignKey(
        Vendor, on_delete=models.CASCADE, related_name="orders"
    )

    # Delivery info
    delivery_name = models.CharField(max_length=150, blank=True)
    delivery_phone = models.CharField(max_length=20, blank=True)
    delivery_address = models.TextField(blank=True)
    pincode = models.CharField(max_length=10, blank=True)

    # Billing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    special_instructions = models.TextField(blank=True, null=True)

    # Payment & Status
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default="cod")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} - {self.vendor.name} ({self.status})"

    # ----------------------
    # Convenience alias
    # ----------------------
    @property
    def items(self):
        """Alias for order_items related manager."""
        return self.order_items

    # ----------------------
    # Billing Helpers
    # ----------------------
    def calculate_subtotal(self):
        return sum((item.total_price for item in self.order_items.all()), Decimal("0.00"))

    def calculate_total(self):
        return self.calculate_subtotal() + (self.delivery_fee or Decimal("0.00")) + (self.tax_amount or Decimal("0.00"))

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if not is_new:  # update totals after first save
            self.subtotal = self.calculate_subtotal()
            self.total_price = self.calculate_total()
            super().save(update_fields=["subtotal", "total_price"])

    # ----------------------
    # Status Update + Tracking
    # ----------------------
    def update_status(self, new_status, note=None):
        self.status = new_status
        self.save()
        OrderTracking.objects.create(order=self, status=new_status, note=note)


# ======================================================
# Order Item
# ======================================================
class OrderItem(TimeStampedModel):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_items"
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="order_items_orders"   # 👈 prevents clash
    )
    combo = models.ForeignKey(
        Combo, on_delete=models.SET_NULL, null=True, blank=True
    )
    custom_combo = models.ForeignKey(
        CustomCombo, on_delete=models.SET_NULL, null=True, blank=True
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    @property
    def total_price(self):
        return (self.price or Decimal("0.00")) * self.quantity

    def get_total(self):
        return self.total_price

    def __str__(self):
        if self.menu_item:
            return f"{self.menu_item.name} ×{self.quantity}"
        if self.combo:
            return f"{self.combo.name} ×{self.quantity}"
        if self.custom_combo:
            return f"{self.custom_combo.title} ×{self.quantity}"
        return f"OrderItem #{self.id}"


# ======================================================
# Combo Rules (AI logic hooks)
# ======================================================
class ComboRule(models.Model):
    """
    Defines a rule that applies when a customer orders a minimum quantity of a given menu item.
    Example: "Buy 2 Idlis" → qualifies for a combo.
    """
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="combo_rules"
    )
    min_quantity = models.PositiveIntegerField(
        default=1,
        help_text="Minimum quantity of this menu item required to trigger the combo"
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Percentage discount applied when rule is triggered"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Easily enable or disable this rule"
    )

    class Meta:
        verbose_name = "Combo Rule"
        verbose_name_plural = "Combo Rules"
        ordering = ["menu_item", "min_quantity"]

    def __str__(self):
        return f"{self.menu_item.name} ≥ {self.min_quantity} ({self.discount_percentage}% off)"


# ======================================================
# Tracking Logs
# ======================================================
class OrderTracking(TimeStampedModel):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="tracking_logs"
    )
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    note = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.order} → {self.status}"
