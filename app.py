import random
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Simulador para mi Esposita",
    page_icon="❤️",
    layout="centered",
)

st.title("Simulador para mi Esposita❤️")
st.caption("Simulación de preguntas de prevención de lavado de activos")

@st.cache_data
def cargar_preguntas():
    try:
        df = pd.read_excel("preguntas.xlsx")
    except FileNotFoundError:
        st.error("No se encontró el archivo preguntas.xlsx")
        st.stop()

    columnas_requeridas = [
        "id",
        "categoria",
        "pregunta",
        "alternativa_a",
        "alternativa_b",
        "alternativa_c",
        "alternativa_d",
        "correcta",
        "explicacion",
    ]

    faltantes = [columna for columna in columnas_requeridas if columna not in df.columns]

    if faltantes:
        st.error(
            "Faltan estas columnas en el Excel: "
            + ", ".join(faltantes)
        )
        st.stop()

    df = df.dropna(subset=["pregunta", "correcta"])
    return df


def iniciar_examen(df, cantidad):
    cantidad_real = min(cantidad, len(df))
    preguntas = df.sample(n=cantidad_real).to_dict("records")

    st.session_state.preguntas = preguntas
    st.session_state.indice = 0
    st.session_state.respuestas = {}
    st.session_state.examen_iniciado = True
    st.session_state.examen_finalizado = False


def reiniciar():
    st.session_state.clear()


df = cargar_preguntas()

if "examen_iniciado" not in st.session_state:
    st.session_state.examen_iniciado = False

if "examen_finalizado" not in st.session_state:
    st.session_state.examen_finalizado = False


if not st.session_state.examen_iniciado:
    st.subheader("Configura tu examen")

    maximo = len(df)

    cantidad = st.number_input(
        "Cantidad de preguntas",
        min_value=1,
        max_value=maximo,
        value=min(20, maximo),
        step=1,
    )

    st.info(f"Banco disponible: {maximo} preguntas")

    if st.button("Comenzar examen", type="primary", use_container_width=True):
        iniciar_examen(df, int(cantidad))
        st.rerun()


elif not st.session_state.examen_finalizado:
    preguntas = st.session_state.preguntas
    indice = st.session_state.indice
    pregunta = preguntas[indice]

    total = len(preguntas)
    progreso = (indice + 1) / total

    st.progress(progreso)
    st.write(f"Pregunta {indice + 1} de {total}")
    st.caption(f"Categoría: {pregunta['categoria']}")

    st.subheader(pregunta["pregunta"])

    alternativas = {
        "A": pregunta["alternativa_a"],
        "B": pregunta["alternativa_b"],
        "C": pregunta["alternativa_c"],
        "D": pregunta["alternativa_d"],
    }

    respuesta_guardada = st.session_state.respuestas.get(indice)

    respuesta = st.radio(
        "Selecciona una respuesta",
        options=list(alternativas.keys()),
        format_func=lambda letra: f"{letra}. {alternativas[letra]}",
        index=(
            list(alternativas.keys()).index(respuesta_guardada)
            if respuesta_guardada in alternativas
            else None
        ),
        key=f"respuesta_{indice}",
    )

    if respuesta:
        st.session_state.respuestas[indice] = respuesta

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "Anterior",
            disabled=indice == 0,
            use_container_width=True,
        ):
            st.session_state.indice -= 1
            st.rerun()

    with col2:
        st.write("")

    with col3:
        if indice < total - 1:
            if st.button("Siguiente", use_container_width=True):
                st.session_state.indice += 1
                st.rerun()
        else:
            if st.button(
                "Finalizar examen",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.examen_finalizado = True
                st.rerun()


else:
    preguntas = st.session_state.preguntas
    respuestas = st.session_state.respuestas

    correctas = 0
    incorrectas = []

    for indice, pregunta in enumerate(preguntas):
        respuesta_usuario = respuestas.get(indice)
        respuesta_correcta = str(pregunta["correcta"]).strip().upper()

        if respuesta_usuario == respuesta_correcta:
            correctas += 1
        else:
            incorrectas.append(
                {
                    "numero": indice + 1,
                    "pregunta": pregunta["pregunta"],
                    "respuesta_usuario": respuesta_usuario,
                    "respuesta_correcta": respuesta_correcta,
                    "explicacion": pregunta["explicacion"],
                }
            )

    total = len(preguntas)
    porcentaje = round((correctas / total) * 100, 1)

    st.title("Resultado")

    col1, col2, col3 = st.columns(3)

    col1.metric("Correctas", correctas)
    col2.metric("Incorrectas", total - correctas)
    col3.metric("Puntaje", f"{porcentaje}%")

    if porcentaje >= 75:
        st.success("Resultado aprobado")
    else:
        st.warning("Debes seguir estudiando")

    st.divider()
    st.subheader("Revisión de errores")

    if not incorrectas:
        st.success("Respondiste correctamente todas las preguntas.")
    else:
        for error in incorrectas:
            with st.expander(
                f"Pregunta {error['numero']}: {error['pregunta']}"
            ):
                respuesta_usuario = error["respuesta_usuario"] or "Sin respuesta"

                st.write(f"Tu respuesta: {respuesta_usuario}")
                st.write(
                    f"Respuesta correcta: {error['respuesta_correcta']}"
                )
                st.info(error["explicacion"])

    if st.button("Hacer otro examen", type="primary"):
        reiniciar()
        st.rerun()