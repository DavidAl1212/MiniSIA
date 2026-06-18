import datetime
import streamlit as st
import pandas as pd
from streamlit_calendar import calendar as st_calendar
from data import *

# ── Configuración ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Micro-SIA", layout="wide")

# ── Constantes de días ────────────────────────────────────────────────────────
DIAS = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]

# Suena redundante, pero el cambio son las tildes. 
DIAS_LABELS = {
    "Lunes":     "Lunes",
    "Martes":    "Martes",
    "Miercoles": "Miércoles",
    "Jueves":    "Jueves",
    "Viernes":   "Viernes",
    "Sabado":    "Sábado",
    "Domingo":   "Domingo",
}

# ── Sidebar: Bloques personales ───────────────────────────────────────────────
with st.sidebar:
    st.header("🔒 Bloquear horas")
    st.caption(
        "Marca el tiempo que no estás disponible. "
        "Puedes elegir varios días a la vez para bloques fijos (ej: trabajo de lunes a viernes)."
    )
    st.divider()

    dias_sel = st.multiselect(
        "Día(s)",
        options=DIAS,
        default=["Lunes"],
        format_func=lambda d: DIAS_LABELS[d],
        key="sb_dias",
        placeholder="Selecciona uno o más días...",
    )

    col_ini, col_fin = st.columns(2)
    with col_ini:
        h_ini = st.time_input("Inicio", value=datetime.time(5, 0), key="sb_ini", step=1800)
    with col_fin:
        h_fin = st.time_input("Fin", value=datetime.time(20, 0), key="sb_fin", step=1800)

    label_bloque = st.text_input(
        "Etiqueta", placeholder="Ej: Trabajo, Gym...", key="sb_label"
    )

    if st.button("Agregar bloque(s)", use_container_width=True, type="primary"):
        if not dias_sel:
            st.error("Selecciona al menos un día.")
        elif not label_bloque.strip():
            st.error("Escribe una etiqueta para el bloque.")
        elif h_ini >= h_fin:
            st.error("La hora de fin debe ser mayor al inicio. Talvez al revés?")
        else:
            nuevos = [
                {
                    "label":  label_bloque.strip(),
                    "dia":    dia,
                    "inicio": h_ini.strftime("%H:%M"),
                    "fin":    h_fin.strftime("%H:%M"),
                }
                for dia in dias_sel
            ]
            st.session_state.setdefault("bloques_personales", []).extend(nuevos)
            n = len(nuevos)
            st.success(f"{'1 bloque agregado' if n == 1 else f'{n} bloques agregados'}.")

    # ── Lista de bloques activos ──
    bloques_pers = st.session_state.get("bloques_personales", [])

    if bloques_pers:
        st.divider()
        st.caption(f"**{len(bloques_pers)} bloque(s) activo(s):**")
        for i, b in enumerate(bloques_pers):
            col_info, col_del = st.columns([4, 1]) # Distribución de los botones - la X es proporcionalmente más pequeño
            with col_info:
                st.write(
                    f"🔒 **{b['label']}** — {DIAS_LABELS[b['dia']]}, "
                    f"{b['inicio']}–{b['fin']}"
                )
            with col_del:
                if st.button("✕", key=f"del_{i}", help="Eliminar bloque"):
                    st.session_state["bloques_personales"].pop(i)
                    st.rerun()
    else:
        st.caption("Sin bloques agregados aún.")

# ── Encabezado ──────────────────────────────────────────────────────
st.title("Micro-SIA 📝")
st.write("Carga la oferta de materias y arma tu horario sin cruces.")
st.divider()

# ── Pasos ─────────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True):
        st.subheader("① Sube archivos")
        st.caption("Carga uno o varios archivos `.xlsx` o `.csv` con la oferta de materias.")
with col2:
    with st.container(border=True):
        st.subheader("② Selecciona clases")
        st.caption("Escoge las materias y grupos que quieres cursar este semestre.")
with col3:
    with st.container(border=True):
        st.subheader("③ Organiza")
        st.caption("Visualiza tu horario y busca materias compatibles con tu agenda.")

st.divider()

# ── Subir archivos ────────────────────────────────────────────────────────────
col_up, col_fmt = st.columns([1, 1], gap="large") # mismo que decir st.columns(2) pero mejor practica para distruibuir el espacio 

with col_up:
    st.subheader("📁 Cargar oferta de materias")
    archivos = st.file_uploader(
        "Arrastra o selecciona tus archivos",
        accept_multiple_files=True,
        type=["xlsx", "csv"],
    )

    if archivos:
        archivos_validos   = [a for a in archivos if a.name.endswith((".xlsx", ".csv"))]
        archivos_invalidos = [a for a in archivos if not a.name.endswith((".xlsx", ".csv"))]

        for a in archivos_invalidos:
            st.error(f"❌ `{a.name}` no es un formato válido.")

        if archivos_validos:
            n = len(archivos_validos)
            st.success(f"{'1 archivo listo' if n == 1 else f'{n} archivos listos'}:")
            for a in archivos_validos:
                size_kb = round(len(a.getvalue()) / 1024, 1)
                st.write(f"📄 `{a.name}` — {size_kb} KB")

            if st.button("✅ Confirmar y procesar", type="primary", use_container_width=True):
                with st.spinner("Procesando archivos..."):
                    frames = [cargar_datos(a) for a in archivos_validos]
                    st.session_state["df"] = pd.concat(frames, ignore_index=True)
                st.success("¡Listo! Selecciona tus materias abajo 👇")

