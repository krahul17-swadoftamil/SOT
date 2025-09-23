from django.db import models
from django.utils import timezone


# 🔹 Individual menu item (raw items)
class MenuItem(models.Model):
    CATEGORY_CHOICES = [
        ("idli", "Idli"),
        ("chutney", "Chutney"),
        ("sambar", "Sambar"),
        ("other", "Other"),
    ]

    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.CASCADE,
        related_name="menu_items"
    )
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # ✅ Availability toggle
    is_available = models.BooleanField(default=True)

    # ✅ Nutrition fields
    calories = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    protein = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    carbs = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    fat = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    fiber = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.vendor.vendor_code})"

    class Meta:
        ordering = ["category", "name"]
        verbose_name = "Menu Item"
        verbose_name_plural = "Menu Items"


# 🔹 Rule for forming a predefined combo
class ComboRule(models.Model):
    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.CASCADE,
        related_name="combo_rules"
    )
    name = models.CharField(max_length=100, help_text="Eg: 4 idli + chutney + sambar")
    required_idli = models.PositiveIntegerField(default=4)
    required_chutney = models.PositiveIntegerField(default=1)
    required_sambar = models.PositiveIntegerField(default=1)
    combo_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - ₹{self.combo_price}"


# 🔹 Base combo (mandatory plate)
class Combo(models.Model):
    vendors = models.ManyToManyField(
    "vendors.Vendor",
    related_name="menuitem_combos",
    blank=True
)
    code = models.CharField(max_length=20, unique=True, blank=True, null=True)  # 🔹 Unique code (e.g., COM001)
    name = models.CharField(max_length=100, default="Idli Plate")
    description = models.TextField(blank=True, null=True)
    
    # 🔹 Base items
    base_idli = models.PositiveIntegerField(default=4)       # fixed 4 idli
    base_chutney = models.PositiveIntegerField(default=2)    # coconut + peanut
    base_sambar = models.PositiveIntegerField(default=1)     # hot sambar

    # 🔹 Pricing & status
    price = models.DecimalField(max_digits=10, decimal_places=2, default=80)
    is_available = models.BooleanField(default=True)

    # 🔹 Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code or 'NoCode'}) - ₹{self.price}"


# 🔹 Add-ons (extra chutney, idli, sambar, etc.)
class AddOn(models.Model):
    vendor = models.ForeignKey("vendors.Vendor", on_delete=models.CASCADE, related_name="addons")
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (+₹{self.price})"
