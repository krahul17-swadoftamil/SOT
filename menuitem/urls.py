# menuitem/urls.py
from django.urls import path
from . import views

app_name = 'menuitem'

urlpatterns = [
    path('', views.menu_list, name='menu_list'),   # list all items with prices
    path('<int:pk>/', views.menu_detail, name='menu_detail'),  # item details
    path("combo/<int:combo_id>/", views.combo_detail, name="combo_detail"),
]
