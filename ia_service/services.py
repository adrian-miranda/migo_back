"""
Servicio de integración con OpenAI para MIGO
"""
import time
import hashlib
from datetime import timedelta
from openai import OpenAI
from django.conf import settings
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from .models import IAConfiguracion, IAConsultasLog, IAMetricasTecnico, IAFeedback
from tickets.models import Ticket, CategoriaTicket
from authentication.models import Usuarios


class OpenAIService:
    """
    Servicio principal para interactuar con la API de OpenAI
    """
    
    def __init__(self):
        self.client = None
        self.modelo = IAConfiguracion.get_valor('modelo_openai', 'gpt-4o-mini')
        self.max_tokens = int(IAConfiguracion.get_valor('max_tokens', '1500'))
        self.temperatura = float(IAConfiguracion.get_valor('temperatura', '0.7'))
        self.activo = IAConfiguracion.get_valor('activo', '1') == '1'
    
    def _get_client(self):
        if self.client is None:
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not api_key:
                raise ValueError("OPENAI_API_KEY no está configurado en settings.py")
            self.client = OpenAI(api_key=api_key)
        return self.client
    
    def _verificar_limite(self, usuario_id: int, limite_diario: int = 50) -> tuple:
        """
        Verifica si el usuario ha excedido el límite diario de consultas
        Retorna (puede_consultar, consultas_restantes)
        """
        from django.utils import timezone
        import datetime
        
        # Obtener inicio del día en zona horaria local
        ahora_local = timezone.localtime(timezone.now())
        inicio_dia_local = ahora_local.replace(hour=0, minute=0, second=0, microsecond=0)
        
        consultas_hoy = IAConsultasLog.objects.filter(
            usuario_id=usuario_id,
            fecha_consulta__gte=inicio_dia_local
        ).count()
        
        puede_consultar = consultas_hoy < limite_diario
        restantes = max(0, limite_diario - consultas_hoy)
        
        return puede_consultar, restantes
    
    def _hacer_consulta(self, prompt: str, usuario_id: int, tipo_consulta: str, ticket_id: int = None) -> dict:
        if not self.activo:
            return {
                'success': False,
                'error': 'El servicio de IA está desactivado',
                'respuesta': None
            }
        
        # Verificar límite de consultas
        limite_diario = int(IAConfiguracion.get_valor('limite_diario', '50'))
        puede_consultar, restantes = self._verificar_limite(usuario_id, limite_diario)
        
        if not puede_consultar:
            return {
                'success': False,
                'error': f'Has alcanzado el límite de {limite_diario} consultas diarias',
                'consultas_restantes': 0,
                'respuesta': None
            }
        
        inicio = time.time()
        
        try:
            client = self._get_client()
            
            response = client.chat.completions.create(
                model=self.modelo,
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un asistente técnico especializado en soporte de TI para la empresa MIGO. 
                        Tu rol es ayudar a los técnicos a resolver tickets de soporte.
                        Responde siempre en español chileno profesional.
                        Sé conciso pero completo en tus respuestas.
                        Estructura tus respuestas con pasos claros cuando sea apropiado."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperatura
            )
            
            tiempo_ms = int((time.time() - inicio) * 1000)
            respuesta_texto = response.choices[0].message.content
            tokens = response.usage.total_tokens if response.usage else None
            
            IAConsultasLog.objects.create(
                ticket_id=ticket_id,
                usuario_id=usuario_id,
                tipo_consulta=tipo_consulta,
                prompt_enviado=prompt,
                respuesta_ia=respuesta_texto,
                tokens_usados=tokens,
                tiempo_respuesta_ms=tiempo_ms
            )
            
            return {
                'success': True,
                'respuesta': respuesta_texto,
                'tokens_usados': tokens,
                'tiempo_ms': tiempo_ms,
                'consultas_restantes': restantes - 1
            }
            
        except Exception as e:
            tiempo_ms = int((time.time() - inicio) * 1000)
            
            IAConsultasLog.objects.create(
                ticket_id=ticket_id,
                usuario_id=usuario_id,
                tipo_consulta=tipo_consulta,
                prompt_enviado=prompt,
                respuesta_ia=f"ERROR: {str(e)}",
                tiempo_respuesta_ms=tiempo_ms
            )
            
            return {
                'success': False,
                'error': str(e),
                'respuesta': None
            }


