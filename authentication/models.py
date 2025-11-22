"""
Modelos para la autenticación y gestión de usuarios
Estos modelos mapean las tablas existentes en la BD migo
"""
from django.db import models


class Roles(models.Model):
    """
    Modelo para la tabla roles
    """
    id_roles = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=45, unique=True)

    class Meta:
        managed = False
        db_table = 'roles'
        ordering = ['id_roles']

    def __str__(self):
        return self.nombre_rol


class Cargos(models.Model):
    """
    Modelo para la tabla cargos
    """
    id_cargos = models.AutoField(primary_key=True)
    nombre_cargo = models.CharField(max_length=45)
    peso_prioridad = models.IntegerField(default=2)  # ← AGREGAR ESTA LÍNEA
    
    class Meta:
        managed = False
        db_table = 'cargos'
        ordering = ['nombre_cargo']
    
    def __str__(self):
        return self.nombre_cargo

class Personas(models.Model):
    """
    Modelo para la tabla personas
    """
    id_personas = models.AutoField(primary_key=True)
    run = models.CharField(max_length=10, unique=True)
    primer_nombre = models.CharField(max_length=45)
    segundo_nombre = models.CharField(max_length=45, null=True, blank=True)
    primer_apellido = models.CharField(max_length=45)
    segundo_apellido = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'personas'
        ordering = ['primer_apellido', 'primer_nombre']

    def __str__(self):
        return f"{self.primer_nombre} {self.primer_apellido}"

    @property
    def nombre_completo(self):
        """
        Retorna el nombre completo de la persona
        """
        if self.segundo_nombre:
            return f"{self.primer_nombre} {self.segundo_nombre} {self.primer_apellido} {self.segundo_apellido}"
        return f"{self.primer_nombre} {self.primer_apellido} {self.segundo_apellido}"


class Usuarios(models.Model):
    """
    Modelo para la tabla usuarios
    """
    id_usuarios = models.AutoField(primary_key=True)
    correo = models.CharField(max_length=45, unique=True)
    contraseña = models.CharField(max_length=45)
    personas_id_personas = models.ForeignKey(
        Personas,
        on_delete=models.CASCADE,
        db_column='personas_id_personas',
        related_name='usuarios'
    )
    roles_id_roles = models.ForeignKey(
        Roles,
        on_delete=models.CASCADE,
        db_column='roles_id_roles',
        related_name='usuarios'
    )
    cargos_id_cargos = models.ForeignKey(
        Cargos,
        on_delete=models.CASCADE,
        db_column='cargos_id_cargos',
        related_name='usuarios'
    )

    class Meta:
        managed = False
        db_table = 'usuarios'
        ordering = ['correo']

    def __str__(self):
        return self.correo

    def verificar_contraseña(self, contraseña):
        """
        Verifica si la contraseña es correcta
        NOTA: En producción usar hash con bcrypt o similar
        """
        return self.contraseña == contraseña