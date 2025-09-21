# vendors/urls.py
from django.urls import path
from . import views

app_name = "vendors"

urlpatterns = [
    # 🏠 Vendor Homepage
    path("", views.home, name="home"),

    # 🔍 Vendor search & list
    path("search/", views.search_vendor, name="search_vendor"),
    path("list/", views.vendor_list, name="vendor_list"),

    # 👨‍🍳 Vendor detail (string vendor code e.g. SOT001)
    path("vendor/<str:code>/", views.vendor_detail, name="vendor_detail"),

    # 💬 Secure WhatsApp Chat
    path("vendor/<int:vendor_id>/chat/", views.vendor_chat, name="vendor_chat"),

    # 🛠 Custom combo order APIs
    path("vendor/<str:code>/create-custom-order/", views.create_custom_order, name="create_custom_order"),
    path("vendor/id/<int:vendor_id>/create-custom-order/", views.create_custom_order_by_id, name="create_custom_order_by_id"),

    # ⚡ Quick order
    path("vendor/<str:code>/quick-order/", views.quick_order, name="quick_order"),

    # 📬 Contact form submission
    path("contact/submit/", views.contact_submit, name="contact_submit"),

    # 💳 Checkout & order success
    path("checkout/<int:order_id>/", views.checkout, name="checkout"),
    path("order-success/<int:order_id>/", views.order_success, name="order_success"),

    # 🧩 Combo Builder (by vendor_id)
    path("vendor/id/<int:vendor_id>/combo-builder/", views.combo_builder, name="combo_builder"),

    # 🎁 Combo detail
    path("combo/<int:pk>/", views.combo_detail, name="combo_detail"),

    # 📝 Vendor apply / onboarding
    path("apply/", views.vendor_apply, name="apply"),

    # API endpoint for menu items
    path("api/<str:vendor_code>/items/", views.vendor_items_api, name="vendor_items_api"),

    
]
