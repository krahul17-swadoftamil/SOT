# streetkitchen/urls.py (root)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Core app (homepage, contact, etc.)
    path('', include(('core.urls', 'core'), namespace='core')),

    # Vendors app
    path('vendors/', include(('vendors.urls', 'vendors'), namespace='vendors')),

    # Orders app
    path('orders/', include(('orders.urls', 'orders'), namespace='orders')),

    # Menu app
    path('menu/', include(('menuitem.urls', 'menuitem'), namespace='menuitem')),

    # Customers app
    path("customers/", include("customers.urls")),

    # Pages app
    path('pages/', include('pages.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
