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
    cancelar_ticket,
    tickets_pendientes,
    # Historial
    obtener_historial_ticket,
    # Estadísticas
    estadisticas_tickets,
    estadisticas_historicas,
    # Calificaciones
    calificar_ticket,
    obtener_calificacion,
    tickets_sin_calificar,
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
    path('tickets-pendientes/', tickets_pendientes, name='tickets-pendientes'),
    path('crear/', crear_ticket, name='crear-ticket'),
    path('<int:id_ticket>/', obtener_ticket, name='obtener-ticket'),
    path('<int:id_ticket>/actualizar/', actualizar_ticket, name='actualizar-ticket'),
    path('<int:id_ticket>/eliminar/', eliminar_ticket, name='eliminar-ticket'),
    path('<int:id_ticket>/cancelar/', cancelar_ticket, name='cancelar-ticket'),
    
    # Historial
    path('<int:id_ticket>/historial/', obtener_historial_ticket, name='historial-ticket'),
    
    # Calificaciones (NUEVAS)
    path('<int:id_ticket>/calificar/', calificar_ticket, name='calificar-ticket'),
    path('<int:id_ticket>/calificacion/', obtener_calificacion, name='obtener-calificacion'),
    path('sin-calificar/', tickets_sin_calificar, name='tickets-sin-calificar'),
    
    # Estadísticas
    path('estadisticas/', estadisticas_tickets, name='estadisticas-tickets'),
    path('estadisticas-historicas/', estadisticas_historicas, name='estadisticas-historicas'),

]