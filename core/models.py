# core/models.py
from django.db import models
from django.db.models import F
from vendors.models import Vendor, Combo


# ----------------------
# Pincode for Quick Search
# ----------------------
class Pincode(models.Model):
    code = models.CharField(max_length=10, unique=True)
    city = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} ({self.city})" if self.city else self.code


# ----------------------
# QuickMenu = Fast Access Menu
# ----------------------
class QuickMenu(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="quick_menus")
    combo = models.ForeignKey(Combo, on_delete=models.CASCADE, related_name="quick_menus")
    display_name = models.CharField(max_length=100)
    highlight_color = models.CharField(max_length=20, default="#ff9900")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["vendor", "combo"], name="unique_quickmenu_vendor_combo")
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"QuickMenu: {self.display_name} ({self.vendor.name})"


# ----------------------
# Vendor Analytics / Tracking
# ----------------------
class VendorAnalytics(models.Model):
    vendor = models.OneToOneField(Vendor, on_delete=models.CASCADE, related_name="analytics")
    total_views = models.PositiveIntegerField(default=0)
    total_clicks = models.PositiveIntegerField(default=0)
    total_orders = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def increment_views(self):
        VendorAnalytics.objects.filter(pk=self.pk).update(total_views=F("total_views") + 1)

    def increment_clicks(self):
        VendorAnalytics.objects.filter(pk=self.pk).update(total_clicks=F("total_clicks") + 1)

    def increment_orders(self):
        VendorAnalytics.objects.filter(pk=self.pk).update(total_orders=F("total_orders") + 1)

    def __str__(self):
        return f"Analytics ({self.vendor.name})"


# ----------------------
# Featured / Quick Access Combos
# ----------------------
class FeaturedCombo(models.Model):
    combo = models.ForeignKey(Combo, on_delete=models.CASCADE, related_name="featured_combos")
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="featured_combos")
    title = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    highlight_color = models.CharField(max_length=20, default="#ffaa33")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["vendor", "combo"], name="unique_featuredcombo_vendor_combo")
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Featured: {self.combo.name} ({self.vendor.name})"
    
class ContactMessage(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General question'),
        ('vendor', 'Vendor request'),
        ('order', 'Order related'),
        ('collab', 'Collaboration'),
    ]

    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    enquiry_type = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    message = models.TextField()
    subscribe = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.enquiry_type})"