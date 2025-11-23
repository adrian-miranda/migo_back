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
    """Obtener estadísticas generales de tickets + satisfacción"""
    try:
        total = Ticket.objects.count()
        abiertos = Ticket.objects.filter(estado_id=1).count()
        en_proceso = Ticket.objects.filter(estado_id=2).count()
        resueltos = Ticket.objects.filter(estado_id=3).count()
        cerrados = Ticket.objects.filter(estado_id=4).count()
        cancelados = Ticket.objects.filter(estado_id=5).count()  # ← AGREGAR
        
        por_prioridad = {}
        for prioridad in PrioridadTicket.objects.all():
            count = Ticket.objects.filter(prioridad_id=prioridad.id_prioridad_ticket).count()
            por_prioridad[prioridad.nombre_prioridad] = count
        
        por_categoria = {}
        for categoria in CategoriaTicket.objects.all():
            count = Ticket.objects.filter(categoria_id=categoria.id_categoria_ticket).count()
            por_categoria[categoria.nombre_categoria] = count
        
        # ESTADÍSTICAS DE SATISFACCIÓN
        calificaciones = CalificacionTicket.objects.all()
        total_calificaciones = calificaciones.count()
        
        satisfaccion_data = None
        if total_calificaciones > 0:
            # Promedio general
            from django.db.models import Avg
            promedio = calificaciones.aggregate(Avg('calificacion'))['calificacion__avg']
            
            # Distribución por estrellas
            distribucion = {}
            for i in range(1, 6):
                distribucion[str(i)] = calificaciones.filter(calificacion=i).count()
            
            satisfaccion_data = {
                'promedio': round(promedio, 2),
                'total': total_calificaciones,
                'distribucion': distribucion
            }
        
        return Response({
            'success': True,
            'estadisticas': {
                'total': total,
                'por_estado': {
                    'abiertos': abiertos,
                    'en_proceso': en_proceso,
                    'resueltos': resueltos,
                    'cerrados': cerrados,
                    'cancelados': cancelados  # ← AGREGAR
                },
                'por_prioridad': por_prioridad,
                'por_categoria': por_categoria,
                'satisfaccion': satisfaccion_data
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        print("Error completo:", traceback.format_exc())
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
    
@api_view(['GET'])
@permission_classes([AllowAny])
def estadisticas_historicas(request):
    """
    Obtener estadísticas históricas basadas en el historial de tickets
    Parámetros opcionales:
    - fecha_inicio: YYYY-MM-DD (default: primer día del mes actual)
    - fecha_fin: YYYY-MM-DD (default: hoy)
    """
    try:
        from datetime import datetime, timedelta
        from django.db.models import Count, Avg, Q
        
        # Obtener parámetros de fecha
        fecha_inicio_param = request.GET.get('fecha_inicio')
        fecha_fin_param = request.GET.get('fecha_fin')
        
        # Si no hay parámetros, usar mes actual por defecto
        if not fecha_inicio_param or not fecha_fin_param:
            hoy = timezone.now()
            fecha_inicio = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            fecha_fin = hoy
        else:
            # Parsear fechas proporcionadas
            fecha_inicio = datetime.strptime(fecha_inicio_param, '%Y-%m-%d')
            fecha_fin = datetime.strptime(fecha_fin_param, '%Y-%m-%d')
            
            # Asegurar que tengan timezone
            if timezone.is_naive(fecha_inicio):
                fecha_inicio = timezone.make_aware(fecha_inicio)
            if timezone.is_naive(fecha_fin):
                fecha_fin = timezone.make_aware(fecha_fin)
            
            # Ajustar fecha_fin al final del día
            fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # ESTADÍSTICAS POR ESTADO (basadas en historial)
        # Contar tickets que PASARON a cada estado en el período
        
        # Tickets que pasaron a "Abierto" (creados)
        abiertos = HistorialTicket.objects.filter(
            estado_nuevo_id=1,
            fecha_cambio__range=[fecha_inicio, fecha_fin]
        ).values('ticket_id').distinct().count()
        
        # Tickets que pasaron a "En Proceso"
        en_proceso = HistorialTicket.objects.filter(
            estado_nuevo_id=2,
            fecha_cambio__range=[fecha_inicio, fecha_fin]
        ).values('ticket_id').distinct().count()
        
        # Tickets que pasaron a "Resuelto"
        resueltos = HistorialTicket.objects.filter(
            estado_nuevo_id=3,
            fecha_cambio__range=[fecha_inicio, fecha_fin]
        ).values('ticket_id').distinct().count()
        
        # Tickets que pasaron a "Cerrado"
        cerrados = HistorialTicket.objects.filter(
            estado_nuevo_id=4,
            fecha_cambio__range=[fecha_inicio, fecha_fin]
        ).values('ticket_id').distinct().count()
        
        # Tickets que pasaron a "Cancelado"
        cancelados = HistorialTicket.objects.filter(
            estado_nuevo_id=5,
            fecha_cambio__range=[fecha_inicio, fecha_fin]
        ).values('ticket_id').distinct().count()
        
        # ESTADÍSTICAS POR PRIORIDAD (tickets creados en el período)
        tickets_creados = Ticket.objects.filter(
            fecha_creacion__range=[fecha_inicio, fecha_fin]
        )
        
        por_prioridad = {}
        for prioridad in PrioridadTicket.objects.all():
            count = tickets_creados.filter(prioridad_id=prioridad.id_prioridad_ticket).count()
            por_prioridad[prioridad.nombre_prioridad] = count
        
        # ESTADÍSTICAS POR CATEGORÍA (tickets creados en el período)
        por_categoria = {}
        for categoria in CategoriaTicket.objects.all():
            count = tickets_creados.filter(categoria_id=categoria.id_categoria_ticket).count()
            por_categoria[categoria.nombre_categoria] = count
        
        # ESTADÍSTICAS DE SATISFACCIÓN (calificaciones en el período)
        calificaciones = CalificacionTicket.objects.filter(
            fecha_calificacion__range=[fecha_inicio, fecha_fin]
        )
        total_calificaciones = calificaciones.count()
        
        satisfaccion_data = None
        if total_calificaciones > 0:
            promedio = calificaciones.aggregate(Avg('calificacion'))['calificacion__avg']
            
            distribucion = {}
            for i in range(1, 6):
                distribucion[str(i)] = calificaciones.filter(calificacion=i).count()
            
            satisfaccion_data = {
                'promedio': round(promedio, 2),
                'total': total_calificaciones,
                'distribucion': distribucion
            }
        
        # MÉTRICAS ADICIONALES
        # Calcular total de tickets con actividad en el período
        tickets_con_actividad = set()
        for estado_id in [1, 2, 3, 4, 5]:
            tickets_estado = HistorialTicket.objects.filter(
                estado_nuevo_id=estado_id,
                fecha_cambio__range=[fecha_inicio, fecha_fin]
            ).values_list('ticket_id', flat=True)
            tickets_con_actividad.update(tickets_estado)
        
        total_actividad = len(tickets_con_actividad)
        total_tickets_periodo = abiertos  # Total de tickets creados en el período
        
        # Tasas basadas en tickets con actividad
        tasa_resolucion = round((resueltos / total_actividad * 100), 1) if total_actividad > 0 else 0
        tasa_cierre = round((cerrados / total_actividad * 100), 1) if total_actividad > 0 else 0
        tasa_cancelacion = round((cancelados / total_actividad * 100), 1) if total_actividad > 0 else 0
        tasa_calificacion = round((total_calificaciones / cerrados * 100), 1) if cerrados > 0 else 0
        
        return Response({
            'success': True,
            'periodo': {
                'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
                'fecha_fin': fecha_fin.strftime('%Y-%m-%d')
            },
            'estadisticas': {
                'total': total_tickets_periodo,
                'total_actividad': total_actividad,
                'por_estado': {
                    'abiertos': abiertos,
                    'en_proceso': en_proceso,
                    'resueltos': resueltos,
                    'cerrados': cerrados,
                    'cancelados': cancelados
                },
                'por_prioridad': por_prioridad,
                'por_categoria': por_categoria,
                'satisfaccion': satisfaccion_data,
                'metricas': {
                    'tasa_resolucion': tasa_resolucion,
                    'tasa_cierre': tasa_cierre,
                    'tasa_cancelacion': tasa_cancelacion,
                    'tasa_calificacion': tasa_calificacion
                }
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        print("Error completo:", traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

## PERFIL TECNICO
# ============================================
# ENDPOINTS PARA TÉCNICOS
# ============================================

@api_view(['GET'])
@permission_classes([AllowAny])
def tecnico_estadisticas(request):
    """
    Obtener estadísticas personales del técnico
    """
    try:
        tecnico_id = request.GET.get('tecnico_id')
        
        if not tecnico_id:
            return Response({
                'success': False,
                'error': 'tecnico_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from django.db.models import Avg, Count
        
        # Tickets asignados al técnico
        tickets_asignados = Ticket.objects.filter(tecnico_asignado_id=tecnico_id)
        
        # Conteos por estado
        total_asignados = tickets_asignados.count()
        en_proceso = tickets_asignados.filter(estado_id=2).count()
        resueltos = tickets_asignados.filter(estado_id=3).count()
        cerrados = tickets_asignados.filter(estado_id=4).count()
        
        # Tickets resueltos este mes (usar fecha_resolucion o fecha_cierre)
        hoy = timezone.now()
        inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        from django.db.models import Q
        resueltos_mes = tickets_asignados.filter(
            estado_id__in=[3, 4]
        ).filter(
            Q(fecha_resolucion__gte=inicio_mes) | Q(fecha_cierre__gte=inicio_mes)
        ).count()
        
        # Tiempo promedio de resolución (en horas)
        tickets_con_resolucion = tickets_asignados.filter(
            fecha_resolucion__isnull=False,
            fecha_asignacion__isnull=False
        )
        
        tiempo_promedio = 0
        if tickets_con_resolucion.exists():
            tiempos = []
            for ticket in tickets_con_resolucion:
                diferencia = (ticket.fecha_resolucion - ticket.fecha_asignacion).total_seconds() / 3600
                tiempos.append(diferencia)
            tiempo_promedio = round(sum(tiempos) / len(tiempos), 1) if tiempos else 0
        
        # Calificación promedio
        calificaciones = CalificacionTicket.objects.filter(
            ticket_id__tecnico_asignado_id=tecnico_id
        )
        total_calificaciones = calificaciones.count()
        promedio_calificacion = 0
        
        if total_calificaciones > 0:
            promedio_calificacion = round(
                calificaciones.aggregate(Avg('calificacion'))['calificacion__avg'], 
                2
            )
        
        # Distribución de calificaciones
        distribucion_calificaciones = {}
        for i in range(1, 6):
            distribucion_calificaciones[str(i)] = calificaciones.filter(calificacion=i).count()
        
        # Tickets por prioridad (activos)
        tickets_activos = tickets_asignados.filter(estado_id__in=[1, 2])
        por_prioridad = {
            'baja': tickets_activos.filter(prioridad_id=1).count(),
            'media': tickets_activos.filter(prioridad_id=2).count(),
            'alta': tickets_activos.filter(prioridad_id=3).count(),
            'urgente': tickets_activos.filter(prioridad_id=4).count()
        }
        
        return Response({
            'success': True,
            'estadisticas': {
                'total_asignados': total_asignados,
                'en_proceso': en_proceso,
                'resueltos': resueltos,
                'cerrados': cerrados,
                'completados': resueltos + cerrados,
                'resueltos_mes': resueltos_mes,
                'tiempo_promedio_horas': tiempo_promedio,
                'calificacion_promedio': promedio_calificacion,
                'total_calificaciones': total_calificaciones,
                'distribucion_calificaciones': distribucion_calificaciones,
                'por_prioridad': por_prioridad
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        print("Error completo:", traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def tecnico_mis_tickets(request):
    """
    Obtener tickets asignados al técnico (activos)
    """
    try:
        tecnico_id = request.GET.get('tecnico_id')
        
        if not tecnico_id:
            return Response({
                'success': False,
                'error': 'tecnico_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filtros opcionales
        estado = request.GET.get('estado')
        prioridad = request.GET.get('prioridad')
        
        # Tickets asignados al técnico
        tickets = Ticket.objects.filter(
            tecnico_asignado_id=tecnico_id
        ).select_related(
            'categoria_id',
            'estado_id',
            'prioridad_id',
            'usuario_creador_id',
            'usuario_creador_id__personas_id_personas'
        )
        
        # Filtrar por estado si se especifica
        if estado:
            # Soportar múltiples estados separados por coma
            if ',' in estado:
                estados_list = [int(e) for e in estado.split(',')]
                tickets = tickets.filter(estado_id__in=estados_list)
            else:
                tickets = tickets.filter(estado_id=estado)
        else:
            # Por defecto solo En Proceso
            tickets = tickets.filter(estado_id=2)
        
        # Filtrar por prioridad
        if prioridad:
            tickets = tickets.filter(prioridad_id=prioridad)
        
        # Ordenar por prioridad (urgente primero) y fecha
        tickets = tickets.order_by('-prioridad_id__nivel', 'fecha_creacion')
        
        serializer = TicketListSerializer(tickets, many=True)
        
        return Response({
            'success': True,
            'count': tickets.count(),
            'tickets': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        print("Error completo:", traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def tecnico_historial(request):
    """
    Obtener historial de tickets resueltos por el técnico
    """
    try:
        tecnico_id = request.GET.get('tecnico_id')
        
        if not tecnico_id:
            return Response({
                'success': False,
                'error': 'tecnico_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filtros de fecha opcionales
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        # Tickets resueltos o cerrados del técnico
        tickets = Ticket.objects.filter(
            tecnico_asignado_id=tecnico_id,
            estado_id__in=[3, 4]  # Resuelto o Cerrado
        ).select_related(
            'categoria_id',
            'estado_id',
            'prioridad_id',
            'usuario_creador_id',
            'usuario_creador_id__personas_id_personas'
        )
        
        # Filtrar por fechas si se proporcionan
        if fecha_inicio:
            from datetime import datetime
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            if timezone.is_naive(fecha_inicio_dt):
                fecha_inicio_dt = timezone.make_aware(fecha_inicio_dt)
            tickets = tickets.filter(fecha_resolucion__gte=fecha_inicio_dt)
        
        if fecha_fin:
            from datetime import datetime
            fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
            if timezone.is_naive(fecha_fin_dt):
                fecha_fin_dt = timezone.make_aware(fecha_fin_dt)
            fecha_fin_dt = fecha_fin_dt.replace(hour=23, minute=59, second=59)
            tickets = tickets.filter(fecha_resolucion__lte=fecha_fin_dt)
        
        # Ordenar por fecha de resolución (más reciente primero)
        tickets = tickets.order_by('-fecha_resolucion')
        
        # Serializar
        serializer = TicketListSerializer(tickets, many=True)
        
        # Agregar calificación a cada ticket
        tickets_data = serializer.data
        for ticket_data in tickets_data:
            try:
                calificacion = CalificacionTicket.objects.get(ticket_id=ticket_data['id_ticket'])
                ticket_data['calificacion'] = {
                    'valor': calificacion.calificacion,
                    'comentario': calificacion.comentario,
                    'fecha': calificacion.fecha_calificacion
                }
            except CalificacionTicket.DoesNotExist:
                ticket_data['calificacion'] = None
        
        return Response({
            'success': True,
            'count': len(tickets_data),
            'tickets': tickets_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        print("Error completo:", traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def tecnico_alertas(request):
    """
    Obtener alertas y notificaciones para el técnico
    """
    try:
        tecnico_id = request.GET.get('tecnico_id')
        
        if not tecnico_id:
            return Response({
                'success': False,
                'error': 'tecnico_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from datetime import timedelta
        
        hoy = timezone.now()
        hace_24h = hoy - timedelta(hours=24)
        hace_3_dias = hoy - timedelta(days=3)
        
        # Tickets urgentes sin resolver
        tickets_urgentes = Ticket.objects.filter(
            tecnico_asignado_id=tecnico_id,
            prioridad_id=4,  # Urgente
            estado_id__in=[1, 2]  # Abierto o En Proceso
        ).count()
        
        # Tickets nuevos (asignados en las últimas 24h)
        tickets_nuevos = Ticket.objects.filter(
            tecnico_asignado_id=tecnico_id,
            fecha_asignacion__gte=hace_24h,
            estado_id__in=[1, 2]
        ).count()
        
        # Tickets sin atender hace más de 3 días
        tickets_antiguos = Ticket.objects.filter(
            tecnico_asignado_id=tecnico_id,
            estado_id=2,  # En Proceso
            fecha_asignacion__lte=hace_3_dias
        ).count()
        
        # Tickets pendientes de atención (Abierto, asignado pero no en proceso)
        tickets_pendientes = Ticket.objects.filter(
            tecnico_asignado_id=tecnico_id,
            estado_id=1  # Abierto
        ).count()
        
        # Lista de tickets urgentes para mostrar
        lista_urgentes = Ticket.objects.filter(
            tecnico_asignado_id=tecnico_id,
            prioridad_id=4,
            estado_id__in=[1, 2]
        ).select_related(
            'categoria_id',
            'estado_id',
            'prioridad_id',
            'usuario_creador_id__personas_id_personas'
        ).order_by('fecha_creacion')[:5]
        
        serializer = TicketListSerializer(lista_urgentes, many=True)
        
        alertas = []
        
        if tickets_urgentes > 0:
            alertas.append({
                'tipo': 'urgente',
                'icono': '🚨',
                'mensaje': f'Tienes {tickets_urgentes} ticket{"s" if tickets_urgentes > 1 else ""} urgente{"s" if tickets_urgentes > 1 else ""} pendiente{"s" if tickets_urgentes > 1 else ""}',
                'cantidad': tickets_urgentes
            })
        
        if tickets_nuevos > 0:
            alertas.append({
                'tipo': 'nuevo',
                'icono': '🆕',
                'mensaje': f'Tienes {tickets_nuevos} ticket{"s" if tickets_nuevos > 1 else ""} nuevo{"s" if tickets_nuevos > 1 else ""} asignado{"s" if tickets_nuevos > 1 else ""}',
                'cantidad': tickets_nuevos
            })
        
        if tickets_antiguos > 0:
            alertas.append({
                'tipo': 'antiguo',
                'icono': '⏰',
                'mensaje': f'Tienes {tickets_antiguos} ticket{"s" if tickets_antiguos > 1 else ""} sin resolver hace más de 3 días',
                'cantidad': tickets_antiguos
            })
        
        if tickets_pendientes > 0:
            alertas.append({
                'tipo': 'pendiente',
                'icono': '📋',
                'mensaje': f'Tienes {tickets_pendientes} ticket{"s" if tickets_pendientes > 1 else ""} pendiente{"s" if tickets_pendientes > 1 else ""} de iniciar',
                'cantidad': tickets_pendientes
            })
        
        return Response({
            'success': True,
            'alertas': alertas,
            'resumen': {
                'urgentes': tickets_urgentes,
                'nuevos': tickets_nuevos,
                'antiguos': tickets_antiguos,
                'pendientes': tickets_pendientes
            },
            'tickets_urgentes': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        print("Error completo:", traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)