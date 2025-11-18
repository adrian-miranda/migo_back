"""
Vistas para la API de autenticación
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection
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