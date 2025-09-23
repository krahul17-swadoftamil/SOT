from django.db import models
from menuitem.models import MenuItem
from django.contrib.auth.models import User



# ------------------------
# Customer
# ------------------------
class Customer(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="customer_profile",
    )
    name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name or (self.user.username if self.user else f"Customer #{self.id}")


# ------------------------
# Custom Combo
# ------------------------
class CustomCombo(models.Model):
    customer = models.ForeignKey(
        "customers.Customer",  # ✅ string reference, avoids NameError
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="combos",
    )
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.customer})" if self.customer else self.title


# ------------------------
# Custom Combo Item
# ------------------------
class CustomComboItem(models.Model):
    custom_combo = models.ForeignKey(
        "customers.CustomCombo",
        on_delete=models.CASCADE,
        related_name="items",
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="custom_combo_items_customers",  # ✅ avoids clash with orders
    )
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.menu_item} x {self.quantity}"