class GuiaSolucionService(OpenAIService):
    """
    Servicio para generar guías de solución para técnicos
    """
    
    def generar_guia(self, ticket_id: int, usuario_id: int, usar_cache: bool = True) -> dict:
        try:
            ticket = Ticket.objects.select_related(
                'categoria_id', 
                'prioridad_id', 
                'estado_id',
                'usuario_creador_id'
            ).get(id_ticket=ticket_id)
        except Ticket.DoesNotExist:
            return {'success': False, 'error': 'Ticket no encontrado'}
        
        # Verificar caché
        if usar_cache:
            cache_result = self._obtener_cache(ticket, 'guia_solucion', usuario_id)
            if cache_result:
                return cache_result
        
        # Buscar tickets similares resueltos
        tickets_similares = self._buscar_tickets_similares(ticket)
        
        # Construir prompt
        prompt = self._construir_prompt_guia(ticket, tickets_similares)
        
        # Hacer consulta
        resultado = self._hacer_consulta(
            prompt=prompt,
            usuario_id=usuario_id,
            tipo_consulta='guia_solucion',
            ticket_id=ticket_id
        )
        
        if resultado['success']:
            resultado['tickets_similares'] = [
                {
                    'id': t.id_ticket,
                    'titulo': t.titulo,
                    'solucion': t.solucion
                } for t in tickets_similares[:3]
            ]
            # Guardar en caché
            self._guardar_cache(ticket, 'guia_solucion', resultado)
            resultado['desde_cache'] = False
        
        return resultado
    
    def _generar_hash(self, ticket):
        """Genera hash del contenido del ticket para detectar cambios"""
        contenido = f"{ticket.titulo}|{ticket.descripcion}|{ticket.categoria_id_id}"
        return hashlib.sha256(contenido.encode()).hexdigest()
    
    def _obtener_cache(self, ticket, tipo_consulta, usuario_id):
        """Obtiene respuesta del caché si existe y es válida"""
        from .models import IACache
        
        hash_actual = self._generar_hash(ticket)
        
        try:
            cache = IACache.objects.get(
                ticket=ticket,
                tipo_consulta=tipo_consulta,
                hash_contenido=hash_actual
            )
            
            if cache.esta_vigente:
                import json
                resultado = json.loads(cache.respuesta_cache)
                resultado['desde_cache'] = True
                
                # Actualizar consultas restantes con valor actual
                _, restantes = self._verificar_limite(usuario_id)
                resultado['consultas_restantes'] = restantes
                
                return resultado
            else:
                # Caché expirado, eliminarlo
                cache.delete()
                
        except IACache.DoesNotExist:
            pass
        
        return None
    
    def _guardar_cache(self, ticket, tipo_consulta, resultado, horas_expiracion=24):
        """Guarda respuesta en caché"""
        from .models import IACache
        import json
        
        hash_contenido = self._generar_hash(ticket)
        fecha_expiracion = timezone.now() + timedelta(hours=horas_expiracion)
        
        # Crear copia sin el flag desde_cache para guardar
        resultado_guardar = {k: v for k, v in resultado.items() if k != 'desde_cache'}
        
        IACache.objects.update_or_create(
            ticket=ticket,
            tipo_consulta=tipo_consulta,
            defaults={
                'respuesta_cache': json.dumps(resultado_guardar),
                'hash_contenido': hash_contenido,
                'fecha_expiracion': fecha_expiracion
            }
        )
    
    def _buscar_tickets_similares(self, ticket: Ticket, limite: int = 5):
        similares = Ticket.objects.filter(
            categoria_id=ticket.categoria_id,
            estado_id__in=[3, 4],
            solucion__isnull=False
        ).exclude(
            id_ticket=ticket.id_ticket
        ).order_by('-fecha_resolucion')[:limite]
        
        return list(similares)
    
    def _construir_prompt_guia(self, ticket: Ticket, tickets_similares: list) -> str:
        prompt = f"""
TICKET ACTUAL:
- ID: #{ticket.id_ticket}
- Título: {ticket.titulo}
- Descripción: {ticket.descripcion}
- Categoría: {ticket.categoria_id.nombre_categoria}
- Prioridad: {ticket.prioridad_id.nombre_prioridad}

"""
        
        if tickets_similares:
            prompt += "TICKETS SIMILARES RESUELTOS ANTERIORMENTE:\n"
            for i, t in enumerate(tickets_similares, 1):
                prompt += f"""
Caso {i}:
- Título: {t.titulo}
- Descripción: {t.descripcion[:200]}...
- Solución aplicada: {t.solucion}

"""
        
        prompt += """
INSTRUCCIONES:
Basándote en la información del ticket y los casos similares resueltos anteriormente, genera una guía de solución que incluya:

1. **DIAGNÓSTICO PROBABLE**: ¿Cuál es la causa más probable del problema?

2. **PASOS DE SOLUCIÓN**: Lista ordenada de pasos a seguir para resolver el problema.

3. **VERIFICACIÓN**: ¿Cómo verificar que el problema quedó resuelto?

4. **NOTAS ADICIONALES**: Cualquier consideración especial o advertencia.

Sé específico y práctico en tus recomendaciones.
"""
        
        return prompt


