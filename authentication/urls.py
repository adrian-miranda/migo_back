"""
URLs para la app de autenticación
"""
from django.urls import path
from .views import (
    verificar_conexion,
    login_view,
    logout_view,
    perfil_view,
    listar_usuarios,
    obtener_usuario
)

app_name = 'authentication'

urlpatterns = [
    # Verificación
    path('verificar/', verificar_conexion, name='verificar-conexion'),
    
    # Autenticación
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('perfil/', perfil_view, name='perfil'),
    
    # Gestión de usuarios
    path('usuarios/', listar_usuarios, name='listar-usuarios'),
    path('usuarios/<int:id_usuario>/', obtener_usuario, name='obtener-usuario'),
]