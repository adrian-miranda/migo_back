"""
Vistas para la API de autenticación
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from .models import Usuarios
from .serializers import (
    LoginSerializer,
    UsuarioSerializer,
    UsuarioBasicoSerializer
)


@api_view(['GET'])
@permission_classes([AllowAny])
def verificar_conexion(request):
    """
    Endpoint para verificar que el backend está funcionando
    y que hay conexión con la base de datos
    """
    try:
        # Intentar hacer una consulta simple
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            
        return Response({
            'status': 'OK',
            'message': 'Backend conectado correctamente',
            'database': 'Conexión a MySQL exitosa'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'status': 'ERROR',
            'message': 'Error en la conexión',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Endpoint para autenticación de usuarios
    
    Body JSON:
    {
        "correo": "usuario@migo.cl",
        "contraseña": "password"
    }
    
    Response:
    {
        "success": true,
        "message": "Login exitoso",
        "usuario": {...},
        "token": "..."
    }
    """
    # Validar datos de entrada
    serializer = LoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'Datos inválidos',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    correo = serializer.validated_data['correo']
    contraseña = serializer.validated_data['contraseña']
    
    try:
        # Buscar usuario con relaciones
        usuario = Usuarios.objects.select_related(
            'personas_id_personas',
            'roles_id_roles',
            'cargos_id_cargos'
        ).get(correo=correo)
        
        # Verificar contraseña
        if not usuario.verificar_contraseña(contraseña):
            return Response({
                'success': False,
                'error': 'Credenciales inválidas'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Serializar datos del usuario
        usuario_data = UsuarioSerializer(usuario).data
        
        # Generar token simple (en producción usar JWT)
        token = f'migo_token_{usuario.id_usuarios}'
        
        return Response({
            'success': True,
            'message': 'Login exitoso',
            'usuario': usuario_data,
            'token': token
        }, status=status.HTTP_200_OK)
        
    except Usuarios.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Credenciales inválidas'
        }, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({
            'success': False,
            'error': 'Error en el servidor',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    """
    Endpoint para cerrar sesión
    En una implementación con JWT, aquí se invalidaría el token
    """
    return Response({
        'success': True,
        'message': 'Logout exitoso'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def perfil_view(request):
    """
    Endpoint para obtener el perfil del usuario autenticado
    Requiere enviar el token en los headers
    """
    # En producción, extraer el usuario del token
    # Por ahora, devolvemos un mensaje de ejemplo
    
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return Response({
            'success': False,
            'error': 'Token no proporcionado'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    token = auth_header.replace('Bearer ', '')
    
    # Extraer ID del usuario del token simple
    try:
        user_id = int(token.replace('migo_token_', ''))
        
        usuario = Usuarios.objects.select_related(
            'personas_id_personas',
            'roles_id_roles',
            'cargos_id_cargos'
        ).get(id_usuarios=user_id)
        
        usuario_data = UsuarioSerializer(usuario).data
        
        return Response({
            'success': True,
            'usuario': usuario_data
        }, status=status.HTTP_200_OK)
        
    except (ValueError, Usuarios.DoesNotExist):
        return Response({
            'success': False,
            'error': 'Token inválido'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_usuarios(request):
    """
    Endpoint para listar todos los usuarios
    Solo para administradores
    """
    try:
        usuarios = Usuarios.objects.select_related(
            'personas_id_personas',
            'roles_id_roles',
            'cargos_id_cargos'
        ).all()
        
        serializer = UsuarioBasicoSerializer(usuarios, many=True)
        
        return Response({
            'success': True,
            'count': usuarios.count(),
            'usuarios': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': 'Error al obtener usuarios',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_usuario(request, id_usuario):
    """
    Endpoint para obtener un usuario específico por ID
    """
    try:
        usuario = Usuarios.objects.select_related(
            'personas_id_personas',
            'roles_id_roles',
            'cargos_id_cargos'
        ).get(id_usuarios=id_usuario)
        
        serializer = UsuarioSerializer(usuario)
        
        return Response({
            'success': True,
            'usuario': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Usuarios.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': 'Error al obtener usuario',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
@permission_classes([AllowAny])
def listar_tecnicos_disponibles(request):
    """
    Obtener técnicos que NO están asignados a tickets activos
    Un técnico está ocupado si tiene tickets en estado Abierto (1) o En Proceso (2)
    """
    try:
        from tickets.models import Ticket
        
        # Obtener IDs de técnicos ocupados (con tickets abiertos o en proceso)
        tecnicos_ocupados = Ticket.objects.filter(
            estado_id__in=[1, 2],  # Abierto o En Proceso
            tecnico_asignado_id__isnull=False
        ).values_list('tecnico_asignado_id', flat=True).distinct()
        
        # Obtener todos los técnicos (rol_id = 1)
        tecnicos = Usuarios.objects.select_related(
            'personas_id_personas',
            'roles_id_roles',
            'cargos_id_cargos'
        ).filter(
            roles_id_roles__id_roles=1  # Solo técnicos
        ).exclude(
            id_usuarios__in=tecnicos_ocupados  # Excluir ocupados
        )
        
        serializer = UsuarioBasicoSerializer(tecnicos, many=True)
        
        return Response({
            'success': True,
            'count': tecnicos.count(),
            'tecnicos': serializer.data,
            'ocupados': len(tecnicos_ocupados)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_todos_tecnicos(request):
    """
    Obtener todos los técnicos con su estado (disponible/ocupado)
    """
    try:
        from tickets.models import Ticket
        
        # Obtener todos los técnicos
        tecnicos = Usuarios.objects.select_related(
            'personas_id_personas',
            'roles_id_roles',
            'cargos_id_cargos'
        ).filter(roles_id_roles__id_roles=1)
        
        # Obtener técnicos ocupados
        tecnicos_ocupados_ids = Ticket.objects.filter(
            estado_id__in=[1, 2],
            tecnico_asignado_id__isnull=False
        ).values_list('tecnico_asignado_id', flat=True).distinct()
        
        # Crear respuesta con estado
        tecnicos_data = []
        for tecnico in tecnicos:
            tecnico_dict = UsuarioBasicoSerializer(tecnico).data
            tecnico_dict['disponible'] = tecnico.id_usuarios not in tecnicos_ocupados_ids
            
            # Contar tickets activos del técnico
            tickets_activos = Ticket.objects.filter(
                tecnico_asignado_id=tecnico.id_usuarios,
                estado_id__in=[1, 2]
            ).count()
            tecnico_dict['tickets_activos'] = tickets_activos
            
            tecnicos_data.append(tecnico_dict)
        
        return Response({
            'success': True,
            'count': len(tecnicos_data),
            'tecnicos': tecnicos_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
"""
Autenticación para el servicio de IA
"""
from rest_framework import status
from rest_framework.response import Response
from authentication.models import Usuarios


def get_usuario_from_token(request):
    """
    Extrae el usuario del token en el header Authorization
    Retorna (usuario, error_response)
    """
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return None, Response({
            'success': False,
            'error': 'Token no proporcionado'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    token = auth_header.replace('Bearer ', '')
    
    try:
        user_id = int(token.replace('migo_token_', ''))
        
        usuario = Usuarios.objects.select_related(
            'personas_id_personas',
            'roles_id_roles',
            'cargos_id_cargos'
        ).get(id_usuarios=user_id)
        
        return usuario, None
        
    except (ValueError, Usuarios.DoesNotExist):
        return None, Response({
            'success': False,
            'error': 'Token inválido'
        }, status=status.HTTP_401_UNAUTHORIZED)


def requiere_autenticacion(view_func):
    """
    Decorador para requerir autenticación en vistas basadas en función
    """
    def wrapper(request, *args, **kwargs):
        usuario, error = get_usuario_from_token(request)
        if error:
            return error
        request.usuario_autenticado = usuario
        return view_func(request, *args, **kwargs)
    return wrapper


class AuthMixin:
    """
    Mixin para requerir autenticación en vistas basadas en clase
    """
    
    def get_usuario(self, request):
        """Obtiene el usuario autenticado o None"""
        usuario, _ = get_usuario_from_token(request)
        return usuario
    
    def requiere_auth(self, request):
        """
        Valida autenticación y retorna (usuario, error_response)
        Usar al inicio de cada método: post, get, etc.
        """
        return get_usuario_from_token(request)
    
    def requiere_rol(self, request, roles_permitidos):
        """
        Valida autenticación y rol del usuario
        roles_permitidos: lista de IDs de roles [1, 2, 3]
        1=Técnico, 2=Trabajador, 3=Administrador
        """
        usuario, error = get_usuario_from_token(request)
        if error:
            return None, error
        
        if usuario.roles_id_roles.id_roles not in roles_permitidos:
            return None, Response({
                'success': False,
                'error': 'No tienes permisos para esta acción'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return usuario, None
    
    def requiere_tecnico(self, request):
        """Requiere que el usuario sea técnico (rol 1) o admin (rol 3)"""
        return self.requiere_rol(request, [1, 3])
    
    def requiere_admin(self, request):
        """Requiere que el usuario sea administrador (rol 3)"""
        return self.requiere_rol(request, [3])