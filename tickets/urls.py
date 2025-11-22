"""
URLs para la app de tickets
"""
from django.urls import path
from .views import (
    # Catálogos
    listar_categorias,
    listar_estados,
    listar_prioridades,
    
    # Tickets CRUD
    listar_tickets,
    obtener_ticket,
    crear_ticket,
    actualizar_ticket,
    eliminar_ticket,
    mis_tickets,
    
    # Historial
    obtener_historial_ticket,
    
    # Estadísticas
    estadisticas_tickets,
)

app_name = 'tickets'

urlpatterns = [
    # Catálogos
    path('categorias/', listar_categorias, name='listar-categorias'),
    path('estados/', listar_estados, name='listar-estados'),
    path('prioridades/', listar_prioridades, name='listar-prioridades'),
    
    # Tickets CRUD
    path('', listar_tickets, name='listar-tickets'),
    path('mis-tickets/', mis_tickets, name='mis-tickets'),
    path('crear/', crear_ticket, name='crear-ticket'),
    path('<int:id_ticket>/', obtener_ticket, name='obtener-ticket'),
    path('<int:id_ticket>/actualizar/', actualizar_ticket, name='actualizar-ticket'),
    path('<int:id_ticket>/eliminar/', eliminar_ticket, name='eliminar-ticket'),
    
    # Historial
    path('<int:id_ticket>/historial/', obtener_historial_ticket, name='historial-ticket'),
    
    # Estadísticas
    path('estadisticas/', estadisticas_tickets, name='estadisticas-tickets'),
]