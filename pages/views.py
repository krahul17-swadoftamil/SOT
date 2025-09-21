# pages/views.py
from django.shortcuts import render

def about_us(request):
    return render(request, "pages/about.html")

def mission(request):
    return render(request, "pages/mission.html")

def brand_story(request):
    return render(request, "pages/brand_story.html")

def contact_view(request):
    return render(request, "pages/contact.html")
