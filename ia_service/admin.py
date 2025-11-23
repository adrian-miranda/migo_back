"""
Admin para el servicio de IA de MIGO
"""
from django.contrib import admin
from .models import IAConfiguracion, IAFeedback, IAMetricasTecnico, IAConsultasLog


@admin.register(IAConfiguracion)
class IAConfiguracionAdmin(admin.ModelAdmin):
    list_display = ['clave', 'valor', 'descripcion', 'fecha_actualizacion']
    search_fields = ['clave', 'descripcion']
    readonly_fields = ['fecha_actualizacion']


@admin.register(IAFeedback)
class IAFeedbackAdmin(admin.ModelAdmin):
    list_display = ['id_feedback', 'ticket', 'tecnico', 'fue_util', 'tipo_consulta', 'fecha_feedback']
    list_filter = ['fue_util', 'tipo_consulta', 'fecha_feedback']
    search_fields = ['ticket__titulo', 'comentario']
    readonly_fields = ['fecha_feedback']


@admin.register(IAMetricasTecnico)
class IAMetricasTecnicoAdmin(admin.ModelAdmin):
    list_display = [
        'tecnico', 
        'categoria', 
        'tickets_resueltos', 
        'tasa_resolucion', 
        'tiempo_promedio_resolucion',
        'tasa_feedback_positivo',
        'fecha_calculo'
    ]
    list_filter = ['categoria', 'fecha_calculo']
    search_fields = ['tecnico__correo']
    readonly_fields = ['fecha_calculo']


@admin.register(IAConsultasLog)
class IAConsultasLogAdmin(admin.ModelAdmin):
    list_display = [
        'id_consulta',
        'tipo_consulta',
        'ticket',
        'usuario',
        'tokens_usados',
        'tiempo_respuesta_ms',
        'fecha_consulta'
    ]
    list_filter = ['tipo_consulta', 'fecha_consulta']
    search_fields = ['prompt_enviado', 'respuesta_ia']
    readonly_fields = ['fecha_consulta']