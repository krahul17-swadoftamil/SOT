# vendors/models.py
from django.db import models, transaction, IntegrityError
from django.utils.text import slugify
from django.urls import reverse


# ======================================================
# Vendor model
# ======================================================
class Vendor(models.Model):
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    experience = models.PositiveIntegerField(default=0)
    signature_dish = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="vendors/images/", blank=True, null=True)
    view_count = models.PositiveIntegerField(default=0)
    menu_card = models.FileField(upload_to="vendors/menus/", blank=True, null=True)
    owner_name = models.CharField(max_length=255, blank=True, null=True)

    # Status flags
    available = models.BooleanField(default=True, help_text="Vendor is currently online/live")
    is_active = models.BooleanField(default=True, help_text="If false, vendor is disabled from system")

    # Item count is updated from menu
    items_count = models.PositiveIntegerField(default=0)

    # 🚀 Auto vendor code (SOT001, SOT002 …)
    vendor_code = models.CharField(max_length=20, unique=True, blank=True, null=True)

    # SEO-friendly slug
    slug = models.SlugField(unique=True, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ==============================
    # Display
    # ==============================
    def __str__(self):
        return f"{self.name} ({self.vendor_code or 'no-code'})"

    @property
    def code(self):
        """Alias: some templates use `vendor.code` instead of `vendor.vendor_code`"""
        return self.vendor_code or ""

    # ==============================
    # Core Business Logic
    # ==============================
    def _generate_new_code(self):
        """Generate the next sequential vendor code (SOT###)."""
        last_vendor = (
            Vendor.objects.exclude(vendor_code__isnull=True)
            .exclude(vendor_code="")
            .order_by("-id")
            .first()
        )
        if last_vendor and last_vendor.vendor_code:
            try:
                last_number = int(last_vendor.vendor_code.replace("SOT", ""))
            except ValueError:
                last_number = 0
            new_number = last_number + 1
        else:
            new_number = 1
        return f"SOT{new_number:03d}"

    def update_items_count(self):
        """Recalculate items count based on MenuItems linked to this vendor."""
        from menuitem.models import MenuItem
        self.items_count = MenuItem.objects.filter(vendor=self).count()
        self.save(update_fields=["items_count"])

    def can_fulfill_combo(self, combo):
        """
        Check if vendor can fulfill a given combo.
        A vendor can fulfill if they have all required menu items in sufficient qty.
        """
        required_items = combo.combo_items.all()
        vendor_items = {item.name.lower(): item for item in self.menu_items.all()}

        for req in required_items:
            menu_name = req.menu_item.name.lower()
            if menu_name not in vendor_items:
                return False
        return True

    # ==============================
    # Save override
    # ==============================
    def save(self, *args, **kwargs):
        # Auto vendor_code if missing
        if not self.vendor_code:
            for attempt in range(5):  # retry in case of race conditions
                self.vendor_code = self._generate_new_code()
                try:
                    with transaction.atomic():
                        super().save(*args, **kwargs)
                        break
                except IntegrityError:
                    if attempt == 4:
                        raise
                    continue
        else:
            super().save(*args, **kwargs)

        # Auto slug from name
        if not self.slug and self.name:
            base_slug = slugify(self.name)
            slug_candidate = base_slug
            counter = 1
            while Vendor.objects.filter(slug=slug_candidate).exclude(pk=self.pk).exists():
                slug_candidate = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug_candidate
            super().save(update_fields=["slug"])

    # ==============================
    # URL
    # ==============================
    def get_absolute_url(self):
        return reverse("vendors:vendor_detail", args=[self.vendor_code])


# ======================================================
# Explicit through model for Combo-Vendor link
# ======================================================
class ComboVendor(models.Model):
    combo = models.ForeignKey("menuitem.Combo", on_delete=models.CASCADE)
    vendor = models.ForeignKey("vendors.Vendor", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("combo", "vendor")
        verbose_name = "Combo Vendor"
        verbose_name_plural = "Combo Vendors"

    def __str__(self):
        return f"{self.combo.name} @ {self.vendor.name}"


# ======================================================
# ComboItem (through model for Combo & MenuItem)
# ======================================================
class ComboItem(models.Model):
    combo = models.ForeignKey("menuitem.Combo", on_delete=models.CASCADE, related_name="combo_items")
    menu_item = models.ForeignKey("menuitem.MenuItem", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("combo", "menu_item")
        verbose_name = "Combo Item"
        verbose_name_plural = "Combo Items"

    def __str__(self):
        return f"{self.menu_item.name} × {self.quantity} (Combo: {self.combo.name})"


# ======================================================
# Vendor Application (Apply form submissions)
# ======================================================
class VendorApplication(models.Model):
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField()
    city = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    speciality = models.CharField(max_length=200, blank=True, null=True)
    story = models.TextField(blank=True, null=True)  # Why join Swad of Tamil
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Application: {self.name} ({self.mobile})"
