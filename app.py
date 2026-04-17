import streamlit as st
import re
from typing import List, Dict, Tuple
import json

# Configuración de la página
st.set_page_config(
    page_title="Examen SnowPro Core",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .stButton button {
        width: 100%;
        font-weight: bold;
    }
    .correct-answer {
        background-color: #d4edda;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #28a745;
        margin: 10px 0;
    }
    .wrong-answer {
        background-color: #f8d7da;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #dc3545;
        margin: 10px 0;
    }
    .info-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        margin-left: 10px;
    }
    .badge-single {
        background-color: #007bff;
        color: white;
    }
    .badge-multiple {
        background-color: #28a745;
        color: white;
    }
    .badge-tf {
        background-color: #ffc107;
        color: #000;
    }
</style>
""", unsafe_allow_html=True)

class ExamenSnowflake:
    def __init__(self, archivo_preguntas):
        self.archivo_preguntas = archivo_preguntas
        self.preguntas = []
        self.cargar_preguntas()
    
    def cargar_preguntas(self):
        """Carga las preguntas desde el archivo de texto"""
        try:
            with open(self.archivo_preguntas, 'r', encoding='utf-8') as file:
                contenido = file.read()
            
            # Separar por bloques de PREGUNTA
            bloques = re.split(r'PREGUNTA (\d+)', contenido)
            
            for i in range(1, len(bloques), 2):
                if i+1 < len(bloques):
                    num_pregunta = int(bloques[i])
                    texto_pregunta = bloques[i+1]
                    
                    pregunta = self.extraer_pregunta_mejorado(texto_pregunta, num_pregunta)
                    if pregunta:
                        self.preguntas.append(pregunta)
            
            st.success(f"✅ Cargadas {len(self.preguntas)} preguntas correctamente")
            
        except Exception as e:
            st.error(f"❌ Error al cargar preguntas: {str(e)}")
            self.preguntas = []
    
    def extraer_pregunta_mejorado(self, texto, num_pregunta):
        """Extrae la información de la pregunta leyendo el tipo explícitamente"""
        
        # Extraer texto original
        original_match = re.search(r'Texto original:\s*(.+?)(?=Traducción:|$)', texto, re.DOTALL)
        original = original_match.group(1).strip() if original_match else ""
        
        # Extraer traducción
        traduccion_match = re.search(r'Traducción:\s*(.+?)(?=A\.|B\.|C\.|D\.|E\.|F\.|Verdadero|Falso|Respuesta correcta:|Selección|Tipo:|$)', texto, re.DOTALL)
        traduccion = traduccion_match.group(1).strip() if traduccion_match else ""
        
        # Detectar tipo de pregunta desde la línea "Tipo:" o desde el contexto
        tipo_pregunta = "Selección única"  # default
        opciones = {}
        
        # Buscar la línea de Tipo:
        tipo_match = re.search(r'Tipo:\s*(.+)', texto)
        if tipo_match:
            tipo_texto = tipo_match.group(1).strip()
            if 'Verdadero' in tipo_texto or 'Falso' in tipo_texto:
                tipo_pregunta = "Verdadero/Falso"
            elif 'Selección múltiple' in tipo_texto:
                if '(2' in tipo_texto or 'dos' in tipo_texto.lower():
                    tipo_pregunta = "Selección múltiple (2)"
                elif '(3' in tipo_texto or 'tres' in tipo_texto.lower():
                    tipo_pregunta = "Selección múltiple (3)"
                elif '(4' in tipo_texto or 'cuatro' in tipo_texto.lower():
                    tipo_pregunta = "Selección múltiple (4)"
                elif 'todas' in tipo_texto.lower():
                    tipo_pregunta = "Selección múltiple (todas)"
            elif 'Selección única' in tipo_texto:
                tipo_pregunta = "Selección única"
        else:
            # Si no hay línea de Tipo, intentar detectar por otras señales
            texto_lower = texto.lower()
            if 'verdadero o falso' in texto_lower or 'true or false' in texto_lower:
                tipo_pregunta = "Verdadero/Falso"
            elif 'elija dos' in texto_lower or 'choose two' in texto_lower:
                tipo_pregunta = "Selección múltiple (2)"
            elif 'elija tres' in texto_lower or 'choose three' in texto_lower:
                tipo_pregunta = "Selección múltiple (3)"
            elif 'elija cuatro' in texto_lower or 'choose four' in texto_lower:
                tipo_pregunta = "Selección múltiple (4)"
            elif 'elija todas' in texto_lower or 'choose all' in texto_lower:
                tipo_pregunta = "Selección múltiple (todas)"
        
        # Para Verdadero/Falso, crear opciones específicas
        if tipo_pregunta == "Verdadero/Falso":
            opciones = {
                'A': 'Verdadero (True)',
                'B': 'Falso (False)'
            }
        else:
            # Extraer opciones con formato A., B., C., etc.
            opciones_raw = re.findall(r'([A-F])\.\s*(.+?)(?=[A-F]\.|Respuesta correcta:|$)', texto, re.DOTALL)
            
            # Si no se encontraron, buscar en líneas separadas
            if not opciones_raw:
                lineas = texto.split('\n')
                for linea in lineas:
                    match = re.match(r'^\s*([A-F])\.\s+(.+)$', linea.strip())
                    if match:
                        letra = match.group(1)
                        texto_opcion = match.group(2).strip()
                        opciones_raw.append((letra, texto_opcion))
            
            for letra, texto_opcion in opciones_raw:
                opciones[letra] = texto_opcion.strip()
        
        # Extraer respuesta correcta
        respuesta_match = re.search(r'Respuesta correcta:\s*([A-F, ]+)', texto)
        respuesta_correcta = respuesta_match.group(1).strip() if respuesta_match else ""
        respuesta_correcta = respuesta_correcta.replace(' ', '')
        
        # Para Verdadero/Falso, mapear
        if tipo_pregunta == "Verdadero/Falso":
            if 'A' in respuesta_correcta or 'VERDADERO' in respuesta_correcta.upper():
                respuesta_correcta = 'A'
            elif 'B' in respuesta_correcta or 'FALSO' in respuesta_correcta.upper():
                respuesta_correcta = 'B'
        
        return {
            'numero': num_pregunta,
            'original': original,
            'traduccion': traduccion,
            'opciones': opciones,
            'respuesta_correcta': respuesta_correcta,
            'tipo': tipo_pregunta
        }
    
    def obtener_preguntas_por_bloque(self, inicio, fin):
        """Obtiene un bloque de preguntas"""
        return self.preguntas[inicio-1:fin]
    
    def verificar_respuesta(self, pregunta, respuesta_usuario):
        """Verifica si la respuesta es correcta según el tipo de pregunta"""
        if pregunta['tipo'] == "Selección única" or pregunta['tipo'] == "Verdadero/Falso":
            return respuesta_usuario == pregunta['respuesta_correcta']
        else:
            # Para selección múltiple, comparar conjuntos
            if isinstance(respuesta_usuario, list):
                respuestas_usuario_set = set(respuesta_usuario)
            elif isinstance(respuesta_usuario, str):
                respuestas_usuario_set = set(respuesta_usuario.split(','))
            else:
                respuestas_usuario_set = set()
            
            respuestas_correctas_set = set(pregunta['respuesta_correcta'].split(','))
            # Limpiar espacios
            respuestas_usuario_set = {r.strip() for r in respuestas_usuario_set}
            respuestas_correctas_set = {r.strip() for r in respuestas_correctas_set}
            return respuestas_usuario_set == respuestas_correctas_set

def mostrar_pregunta(pregunta, key_suffix=""):
    """Muestra una pregunta individual con su tipo específico"""
    
    # Badge según tipo
    badge_class = "badge-single"
    if "múltiple" in pregunta['tipo']:
        badge_class = "badge-multiple"
    elif pregunta['tipo'] == "Verdadero/Falso":
        badge_class = "badge-tf"
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 10px;">
        <h3 style="margin: 0;">Pregunta {pregunta['numero']}</h3>
        <span class="info-badge {badge_class}">{pregunta['tipo']}</span>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("📖 Ver en inglés", expanded=False):
        st.markdown(pregunta['original'])
    
    st.markdown(f"**{pregunta['traduccion']}**")
    
    clave_respuesta = f"pregunta_{pregunta['numero']}_{key_suffix}"
    respuesta_actual = st.session_state.respuestas_usuario.get(clave_respuesta, None)
    
    respuesta_seleccionada = None
    
    # Renderizar según el tipo de pregunta
    if pregunta['tipo'] == "Verdadero/Falso":
        # Radio buttons para Verdadero/Falso
        st.info("📌 **Selecciona una opción**")
        opciones_tf = ["Verdadero (True)", "Falso (False)"]
        indice_actual = None
        
        if respuesta_actual:
            if respuesta_actual == 'A':
                indice_actual = 0
            elif respuesta_actual == 'B':
                indice_actual = 1
        
        respuesta_seleccionada = st.radio(
            "Respuesta:",
            options=opciones_tf,
            key=clave_respuesta,
            index=indice_actual if indice_actual is not None else None,
            label_visibility="collapsed"
        )
        
        if respuesta_seleccionada:
            respuesta_seleccionada = 'A' if respuesta_seleccionada == "Verdadero (True)" else 'B'
    
    elif "múltiple" in pregunta['tipo']:
        # Checkboxes para selección múltiple
        st.info(f"📌 **Selecciona todas las que correspondan**")
        
        opciones_lista = [f"{letra}. {texto}" for letra, texto in pregunta['opciones'].items()]
        
        # Obtener selecciones actuales
        valores_seleccionados_actuales = []
        if respuesta_actual and isinstance(respuesta_actual, list):
            valores_seleccionados_actuales = respuesta_actual
        elif respuesta_actual and isinstance(respuesta_actual, str):
            valores_seleccionados_actuales = respuesta_actual.split(',')
        
        # Crear checkboxes
        seleccionados = []
        
        # Mostrar en 2 columnas para mejor organización
        cols = st.columns(2)
        for idx, opcion in enumerate(opciones_lista):
            letra = opcion[0]
            is_checked = letra in valores_seleccionados_actuales
            col_idx = idx % 2
            with cols[col_idx]:
                checked = st.checkbox(opcion, value=is_checked, key=f"{clave_respuesta}_{letra}")
                if checked:
                    seleccionados.append(letra)
        
        respuesta_seleccionada = seleccionados
        
        # Mostrar sugerencia según el tipo
        if '(2)' in pregunta['tipo']:
            st.caption("💡 Sugerencia: Debes seleccionar 2 opciones")
        elif '(3)' in pregunta['tipo']:
            st.caption("💡 Sugerencia: Debes seleccionar 3 opciones")
        elif '(4)' in pregunta['tipo']:
            st.caption("💡 Sugerencia: Debes seleccionar 4 opciones")
        
        # Actualizar respuesta en session state
        if seleccionados:
            st.session_state.respuestas_usuario[clave_respuesta] = seleccionados
        elif clave_respuesta in st.session_state.respuestas_usuario:
            del st.session_state.respuestas_usuario[clave_respuesta]
    
    else:  # Selección única
        # Radio buttons para selección única
        st.info("📌 **Selecciona una opción**")
        opciones_lista = [f"{letra}. {texto}" for letra, texto in pregunta['opciones'].items()]
        indice_actual = None
        
        if respuesta_actual and respuesta_actual in pregunta['opciones']:
            try:
                indice_actual = opciones_lista.index(f"{respuesta_actual}. {pregunta['opciones'][respuesta_actual]}")
            except ValueError:
                indice_actual = None
        
        respuesta_seleccionada = st.radio(
            "Respuesta:",
            options=opciones_lista,
            key=clave_respuesta,
            index=indice_actual if indice_actual is not None else None,
            label_visibility="collapsed"
        )
        
        if respuesta_seleccionada:
            respuesta_seleccionada = respuesta_seleccionada[0]
    
    # Verificar respuesta y mostrar feedback
    if respuesta_seleccionada is not None and respuesta_seleccionada != "" and respuesta_seleccionada != []:
        st.session_state.respuestas_usuario[clave_respuesta] = respuesta_seleccionada
        
        es_correcta = st.session_state.examen.verificar_respuesta(pregunta, respuesta_seleccionada)
        
        if es_correcta:
            st.markdown('<div class="correct-answer">✅ ¡Correcto!</div>', unsafe_allow_html=True)
        else:
            if "múltiple" in pregunta['tipo']:
                respuestas_correctas_texto = ", ".join(pregunta['respuesta_correcta'].split(','))
                st.markdown(f'<div class="wrong-answer">❌ Incorrecto. Las respuestas correctas son: {respuestas_correctas_texto}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="wrong-answer">❌ Incorrecto. La respuesta correcta es: {pregunta["respuesta_correcta"]}</div>', unsafe_allow_html=True)
    
    st.markdown("---")

def main():
    st.title("❄️ Examen SnowPro Core Certification")
    st.markdown("---")
    
    # Inicializar el examinador
    if 'examen' not in st.session_state:
        st.session_state.examen = ExamenSnowflake('preguntas_snowflake.txt')
    
    if not st.session_state.examen.preguntas:
        st.warning("No se pudieron cargar las preguntas. Verifica el archivo.")
        return
    
    # Inicializar respuestas
    if 'respuestas_usuario' not in st.session_state:
        st.session_state.respuestas_usuario = {}
    
    # Sidebar
    with st.sidebar:
        st.header("📚 Navegación")
        
        total_preguntas = len(st.session_state.examen.preguntas)
        
        # Estadísticas de tipos de preguntas
        st.subheader("📊 Tipos de Preguntas")
        tipos_count = {}
        for p in st.session_state.examen.preguntas:
            tipo_base = p['tipo'].split('(')[0].strip()
            tipos_count[tipo_base] = tipos_count.get(tipo_base, 0) + 1
        
        for tipo, count in tipos_count.items():
            st.caption(f"{tipo}: {count} preguntas")
        
        st.markdown("---")
        
        # Configuración de bloques
        preguntas_por_bloque = st.selectbox(
            "Tamaño del bloque",
            options=[10, 20, 30, 50, 100],
            index=0
        )
        
        num_bloques = (total_preguntas + preguntas_por_bloque - 1) // preguntas_por_bloque
        
        bloque_seleccionado = st.selectbox(
            f"Selecciona bloque (1-{num_bloques})",
            options=range(1, num_bloques + 1),
            format_func=lambda x: f"Bloque {x} (Preguntas {(x-1)*preguntas_por_bloque + 1} - {min(x*preguntas_por_bloque, total_preguntas)})"
        )
        
        st.markdown("---")
        
        # Progreso
        st.subheader("📊 Progreso")
        respondidas = len(st.session_state.respuestas_usuario)
        porcentaje = (respondidas / total_preguntas) * 100 if total_preguntas > 0 else 0
        st.metric("Preguntas Respondidas", f"{respondidas}/{total_preguntas}")
        st.progress(porcentaje / 100)
        
        st.markdown("---")
        
        # Botones
        if st.button("🔄 Reiniciar Examen", use_container_width=True):
            st.session_state.respuestas_usuario = {}
            if 'mostrar_resultados' in st.session_state:
                del st.session_state.mostrar_resultados
            st.rerun()
        
        if st.button("📝 Ver Resultados", use_container_width=True):
            st.session_state.mostrar_resultados = True
            st.rerun()
    
    # Área principal
    if 'mostrar_resultados' in st.session_state and st.session_state.mostrar_resultados:
        mostrar_resultados()
    else:
        inicio = (bloque_seleccionado - 1) * preguntas_por_bloque + 1
        fin = min(bloque_seleccionado * preguntas_por_bloque, total_preguntas)
        
        st.header(f"📖 Bloque {bloque_seleccionado}")
        st.caption(f"Preguntas {inicio} - {fin} de {total_preguntas}")
        
        preguntas_bloque = st.session_state.examen.obtener_preguntas_por_bloque(inicio, fin)
        
        for pregunta in preguntas_bloque:
            mostrar_pregunta(pregunta, f"bloque_{bloque_seleccionado}")

def mostrar_resultados():
    """Muestra los resultados completos del examen"""
    st.header("📊 Resultados del Examen")
    
    total_preguntas = len(st.session_state.examen.preguntas)
    respuestas = st.session_state.respuestas_usuario
    
    correctas = 0
    incorrectas = 0
    no_respondidas = 0
    
    resultados_por_pregunta = []
    
    for pregunta in st.session_state.examen.preguntas:
        # Buscar la clave que coincide
        respuesta_usuario = None
        for key in respuestas:
            if key.startswith(f"pregunta_{pregunta['numero']}_"):
                respuesta_usuario = respuestas[key]
                break
        
        if respuesta_usuario is None:
            no_respondidas += 1
            resultados_por_pregunta.append({
                'numero': pregunta['numero'],
                'estado': 'No respondida',
                'respuesta_usuario': None,
                'respuesta_correcta': pregunta['respuesta_correcta'],
                'texto': pregunta['traduccion'][:100] + "...",
                'tipo': pregunta['tipo']
            })
        else:
            es_correcta = st.session_state.examen.verificar_respuesta(pregunta, respuesta_usuario)
            if es_correcta:
                correctas += 1
                estado = 'Correcta'
            else:
                incorrectas += 1
                estado = 'Incorrecta'
            
            # Formatear respuesta para mostrar
            if isinstance(respuesta_usuario, list):
                resp_mostrar = ', '.join(respuesta_usuario)
            else:
                resp_mostrar = respuesta_usuario
            
            resultados_por_pregunta.append({
                'numero': pregunta['numero'],
                'estado': estado,
                'respuesta_usuario': resp_mostrar,
                'respuesta_correcta': pregunta['respuesta_correcta'],
                'texto': pregunta['traduccion'][:100] + "...",
                'tipo': pregunta['tipo']
            })
    
    # Estadísticas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Preguntas", total_preguntas)
    with col2:
        st.metric("✅ Correctas", correctas)
    with col3:
        st.metric("❌ Incorrectas", incorrectas)
    with col4:
        st.metric("⏳ No respondidas", no_respondidas)
    
    porcentaje = (correctas / total_preguntas) * 100 if total_preguntas > 0 else 0
    st.progress(porcentaje / 100)
    st.markdown(f"<h2 style='text-align: center;'>Puntaje Final: {porcentaje:.1f}%</h2>", unsafe_allow_html=True)
    
    # Filtros
    st.subheader("📋 Detalle por Pregunta")
    filtro = st.radio(
        "Filtrar por:",
        ["Todas", "Correctas", "Incorrectas", "No respondidas"],
        horizontal=True
    )
    
    for resultado in resultados_por_pregunta:
        mostrar = False
        if filtro == "Todas":
            mostrar = True
        elif filtro == "Correctas" and resultado['estado'] == 'Correcta':
            mostrar = True
        elif filtro == "Incorrectas" and resultado['estado'] == 'Incorrecta':
            mostrar = True
        elif filtro == "No respondidas" and resultado['estado'] == 'No respondida':
            mostrar = True
        
        if mostrar:
            if resultado['estado'] == 'Correcta':
                color = "green"
                icono = "✅"
            elif resultado['estado'] == 'Incorrecta':
                color = "red"
                icono = "❌"
            else:
                color = "orange"
                icono = "⏳"
            
            badge_type = ""
            if "múltiple" in resultado['tipo']:
                badge_type = "🎯 Múltiple"
            elif resultado['tipo'] == "Verdadero/Falso":
                badge_type = "↕️ V/F"
            else:
                badge_type = "🔘 Única"
            
            st.markdown(f"""
            <div style='padding: 10px; margin: 5px 0; border-left: 4px solid {color}; background-color: #f9f9f9;'>
                <b>{icono} Pregunta {resultado['numero']}</b> 
                <span style='font-size: 12px; color: #666;'>({badge_type})</span><br>
                <small>{resultado['texto']}</small><br>
                <span style='color: {color};'>
                    Tu respuesta: {resultado['respuesta_usuario'] if resultado['respuesta_usuario'] else '—'} | 
                    Correcta: {resultado['respuesta_correcta']}
                </span>
            </div>
            """, unsafe_allow_html=True)
    
    if st.button("← Volver al Examen"):
        st.session_state.mostrar_resultados = False
        st.rerun()

if __name__ == "__main__":
    main()
