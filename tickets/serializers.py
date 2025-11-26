"""
Serializers para el sistema de tickets
"""
from rest_framework import serializers
from authentication.serializers import UsuarioSerializer, UsuarioBasicoSerializer
from .models import (
    CategoriaTicket, 
    EstadoTicket, 
    PrioridadTicket, 
    Ticket, 
    HistorialTicket,
    CalificacionTicket,
    Reclamo
)


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
            'fecha_resolucion',
            'fecha_cierre',
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


class TicketDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalle de ticket"""
    categoria = serializers.CharField(source='categoria_id.nombre_categoria', read_only=True)
    categoria_id_value = serializers.IntegerField(source='categoria_id.id_categoria_ticket', read_only=True)
    
    estado = serializers.CharField(source='estado_id.nombre_estado', read_only=True)
    estado_id_value = serializers.IntegerField(source='estado_id.id_estado_ticket', read_only=True)
    estado_color = serializers.CharField(source='estado_id.color', read_only=True)
    
    prioridad = serializers.CharField(source='prioridad_id.nombre_prioridad', read_only=True)
    prioridad_id_value = serializers.IntegerField(source='prioridad_id.id_prioridad_ticket', read_only=True)
    prioridad_color = serializers.CharField(source='prioridad_id.color', read_only=True)
    prioridad_nivel = serializers.IntegerField(source='prioridad_id.nivel', read_only=True)
    
    usuario_creador = serializers.SerializerMethodField()
    tecnico_asignado = serializers.SerializerMethodField()
    calificacion_ticket = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id_ticket', 'titulo', 'descripcion',
            'fecha_creacion', 'fecha_asignacion', 'fecha_resolucion', 'fecha_cierre',
            'solucion', 
            'categoria', 'categoria_id_value',
            'estado', 'estado_id_value', 'estado_color',
            'prioridad', 'prioridad_id_value', 'prioridad_color', 'prioridad_nivel',
            'usuario_creador', 'tecnico_asignado', 'prioridad_manual',
            'calificacion_ticket'
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
    
    def get_calificacion_ticket(self, obj):
        try:
            calificacion = obj.calificacion
            return CalificacionTicketSerializer(calificacion).data
        except CalificacionTicket.DoesNotExist:
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

class CalificacionTicketSerializer(serializers.ModelSerializer):
    """Serializer para calificaciones de tickets"""
    usuario = serializers.SerializerMethodField()
    
    class Meta:
        model = CalificacionTicket
        fields = [
            'id_calificacion',
            'calificacion',
            'comentario',
            'fecha_calificacion',
            'usuario'
        ]
    
    def get_usuario(self, obj):
        return {
            'id': obj.usuario_id.id_usuarios,
            'nombre': obj.usuario_id.personas_id_personas.nombre_completo
        }


class CalificacionCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear calificaciones"""
    class Meta:
        model = CalificacionTicket
        fields = ['calificacion', 'comentario']
    
    def validate_calificacion(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("La calificación debe estar entre 1 y 5")
        return value

class ReclamoListSerializer(serializers.ModelSerializer):
    ticket_titulo = serializers.CharField(source='ticket_id.titulo', read_only=True)
    ticket_id_value = serializers.IntegerField(source='ticket_id.id_ticket', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario_id.personas_id_personas.nombre_completo', read_only=True)
    usuario_correo = serializers.CharField(source='usuario_id.correo', read_only=True)
    tecnico_nombre = serializers.CharField(source='tecnico_id.personas_id_personas.nombre_completo', read_only=True)
    tecnico_correo = serializers.CharField(source='tecnico_id.correo', read_only=True)
    categoria_label = serializers.CharField(source='get_categoria_display', read_only=True)
    estado_label = serializers.CharField(source='get_estado_display', read_only=True)
    prioridad_label = serializers.CharField(source='get_prioridad_display', read_only=True)
    
    class Meta:
        model = Reclamo
        fields = [
            'id_reclamo', 'ticket_id_value', 'ticket_titulo',
            'categoria', 'categoria_label', 'estado', 'estado_label',
            'prioridad', 'prioridad_label', 'usuario_nombre', 'usuario_correo',
            'tecnico_nombre', 'tecnico_correo', 'fecha_creacion', 'fecha_resolucion', 'descripcion' 
        ]


class ReclamoDetailSerializer(serializers.ModelSerializer):
    ticket = serializers.SerializerMethodField()
    usuario = serializers.SerializerMethodField()
    tecnico = serializers.SerializerMethodField()
    admin_revisor = serializers.SerializerMethodField()
    categoria_label = serializers.CharField(source='get_categoria_display', read_only=True)
    estado_label = serializers.CharField(source='get_estado_display', read_only=True)
    prioridad_label = serializers.CharField(source='get_prioridad_display', read_only=True)
    
    class Meta:
        model = Reclamo
        fields = [
            'id_reclamo', 'ticket', 'usuario', 'tecnico',
            'categoria', 'categoria_label', 'descripcion',
            'estado', 'estado_label', 'prioridad', 'prioridad_label',
            'respuesta_admin', 'admin_revisor',
            'fecha_creacion', 'fecha_actualizacion', 'fecha_resolucion'
        ]
    
    def get_ticket(self, obj):
        return {
            'id': obj.ticket_id.id_ticket,
            'titulo': obj.ticket_id.titulo,
            'categoria': obj.ticket_id.categoria_id.nombre_categoria,
            'estado': obj.ticket_id.estado_id.nombre_estado,
        }
    
    def get_usuario(self, obj):
        return {
            'id': obj.usuario_id.id_usuarios,
            'nombre': obj.usuario_id.personas_id_personas.nombre_completo,
            'correo': obj.usuario_id.correo,
        }
    
    def get_tecnico(self, obj):
        return {
            'id': obj.tecnico_id.id_usuarios,
            'nombre': obj.tecnico_id.personas_id_personas.nombre_completo,
            'correo': obj.tecnico_id.correo,
        }
    
    def get_admin_revisor(self, obj):
        if obj.admin_revisor_id:
            return {
                'id': obj.admin_revisor_id.id_usuarios,
                'nombre': obj.admin_revisor_id.personas_id_personas.nombre_completo,
            }
        return None