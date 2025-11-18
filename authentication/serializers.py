"""
Serializers para la API de autenticación
"""
from rest_framework import serializers
from .models import Usuarios, Personas, Roles, Cargos


class RolesSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Roles
    """
    class Meta:
        model = Roles
        fields = ['id_roles', 'nombre_rol']


class CargosSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Cargos
    """
    class Meta:
        model = Cargos
        fields = ['id_cargos', 'nombre_cargo']


class PersonasSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Personas
    """
    nombre_completo = serializers.ReadOnlyField()

    class Meta:
        model = Personas
        fields = [
            'id_personas',
            'run',
            'primer_nombre',
            'segundo_nombre',
            'primer_apellido',
            'segundo_apellido',
            'nombre_completo'
        ]


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo Usuarios
    Incluye información relacionada de persona, rol y cargo
    """
    persona = PersonasSerializer(source='personas_id_personas', read_only=True)
    rol = RolesSerializer(source='roles_id_roles', read_only=True)
    cargo = CargosSerializer(source='cargos_id_cargos', read_only=True)

    class Meta:
        model = Usuarios
        fields = [
            'id_usuarios',
            'correo',
            'persona',
            'rol',
            'cargo'
        ]


class LoginSerializer(serializers.Serializer):
    """
    Serializer para validar datos de login
    """
    correo = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'El correo es obligatorio',
            'invalid': 'Ingrese un correo válido'
        }
    )
    contraseña = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        error_messages={
            'required': 'La contraseña es obligatoria'
        }
    )

    def validate_correo(self, value):
        """
        Validar formato del correo
        """
        return value.lower().strip()


class UsuarioBasicoSerializer(serializers.ModelSerializer):
    """
    Serializer básico para listados de usuarios
    """
    nombre_completo = serializers.CharField(
        source='personas_id_personas.nombre_completo',
        read_only=True
    )
    nombre_rol = serializers.CharField(
        source='roles_id_roles.nombre_rol',
        read_only=True
    )
    nombre_cargo = serializers.CharField(
        source='cargos_id_cargos.nombre_cargo',
        read_only=True
    )

    class Meta:
        model = Usuarios
        fields = [
            'id_usuarios',
            'correo',
            'nombre_completo',
            'nombre_rol',
            'nombre_cargo'
        ]