# vendors/forms.py
from django import forms
from .models import VendorApplication


class VendorApplicationForm(forms.ModelForm):
    class Meta:
        model = VendorApplication
        fields = [
            "name",
            "mobile",
            "email",
            "city",
            "speciality",   # ✅ must match model exactly
            "message",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Enter your full name"}),
            "mobile": forms.TextInput(attrs={"placeholder": "Mobile / WhatsApp"}),
            "city": forms.TextInput(attrs={"placeholder": "City"}),
            "specialty": forms.TextInput(attrs={"placeholder": "Eg: Idli, Dosa"}),
            "message": forms.Textarea(attrs={"rows":4, "placeholder": "Tell us your story"}),
        }