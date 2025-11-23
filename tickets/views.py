"""
Vistas para el sistema de tickets
"""
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

from .models import (
    CategoriaTicket,
    EstadoTicket,
    PrioridadTicket,
    Ticket,
    HistorialTicket,
    CalificacionTicket
)
from .serializers import (
    CategoriaTicketSerializer,
    EstadoTicketSerializer,
    PrioridadTicketSerializer,
    TicketListSerializer,
    TicketDetailSerializer,
    TicketCreateSerializer,
    HistorialTicketSerializer,
    CalificacionTicketSerializer,
    CalificacionCreateSerializer
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


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def crear_ticket(request):
    """Crear un nuevo ticket con prioridad automática"""
    try:
        # Obtener datos del request
        titulo = request.data.get('titulo')
        descripcion = request.data.get('descripcion')
        categoria_id = request.data.get('categoria_id')
        user_id = request.data.get('usuario_creador_id')
        
        # Validaciones básicas
        if not titulo or not descripcion or not categoria_id or not user_id:
            return Response({
                'success': False,
                'error': 'Todos los campos son obligatorios'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener usuario con cargo
        usuario = Usuarios.objects.select_related('cargos_id_cargos').get(id_usuarios=user_id)
        
        # Obtener categoría
        categoria = CategoriaTicket.objects.get(id_categoria_ticket=categoria_id)
        
        # CALCULAR PRIORIDAD AUTOMÁTICAMENTE
        peso_cargo = usuario.cargos_id_cargos.peso_prioridad
        multiplicador_categoria = float(categoria.multiplicador_prioridad)
        
        # Calcular puntaje de prioridad
        puntaje_prioridad = peso_cargo * multiplicador_categoria
        
        # Determinar nivel de prioridad basado en puntaje
        if puntaje_prioridad >= 6.0:
            prioridad_id = 4  # Urgente
        elif puntaje_prioridad >= 4.0:
            prioridad_id = 3  # Alta
        elif puntaje_prioridad >= 2.0:
            prioridad_id = 2  # Media
        else:
            prioridad_id = 1  # Baja
        
        # Crear ticket
        ticket = Ticket.objects.create(
            titulo=titulo,
            descripcion=descripcion,
            categoria_id_id=categoria_id,
            prioridad_id_id=prioridad_id,
            usuario_creador_id_id=user_id,
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
    except CategoriaTicket.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Categoría no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        print("Error completo:", traceback.format_exc())
        return Response({
            'success': False,
            'error': f'Error en el servidor: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    """Crear un nuevo ticket con prioridad automática"""
    try:
        serializer = TicketCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'error': 'Datos inválidos',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener usuario
        user_id = request.data.get('usuario_creador_id')
        
        if not user_id:
            return Response({
                'success': False,
                'error': 'usuario_creador_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        usuario = Usuarios.objects.select_related('cargos_id_cargos').get(id_usuarios=user_id)
        
        # Obtener categoría
        categoria_id = serializer.validated_data.get('categoria_id')
        categoria = CategoriaTicket.objects.get(id_categoria_ticket=categoria_id.id_categoria_ticket)
        
        # CALCULAR PRIORIDAD AUTOMÁTICAMENTE
        peso_cargo = usuario.cargos_id_cargos.peso_prioridad
        multiplicador_categoria = float(categoria.multiplicador_prioridad)
        
        # Calcular puntaje de prioridad
        puntaje_prioridad = peso_cargo * multiplicador_categoria
        
        # Determinar nivel de prioridad basado en puntaje
        if puntaje_prioridad >= 6.0:
            prioridad_id = 4  # Urgente
        elif puntaje_prioridad >= 4.0:
            prioridad_id = 3  # Alta
        elif puntaje_prioridad >= 2.0:
            prioridad_id = 2  # Media
        else:
            prioridad_id = 1  # Baja
        
        # Crear ticket con prioridad calculada
        ticket = serializer.save(
            usuario_creador_id=usuario,
            estado_id_id=1,  # Estado: Abierto
            prioridad_id_id=prioridad_id  # Prioridad automática
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
    except CategoriaTicket.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Categoría no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
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


@csrf_exempt
@api_view(['PUT', 'PATCH'])
@permission_classes([AllowAny])
def actualizar_ticket(request, id_ticket):
    """Actualizar un ticket existente"""
    try:
        ticket = Ticket.objects.get(id_ticket=id_ticket)
        
        # ❌ BLOQUEO: No se puede modificar un ticket cerrado
        if ticket.estado_id.id_estado_ticket == 4:
            return Response({
                'success': False,
                'error': 'No se puede modificar un ticket cerrado'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Guardar estado anterior para historial
        estado_anterior = ticket.estado_id
        
        # ❌ BLOQUEO: No se puede establecer manualmente el estado "Cerrado"
        if 'estado_id' in request.data and int(request.data['estado_id']) == 4:
            return Response({
                'success': False,
                'error': 'El estado "Cerrado" solo se establece automáticamente después de calificar'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Asignar técnico
        if 'tecnico_asignado_id' in request.data:
            tecnico_id = request.data['tecnico_asignado_id']
            if tecnico_id:
                ticket.tecnico_asignado_id_id = tecnico_id
                if not ticket.fecha_asignacion:
                    ticket.fecha_asignacion = timezone.now()
                    # Si está en Abierto, cambiar a En Proceso automáticamente
                    if ticket.estado_id.id_estado_ticket == 1:
                        ticket.estado_id_id = 2  # En Proceso
            else:
                ticket.tecnico_asignado_id = None
        
        # Cambiar estado
        if 'estado_id' in request.data:
            nuevo_estado_id = int(request.data['estado_id'])
            
            # Validar que si cambia a Resuelto (3), debe tener solución
            if nuevo_estado_id == 3:
                solucion = request.data.get('solucion', ticket.solucion)
                if not solucion or len(solucion.strip()) < 10:
                    return Response({
                        'success': False,
                        'error': 'Debe ingresar una solución de al menos 10 caracteres para cambiar a "Resuelto"'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # ❌ BLOQUEO: No se puede volver a estados anteriores desde Resuelto
            if ticket.estado_id.id_estado_ticket == 3 and nuevo_estado_id < 3:
                return Response({
                    'success': False,
                    'error': 'No se puede volver a estados anteriores desde "Resuelto"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            ticket.estado_id_id = nuevo_estado_id
            
            # Actualizar fechas según el estado
            if nuevo_estado_id == 3 and not ticket.fecha_resolucion:  # Resuelto
                ticket.fecha_resolucion = timezone.now()
            elif nuevo_estado_id == 5:  # Cancelado
                # No actualizar fecha_cierre para cancelados
                pass
        
        # Actualizar solución
        if 'solucion' in request.data:
            ticket.solucion = request.data['solucion']
        
        # Guardar cambios
        ticket.save()
        
        # Crear entrada en historial si cambió el estado
        if 'estado_id' in request.data and estado_anterior.id_estado_ticket != ticket.estado_id.id_estado_ticket:
            comentario_historial = f'Estado cambiado de "{estado_anterior.nombre_estado}" a "{ticket.estado_id.nombre_estado}"'
            
            # Si se canceló, agregar mensaje especial
            if ticket.estado_id.id_estado_ticket == 5:
                motivo_cancelacion = request.data.get('motivo_cancelacion', 'Sin motivo especificado')
                comentario_historial = f'Ticket cancelado. Motivo: {motivo_cancelacion}'
            
            HistorialTicket.objects.create(
                ticket_id=ticket,
                usuario_id=ticket.usuario_creador_id,
                estado_anterior_id=estado_anterior,
                estado_nuevo_id=ticket.estado_id,
                comentario=comentario_historial
            )
        
        # Crear historial si se asignó técnico por primera vez
        if 'tecnico_asignado_id' in request.data and request.data['tecnico_asignado_id'] and not estado_anterior.id_estado_ticket == ticket.estado_id.id_estado_ticket:
            try:
                tecnico = Usuarios.objects.get(id_usuarios=request.data['tecnico_asignado_id'])
                HistorialTicket.objects.create(
                    ticket_id=ticket,
                    usuario_id=ticket.usuario_creador_id,
                    estado_anterior_id=estado_anterior,
                    estado_nuevo_id=ticket.estado_id,
                    comentario=f'Ticket asignado a {tecnico.personas_id_personas.nombre_completo}'
                )
            except:
                pass
        
        # Serializar respuesta
        response_serializer = TicketDetailSerializer(ticket)
        
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
        import traceback
        print("Error completo:", traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
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
    


@api_view(['GET'])
@permission_classes([AllowAny])
def mis_tickets(request):
    """
    Obtener solo los tickets del usuario autenticado (trabajador)
    """
    try:
        # Obtener user_id del query param (temporal, luego será del token)
        user_id = request.query_params.get('user_id')
        
        if not user_id:
            return Response({
                'success': False,
                'error': 'user_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener tickets del usuario
        tickets = Ticket.objects.filter(
            usuario_creador_id=user_id
        ).select_related(
            'categoria_id',
            'estado_id',
            'prioridad_id',
            'tecnico_asignado_id'
        ).order_by('-fecha_creacion')
        
        # Filtros opcionales
        estado = request.query_params.get('estado')
        if estado:
            tickets = tickets.filter(estado_id__nombre_estado=estado)
        
        categoria = request.query_params.get('categoria')
        if categoria:
            tickets = tickets.filter(categoria_id__nombre_categoria=categoria)
        
        prioridad = request.query_params.get('prioridad')
        if prioridad:
            tickets = tickets.filter(prioridad_id__nombre_prioridad=prioridad)
        
        serializer = TicketListSerializer(tickets, many=True)
        
        return Response({
            'success': True,
            'count': tickets.count(),
            'tickets': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def cancelar_ticket(request, id_ticket):
    """
    Cancelar un ticket (solo si está Abierto y es el creador)
    """
    try:
        ticket = Ticket.objects.get(id_ticket=id_ticket)
        
        # Obtener usuario del request
        user_id = request.data.get('usuario_id')
        
        if not user_id:
            return Response({
                'success': False,
                'error': 'usuario_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar que el usuario sea el creador
        if ticket.usuario_creador_id.id_usuarios != int(user_id):
            return Response({
                'success': False,
                'error': 'Solo el creador puede cancelar el ticket'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Verificar que el ticket esté en estado "Abierto"
        if ticket.estado_id.id_estado_ticket != 1:
            return Response({
                'success': False,
                'error': 'Solo se pueden cancelar tickets en estado Abierto'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Guardar estado anterior para historial
        estado_anterior = ticket.estado_id
        
        # Cambiar estado a Cancelado (id: 5)
        ticket.estado_id_id = 5
        ticket.save()
        
        # Registrar en historial
        HistorialTicket.objects.create(
            ticket_id=ticket,
            usuario_id=ticket.usuario_creador_id,
            estado_anterior_id=estado_anterior,
            estado_nuevo_id_id=5,
            comentario='Ticket cancelado por el usuario creador'
        )
        
        return Response({
            'success': True,
            'message': 'Ticket cancelado exitosamente'
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

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def mis_tickets(request):
    """
    Obtener todos los tickets de un usuario
    """
    try:
        user_id = request.GET.get('user_id')
        
        if not user_id:
            return Response({
                'success': False,
                'error': 'user_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener tickets del usuario
        tickets = Ticket.objects.filter(
            usuario_creador_id=user_id
        ).select_related(
            'categoria_id',
            'estado_id',
            'prioridad_id',
            'tecnico_asignado_id',
            'tecnico_asignado_id__personas_id_personas'
        ).order_by('-fecha_creacion')
        
        # Serializar
        serializer = TicketListSerializer(tickets, many=True)
        
        return Response({
            'success': True,
            'tickets': serializer.data,
            'total': tickets.count()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def tickets_pendientes(request):
    """
    Obtener tickets pendientes (Abierto o En Proceso) de un usuario
    """
    try:
        user_id = request.GET.get('user_id')
        
        if not user_id:
            return Response({
                'success': False,
                'error': 'user_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener tickets pendientes (estado 1=Abierto, 2=En Proceso)
        tickets = Ticket.objects.filter(
            usuario_creador_id=user_id,
            estado_id__in=[1, 2]
        ).select_related(
            'categoria_id',
            'estado_id',
            'prioridad_id',
            'tecnico_asignado_id',
            'tecnico_asignado_id__personas_id_personas'
        ).order_by('-fecha_creacion')
        
        # Serializar
        serializer = TicketListSerializer(tickets, many=True)
        
        return Response({
            'success': True,
            'tickets': serializer.data,
            'total': tickets.count()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def calificar_ticket(request, id_ticket):
    """
    Calificar un ticket resuelto (cambia automáticamente a Cerrado)
    """
    try:
        ticket = Ticket.objects.get(id_ticket=id_ticket)
        user_id = request.data.get('usuario_id')
        
        if not user_id:
            return Response({
                'success': False,
                'error': 'usuario_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar que el ticket esté RESUELTO
        if ticket.estado_id.id_estado_ticket != 3:
            return Response({
                'success': False,
                'error': 'Solo se pueden calificar tickets en estado "Resuelto"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar que sea el usuario creador
        if ticket.usuario_creador_id.id_usuarios != int(user_id):
            return Response({
                'success': False,
                'error': 'Solo el creador del ticket puede calificarlo'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Verificar que NO tenga calificación previa
        if CalificacionTicket.objects.filter(ticket_id=ticket).exists():
            return Response({
                'success': False,
                'error': 'Este ticket ya fue calificado'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear calificación
        serializer = CalificacionCreateSerializer(data=request.data)
        if serializer.is_valid():
            calificacion = serializer.save(
                ticket_id=ticket,
                usuario_id=ticket.usuario_creador_id
            )
            
            # ✅ CAMBIAR AUTOMÁTICAMENTE A CERRADO
            estado_anterior = ticket.estado_id
            ticket.estado_id_id = 4  # Cerrado
            ticket.fecha_cierre = timezone.now()
            ticket.save()
            
            # Registrar en historial
            HistorialTicket.objects.create(
                ticket_id=ticket,
                usuario_id=ticket.usuario_creador_id,
                estado_anterior_id=estado_anterior,
                estado_nuevo_id_id=4,
                comentario=f'Ticket cerrado automáticamente después de calificación ({calificacion.calificacion}/5 estrellas)'
            )
            
            response_serializer = CalificacionTicketSerializer(calificacion)
            
            return Response({
                'success': True,
                'message': 'Calificación registrada exitosamente. El ticket ha sido cerrado.',
                'calificacion': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Ticket.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Ticket no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        print("Error completo:", traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_calificacion(request, id_ticket):
    """
    Obtener la calificación de un ticket
    """
    try:
        ticket = Ticket.objects.get(id_ticket=id_ticket)
        
        try:
            calificacion = CalificacionTicket.objects.get(ticket_id=ticket)
            serializer = CalificacionTicketSerializer(calificacion)
            
            return Response({
                'success': True,
                'calificacion': serializer.data
            }, status=status.HTTP_200_OK)
        except CalificacionTicket.DoesNotExist:
            return Response({
                'success': True,
                'calificacion': None
            }, status=status.HTTP_200_OK)
        
    except Ticket.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Ticket no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def tickets_sin_calificar(request):
    """
    Obtener tickets resueltos sin calificar del usuario
    """
    try:
        user_id = request.GET.get('user_id')
        
        if not user_id:
            return Response({
                'success': False,
                'error': 'user_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Tickets RESUELTOS del usuario sin calificación
        tickets = Ticket.objects.filter(
            usuario_creador_id=user_id,
            estado_id=3  # Resuelto (no Cerrado)
        ).exclude(
            id_ticket__in=CalificacionTicket.objects.values_list('ticket_id', flat=True)
        ).order_by('-fecha_resolucion')
        
        serializer = TicketListSerializer(tickets, many=True)
        
        return Response({
            'success': True,
            'tickets': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        print("Error completo:", traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)