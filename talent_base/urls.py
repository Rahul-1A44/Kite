"""
URL configuration for talent_base project.
"""
from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static

# ✅ FIXED IMPORT: Changed 'list_adverts' to 'home'
from application_tracking.views import home

urlpatterns = [
    # Homepage
    path("", home, name="home"),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Auth URLs (Login, Register for candidates)
    path("auth/", include("accounts.urls")),
    
    # App URLs (Job Adverts, Profile, Dashboard)
    path("adverts/", include("application_tracking.urls")),

    # ✅ NEW: Organization URLs (Registration, Status, Payments)
    path("org/", include("organization.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)