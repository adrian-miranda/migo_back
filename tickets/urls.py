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
    #tecnicos
    tecnico_estadisticas,
    tecnico_mis_tickets,
    tecnico_historial,
    tecnico_alertas,
    #reclamos
    listar_reclamos, 
    obtener_reclamo, 
    crear_reclamo,
    actualizar_reclamo,
    estadisticas_reclamos,

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

    # Endpoints para Técnicos
    path('tecnico/estadisticas/', tecnico_estadisticas, name='tecnico-estadisticas'),
    path('tecnico/mis-tickets/', tecnico_mis_tickets, name='tecnico-mis-tickets'),
    path('tecnico/historial/', tecnico_historial, name='tecnico-historial'),
    path('tecnico/alertas/', tecnico_alertas, name='tecnico-alertas'),

    # Reclamos
    path('reclamos/', listar_reclamos, name='listar-reclamos'),
    path('reclamos/crear/', crear_reclamo, name='crear-reclamo'),
    path('reclamos/estadisticas/', estadisticas_reclamos, name='estadisticas-reclamos'),
    path('reclamos/<int:id_reclamo>/', obtener_reclamo, name='obtener-reclamo'),
    path('reclamos/<int:id_reclamo>/actualizar/', actualizar_reclamo, name='actualizar-reclamo'),

]