class RecomendadorTecnicoService(OpenAIService):
    """
    Servicio para recomendar el mejor técnico para un ticket
    """
    
    def recomendar_tecnico(self, ticket_id: int, usuario_id: int) -> dict:
        try:
            ticket = Ticket.objects.select_related('categoria_id', 'prioridad_id').get(id_ticket=ticket_id)
        except Ticket.DoesNotExist:
            return {'success': False, 'error': 'Ticket no encontrado'}
        
        metricas = self._obtener_metricas_tecnicos(ticket.categoria_id)
        
        if not metricas:
            return {
                'success': False,
                'error': 'No hay métricas de técnicos disponibles para esta categoría'
            }
        
        prompt = self._construir_prompt_recomendacion(ticket, metricas)
        
        resultado = self._hacer_consulta(
            prompt=prompt,
            usuario_id=usuario_id,
            tipo_consulta='recomendar_tecnico',
            ticket_id=ticket_id
        )
        
        if resultado['success']:
            resultado['metricas_tecnicos'] = [
                {
                    'tecnico_id': m.tecnico_id,
                    'nombre': f"{m.tecnico.personas_id_personas.primer_nombre} {m.tecnico.personas_id_personas.primer_apellido}",
                    'tasa_resolucion': float(m.tasa_resolucion) if m.tasa_resolucion else 0,
                    'tiempo_promedio': float(m.tiempo_promedio_resolucion) if m.tiempo_promedio_resolucion else 0,
                    'feedback_positivo': float(m.tasa_feedback_positivo) if m.tasa_feedback_positivo else 0,
                    'tickets_resueltos': m.tickets_resueltos
                } for m in metricas
            ]
        
        return resultado
    
    def _obtener_metricas_tecnicos(self, categoria):
        return IAMetricasTecnico.objects.filter(
            categoria=categoria
        ).select_related(
            'tecnico',
            'tecnico__personas_id_personas'
        ).order_by('-tasa_resolucion', '-tasa_feedback_positivo')
    
    def _construir_prompt_recomendacion(self, ticket, metricas) -> str:
        prompt = f"""
TICKET A ASIGNAR:
- ID: #{ticket.id_ticket}
- Título: {ticket.titulo}
- Categoría: {ticket.categoria_id.nombre_categoria}
- Prioridad: {ticket.prioridad_id.nombre_prioridad}
- Descripción: {ticket.descripcion[:300]}

TÉCNICOS DISPONIBLES Y SUS MÉTRICAS EN ESTA CATEGORÍA:
"""
        
        for m in metricas:
            nombre = f"{m.tecnico.personas_id_personas.primer_nombre} {m.tecnico.personas_id_personas.primer_apellido}"
            prompt += f"""
- {nombre} (ID: {m.tecnico_id}):
  * Tickets resueltos: {m.tickets_resueltos}
  * Tasa de resolución: {m.tasa_resolucion or 0}%
  * Tiempo promedio: {m.tiempo_promedio_resolucion or 0} horas
  * Feedback positivo: {m.tasa_feedback_positivo or 0}%
"""
        
        prompt += """
INSTRUCCIONES:
Analiza las métricas de los técnicos y recomienda el mejor para este ticket.

Considera:
1. Experiencia en la categoría (tickets resueltos)
2. Efectividad (tasa de resolución)
3. Rapidez (tiempo promedio)
4. Calidad (feedback positivo)

Responde con:
1. **TÉCNICO RECOMENDADO**: Nombre y ID del técnico
2. **JUSTIFICACIÓN**: Por qué es la mejor opción
3. **ALTERNATIVA**: Segundo mejor técnico en caso de no disponibilidad
"""
        
        return prompt


