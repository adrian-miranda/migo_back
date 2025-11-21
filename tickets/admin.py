"""
Configuración del panel de administración para tickets
"""
from django.contrib import admin
from .models import (
    CategoriaTicket,
    EstadoTicket,
    PrioridadTicket,
    Ticket,
    HistorialTicket
)


@admin.register(CategoriaTicket)
class CategoriaTicketAdmin(admin.ModelAdmin):
    list_display = [
        'id_categoria_ticket',
        'nombre_categoria',
        'multiplicador_prioridad',
        'descripcion'
    ]
    search_fields = ['nombre_categoria']
    list_filter = ['multiplicador_prioridad']


@admin.register(EstadoTicket)
class EstadoTicketAdmin(admin.ModelAdmin):
    list_display = [
        'id_estado_ticket',
        'nombre_estado',
        'color',
        'descripcion'
    ]
    search_fields = ['nombre_estado']


@admin.register(PrioridadTicket)
class PrioridadTicketAdmin(admin.ModelAdmin):
    list_display = [
        'id_prioridad_ticket',
        'nombre_prioridad',
        'nivel',
        'color'
    ]
    list_filter = ['nivel']
    ordering = ['nivel']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = [
        'id_ticket',
        'titulo',
        'get_usuario_creador',
        'get_tecnico_asignado',
        'get_categoria',
        'get_estado',
        'get_prioridad',
        'fecha_creacion'
    ]
    list_filter = [
        'estado_id',
        'prioridad_id',
        'categoria_id',
        'fecha_creacion'
    ]
    search_fields = [
        'titulo',
        'descripcion',
        'usuario_creador_id__correo',
        'tecnico_asignado_id__correo'
    ]
    readonly_fields = [
        'fecha_creacion',
        'fecha_asignacion',
        'fecha_resolucion',
        'fecha_cierre'
    ]
    
    fieldsets = (
        ('Información del Ticket', {
            'fields': ('titulo', 'descripcion', 'categoria_id')
        }),
        ('Estado y Prioridad', {
            'fields': ('estado_id', 'prioridad_id', 'prioridad_manual')
        }),
        ('Asignación', {
            'fields': ('usuario_creador_id', 'tecnico_asignado_id')
        }),
        ('Solución', {
            'fields': ('solucion',)
        }),
        ('Fechas', {
            'fields': (
                'fecha_creacion',
                'fecha_asignacion',
                'fecha_resolucion',
                'fecha_cierre'
            )
        }),
    )
    
    def get_usuario_creador(self, obj):
        return obj.usuario_creador_id.personas_id_personas.nombre_completo
    get_usuario_creador.short_description = 'Usuario Creador'
    
    def get_tecnico_asignado(self, obj):
        if obj.tecnico_asignado_id:
            return obj.tecnico_asignado_id.personas_id_personas.nombre_completo
        return 'Sin asignar'
    get_tecnico_asignado.short_description = 'Técnico Asignado'
    
    def get_categoria(self, obj):
        return obj.categoria_id.nombre_categoria
    get_categoria.short_description = 'Categoría'
    
    def get_estado(self, obj):
        return obj.estado_id.nombre_estado
    get_estado.short_description = 'Estado'
    
    def get_prioridad(self, obj):
        return obj.prioridad_id.nombre_prioridad
    get_prioridad.short_description = 'Prioridad'


@admin.register(HistorialTicket)
class HistorialTicketAdmin(admin.ModelAdmin):
    list_display = [
        'id_historial',
        'get_ticket',
        'get_usuario',
        'get_estado_anterior',
        'get_estado_nuevo',
        'fecha_cambio'
    ]
    list_filter = [
        'estado_nuevo_id',
        'fecha_cambio'
    ]
    search_fields = [
        'ticket_id__titulo',
        'usuario_id__correo',
        'comentario'
    ]
    readonly_fields = [
        'ticket_id',
        'usuario_id',
        'estado_anterior_id',
        'estado_nuevo_id',
        'comentario',
        'fecha_cambio'
    ]
    
    def get_ticket(self, obj):
        return f"#{obj.ticket_id.id_ticket} - {obj.ticket_id.titulo}"
    get_ticket.short_description = 'Ticket'
    
    def get_usuario(self, obj):
        return obj.usuario_id.personas_id_personas.nombre_completo
    get_usuario.short_description = 'Usuario'
    
    def get_estado_anterior(self, obj):
        return obj.estado_anterior_id.nombre_estado if obj.estado_anterior_id else 'N/A'
    get_estado_anterior.short_description = 'Estado Anterior'
    
    def get_estado_nuevo(self, obj):
        return obj.estado_nuevo_id.nombre_estado
    get_estado_nuevo.short_description = 'Estado Nuevo'