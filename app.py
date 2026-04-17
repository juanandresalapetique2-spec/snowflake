import streamlit as st
import re
from typing import List, Dict
import json

# Configuración de la página
st.set_page_config(
    page_title="Examen SnowPro Core",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para mejor apariencia
st.markdown("""
<style>
    .stButton button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
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
    .question-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .progress-text {
        font-size: 14px;
        color: #666;
        margin-top: 10px;
    }
    .stRadio > div {
        margin: 10px 0;
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
                    
                    pregunta = self.extraer_pregunta(texto_pregunta, num_pregunta)
                    if pregunta:
                        self.preguntas.append(pregunta)
            
            st.success(f"✅ Cargadas {len(self.preguntas)} preguntas correctamente")
            
        except Exception as e:
            st.error(f"❌ Error al cargar preguntas: {str(e)}")
            self.preguntas = []
    
    def extraer_pregunta(self, texto, num_pregunta):
        """Extrae la información de una pregunta del texto"""
        # Extraer texto original
        original_match = re.search(r'Texto original:\s*(.+?)(?=Traducción:|$)', texto, re.DOTALL)
        original = original_match.group(1).strip() if original_match else ""
        
        # Extraer traducción
        traduccion_match = re.search(r'Traducción:\s*(.+?)(?=A\.|B\.|C\.|D\.|Respuesta correcta:|$)', texto, re.DOTALL)
        traduccion = traduccion_match.group(1).strip() if traduccion_match else ""
        
        # Extraer opciones
        opciones = {}
        opciones_raw = re.findall(r'([A-D])\.\s*(.+?)(?=[A-D]\.|Respuesta correcta:|$)', texto, re.DOTALL)
        for letra, texto_opcion in opciones_raw:
            opciones[letra] = texto_opcion.strip()
        
        # Extraer respuesta correcta
        respuesta_match = re.search(r'Respuesta correcta:\s*([A-D, ]+)', texto)
        respuesta_correcta = respuesta_match.group(1).strip() if respuesta_match else ""
        
        # Extraer tipo
        tipo_match = re.search(r'Tipo:\s*(.+)', texto)
        tipo = tipo_match.group(1).strip() if tipo_match else "Selección única"
        
        # Si no se encontraron datos específicos, intentar formato alternativo
        if not original and not traduccion:
            lineas = texto.strip().split('\n')
            if lineas:
                original = lineas[0]
                traduccion = lineas[1] if len(lineas) > 1 else ""
        
        return {
            'numero': num_pregunta,
            'original': original,
            'traduccion': traduccion,
            'opciones': opciones,
            'respuesta_correcta': respuesta_correcta,
            'tipo': tipo
        }
    
    def obtener_preguntas_por_bloque(self, inicio, fin):
        """Obtiene un bloque de preguntas"""
        return self.preguntas[inicio-1:fin]

def main():
    st.title("❄️ Examen SnowPro Core Certification")
    st.markdown("---")
    
    # Inicializar el examinador
    if 'examen' not in st.session_state:
        st.session_state.examen = ExamenSnowflake('preguntas_snowflake.txt')
    
    if not st.session_state.examen.preguntas:
        st.warning("No se pudieron cargar las preguntas. Verifica el archivo.")
        return
    
    # Sidebar para navegación
    with st.sidebar:
        st.header("📚 Navegación")
        
        # Configuración del bloque
        total_preguntas = len(st.session_state.examen.preguntas)
        
        st.subheader("Configuración del Examen")
        
        # Seleccionar bloque de preguntas
        preguntas_por_bloque = st.selectbox(
            "Tamaño del bloque",
            options=[10, 20, 30, 50, 100],
            index=0
        )
        
        # Calcular número de bloques
        num_bloques = (total_preguntas + preguntas_por_bloque - 1) // preguntas_por_bloque
        
        bloque_seleccionado = st.selectbox(
            f"Selecciona bloque (1-{num_bloques})",
            options=range(1, num_bloques + 1),
            format_func=lambda x: f"Bloque {x} (Preguntas {(x-1)*preguntas_por_bloque + 1} - {min(x*preguntas_por_bloque, total_preguntas)})"
        )
        
        st.markdown("---")
        
        # Estadísticas
        st.subheader("📊 Progreso")
        
        if 'respuestas_usuario' in st.session_state:
            respondidas = len(st.session_state.respuestas_usuario)
            porcentaje = (respondidas / total_preguntas) * 100
            st.metric("Preguntas Respondidas", f"{respondidas}/{total_preguntas}")
            st.progress(porcentaje / 100)
        
        st.markdown("---")
        
        # Botones de control
        if st.button("🔄 Reiniciar Examen", use_container_width=True):
            if 'respuestas_usuario' in st.session_state:
                del st.session_state.respuestas_usuario
            if 'mostrar_resultados' in st.session_state:
                del st.session_state.mostrar_resultados
            st.rerun()
        
        if st.button("📝 Ver Resultados", use_container_width=True):
            st.session_state.mostrar_resultados = True
            st.rerun()
    
    # Área principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header(f"📖 Bloque {bloque_seleccionado}")
        
        # Calcular rango de preguntas
        inicio = (bloque_seleccionado - 1) * preguntas_por_bloque + 1
        fin = min(bloque_seleccionado * preguntas_por_bloque, total_preguntas)
        
        st.caption(f"Preguntas {inicio} - {fin} de {total_preguntas}")
        
        # Mostrar preguntas del bloque
        preguntas_bloque = st.session_state.examen.obtener_preguntas_por_bloque(inicio, fin)
        
        # Inicializar respuestas del usuario si no existe
        if 'respuestas_usuario' not in st.session_state:
            st.session_state.respuestas_usuario = {}
        
        # Mostrar cada pregunta
        for pregunta in preguntas_bloque:
            with st.container():
                st.markdown(f"### Pregunta {pregunta['numero']}")
                
                with st.expander("📖 Ver en inglés", expanded=False):
                    st.markdown(pregunta['original'])
                
                st.markdown(f"**{pregunta['traduccion']}**")
                
                # Mostrar opciones
                opcion_seleccionada = None
                
                if pregunta['tipo'] == "Selección única":
                    opciones_lista = [f"{letra}. {texto}" for letra, texto in pregunta['opciones'].items()]
                    clave_respuesta = f"pregunta_{pregunta['numero']}"
                    
                    respuesta_actual = st.session_state.respuestas_usuario.get(clave_respuesta, None)
                    indice_actual = None
                    
                    if respuesta_actual and respuesta_actual in pregunta['opciones']:
                        indice_actual = opciones_lista.index(f"{respuesta_actual}. {pregunta['opciones'][respuesta_actual]}")
                    
                    opcion_seleccionada = st.radio(
                        "Selecciona tu respuesta:",
                        options=opciones_lista,
                        key=clave_respuesta,
                        index=indice_actual if indice_actual is not None else None,
                        label_visibility="collapsed"
                    )
                    
                    if opcion_seleccionada:
                        letra_seleccionada = opcion_seleccionada[0]
                        st.session_state.respuestas_usuario[clave_respuesta] = letra_seleccionada
                        
                        # Verificar respuesta
                        if letra_seleccionada == pregunta['respuesta_correcta']:
                            st.markdown('<div class="correct-answer">✅ ¡Correcto!</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="wrong-answer">❌ Incorrecto. La respuesta correcta es: {pregunta["respuesta_correcta"]}</div>', unsafe_allow_html=True)
                
                st.markdown("---")
    
    with col2:
        st.header("ℹ️ Información")
        
        # Mostrar información de la pregunta actual
        if preguntas_bloque:
            primera_pregunta = preguntas_bloque[0]
            st.info(f"""
            **Tipo de pregunta:** {primera_pregunta['tipo']}
            
            **Total de preguntas en este bloque:** {len(preguntas_bloque)}
            
            **Consejo:** Las preguntas de selección única tienen una sola respuesta correcta.
            """)
        
        # Mostrar resumen de respuestas del bloque
        if 'respuestas_usuario' in st.session_state:
            respondidas_bloque = 0
            correctas_bloque = 0
            
            for pregunta in preguntas_bloque:
                clave = f"pregunta_{pregunta['numero']}"
                if clave in st.session_state.respuestas_usuario:
                    respondidas_bloque += 1
                    if st.session_state.respuestas_usuario[clave] == pregunta['respuesta_correcta']:
                        correctas_bloque += 1
            
            if respondidas_bloque > 0:
                porcentaje_bloque = (correctas_bloque / respondidas_bloque) * 100
                st.markdown("### 📈 Rendimiento del Bloque")
                st.metric("Respuestas en este bloque", f"{respondidas_bloque}/{len(preguntas_bloque)}")
                st.metric("Aciertos en este bloque", f"{correctas_bloque}/{respondidas_bloque}")
                st.metric("Porcentaje", f"{porcentaje_bloque:.1f}%")
                
                # Mostrar barra de progreso
                st.progress(correctas_bloque / respondidas_bloque if respondidas_bloque > 0 else 0)

def mostrar_resultados():
    """Muestra los resultados completos del examen"""
    st.header("📊 Resultados del Examen")
    
    total_preguntas = len(st.session_state.examen.preguntas)
    respuestas = st.session_state.respuestas_usuario
    
    correctas = 0
    resultados_por_pregunta = []
    
    for pregunta in st.session_state.examen.preguntas:
        clave = f"pregunta_{pregunta['numero']}"
        if clave in respuestas:
            es_correcta = respuestas[clave] == pregunta['respuesta_correcta']
            if es_correcta:
                correctas += 1
            resultados_por_pregunta.append({
                'numero': pregunta['numero'],
                'correcta': es_correcta,
                'respuesta_usuario': respuestas[clave],
                'respuesta_correcta': pregunta['respuesta_correcta'],
                'texto': pregunta['traduccion'][:100] + "..."
            })
    
    # Estadísticas generales
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Preguntas", total_preguntas)
    with col2:
        st.metric("Respuestas Correctas", correctas)
    with col3:
        porcentaje = (correctas / total_preguntas) * 100 if total_preguntas > 0 else 0
        st.metric("Porcentaje", f"{porcentaje:.1f}%")
    
    # Gráfico de progreso
    st.progress(porcentaje / 100)
    
    # Mostrar resultados detallados
    st.subheader("📋 Detalle por Pregunta")
    
    # Filtros
    filtro = st.radio(
        "Filtrar por:",
        ["Todas", "Correctas", "Incorrectas", "No respondidas"],
        horizontal=True
    )
    
    for resultado in resultados_por_pregunta:
        mostrar = False
        if filtro == "Todas":
            mostrar = True
        elif filtro == "Correctas" and resultado['correcta']:
            mostrar = True
        elif filtro == "Incorrectas" and not resultado['correcta']:
            mostrar = True
        
        if mostrar:
            icono = "✅" if resultado['correcta'] else "❌"
            color = "green" if resultado['correcta'] else "red"
            st.markdown(f"""
            <div style='padding: 10px; margin: 5px 0; border-left: 4px solid {color}; background-color: #f9f9f9;'>
                <b>{icono} Pregunta {resultado['numero']}</b><br>
                <small>{resultado['texto']}</small><br>
                <span style='color: {color};'>
                    Tu respuesta: {resultado['respuesta_usuario']} | 
                    Correcta: {resultado['respuesta_correcta']}
                </span>
            </div>
            """, unsafe_allow_html=True)
    
    # Botón para volver
    if st.button("← Volver al Examen"):
        st.session_state.mostrar_resultados = False
        st.rerun()

# Ejecutar la aplicación
if __name__ == "__main__":
    if 'mostrar_resultados' in st.session_state and st.session_state.mostrar_resultados:
        mostrar_resultados()
    else:
        main()
