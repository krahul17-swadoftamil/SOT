# core/forms.py
from django import forms
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "mobile", "email", "enquiry_type", "message", "subscribe"]
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "Your name",
                "class": "form-control"
            }),
            "mobile": forms.TextInput(attrs={
                "placeholder": "Mobile / WhatsApp",
                "class": "form-control"
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "Email (optional)",
                "class": "form-control"
            }),
            "enquiry_type": forms.Select(attrs={
                "class": "form-select"
            }),
            "message": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Write your message...",
                "class": "form-control"
            }),
            "subscribe": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }

def clean_mobile(self):
    mobile = self.cleaned_data.get("mobile")
    if not mobile.isdigit():
        raise forms.ValidationError("📱 Mobile number should contain digits only.")
    return mobile
