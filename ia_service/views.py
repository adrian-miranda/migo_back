"""
Views para el servicio de IA de MIGO
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count

from .models import IAFeedback, IAMetricasTecnico, IAConsultasLog, IAConfiguracion
from .services import (
    GuiaSolucionService,
    RecomendadorTecnicoService,
    DetectorPatronesService,
    CalculadorMetricasService,
    PriorizadorTicketService
)
from .serializers import (
    IAFeedbackSerializer,
    IAFeedbackCreateSerializer,
    IAMetricasTecnicoSerializer,
    IAConsultasLogSerializer,
    IAConfiguracionSerializer,
    GuiaSolucionRequestSerializer,
    RecomendarTecnicoRequestSerializer,
    AnalizarPatronesRequestSerializer
)
from .authentication import AuthMixin, get_usuario_from_token


# =============================================================================
# VISTAS PARA TÉCNICOS
# =============================================================================

class GuiaSolucionView(AuthMixin, APIView):
    """
    POST: Genera una guía de solución para un ticket
    Requiere: Técnico o Administrador
    """
    
    def post(self, request):
        usuario, error = self.requiere_tecnico(request)
        if error:
            return error
        
        serializer = GuiaSolucionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        ticket_id = serializer.validated_data['ticket_id']
        
        service = GuiaSolucionService()
        resultado = service.generar_guia(ticket_id, usuario.id_usuarios)
        
        if resultado['success']:
            return Response(resultado, status=status.HTTP_200_OK)
        else:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)


class TicketsSimilaresView(AuthMixin, APIView):
    """
    GET: Obtiene tickets similares resueltos
    Requiere: Técnico o Administrador
    """
    
    def get(self, request, ticket_id):
        usuario, error = self.requiere_tecnico(request)
        if error:
            return error
        
        from tickets.models import Ticket
        
        try:
            ticket = Ticket.objects.select_related('categoria_id').get(id_ticket=ticket_id)
        except Ticket.DoesNotExist:
            return Response(
                {'error': 'Ticket no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        similares = Ticket.objects.filter(
            categoria_id=ticket.categoria_id,
            estado_id__in=[3, 4],
            solucion__isnull=False
        ).exclude(
            id_ticket=ticket_id
        ).values(
            'id_ticket',
            'titulo',
            'descripcion',
            'solucion',
            'fecha_resolucion'
        ).order_by('-fecha_resolucion')[:5]
        
        return Response({
            'ticket_id': ticket_id,
            'categoria': ticket.categoria_id.nombre_categoria,
            'tickets_similares': list(similares)
        })


class FeedbackIAView(AuthMixin, APIView):
    """
    POST: Registrar feedback sobre la ayuda de IA
    GET: Obtener feedback del técnico actual
    Requiere: Técnico o Administrador
    """
    
    def post(self, request):
        usuario, error = self.requiere_tecnico(request)
        if error:
            return error
        
        serializer = IAFeedbackCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        feedback = IAFeedback.objects.create(
            ticket_id=serializer.validated_data['ticket_id'],
            tecnico_id=usuario.id_usuarios,
            fue_util=serializer.validated_data['fue_util'],
            comentario=serializer.validated_data.get('comentario', ''),
            tipo_consulta=serializer.validated_data.get('tipo_consulta', 'guia_solucion')
        )
        
        from tickets.models import Ticket
        try:
            ticket = Ticket.objects.get(id_ticket=serializer.validated_data['ticket_id'])
            CalculadorMetricasService.actualizar_metricas_tecnico(
                usuario.id_usuarios,
                ticket.categoria_id.id_categoria_ticket
            )
        except Ticket.DoesNotExist:
            pass
        
        return Response(
            IAFeedbackSerializer(feedback).data,
            status=status.HTTP_201_CREATED
        )
    
    def get(self, request):
        usuario, error = self.requiere_tecnico(request)
        if error:
            return error
        
        # Técnico ve solo su feedback, admin ve todo
        feedbacks = IAFeedback.objects.all()
        if usuario.roles_id_roles.id_roles != 3:  # No es admin
            feedbacks = feedbacks.filter(tecnico_id=usuario.id_usuarios)
        
        feedbacks = feedbacks.order_by('-fecha_feedback')[:20]
        
        return Response(IAFeedbackSerializer(feedbacks, many=True).data)


class PriorizarTicketView(AuthMixin, APIView):
    """
    POST: Sugiere prioridad para un ticket usando IA
    Requiere: Técnico o Administrador
    """
    
    def post(self, request):
        usuario, error = self.requiere_tecnico(request)
        if error:
            return error
        
        ticket_id = request.data.get('ticket_id')
        if not ticket_id:
            return Response(
                {'error': 'Se requiere ticket_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = PriorizadorTicketService()
        resultado = service.sugerir_prioridad(ticket_id, usuario.id_usuarios)
        
        if resultado['success']:
            return Response(resultado, status=status.HTTP_200_OK)
        else:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)

# =============================================================================
# VISTAS PARA ADMINISTRADOR
# =============================================================================

class RecomendarTecnicoView(AuthMixin, APIView):
    """
    POST: Recomienda el mejor técnico para un ticket
    Requiere: Administrador
    """
    
    def post(self, request):
        usuario, error = self.requiere_admin(request)
        if error:
            return error
        
        serializer = RecomendarTecnicoRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        ticket_id = serializer.validated_data['ticket_id']
        
        service = RecomendadorTecnicoService()
        resultado = service.recomendar_tecnico(ticket_id, usuario.id_usuarios)
        
        if resultado['success']:
            return Response(resultado, status=status.HTTP_200_OK)
        else:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)


class AnalizarPatronesView(AuthMixin, APIView):
    """
    POST: Analiza patrones en tickets
    Requiere: Administrador
    """
    
    def post(self, request):
        usuario, error = self.requiere_admin(request)
        if error:
            return error
        
        serializer = AnalizarPatronesRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        dias = serializer.validated_data.get('dias', 30)
        
        service = DetectorPatronesService()
        resultado = service.analizar_patrones(usuario.id_usuarios, dias)
        
        if resultado['success']:
            return Response(resultado, status=status.HTTP_200_OK)
        else:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)


class MetricasTecnicosView(AuthMixin, APIView):
    """
    GET: Obtener métricas de todos los técnicos
    POST: Recalcular métricas
    Requiere: Administrador
    """
    
    def get(self, request):
        usuario, error = self.requiere_admin(request)
        if error:
            return error
        
        categoria_id = request.query_params.get('categoria_id')
        tecnico_id = request.query_params.get('tecnico_id')
        
        metricas = IAMetricasTecnico.objects.select_related(
            'tecnico',
            'tecnico__personas_id_personas',
            'categoria'
        )
        
        if categoria_id:
            metricas = metricas.filter(categoria_id=categoria_id)
        if tecnico_id:
            metricas = metricas.filter(tecnico_id=tecnico_id)
        
        metricas = metricas.order_by('-tasa_resolucion')
        
        return Response(IAMetricasTecnicoSerializer(metricas, many=True).data)
    
    def post(self, request):
        usuario, error = self.requiere_admin(request)
        if error:
            return error
        
        actualizadas = CalculadorMetricasService.actualizar_todas_metricas()
        
        return Response({
            'success': True,
            'mensaje': f'Se actualizaron {actualizadas} métricas',
            'metricas_actualizadas': actualizadas
        })


class InsightsCapacitacionView(AuthMixin, APIView):
    """
    GET: Obtener insights para capacitación de técnicos
    Requiere: Administrador
    """
    
    def get(self, request):
        usuario, error = self.requiere_admin(request)
        if error:
            return error
        
        from tickets.models import Ticket, CategoriaTicket
        from authentication.models import Usuarios
        from django.db.models import Count
        
        metricas_bajas = IAMetricasTecnico.objects.filter(
            tasa_resolucion__lt=70,
            tickets_totales__gte=3
        ).select_related(
            'tecnico__personas_id_personas',
            'categoria'
        )
        
        capacitaciones_sugeridas = []
        for m in metricas_bajas:
            nombre = f"{m.tecnico.personas_id_personas.primer_nombre} {m.tecnico.personas_id_personas.primer_apellido}"
            capacitaciones_sugeridas.append({
                'tecnico_id': m.tecnico_id,
                'tecnico_nombre': nombre,
                'categoria': m.categoria.nombre_categoria,
                'tasa_resolucion': float(m.tasa_resolucion) if m.tasa_resolucion else 0,
                'tickets_totales': m.tickets_totales,
                'sugerencia': f"Capacitar en {m.categoria.nombre_categoria}"
            })
        
        categorias_problematicas = Ticket.objects.filter(
            estado_id__in=[1, 2]
        ).values(
            'categoria_id__nombre_categoria'
        ).annotate(
            sin_resolver=Count('id_ticket')
        ).order_by('-sin_resolver')[:5]
        
        feedback_negativo = IAFeedback.objects.filter(
            fue_util=False
        ).values(
            'tecnico_id'
        ).annotate(
            total_negativo=Count('id_feedback')
        ).order_by('-total_negativo')[:5]
        
        return Response({
            'capacitaciones_sugeridas': capacitaciones_sugeridas,
            'categorias_problematicas': list(categorias_problematicas),
            'tecnicos_con_feedback_negativo': list(feedback_negativo)
        })


# =============================================================================
# VISTAS DE CONFIGURACIÓN (Solo Admin)
# =============================================================================

class ConfiguracionIAView(AuthMixin, APIView):
    """
    GET: Obtener configuración actual de IA
    PUT: Actualizar configuración
    Requiere: Administrador
    """
    
    def get(self, request):
        usuario, error = self.requiere_admin(request)
        if error:
            return error
        
        configs = IAConfiguracion.objects.all()
        return Response(IAConfiguracionSerializer(configs, many=True).data)
    
    def put(self, request):
        usuario, error = self.requiere_admin(request)
        if error:
            return error
        
        clave = request.data.get('clave')
        valor = request.data.get('valor')
        
        if not clave or valor is None:
            return Response(
                {'error': 'Se requiere clave y valor'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            config = IAConfiguracion.objects.get(clave=clave)
            config.valor = valor
            config.save()
            return Response(IAConfiguracionSerializer(config).data)
        except IAConfiguracion.DoesNotExist:
            return Response(
                {'error': f'Configuración "{clave}" no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )


class HistorialConsultasView(AuthMixin, APIView):
    """
    GET: Obtener historial de consultas a la IA
    Requiere: Administrador
    """
    
    def get(self, request):
        usuario, error = self.requiere_admin(request)
        if error:
            return error
        
        limite = int(request.query_params.get('limite', 50))
        tipo = request.query_params.get('tipo')
        
        consultas = IAConsultasLog.objects.select_related('ticket', 'usuario')
        
        if tipo:
            consultas = consultas.filter(tipo_consulta=tipo)
        
        consultas = consultas.order_by('-fecha_consulta')[:limite]
        
        return Response(IAConsultasLogSerializer(consultas, many=True).data)


# =============================================================================
# VISTA DE ESTADO (Público)
# =============================================================================


class ConsultasRestantesView(AuthMixin, APIView):
    """
    GET: Obtener consultas restantes del usuario actual
    """
    
    def get(self, request):
        usuario, error = self.requiere_auth(request)
        if error:
            return error
        
        from django.utils import timezone
        
        hoy = timezone.now().date()
        limite_diario = int(IAConfiguracion.get_valor('limite_diario', '50'))
        
        consultas_hoy = IAConsultasLog.objects.filter(
            usuario_id=usuario.id_usuarios,
            fecha_consulta__date=hoy
        ).count()
        
        restantes = max(0, limite_diario - consultas_hoy)
        
        return Response({
            'usuario_id': usuario.id_usuarios,
            'limite_diario': limite_diario,
            'consultas_realizadas': consultas_hoy,
            'consultas_restantes': restantes,
            'fecha': str(hoy)
        })

@api_view(['GET'])
def ia_status(request):
    """
    Verificar estado del servicio de IA (público)
    """
    from django.utils import timezone
    from django.db.models import Q
    
    activo = IAConfiguracion.get_valor('activo', '0') == '1'
    modelo = IAConfiguracion.get_valor('modelo_openai', 'no configurado')
    
    total_consultas = IAConsultasLog.objects.count()
    consultas_hoy = IAConsultasLog.objects.filter(
        fecha_consulta__date=timezone.now().date()
    ).count()
    
    feedback_stats = IAFeedback.objects.aggregate(
        total=Count('id_feedback'),
        positivos=Count('id_feedback', filter=Q(fue_util=True))
    )
    
    tasa_utilidad = 0
    if feedback_stats['total'] > 0:
        tasa_utilidad = round(feedback_stats['positivos'] / feedback_stats['total'] * 100, 2)
    
    return Response({
        'servicio_activo': activo,
        'modelo': modelo,
        'estadisticas': {
            'total_consultas': total_consultas,
            'consultas_hoy': consultas_hoy,
            'total_feedbacks': feedback_stats['total'],
            'tasa_utilidad': tasa_utilidad
        }
    })