"""
URL configuration for migo_back project.
"""
from django.contrib import admin
from django.urls import path, include

# Personalizar títulos del admin
admin.site.site_header = "Administración de MIGO"
admin.site.site_title = "MIGO Admin"
admin.site.index_title = "Panel de Administración"


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/tickets/', include('tickets.urls')),
]