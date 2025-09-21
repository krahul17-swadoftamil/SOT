from django.db import models
from decimal import Decimal
from menuitem.models import MenuItem
from vendors.models import Vendor, Combo
from customers.models import Customer


# ----------------------
# Custom Combo (Customer saved packs)
# ----------------------
class CustomCombo(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="custom_combos")
    title = models.CharField(max_length=100, default="My Custom Combo")
    items = models.ManyToManyField(MenuItem, through="CustomComboItem", related_name="custom_combos")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    mood = models.CharField(
        max_length=20,
        choices=[
            ("light", "Light"),
            ("heavy", "Heavy"),
            ("snack", "Snack"),
            ("family", "Family"),
        ],
        default="light",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Custom Combo"
        verbose_name_plural = "Custom Combos"

    def calculate_price(self):
        """Recalculate and update total combo price from its items."""
        total = sum(
            (cci.menu_item.price or Decimal("0.00")) * cci.quantity
            for cci in self.customcomboitem_set.select_related("menu_item")
        )
        self.price = total
        self.save(update_fields=["price"])
        return total

    def __str__(self):
        return f"{self.title} - {self.customer.user.username}"


class CustomComboItem(models.Model):
    combo = models.ForeignKey(CustomCombo, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("combo", "menu_item")

    def __str__(self):
        return f"{self.combo.title} - {self.menu_item.name} × {self.quantity}"


# ----------------------
# Order Model
# ----------------------
ORDER_STATUS = [
    ("pending", "Pending"),
    ("confirmed", "Confirmed"),
    ("delivered", "Delivered"),
    ("cancelled", "Cancelled"),
]

PAYMENT_METHODS = [
    ("cod", "Cash on Delivery"),
    ("online", "Online Payment"),
]


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    vendor = models.ForeignKey(
    "vendors.Vendor",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="orders"
)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default="pending")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default="cod")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    address = models.TextField(blank=True, null=True)
    special_instructions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"Order #{self.id} - {self.customer.user.username}"

    def calculate_total(self):
        """Recalculate order total from related items."""
        total = sum(item.total_price for item in self.order_items.all())
        self.total_price = total
        self.save(update_fields=["total_price"])
        return total


# ----------------------
# Order Item Model
# ----------------------
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    combo = models.ForeignKey(Combo, on_delete=models.SET_NULL, null=True, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    custom_combo = models.ForeignKey(CustomCombo, on_delete=models.SET_NULL, null=True, blank=True)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    addons = models.JSONField(
        blank=True, null=True,
        help_text='Example: {"chutney": 20, "sambar": 30}'
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def save(self, *args, **kwargs):
        """Auto-calc total price before saving."""
        price = Decimal("0.00")
        if self.combo:
            price += self.combo.price
        if self.custom_combo:
            price += self.custom_combo.price
        if self.menu_item and self.menu_item.price:
            price += self.menu_item.price
        if self.addons:
            price += sum(Decimal(str(v)) for v in self.addons.values())

        self.total_price = price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        if self.combo:
            return f"{self.combo.name} × {self.quantity}"
        if self.custom_combo:
            return f"{self.custom_combo.title} × {self.quantity}"
        if self.menu_item:
            return f"{self.menu_item.name} × {self.quantity}"
        return f"OrderItem #{self.id}"
