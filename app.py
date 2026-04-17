import streamlit as st
import json

st.set_page_config(page_title="Cuestionario", layout="centered")

st.title(" Cuestionario por bloques")

# ------------------------
# Cargar preguntas
# ------------------------
@st.cache_data
def cargar_preguntas():
    with open("preguntas.json", "r", encoding="utf-8") as f:
        return json.load(f)

preguntas = cargar_preguntas()

# ------------------------
# Configuración bloques
# ------------------------
tam_bloque = 100
total_bloques = (len(preguntas) // tam_bloque) + (1 if len(preguntas) % tam_bloque > 0 else 0)

bloque = st.selectbox(
    "Selecciona el bloque:",
    options=list(range(1, total_bloques + 1)),
    format_func=lambda x: f"{((x-1)*100)+1} - {min(x*100, len(preguntas))}"
)

# ------------------------
# Inicializar estado
# ------------------------
if "bloque_actual" not in st.session_state or st.session_state.bloque_actual != bloque:
    inicio = (bloque - 1) * tam_bloque
    fin = inicio + tam_bloque

    st.session_state.preguntas = preguntas[inicio:fin]
    st.session_state.index = 0
    st.session_state.respuestas_usuario = [None] * len(st.session_state.preguntas)
    st.session_state.bloque_actual = bloque

# ------------------------
# Pregunta actual
# ------------------------
preguntas_bloque = st.session_state.preguntas
index = st.session_state.index
p = preguntas_bloque[index]

st.subheader(f"Pregunta {index + 1} de {len(preguntas_bloque)}")
st.write(p["pregunta"])

# Mostrar opciones
respuesta_guardada = st.session_state.respuestas_usuario[index]

if p["tipo"] == "multiple":
    respuesta = st.radio(
        "Selecciona una opción:",
        p["opciones"],
        index=p["opciones"].index(respuesta_guardada) if respuesta_guardada in p["opciones"] else None
    )
else:
    opciones_vf = ["Verdadero", "Falso"]
    respuesta = st.radio(
        "Selecciona:",
        opciones_vf,
        index=opciones_vf.index(respuesta_guardada) if respuesta_guardada in opciones_vf else None
    )

# Guardar respuesta
st.session_state.respuestas_usuario[index] = respuesta

# ------------------------
# Botones navegación
# ------------------------
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("⬅ Anterior"):
        if st.session_state.index > 0:
            st.session_state.index -= 1
            st.rerun()

with col2:
    if st.button(" Siguiente"):
        if st.session_state.index < len(preguntas_bloque) - 1:
            st.session_state.index += 1
            st.rerun()

with col3:
    if st.button(" Finalizar"):
        st.session_state.finalizado = True
        st.rerun()

# ------------------------
# Resultado final
# ------------------------
if "finalizado" in st.session_state and st.session_state.finalizado:

    puntaje = 0

    for i, p in enumerate(preguntas_bloque):
        if st.session_state.respuestas_usuario[i] == p["respuesta"]:
            puntaje += 1

    st.success("🎉 Cuestionario terminado")
    st.write(f"Puntaje: {puntaje}/{len(preguntas_bloque)}")

    if st.button(" Reiniciar bloque"):
        del st.session_state["finalizado"]
        st.session_state.index = 0
        st.session_state.respuestas_usuario = [None] * len(preguntas_bloque)
        st.rerun()