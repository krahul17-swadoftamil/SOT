# customers/urls.py
from django.urls import path
from . import views

app_name = "customers"

urlpatterns = [
    path("profile/", views.customer_profile, name="profile"),
    path("list/", views.customer_list, name="list"),
    path("<int:pk>/", views.customer_detail, name="detail"),
]