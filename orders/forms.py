from django import forms

PAYMENT_METHODS = [
    ("cod", "Cash on Delivery"),
    ("online", "Online Payment"),
]

class CheckoutForm(forms.Form):
    name = forms.CharField(max_length=100, label="Full Name")
    email = forms.EmailField(label="Email")
    phone = forms.CharField(max_length=15, label="Mobile Number")
    address = forms.CharField(widget=forms.Textarea, label="Delivery Address")
    special_instructions = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label="Special Instructions"
    )
    payment_method = forms.ChoiceField(choices=PAYMENT_METHODS, label="Payment Method")
