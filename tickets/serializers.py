"""
Serializers para el sistema de tickets
"""
from rest_framework import serializers
from .models import (
    CategoriaTicket, 
    EstadoTicket, 
    PrioridadTicket, 
    Ticket, 
    HistorialTicket
)
from authentication.serializers import UsuarioSerializer, UsuarioBasicoSerializer


class CategoriaTicketSerializer(serializers.ModelSerializer):
    """Serializer para categorías de tickets"""
    class Meta:
        model = CategoriaTicket
        fields = [
            'id_categoria_ticket',
            'nombre_categoria',
            'descripcion',
            'multiplicador_prioridad'
        ]


class EstadoTicketSerializer(serializers.ModelSerializer):
    """Serializer para estados de tickets"""
    class Meta:
        model = EstadoTicket
        fields = [
            'id_estado_ticket',
            'nombre_estado',
            'descripcion',
            'color'
        ]


class PrioridadTicketSerializer(serializers.ModelSerializer):
    """Serializer para prioridades de tickets"""
    class Meta:
        model = PrioridadTicket
        fields = [
            'id_prioridad_ticket',
            'nombre_prioridad',
            'nivel',
            'color'
        ]


class TicketListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados de tickets"""
    categoria = serializers.CharField(source='categoria_id.nombre_categoria', read_only=True)
    estado = serializers.CharField(source='estado_id.nombre_estado', read_only=True)
    estado_color = serializers.CharField(source='estado_id.color', read_only=True)
    prioridad = serializers.CharField(source='prioridad_id.nombre_prioridad', read_only=True)
    prioridad_color = serializers.CharField(source='prioridad_id.color', read_only=True)
    prioridad_nivel = serializers.IntegerField(source='prioridad_id.nivel', read_only=True)
    
    usuario_creador = serializers.SerializerMethodField()
    tecnico_asignado = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id_ticket',
            'titulo',
            'descripcion',
            'fecha_creacion',
            'fecha_asignacion',
            'categoria',
            'estado',
            'estado_color',
            'prioridad',
            'prioridad_color',
            'prioridad_nivel',
            'usuario_creador',
            'tecnico_asignado'
        ]

    def get_usuario_creador(self, obj):
        return {
            'id': obj.usuario_creador_id.id_usuarios,
            'nombre': obj.usuario_creador_id.personas_id_personas.nombre_completo,
            'correo': obj.usuario_creador_id.correo
        }

    def get_tecnico_asignado(self, obj):
        if obj.tecnico_asignado_id:
            return {
                'id': obj.tecnico_asignado_id.id_usuarios,
                'nombre': obj.tecnico_asignado_id.personas_id_personas.nombre_completo,
                'correo': obj.tecnico_asignado_id.correo
            }
        return None


class TicketDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle de ticket"""
    categoria = serializers.CharField(source='categoria_id.nombre_categoria', read_only=True)
    estado = serializers.CharField(source='estado_id.nombre_estado', read_only=True)
    estado_color = serializers.CharField(source='estado_id.color', read_only=True)
    prioridad = serializers.CharField(source='prioridad_id.nombre_prioridad', read_only=True)
    prioridad_color = serializers.CharField(source='prioridad_id.color', read_only=True)
    prioridad_nivel = serializers.IntegerField(source='prioridad_id.nivel', read_only=True)
    usuario_creador = serializers.SerializerMethodField()
    tecnico_asignado = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id_ticket', 'titulo', 'descripcion',
            'fecha_creacion', 'fecha_asignacion', 'fecha_resolucion', 'fecha_cierre',
            'solucion', 'categoria', 'estado', 'estado_color',
            'prioridad', 'prioridad_color', 'prioridad_nivel',
            'usuario_creador', 'tecnico_asignado', 'prioridad_manual'
        ]
    
    def get_usuario_creador(self, obj):
        if obj.usuario_creador_id:
            return {
                'id': obj.usuario_creador_id.id_usuarios,
                'nombre': obj.usuario_creador_id.personas_id_personas.nombre_completo,
                'correo': obj.usuario_creador_id.correo
            }
        return None
    
    def get_tecnico_asignado(self, obj):
        if obj.tecnico_asignado_id:
            return {
                'id': obj.tecnico_asignado_id.id_usuarios,
                'nombre': obj.tecnico_asignado_id.personas_id_personas.nombre_completo,
                'correo': obj.tecnico_asignado_id.correo
            }
        return None


class TicketCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear tickets"""
    class Meta:
        model = Ticket
        fields = [
            'titulo',
            'descripcion',
            'categoria_id',
            'prioridad_manual'
        ]

    def create(self, validated_data):
        # El usuario_creador_id se asigna desde la vista
        return Ticket.objects.create(**validated_data)


class TicketUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar tickets"""
    class Meta:
        model = Ticket
        fields = [
            'titulo',
            'descripcion',
            'categoria_id',
            'estado_id',
            'prioridad_id',
            'tecnico_asignado_id',
            'solucion',
            'prioridad_manual'
        ]


class HistorialTicketSerializer(serializers.ModelSerializer):
    """Serializer para historial de tickets"""
    usuario = serializers.SerializerMethodField()
    estado_anterior = serializers.CharField(
        source='estado_anterior_id.nombre_estado',
        read_only=True
    )
    estado_nuevo = serializers.CharField(
        source='estado_nuevo_id.nombre_estado',
        read_only=True
    )

    class Meta:
        model = HistorialTicket
        fields = [
            'id_historial',
            'fecha_cambio',
            'usuario',
            'estado_anterior',
            'estado_nuevo',
            'comentario'
        ]

    def get_usuario(self, obj):
        return {
            'id': obj.usuario_id.id_usuarios,
            'nombre': obj.usuario_id.personas_id_personas.nombre_completo
        }