class DetectorPatronesService(OpenAIService):
    """
    Servicio para detectar patrones y tendencias en tickets
    """
    
    def analizar_patrones(self, dias: int, usuario_id: int, categoria: str = None, prioridad: str = None) -> dict:
        estadisticas = self._obtener_estadisticas(dias, categoria, prioridad)
        prompt = self._construir_prompt_patrones(estadisticas, dias, categoria, prioridad)
        
        resultado = self._hacer_consulta(
            prompt=prompt,
            usuario_id=usuario_id,
            tipo_consulta='analizar_patrones'
        )
        
        if resultado['success']:
            resultado['estadisticas'] = estadisticas
            resultado['filtros'] = {
                'dias': dias,
                'categoria': categoria,
                'prioridad': prioridad
            }
        
        return resultado
    
    def _obtener_estadisticas(self, dias: int, categoria: str = None, prioridad: str = None) -> dict:
        from datetime import timedelta
        fecha_inicio = timezone.now() - timedelta(days=dias)
        
        tickets = Ticket.objects.filter(fecha_creacion__gte=fecha_inicio)
        
        # Aplicar filtro de categoría
        if categoria:
            tickets = tickets.filter(categoria_id__nombre_categoria=categoria)
        
        # Aplicar filtro de prioridad
        if prioridad:
            tickets = tickets.filter(prioridad_id__nombre_prioridad=prioridad)
        
        total = tickets.count()
        
        por_categoria = tickets.values('categoria_id__nombre_categoria').annotate(
            count=Count('id_ticket')
        )
        
        por_estado = tickets.values('estado_id__nombre_estado').annotate(
            count=Count('id_ticket')
        )
        
        por_prioridad = tickets.values('prioridad_id__nombre_prioridad').annotate(
            count=Count('id_ticket')
        )
        
        resueltos = tickets.filter(estado_id__in=[3, 4]).count()
        sin_resolver = tickets.filter(estado_id__in=[1, 2]).count()
        
        return {
            'total_tickets': total,
            'resueltos': resueltos,
            'sin_resolver': sin_resolver,
            'tasa_resolucion': round((resueltos / total * 100), 2) if total > 0 else 0,
            'por_categoria': {item['categoria_id__nombre_categoria']: item['count'] for item in por_categoria},
            'por_estado': {item['estado_id__nombre_estado']: item['count'] for item in por_estado},
            'por_prioridad': {item['prioridad_id__nombre_prioridad']: item['count'] for item in por_prioridad}
        }
    
    def _construir_prompt_patrones(self, estadisticas: dict, dias: int, categoria: str = None, prioridad: str = None) -> str:
        filtros_texto = f"últimos {dias} días"
        if categoria:
            filtros_texto += f", categoría: {categoria}"
        if prioridad:
            filtros_texto += f", prioridad: {prioridad}"
        
        prompt = f"""
ANÁLISIS DE TICKETS ({filtros_texto}):

ESTADÍSTICAS GENERALES:
- Total de tickets: {estadisticas['total_tickets']}
- Resueltos: {estadisticas['resueltos']}
- Sin resolver: {estadisticas['sin_resolver']}
- Tasa de resolución: {estadisticas['tasa_resolucion']}%

POR CATEGORÍA:
{estadisticas['por_categoria']}

POR ESTADO:
{estadisticas['por_estado']}

POR PRIORIDAD:
{estadisticas['por_prioridad']}

INSTRUCCIONES:
Analiza estos datos y proporciona:

1. **PATRONES DETECTADOS**: ¿Qué tendencias o patrones observas en los datos?

2. **ÁREAS DE PREOCUPACIÓN**: ¿Hay categorías o prioridades con problemas evidentes?

3. **RECOMENDACIONES**: ¿Qué acciones sugieres para mejorar la gestión de tickets?

4. **PREDICCIÓN**: Basándote en los datos, ¿qué podría pasar si no se toman medidas?

Sé específico y basa tus conclusiones en los números proporcionados.
"""
        return prompt


