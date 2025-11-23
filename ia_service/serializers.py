"""
Serializers para el servicio de IA
"""
from rest_framework import serializers
from .models import IAFeedback, IAMetricasTecnico, IAConsultasLog, IAConfiguracion


class IAFeedbackSerializer(serializers.ModelSerializer):
    """Serializer para feedback de IA"""
    
    class Meta:
        model = IAFeedback
        fields = [
            'id_feedback',
            'ticket',
            'tecnico',
            'fue_util',
            'comentario',
            'tipo_consulta',
            'fecha_feedback'
        ]
        read_only_fields = ['id_feedback', 'fecha_feedback']


class IAFeedbackCreateSerializer(serializers.Serializer):
    """Serializer para crear feedback"""
    ticket_id = serializers.IntegerField()
    fue_util = serializers.BooleanField()
    comentario = serializers.CharField(required=False, allow_blank=True)
    tipo_consulta = serializers.ChoiceField(
        choices=['guia_solucion', 'tickets_similares', 'otro'],
        default='guia_solucion'
    )


class IAMetricasTecnicoSerializer(serializers.ModelSerializer):
    """Serializer para métricas de técnicos"""
    tecnico_nombre = serializers.SerializerMethodField()
    categoria_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = IAMetricasTecnico
        fields = [
            'id_metrica',
            'tecnico',
            'tecnico_nombre',
            'categoria',
            'categoria_nombre',
            'tickets_resueltos',
            'tickets_totales',
            'tiempo_promedio_resolucion',
            'tasa_resolucion',
            'feedback_positivo',
            'feedback_total',
            'tasa_feedback_positivo',
            'fecha_calculo'
        ]
    
    def get_tecnico_nombre(self, obj):
        if obj.tecnico and obj.tecnico.personas_id_personas:
            persona = obj.tecnico.personas_id_personas
            return f"{persona.primer_nombre} {persona.primer_apellido}"
        return None
    
    def get_categoria_nombre(self, obj):
        return obj.categoria.nombre_categoria if obj.categoria else None


class IAConsultasLogSerializer(serializers.ModelSerializer):
    """Serializer para log de consultas"""
    
    class Meta:
        model = IAConsultasLog
        fields = [
            'id_consulta',
            'ticket',
            'usuario',
            'tipo_consulta',
            'prompt_enviado',
            'respuesta_ia',
            'tokens_usados',
            'tiempo_respuesta_ms',
            'fecha_consulta'
        ]


class GuiaSolucionRequestSerializer(serializers.Serializer):
    """Serializer para solicitar guía de solución"""
    ticket_id = serializers.IntegerField()


class GuiaSolucionResponseSerializer(serializers.Serializer):
    """Serializer para respuesta de guía de solución"""
    success = serializers.BooleanField()
    respuesta = serializers.CharField(allow_null=True)
    error = serializers.CharField(required=False, allow_null=True)
    tokens_usados = serializers.IntegerField(required=False, allow_null=True)
    tiempo_ms = serializers.IntegerField(required=False, allow_null=True)
    tickets_similares = serializers.ListField(required=False)


class RecomendarTecnicoRequestSerializer(serializers.Serializer):
    """Serializer para solicitar recomendación de técnico"""
    ticket_id = serializers.IntegerField()


class RecomendarTecnicoResponseSerializer(serializers.Serializer):
    """Serializer para respuesta de recomendación"""
    success = serializers.BooleanField()
    respuesta = serializers.CharField(allow_null=True)
    error = serializers.CharField(required=False, allow_null=True)
    metricas_tecnicos = serializers.ListField(required=False)


class AnalizarPatronesRequestSerializer(serializers.Serializer):
    """Serializer para solicitar análisis de patrones"""
    dias = serializers.IntegerField(default=30, min_value=1, max_value=365)


class AnalizarPatronesResponseSerializer(serializers.Serializer):
    """Serializer para respuesta de análisis de patrones"""
    success = serializers.BooleanField()
    respuesta = serializers.CharField(allow_null=True)
    error = serializers.CharField(required=False, allow_null=True)
    estadisticas = serializers.DictField(required=False)


class IAConfiguracionSerializer(serializers.ModelSerializer):
    """Serializer para configuración de IA"""
    
    class Meta:
        model = IAConfiguracion
        fields = ['id_configuracion', 'clave', 'valor', 'descripcion', 'fecha_actualizacion']
        read_only_fields = ['id_configuracion', 'fecha_actualizacion']