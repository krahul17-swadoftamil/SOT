# core/urls.py
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = "core"

urlpatterns = [
    # 🏠 Homepage
    path("", views.home, name="home"),

    # 🔍 Vendor search & detail
    path("search_vendor/", views.search_vendor, name="search_vendor"),
    path("search/", views.search_vendor, name="search"),
    path("vendor/<str:code>/", views.vendor_detail, name="vendor_detail"),
    path("vendor/<str:code>/create-order/", views.create_order, name="create_order"),

    # 📬 Contact
    path("contact/", views.contact_view, name="contact"),
    path("contact/", views.contact_view, name="contact_view"),  # 👈 add this

    # ℹ️ Info pages
    path("about/", views.about_us, name="about_us"),
    path("brand-story/", views.brand_story, name="brand_story"),
    path("mission/", views.mission, name="mission"),

    # 🛒 Products & Menu
    path("products/", views.products, name="products"),
    path("menu/", views.menu, name="menu"),
    
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
