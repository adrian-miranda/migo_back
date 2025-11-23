"""
URLs para el servicio de IA de MIGO
"""
from django.urls import path
from . import views

app_name = 'ia_service'

urlpatterns = [
    # ==========================================================================
    # ENDPOINTS PARA TÉCNICOS
    # ==========================================================================
    
    # Generar guía de solución para un ticket
    # POST /api/ia/guia-solucion/
    # Body: {"ticket_id": 123, "usuario_id": 1}
    path('guia-solucion/', views.GuiaSolucionView.as_view(), name='guia_solucion'),
    
    # Obtener tickets similares resueltos
    # GET /api/ia/tickets-similares/<ticket_id>/
    path('tickets-similares/<int:ticket_id>/', views.TicketsSimilaresView.as_view(), name='tickets_similares'),
    
    # Registrar feedback sobre la ayuda de IA
    # POST /api/ia/feedback/
    # Body: {"ticket_id": 123, "tecnico_id": 1, "fue_util": true, "comentario": "..."}
    # GET /api/ia/feedback/?tecnico_id=1
    path('feedback/', views.FeedbackIAView.as_view(), name='feedback'),

    # Sugerir prioridad para un ticket
    # POST /api/ia/priorizar-ticket/
    # Body: {"ticket_id": 123}
    path('priorizar-ticket/', views.PriorizarTicketView.as_view(), name='priorizar_ticket'),
    
    # ==========================================================================
    # ENDPOINTS PARA ADMINISTRADOR
    # ==========================================================================
    
    # Recomendar mejor técnico para un ticket
    # POST /api/ia/recomendar-tecnico/
    # Body: {"ticket_id": 123, "usuario_id": 1}
    path('recomendar-tecnico/', views.RecomendarTecnicoView.as_view(), name='recomendar_tecnico'),
    
    # Analizar patrones en tickets
    # POST /api/ia/analizar-patrones/
    # Body: {"dias": 30, "usuario_id": 1}
    path('analizar-patrones/', views.AnalizarPatronesView.as_view(), name='analizar_patrones'),
    
    # Métricas de técnicos
    # GET /api/ia/metricas-tecnicos/?categoria_id=1&tecnico_id=5
    # POST /api/ia/metricas-tecnicos/ (recalcular todas)
    path('metricas-tecnicos/', views.MetricasTecnicosView.as_view(), name='metricas_tecnicos'),
    
    # Insights para capacitación
    # GET /api/ia/insights-capacitacion/
    path('insights-capacitacion/', views.InsightsCapacitacionView.as_view(), name='insights_capacitacion'),
    
    # ==========================================================================
    # ENDPOINTS DE CONFIGURACIÓN Y MONITOREO
    # ==========================================================================
    
    # Configuración de IA
    # GET /api/ia/configuracion/
    # PUT /api/ia/configuracion/ Body: {"clave": "modelo_openai", "valor": "gpt-4o"}
    path('configuracion/', views.ConfiguracionIAView.as_view(), name='configuracion'),
    
    # Historial de consultas
    # GET /api/ia/historial/?limite=50&tipo=guia_solucion
    path('historial/', views.HistorialConsultasView.as_view(), name='historial'),
    

    # Consultas restantes del usuario
    # GET /api/ia/consultas-restantes/
    path('consultas-restantes/', views.ConsultasRestantesView.as_view(), name='consultas_restantes'),

    # Estado del servicio
    # GET /api/ia/status/
    path('status/', views.ia_status, name='status'),
]