class CalculadorMetricasService:
    """
    Servicio para calcular y actualizar métricas de técnicos
    """
    
    @staticmethod
    def actualizar_metricas_tecnico(tecnico_id: int, categoria_id: int):
        tickets = Ticket.objects.filter(
            tecnico_asignado_id=tecnico_id,
            categoria_id=categoria_id
        )
        
        total = tickets.count()
        resueltos = tickets.filter(estado_id__in=[3, 4]).count()
        
        tickets_con_tiempo = tickets.filter(
            fecha_resolucion__isnull=False,
            fecha_asignacion__isnull=False
        )
        
        tiempo_promedio = None
        if tickets_con_tiempo.exists():
            tiempos = []
            for t in tickets_con_tiempo:
                diff = (t.fecha_resolucion - t.fecha_asignacion).total_seconds() / 3600
                tiempos.append(diff)
            tiempo_promedio = sum(tiempos) / len(tiempos) if tiempos else None
        
        feedbacks = IAFeedback.objects.filter(
            tecnico_id=tecnico_id,
            ticket__categoria_id=categoria_id
        )
        feedback_total = feedbacks.count()
        feedback_positivo = feedbacks.filter(fue_util=True).count()
        
        metrica, created = IAMetricasTecnico.objects.update_or_create(
            tecnico_id=tecnico_id,
            categoria_id=categoria_id,
            defaults={
                'tickets_resueltos': resueltos,
                'tickets_totales': total,
                'tiempo_promedio_resolucion': tiempo_promedio,
                'tasa_resolucion': (resueltos / total * 100) if total > 0 else None,
                'feedback_positivo': feedback_positivo,
                'feedback_total': feedback_total,
                'tasa_feedback_positivo': (feedback_positivo / feedback_total * 100) if feedback_total > 0 else None
            }
        )
        
        return metrica
    
    @staticmethod
    def actualizar_todas_metricas():
        tecnicos = Usuarios.objects.filter(roles_id_roles=1)
        categorias = CategoriaTicket.objects.all()
        
        actualizadas = 0
        for tecnico in tecnicos:
            for categoria in categorias:
                if Ticket.objects.filter(
                    tecnico_asignado_id=tecnico.id_usuarios,
                    categoria_id=categoria.id_categoria_ticket
                ).exists():
                    CalculadorMetricasService.actualizar_metricas_tecnico(
                        tecnico.id_usuarios,
                        categoria.id_categoria_ticket
                    )
                    actualizadas += 1
        
        return actualizadas

