"""
Configuración del panel de administración
"""
from django.contrib import admin
from .models import Roles, Cargos, Personas, Usuarios


@admin.register(Roles)
class RolesAdmin(admin.ModelAdmin):
    list_display = ['id_roles', 'nombre_rol']
    search_fields = ['nombre_rol']


@admin.register(Cargos)
class CargosAdmin(admin.ModelAdmin):
    list_display = ['id_cargos', 'nombre_cargo']
    search_fields = ['nombre_cargo']


@admin.register(Personas)
class PersonasAdmin(admin.ModelAdmin):
    list_display = ['id_personas', 'run', 'nombre_completo']
    search_fields = ['run', 'primer_nombre', 'primer_apellido']


@admin.register(Usuarios)
class UsuariosAdmin(admin.ModelAdmin):
    list_display = ['id_usuarios', 'correo', 'get_nombre', 'get_rol', 'get_cargo']
    search_fields = ['correo', 'personas_id_personas__primer_nombre']
    list_filter = ['roles_id_roles', 'cargos_id_cargos']
    
    def get_nombre(self, obj):
        return obj.personas_id_personas.nombre_completo
    get_nombre.short_description = 'Nombre'
    
    def get_rol(self, obj):
        return obj.roles_id_roles.nombre_rol
    get_rol.short_description = 'Rol'
    
    def get_cargo(self, obj):
        return obj.cargos_id_cargos.nombre_cargo
    get_cargo.short_description = 'Cargo'