with col_fmt:
    st.subheader("ℹ️ Formato esperado")
    st.caption("Los archivos deben tener las siguientes columnas:")
    st.dataframe(
        pd.DataFrame({
            "Columna": [
                "Asignatura", "Grupo", "Dia",
                "Hora_inicio", "Hora_fin", "Profesor", "Programa",
            ],
            "Descripción": [
                "Nombre del curso",
                "Número o código de grupo",
                "Lunes, Martes…",
                'Ej: "10:00"',
                'Ej: "12:00"',
                "Nombre del docente (opcional)",
                "Facultad o carrera (opcional)",
            ],
        }),
        hide_index=True,
        use_container_width=True,
    )

# ── Testing: para verificar que se suban archivos ──────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.stop()

st.divider()
df = st.session_state["df"]

# ── Selección de materias ─────────────────────────────────────────────────────
st.subheader("📚 Selecciona tus materias")

opciones = sorted(
    list(df[["Asignatura", "Grupo"]].drop_duplicates().itertuples(index=False, name=None)) #Quita los duplicados porque el archivo base tiene duplicados. 
)

seleccion = st.multiselect(
    "Busca y elige tus cursos:",
    options=opciones, # Tiene que ser dataframe, set o lista. Entonces tiene una lista de tuplas. Ejm: [(Calculo, 1), (Calculo, 2)]
    format_func=lambda x: f"{x[0]}  —  Grupo {x[1]}", 
    placeholder="Escribe el nombre de una materia...",
)

bloques_pers_activos = st.session_state.get("bloques_personales", [])

if not seleccion:
    if bloques_pers_activos:
        st.info(
            f"Tienes **{len(bloques_pers_activos)} bloque(s)** personal(es) activo(s). "
            "Selecciona al menos una materia para ver el horario."
        )
    else:
        st.info("Selecciona al menos una materia para ver el horario.")
    st.stop()

# ── Tabs: Horario / Materias compatibles ──────────────────────────────────────
st.divider()
tab_horario, tab_compatibles = st.tabs(["🗓️ Horario semanal", "🔍 Materias disponibles"])

# ── Tab 1: Horario ────────────────────────────────────────────────────────────
with tab_horario:
    if bloques_pers_activos:
        st.info(
            f"🔒 Las zonas sombreadas representan tus "
            f"**{len(bloques_pers_activos)} bloque(s) bloqueados."
        )

    eventos = eventos_calendario(df, seleccion) + eventos_bloques_personales(bloques_pers_activos)

    st_calendar(
        events=eventos,
        options={
            "initialView":     "timeGridWeek",
            "initialDate":     "2024-01-01",
            "locale":          "es",
            "headerToolbar":   {"left": "", "center": "Vista previa de horario", "right": ""},
            "dayHeaderFormat": {"weekday": "long"},
            "slotMinTime":     "07:00:00",
            "slotMaxTime":     "22:00:00",
            "allDaySlot":      False,
            "height":          620,
            "slotLabelFormat": {"hour": "2-digit", "minute": "2-digit", "hour12": False},
            "nowIndicator":    True,
        },
    )

# ── Tab 2: Materias compatibles ───────────────────────────────────────────────
with tab_compatibles:
    st.write(
        "Busca cursos que no se crucen con tu horario actual"
        + (f" ni con tus **{len(bloques_pers_activos)} bloque(s) personal(es)**." if bloques_pers_activos else ".")
    )

    if st.button("Buscar materias compatibles", type="primary", use_container_width=True):
        with st.spinner("Analizando compatibilidades..."):
            bloques_cursos    = bloques_seleccionados(df, seleccion)
            bloques_pers_conv = bloques_personales_a_bloques(bloques_pers_activos)
            todos_bloques     = bloques_cursos + bloques_pers_conv

            compatibles = cursos_compatibles(df, todos_bloques)

            ya_sel = {(a, str(g)) for a, g in seleccion}
            compatibles = compatibles[
                ~compatibles.apply(
                    lambda r: (r["Asignatura"], str(r["Grupo"])) in ya_sel, axis=1
                )
            ]

        st.session_state["compatibles"] = compatibles

    if "compatibles" in st.session_state:
        compatibles = st.session_state["compatibles"]
        # Toca volver a declarar compatibles porque el anterior es una variable unica dentro del if anterior, si no entonces usar todo el tiempo session_state[compatibles]

        nota_pers = (
            f" (incluyendo {len(bloques_pers_activos)} bloque(s) personal(es))"
            if bloques_pers_activos else ""
        )
        st.success(f"✅ **{len(compatibles)}** materias sin conflicto{nota_pers}")

        if compatibles.empty:
            st.warning("No se encontraron materias adicionales sin conflicto.")
        else:
            busqueda = st.text_input(
                "🔎 Filtrar por nombre:", placeholder="Ej: cálculo, historia..."
            )
            df_mostrar = compatibles.copy()

            if busqueda:
                df_mostrar = df_mostrar[
                    df_mostrar["Asignatura"].str.contains(busqueda, case=False, na=False)
                ]
                if df_mostrar.empty:
                    st.info(f'Sin coincidencias para "{busqueda}".')

            if not df_mostrar.empty:
                st.dataframe(
                    df_mostrar.reset_index(drop=True),
                    use_container_width=True,
                    hide_index=True,
                )