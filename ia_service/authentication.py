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