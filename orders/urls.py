from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    # ------------------------
    # Order creation
    # ------------------------
    path("create/<str:vendor_code>/", views.create_order, name="create_order"),
    path("vendor/<str:code>/create-order/", views.create_custom_order, name="create_custom_order"),

    # ------------------------
    # Order flow
    # ------------------------
    path("summary/<int:order_id>/", views.order_summary, name="order_summary"),
    path("confirm/<int:order_id>/", views.confirm_order, name="confirm_order"),
    path("list/", views.orders_list, name="orders_list"),
    path("detail/<int:order_id>/", views.order_detail, name="order_detail"),
    path("confirm/<int:order_id>/", views.confirm_order, name="confirm_order"),
    path("confirmation/<int:order_id>/", views.order_confirmation, name="order_confirmation"),

    # ------------------------
    # Combo Builder
    # ------------------------
    path("combo-builder/<str:code>/", views.combo_builder, name="combo_builder"),

    # ------------------------
    # Cart
    # ------------------------
    path("cart/", views.view_cart, name="view_cart"),
    path("cart/add/<int:combo_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:combo_id>/", views.update_cart, name="update_cart"),
    path("cart/remove/<int:combo_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("confirm-order/<int:order_id>/", views.order_confirmation, name="order_confirmation"),
    path("track/<int:order_id>/", views.track_order, name="track_order"),
    path("track/status/<int:order_id>/", views.track_status_api, name="track_status_api"),
    path("detail/<int:order_id>/", views.order_detail, name="order_detail"),
    path('empty/', views.empty_cart, name='empty_cart'),
    path("", views.orders_list, name="orders_home"),      # -> /orders/
    path("list/", views.orders_list, name="orders_list"),
    path("create/<str:vendor_code>/", views.create_custom_order, name="create_order"),
    path("confirmation/<int:order_id>/", views.order_confirmation, name="order_confirmation"),
    path("", views.order_list, name="order_list"),   # ✅ My Orders page
    path("<int:pk>/", views.order_detail, name="order_detail"),  # Single order
    path("place/", views.track_order, name="place_order"),   
]