class PriorizadorTicketService(OpenAIService):
    """
    Servicio para sugerir prioridad de un ticket usando IA
    """
    
    def sugerir_prioridad(self, ticket_id: int, usuario_id: int) -> dict:
        try:
            ticket = Ticket.objects.select_related(
                'categoria_id',
                'usuario_creador_id',
                'usuario_creador_id__cargos_id_cargos'
            ).get(id_ticket=ticket_id)
        except Ticket.DoesNotExist:
            return {'success': False, 'error': 'Ticket no encontrado'}
        
        # Obtener datos del cargo del usuario creador
        cargo = ticket.usuario_creador_id.cargos_id_cargos
        categoria = ticket.categoria_id
        
        # Calcular prioridad automática (según tu lógica existente)
        peso_cargo = float(cargo.peso_prioridad) if cargo else 1.0
        multiplicador = float(categoria.multiplicador_prioridad) if categoria else 1.0
        puntaje_calculado = peso_cargo * multiplicador
        
        # Mapear puntaje a prioridad
        if puntaje_calculado >= 3.5:
            prioridad_sugerida = 4  # Urgente
        elif puntaje_calculado >= 2.5:
            prioridad_sugerida = 3  # Alta
        elif puntaje_calculado >= 1.5:
            prioridad_sugerida = 2  # Media
        else:
            prioridad_sugerida = 1  # Baja
        
        prompt = self._construir_prompt_prioridad(ticket, cargo, puntaje_calculado, prioridad_sugerida)
        
        resultado = self._hacer_consulta(
            prompt=prompt,
            usuario_id=usuario_id,
            tipo_consulta='priorizar',
            ticket_id=ticket_id
        )
        
        if resultado['success']:
            resultado['prioridad_calculada'] = {
                'puntaje': puntaje_calculado,
                'prioridad_id': prioridad_sugerida,
                'peso_cargo': peso_cargo,
                'multiplicador_categoria': multiplicador
            }
        
        return resultado
    
    def _construir_prompt_prioridad(self, ticket, cargo, puntaje, prioridad_sugerida) -> str:
        nombres_prioridad = {1: 'Baja', 2: 'Media', 3: 'Alta', 4: 'Urgente'}
        
        prompt = f"""
TICKET A EVALUAR:
- ID: #{ticket.id_ticket}
- Título: {ticket.titulo}
- Descripción: {ticket.descripcion}
- Categoría: {ticket.categoria_id.nombre_categoria}
- Cargo del solicitante: {cargo.nombre_cargo if cargo else 'No especificado'}

CÁLCULO AUTOMÁTICO:
- Peso del cargo: {float(cargo.peso_prioridad) if cargo else 1.0}
- Multiplicador categoría: {float(ticket.categoria_id.multiplicador_prioridad)}
- Puntaje calculado: {puntaje}
- Prioridad sugerida: {nombres_prioridad.get(prioridad_sugerida, 'Media')}

INSTRUCCIONES:
Analiza el ticket y proporciona:

1. **VALIDACIÓN**: ¿La prioridad calculada ({nombres_prioridad.get(prioridad_sugerida, 'Media')}) es adecuada? ¿Por qué?

2. **AJUSTE SUGERIDO**: Si consideras que debería ser diferente, indica cuál y justifica.

3. **PALABRAS CLAVE DETECTADAS**: ¿Hay palabras en la descripción que sugieran urgencia? (ej: "urgente", "no puedo trabajar", "crítico", "gerencia")

4. **RECOMENDACIÓN FINAL**: Prioridad recomendada (Baja, Media, Alta, Urgente)

Sé conciso y práctico.
"""
        return prompt