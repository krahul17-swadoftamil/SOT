# pages/urls.py
from django.urls import path
from . import views

app_name = "pages"

urlpatterns = [
    path("about/", views.about_us, name="about_us"),
    path("mission/", views.mission, name="mission"),
    path("brand-story/", views.brand_story, name="story"),
    path("contact/", views.contact_view, name="contact"),
]
