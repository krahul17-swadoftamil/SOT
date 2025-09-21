# vendors/models.py
from django.db import models, transaction, IntegrityError


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
    available = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    items_count = models.PositiveIntegerField(default=0)

    # 🚀 Auto vendor code (SOT001, SOT002 …)
    vendor_code = models.CharField(
    max_length=20,
    unique=True,
    editable=False,
    blank=True,
    null=True   # ✅ allow null during migration
)

    def __str__(self):
        return f"{self.name} ({self.vendor_code or 'no-code'})"

    @property
    def code(self):
        """
        Compatibility alias: some templates/views still use `vendor.code`.
        Always returns vendor_code (or empty string if missing).
        """
        return self.vendor_code or ""

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

    def save(self, *args, **kwargs):
        if not self.vendor_code:
            # Retry a few times in case of IntegrityError on unique constraint
            for attempt in range(5):
                self.vendor_code = self._generate_new_code()
                try:
                    with transaction.atomic():
                        super().save(*args, **kwargs)
                    break
                except IntegrityError:
                    if attempt == 4:  # last attempt failed
                        raise
                    continue
        else:
            super().save(*args, **kwargs)


# ======================================================
# Combo model
# ======================================================
class Combo(models.Model):
    vendors = models.ManyToManyField(
        Vendor,
        through="ComboVendor",   # through model for vendor-combo mapping
        related_name="combos",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="combos/", blank=True, null=True)
    details = models.TextField(blank=True, null=True)  # Extra JSON/info
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Relation to menu items (through ComboItem)
    menu_items = models.ManyToManyField(
        "menuitem.MenuItem",
        through="ComboItem",
        related_name="combos",
    )

    def __str__(self):
        return self.name

    def total_items(self):
        """Return total quantity of menu items in this combo."""
        return self.comboitem_set.aggregate(total=models.Sum("quantity"))["total"] or 0


# ======================================================
# Explicit through model for Combo-Vendor link
# ======================================================
class ComboVendor(models.Model):
    combo = models.ForeignKey(Combo, on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
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
    combo = models.ForeignKey(Combo, on_delete=models.CASCADE)
    menu_item = models.ForeignKey(
        "menuitem.MenuItem",
        on_delete=models.CASCADE,
        related_name="vendor_combo_items",
    )
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
    mobile = models.CharField(max_length=15, null=True, blank=True)  # ✅ allows empty
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
    
def get_absolute_url(self):
    from django.urls import reverse
    return reverse("vendors:vendor_detail", args=[self.vendor_code])    
