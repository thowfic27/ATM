"""
URL configuration for the atm_project project.

The home page and all ATM pages live in the `atm` app -
see atm/urls.py for the full list of pages.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('atm.urls')),
]
