import pandas as pd
import streamlit as st
import random_color_hex as RCH

COLS_TEXTO = ["Asignatura", "Profesor", "Programa", "Semestre"]

# ── Normalización ─────────────────────────────────────────────────────────────

def normalizar_texto(s):
    if pd.isna(s):
        return s
    return str(s).strip().title()

def cargar_datos(archivo):
    nombre = getattr(archivo, "name", "")
    if nombre.endswith(".csv"):
        df = pd.read_csv(archivo)
    else:
        df = pd.read_excel(archivo)
        
    df = df.dropna(subset=["Asignatura"])

    for col in COLS_TEXTO:
        if col in df.columns:
            df[col] = df[col].apply(normalizar_texto)

    if "Dia" in df.columns:
        df["Dia"] = df["Dia"].apply(lambda s: str(s).strip().title() if pd.notna(s) else s)
        df["Dia"] = df["Dia"].replace({"Miércoles": "Miercoles", "Sábado": "Sabado"})

    if "Grupo" in df.columns:
        df["Grupo"] = df["Grupo"].astype(str).str.strip()
        
    return df

# ── Horarios ──────────────────────────────────────────────────────────────────

def bloques_de_curso(filas):
    """Lista de (dia, inicio, fin) usando objetos de tiempo reales."""
    bloques = []
    
    for _, fila in filas.iterrows():
        dia = fila.get("Dia")
        h_inicio = fila.get("Hora_inicio")
        h_fin = fila.get("Hora_fin")
        
        if pd.notna(dia) and pd.notna(h_inicio) and pd.notna(h_fin):
            try:
                inicio = pd.to_datetime(str(h_inicio)).time()
                fin = pd.to_datetime(str(h_fin)).time()
                bloques.append((str(dia), inicio, fin))
            except Exception:
                pass
                
    return list(set(bloques))

# ── Bloques personales ────────────────────────────────────────────────────────

def bloques_personales_a_bloques(bloques_personales):
    """
    Convierte la lista de dicts de bloques personales (guardados en session_state)
    al mismo formato (dia, inicio, fin) que usa el resto del sistema.
    
    Cada dict debe tener: {"label": str, "dia": str, "inicio": "HH:MM", "fin": "HH:MM"}
    """
    result = []
    for b in bloques_personales:
        try:
            inicio = pd.to_datetime(b["inicio"]).time()
            fin    = pd.to_datetime(b["fin"]).time()
            result.append((b["dia"], inicio, fin))
        except Exception:
            pass
    return result

# ── Lógica principal ──────────────────────────────────────────────────────────

def hay_conflicto(bloques_a, bloques_b):
    for (da, ia, fa) in bloques_a:
        for (db, ib, fb) in bloques_b:
            if da == db and ia < fb and ib < fa:
                return True
    return False

def bloques_seleccionados(df, seleccion):
    """Todos los bloques de los cursos en seleccion (lista de tuplas)."""
    todos = []
    for asignatura, grupo in seleccion:
        filas = df[(df["Asignatura"] == asignatura) & (df["Grupo"] == str(grupo))]
        todos.extend(bloques_de_curso(filas))
    return todos

@st.cache_data
def cursos_compatibles(df, bloques_actuales):
    """DataFrame de cursos que no chocan con bloques_actuales."""
    resultado = []
    for (asignatura, grupo), filas in df.groupby(["Asignatura", "Grupo"]):
        b = bloques_de_curso(filas)
        if b and not hay_conflicto(b, bloques_actuales):
            fila = filas.iloc[0]
            resultado.append({
                "Asignatura": asignatura,
                "Grupo": grupo,
                "Profesor": fila.get("Profesor", ""),
                "Programa": fila.get("Programa", ""),
            })
    return pd.DataFrame(resultado)

# ── Calendario ────────────────────────────────────────────────────────────────

FECHA_BASE = {
    "Lunes":     "2024-01-01",
    "Martes":    "2024-01-02",
    "Miercoles": "2024-01-03",
    "Jueves":    "2024-01-04",
    "Viernes":   "2024-01-05",
    "Sabado":    "2024-01-06",
    "Domingo":   "2024-01-07"
}

# Creación de colores. 

if "colores" not in st.session_state:
    st.session_state["colores"] = {}

def obtener_color(asignatura, grupo):
    key = f"{asignatura}-{grupo}"

    if key not in st.session_state["colores"]:
        st.session_state["colores"][key] = RCH.main(how_different_should_colors_be='l') #l = very different, python library. 
    return st.session_state["colores"][key]


def eventos_calendario(df, seleccion):
    """Lista de eventos de materias en formato FullCalendar."""
    eventos = []
    for asignatura, grupo in seleccion:
        filas = df[(df["Asignatura"] == asignatura) & (df["Grupo"] == str(grupo))]
        color =  obtener_color(asignatura, grupo)
        
        for (dia, inicio, fin) in bloques_de_curso(filas):
            fecha = FECHA_BASE.get(dia)
            if fecha:
                eventos.append({
                    "title": f"{asignatura} — G{grupo}",
                    "start": f"{fecha}T{inicio.strftime('%H:%M:%S')}",
                    "end":   f"{fecha}T{fin.strftime('%H:%M:%S')}",
                    "color": color,
                })
    return eventos

def eventos_bloques_personales(bloques_personales):
    """
    Lista de eventos de bloqueos personales en formato FullCalendar.
    Se muestran como fondo sombreado (display: background) para diferenciarlos
    visualmente de las materias seleccionadas.
    """
    eventos = []
    for b in bloques_personales:
        fecha = FECHA_BASE.get(b["dia"])
        if fecha:
            eventos.append({
                "title":   f"🔒 {b['label']}",
                "start":   f"{fecha}T{b['inicio']}:00",
                "end":     f"{fecha}T{b['fin']}:00",
                "display": "background",
                "color":   "#A13569",
            })
    return eventos
