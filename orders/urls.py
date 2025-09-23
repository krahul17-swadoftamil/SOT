from django.urls import path
from . import views
from vendors import views as vendor_views

app_name = "orders"

urlpatterns = [
    # 🔍 Vendor search
    path("search/", vendor_views.search_vendor, name="vendor_search"),

    # 📝 Place a new order (from combo)
    path("place/<int:combo_id>/", views.place_order, name="place_order"),

    # 💳 Payment & confirmation
    path("payment/<int:pk>/", views.payment_page, name="payment_page"),
    path("confirm/<int:order_id>/", views.confirm_order, name="confirm_order"),
    path("success/<int:order_id>/", views.order_success, name="order_success"),

    # 📦 Orders
    path("", views.order_list, name="order_list"),  # list all orders
    path("<int:order_id>/summary/", views.order_summary, name="order_summary"),
    path("<int:order_id>/", views.order_detail, name="order_detail"),

    # 🚚 Tracking
    path("<int:order_id>/track/", views.track_order, name="track_order"),
    path("<int:order_id>/track/status/", views.track_status_api, name="track_status_api"),
    path("<int:order_id>/tracking/history/", views.order_tracking_status, name="order_tracking_status"),
]
