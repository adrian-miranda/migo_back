"""
Vistas para el sistema de tickets
"""
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q

from .models import (
    CategoriaTicket,
    EstadoTicket,
    PrioridadTicket,
    Ticket,
    HistorialTicket
)
from .serializers import (
    CategoriaTicketSerializer,
    EstadoTicketSerializer,
    PrioridadTicketSerializer,
    TicketListSerializer,
    TicketDetailSerializer,
    TicketCreateSerializer,
    TicketUpdateSerializer,
    HistorialTicketSerializer
)
from authentication.models import Usuarios


# ============================================
# CATÁLOGOS (Categorías, Estados, Prioridades)
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])
def listar_categorias(request):
    """Obtener todas las categorías de tickets"""
    try:
        categorias = CategoriaTicket.objects.all()
        serializer = CategoriaTicketSerializer(categorias, many=True)
        
        return Response({
            'success': True,
            'categorias': serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_estados(request):
    """Obtener todos los estados de tickets"""
    try:
        estados = EstadoTicket.objects.all()
        serializer = EstadoTicketSerializer(estados, many=True)
        
        return Response({
            'success': True,
            'estados': serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_prioridades(request):
    """Obtener todas las prioridades de tickets"""
    try:
        prioridades = PrioridadTicket.objects.all()
        serializer = PrioridadTicketSerializer(prioridades, many=True)
        
        return Response({
            'success': True,
            'prioridades': serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================
# TICKETS - CRUD
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])
def listar_tickets(request):
    """
    Listar tickets según el rol del usuario
    - Admin/Gerente: ve todos los tickets
    - Técnico: ve tickets asignados a él
    - Trabajador: ve solo sus tickets
    """
    try:
        # TODO: Obtener usuario del token
        # Por ahora, recibir user_id por query param para pruebas
        user_id = request.query_params.get('user_id')
        
        if not user_id:
            tickets = Ticket.objects.all()
        else:
            usuario = Usuarios.objects.get(id_usuarios=user_id)
            rol_id = usuario.roles_id_roles.id_roles
            
            if rol_id == 3:  # Administrador
                tickets = Ticket.objects.all()
            elif rol_id == 1:  # Técnico
                tickets = Ticket.objects.filter(tecnico_asignado_id=user_id)
            elif rol_id == 2:  # Trabajador
                tickets = Ticket.objects.filter(usuario_creador_id=user_id)
            else:
                tickets = Ticket.objects.none()
        
        # Filtros opcionales
        estado = request.query_params.get('estado')
        if estado:
            tickets = tickets.filter(estado_id=estado)
        
        prioridad = request.query_params.get('prioridad')
        if prioridad:
            tickets = tickets.filter(prioridad_id=prioridad)
        
        categoria = request.query_params.get('categoria')
        if categoria:
            tickets = tickets.filter(categoria_id=categoria)
        
        serializer = TicketListSerializer(tickets, many=True)
        
        return Response({
            'success': True,
            'count': tickets.count(),
            'tickets': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Usuarios.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_ticket(request, id_ticket):
    """Obtener detalle de un ticket específico"""
    try:
        ticket = Ticket.objects.select_related(
            'categoria_id',
            'estado_id',
            'prioridad_id',
            'usuario_creador_id',
            'tecnico_asignado_id'
        ).get(id_ticket=id_ticket)
        
        serializer = TicketDetailSerializer(ticket)
        
        return Response({
            'success': True,
            'ticket': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Ticket.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Ticket no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def crear_ticket(request):
    """Crear un nuevo ticket"""
    try:
        serializer = TicketCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Datos inválidos',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # TODO: Obtener usuario del token
        # Por ahora, recibir user_id del request
        user_id = request.data.get('usuario_creador_id')
        
        if not user_id:
            return Response({
                'success': False,
                'error': 'usuario_creador_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        usuario = Usuarios.objects.get(id_usuarios=user_id)
        
        # Crear ticket
        ticket = serializer.save(
            usuario_creador_id=usuario,
            estado_id_id=1  # Estado: Abierto
        )
        
        # Serializar respuesta
        response_serializer = TicketDetailSerializer(ticket)
        
        return Response({
            'success': True,
            'message': 'Ticket creado exitosamente',
            'ticket': response_serializer.data
        }, status=status.HTTP_201_CREATED)
        
    except Usuarios.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([AllowAny])
def actualizar_ticket(request, id_ticket):
    """Actualizar un ticket existente"""
    try:
        ticket = Ticket.objects.get(id_ticket=id_ticket)
        
        # Guardar estado anterior para historial
        estado_anterior = ticket.estado_id
        
        serializer = TicketUpdateSerializer(ticket, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Datos inválidos',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Actualizar fechas según cambios
        if 'tecnico_asignado_id' in request.data and not ticket.fecha_asignacion:
            serializer.validated_data['fecha_asignacion'] = timezone.now()
            serializer.validated_data['estado_id_id'] = 2  # En Proceso
        
        if 'estado_id' in request.data:
            nuevo_estado = request.data['estado_id']
            if nuevo_estado == 3 and not ticket.fecha_resolucion:  # Resuelto
                serializer.validated_data['fecha_resolucion'] = timezone.now()
            elif nuevo_estado == 4 and not ticket.fecha_cierre:  # Cerrado
                serializer.validated_data['fecha_cierre'] = timezone.now()
        
        ticket_actualizado = serializer.save()
        
        # Crear entrada en historial si cambió el estado
        if estado_anterior.id_estado_ticket != ticket_actualizado.estado_id.id_estado_ticket:
            HistorialTicket.objects.create(
                ticket_id=ticket_actualizado,
                usuario_id=ticket_actualizado.usuario_creador_id,  # TODO: usar usuario del token
                estado_anterior_id=estado_anterior,
                estado_nuevo_id=ticket_actualizado.estado_id,
                comentario=f'Estado cambiado de "{estado_anterior.nombre_estado}" a "{ticket_actualizado.estado_id.nombre_estado}"'
            )
        
        response_serializer = TicketDetailSerializer(ticket_actualizado)
        
        return Response({
            'success': True,
            'message': 'Ticket actualizado exitosamente',
            'ticket': response_serializer.data
        }, status=status.HTTP_200_OK)
        
    except Ticket.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Ticket no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def eliminar_ticket(request, id_ticket):
    """Eliminar un ticket (solo administradores)"""
    try:
        ticket = Ticket.objects.get(id_ticket=id_ticket)
        ticket.delete()
        
        return Response({
            'success': True,
            'message': 'Ticket eliminado exitosamente'
        }, status=status.HTTP_200_OK)
        
    except Ticket.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Ticket no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================
# HISTORIAL
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_historial_ticket(request, id_ticket):
    """Obtener historial de cambios de un ticket"""
    try:
        historial = HistorialTicket.objects.filter(ticket_id=id_ticket).order_by('-fecha_cambio')
        serializer = HistorialTicketSerializer(historial, many=True)
        
        return Response({
            'success': True,
            'count': historial.count(),
            'historial': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================
# ESTADÍSTICAS
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])
def estadisticas_tickets(request):
    """Obtener estadísticas generales de tickets"""
    try:
        total = Ticket.objects.count()
        abiertos = Ticket.objects.filter(estado_id=1).count()
        en_proceso = Ticket.objects.filter(estado_id=2).count()
        resueltos = Ticket.objects.filter(estado_id=3).count()
        cerrados = Ticket.objects.filter(estado_id=4).count()
        
        por_prioridad = {}
        for prioridad in PrioridadTicket.objects.all():
            count = Ticket.objects.filter(prioridad_id=prioridad.id_prioridad_ticket).count()
            por_prioridad[prioridad.nombre_prioridad] = count
        
        por_categoria = {}
        for categoria in CategoriaTicket.objects.all():
            count = Ticket.objects.filter(categoria_id=categoria.id_categoria_ticket).count()
            por_categoria[categoria.nombre_categoria] = count
        
        return Response({
            'success': True,
            'estadisticas': {
                'total': total,
                'por_estado': {
                    'abiertos': abiertos,
                    'en_proceso': en_proceso,
                    'resueltos': resueltos,
                    'cerrados': cerrados
                },
                'por_prioridad': por_prioridad,
                'por_categoria': por_categoria
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)