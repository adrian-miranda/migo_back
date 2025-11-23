"""
Modelos para el servicio de IA de MIGO
"""
from django.db import models
from authentication.models import Usuarios
from tickets.models import Ticket, CategoriaTicket


class IAConfiguracion(models.Model):
    """
    Configuración global del servicio de IA
    """
    id_configuracion = models.AutoField(primary_key=True)
    clave = models.CharField(max_length=50, unique=True)
    valor = models.TextField()
    descripcion = models.CharField(max_length=200, null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'ia_configuracion'
        verbose_name = 'Configuración IA'
        verbose_name_plural = 'Configuraciones IA'

    def __str__(self):
        return f"{self.clave}: {self.valor}"

    @classmethod
    def get_valor(cls, clave, default=None):
        """Obtener valor de configuración por clave"""
        try:
            config = cls.objects.get(clave=clave)
            return config.valor
        except cls.DoesNotExist:
            return default


class IAFeedback(models.Model):
    """
    Feedback de técnicos sobre las sugerencias de IA
    """
    TIPO_CONSULTA_CHOICES = [
        ('guia_solucion', 'Guía de Solución'),
        ('tickets_similares', 'Tickets Similares'),
        ('otro', 'Otro'),
    ]

    id_feedback = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        db_column='ticket_id',
        related_name='feedbacks_ia'
    )
    tecnico = models.ForeignKey(
        Usuarios,
        on_delete=models.CASCADE,
        db_column='tecnico_id',
        related_name='feedbacks_ia'
    )
    fue_util = models.BooleanField(help_text='True=Sí, False=No')
    comentario = models.TextField(null=True, blank=True)
    tipo_consulta = models.CharField(
        max_length=20,
        choices=TIPO_CONSULTA_CHOICES,
        default='guia_solucion'
    )
    fecha_feedback = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'ia_feedback'
        verbose_name = 'Feedback IA'
        verbose_name_plural = 'Feedbacks IA'
        ordering = ['-fecha_feedback']

    def __str__(self):
        util = "Útil" if self.fue_util else "No útil"
        return f"Feedback Ticket #{self.ticket_id} - {util}"


class IAMetricasTecnico(models.Model):
    """
    Métricas calculadas por técnico y categoría (cache)
    """
    id_metrica = models.AutoField(primary_key=True)
    tecnico = models.ForeignKey(
        Usuarios,
        on_delete=models.CASCADE,
        db_column='tecnico_id',
        related_name='metricas_ia'
    )
    categoria = models.ForeignKey(
        CategoriaTicket,
        on_delete=models.CASCADE,
        db_column='categoria_id',
        related_name='metricas_tecnicos'
    )
    tickets_resueltos = models.IntegerField(default=0)
    tickets_totales = models.IntegerField(default=0)
    tiempo_promedio_resolucion = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='En horas'
    )
    tasa_resolucion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Porcentaje 0-100'
    )
    feedback_positivo = models.IntegerField(default=0)
    feedback_total = models.IntegerField(default=0)
    tasa_feedback_positivo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Porcentaje 0-100'
    )
    fecha_calculo = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'ia_metricas_tecnico'
        verbose_name = 'Métrica Técnico'
        verbose_name_plural = 'Métricas Técnicos'
        unique_together = ['tecnico', 'categoria']

    def __str__(self):
        return f"Métricas {self.tecnico} - {self.categoria}"


class IAConsultasLog(models.Model):
    """
    Log de consultas realizadas a la IA
    """
    TIPO_CONSULTA_CHOICES = [
        ('guia_solucion', 'Guía de Solución'),
        ('recomendar_tecnico', 'Recomendar Técnico'),
        ('detectar_patron', 'Detectar Patrón'),
        ('priorizar', 'Priorizar Ticket'),
    ]

    id_consulta = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.SET_NULL,
        db_column='ticket_id',
        related_name='consultas_ia',
        null=True,
        blank=True
    )
    usuario = models.ForeignKey(
        Usuarios,
        on_delete=models.CASCADE,
        db_column='usuario_id',
        related_name='consultas_ia'
    )
    tipo_consulta = models.CharField(max_length=20, choices=TIPO_CONSULTA_CHOICES)
    prompt_enviado = models.TextField()
    respuesta_ia = models.TextField(null=True, blank=True)
    tokens_usados = models.IntegerField(null=True, blank=True)
    tiempo_respuesta_ms = models.IntegerField(null=True, blank=True)
    fecha_consulta = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'ia_consultas_log'
        verbose_name = 'Consulta IA'
        verbose_name_plural = 'Consultas IA'
        ordering = ['-fecha_consulta']

    def __str__(self):
        return f"Consulta {self.tipo_consulta} - {self.fecha_consulta}"

class IACache(models.Model):
    """
    Caché de respuestas de IA para evitar consultas repetidas
    """
    id_cache = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        db_column='ticket_id',
        related_name='cache_ia'
    )
    tipo_consulta = models.CharField(max_length=20)
    respuesta_cache = models.TextField()
    hash_contenido = models.CharField(
        max_length=64,
        help_text='Hash del título+descripción para detectar cambios'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    
    class Meta:
        managed = True  # Django manejará esta tabla
        db_table = 'ia_cache'
        verbose_name = 'Caché IA'
        verbose_name_plural = 'Caché IA'
        unique_together = ['ticket', 'tipo_consulta']
    
    def __str__(self):
        return f"Cache Ticket #{self.ticket_id} - {self.tipo_consulta}"
    
    @property
    def esta_vigente(self):
        from django.utils import timezone
        return timezone.now() < self.fecha_expiracion