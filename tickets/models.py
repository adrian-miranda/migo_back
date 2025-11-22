"""
Modelos para el sistema de tickets
"""
from django.db import models
from authentication.models import Usuarios
from django.core.validators import MinValueValidator, MaxValueValidator


class CategoriaTicket(models.Model):
    """
    Categorías de tickets (Hardware, Software, Red, etc.)
    """
    id_categoria_ticket = models.AutoField(primary_key=True)
    nombre_categoria = models.CharField(max_length=45, unique=True)
    descripcion = models.CharField(max_length=200, null=True, blank=True)
    multiplicador_prioridad = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=1.00,
        help_text='Multiplicador de prioridad (0.5 a 2.0)'
    )

    class Meta:
        managed = False
        db_table = 'categoria_ticket'
        ordering = ['nombre_categoria']

    def __str__(self):
        return self.nombre_categoria


class EstadoTicket(models.Model):
    """
    Estados posibles de un ticket (Abierto, En Proceso, Cerrado, etc.)
    """
    id_estado_ticket = models.AutoField(primary_key=True)
    nombre_estado = models.CharField(max_length=45, unique=True)
    descripcion = models.CharField(max_length=200, null=True, blank=True)
    color = models.CharField(
        max_length=7, 
        null=True, 
        blank=True,
        help_text='Color hex para UI'
    )

    class Meta:
        managed = False
        db_table = 'estado_ticket'
        ordering = ['id_estado_ticket']

    def __str__(self):
        return self.nombre_estado


class PrioridadTicket(models.Model):
    """
    Prioridades de tickets (Baja, Media, Alta, Urgente)
    """
    id_prioridad_ticket = models.AutoField(primary_key=True)
    nombre_prioridad = models.CharField(max_length=45, unique=True)
    nivel = models.IntegerField(help_text='1=Baja, 2=Media, 3=Alta, 4=Urgente')
    color = models.CharField(max_length=7, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'prioridad_ticket'
        ordering = ['nivel']

    def __str__(self):
        return self.nombre_prioridad


class Ticket(models.Model):
    """
    Modelo principal de Tickets
    """
    id_ticket = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_asignacion = models.DateTimeField(null=True, blank=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    solucion = models.TextField(
        null=True, 
        blank=True,
        help_text='Descripción de la solución aplicada'
    )
    
    # Relaciones con usuarios
    usuario_creador_id = models.ForeignKey(
        Usuarios,
        on_delete=models.RESTRICT,
        db_column='usuario_creador_id',
        related_name='tickets_creados'
    )
    tecnico_asignado_id = models.ForeignKey(
        Usuarios,
        on_delete=models.SET_NULL,
        db_column='tecnico_asignado_id',
        related_name='tickets_asignados',
        null=True,
        blank=True
    )
    
    # Relaciones con catálogos
    categoria_id = models.ForeignKey(
        CategoriaTicket,
        on_delete=models.RESTRICT,
        db_column='categoria_id',
        related_name='tickets'
    )
    estado_id = models.ForeignKey(
        EstadoTicket,
        on_delete=models.RESTRICT,
        db_column='estado_id',
        related_name='tickets',
        default=1
    )
    prioridad_id = models.ForeignKey(
        PrioridadTicket,
        on_delete=models.RESTRICT,
        db_column='prioridad_id',
        related_name='tickets',
        default=2
    )
    
    # Control de prioridad
    prioridad_manual = models.BooleanField(
        default=False,
        help_text='False=Automática, True=Manual (no recalcular)'
    )

    class Meta:
        managed = False
        db_table = 'tickets'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"#{self.id_ticket} - {self.titulo}"


class HistorialTicket(models.Model):
    """
    Historial de cambios en tickets
    """
    id_historial = models.AutoField(primary_key=True)
    ticket_id = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        db_column='ticket_id',
        related_name='historial'
    )
    usuario_id = models.ForeignKey(
        Usuarios,
        on_delete=models.RESTRICT,
        db_column='usuario_id',
        related_name='acciones_historial'
    )
    estado_anterior_id = models.ForeignKey(
        EstadoTicket,
        on_delete=models.RESTRICT,
        db_column='estado_anterior_id',
        related_name='historial_estado_anterior',
        null=True,
        blank=True
    )
    estado_nuevo_id = models.ForeignKey(
        EstadoTicket,
        on_delete=models.RESTRICT,
        db_column='estado_nuevo_id',
        related_name='historial_estado_nuevo'
    )
    comentario = models.TextField(null=True, blank=True)
    fecha_cambio = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'historial_ticket'
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f"Historial #{self.id_historial} - Ticket #{self.ticket_id.id_ticket}"
    
class CalificacionTicket(models.Model):
    """
    Modelo para calificaciones de tickets
    """
    id_calificacion = models.AutoField(primary_key=True)
    ticket_id = models.OneToOneField(
        Ticket,
        on_delete=models.CASCADE,
        db_column='ticket_id_ticket',
        related_name='calificacion'
    )
    usuario_id = models.ForeignKey(
        'authentication.Usuarios',
        on_delete=models.CASCADE,
        db_column='usuario_id_usuarios'
    )
    calificacion = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comentario = models.TextField(blank=True, null=True)
    fecha_calificacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'calificacion_ticket'
        ordering = ['-fecha_calificacion']

    def __str__(self):
        return f"Calificación {self.calificacion}/5 - Ticket #{self.ticket_id.id_ticket}"