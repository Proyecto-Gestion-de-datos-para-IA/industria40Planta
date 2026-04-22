import streamlit as st
import pandas as pd
import plotly.express as px
import s3fs
from datetime import datetime, timedelta, timezone # Para el filtro de tiempo
import time

st.set_page_config(page_title="Analítica Histórica V2.5", page_icon="📊", layout="wide")

#"""
##=============================================================================
#MÓDULO: Analítica Histórica y Exploración del Data Lake
#ARCHIVO: pages/5_📊_Analitica_Historica.py
#VERSIÓN: 2.5
#=============================================================================
#DESCRIPCIÓN:
#Conexión directa a la capa de almacenamiento masivo (MinIO/S3).
#Extrae y procesa los archivos Parquet generados por Apache Spark para 
#realizar análisis exploratorio de datos (EDA) a largo plazo, sin 
#sobrecargar la base de datos operacional (Postgres).
#=============================================================================
#"""

st.title("📊 Analítica Histórica de la Planta")
st.write("Exploración profunda del Data Lake (MinIO) para identificación de tendencias a largo plazo.")

# =============================================================================
# 1. CONEXIÓN AL DATA LAKE (MINIO)
# =============================================================================
# Usamos caché para no descargar gigabytes de datos cada vez que mueves un botón
@st.cache_data(ttl=300) 
def cargar_data_lake():
    # 1. Configuración de conexión (Path Style para Docker)
    storage_options = {
        "key": "admin",
        "secret": "Industria40_Secure",
        "client_kwargs": {"endpoint_url": "http://minio:9000"},
        "config_kwargs": {"s3": {"addressing_style": "path"}}
    }
    
    try:
        fs = s3fs.S3FileSystem(**storage_options)
        
        # 1. Obtenemos los metadatos de los archivos (incluyendo la fecha de creación)
        # info() nos da el 'LastModified' de cada archivo en MinIO
        archivos_info = fs.ls("datasets/historico_planta", detail=True)
        
        # 2. Definimos nuestra ventana de tiempo (ej: últimas 4 horas)
        hace_4_horas = datetime.now(timezone.utc) - timedelta(hours=4)
        
        # 3. Filtramos: Solo archivos .parquet Y que sean nuevos
        archivos_validos = [
            f['name'] for f in archivos_info 
            if f['name'].endswith(".parquet") and f['LastModified'] > hace_4_horas
        ]
        
        if not archivos_validos:
            st.warning("No hay datos nuevos en las últimas 4 horas.")
            return None

        # 4. ABRIMOS MANUALMENTE (Para evitar el error de buffer/URL)
        lista_dfs = []
        for f in archivos_validos:
            with fs.open(f) as f_obj:
                # Al pasarle el objeto abierto (f_obj), no necesitamos storage_options aquí
                lista_dfs.append(pd.read_parquet(f_obj, engine='pyarrow'))
        
        # Juntamos todos los archivos en un solo DataFrame
        if not lista_dfs:
            return None
            
        df = pd.concat(lista_dfs, ignore_index=True)
        
        # 5. Parseo de la ventana de Spark
        # Spark suele guardar el 'window' como un diccionario/struct
        df['timestamp_ventana'] = df['window'].apply(lambda x: x['end'] if isinstance(x, dict) else x)
        df['timestamp_ventana'] = pd.to_datetime(df['timestamp_ventana'])
        df = df.sort_values('timestamp_ventana')
        
        return df
        
    except Exception as e:
        st.error(f"💥 Error al leer el Data Lake: {e}")
        return None

with st.spinner("⏳ Extrayendo millones de registros del Data Lake (MinIO)..."):
    df_historico = cargar_data_lake()

# =============================================================================
# 2. RENDERIZADO DE ANALÍTICA VISUAL
# =============================================================================
if df_historico is not None and not df_historico.empty:
    
    # KPIs Históricos
    st.subheader("Resumen del Periodo")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Ventanas Procesadas", f"{len(df_historico):,}")
    col2.metric("Picos de Temperatura Crítica", len(df_historico[df_historico['t_avg'] > 85]))
    col3.metric("Picos de Vibración Crítica", len(df_historico[df_historico['v_avg'] > 40]))
    
    st.divider()

    # Layout de gráficos
    graf_izq, graf_der = st.columns(2)
    
    with graf_izq:
        st.subheader("Dispersión: Temperatura vs Vibración")
        st.caption("Revela cómo se agrupan los estados de salud de la máquina.")
        
        # Mapeo de colores según la decisión de la IA (Semaforo)
        color_map = {0: 'green', 1: 'orange', 2: 'red'}
        df_historico['Estado_IA'] = df_historico['decision_id'].map({0: 'Normal', 1: 'Riesgo', 2: 'Falla'})
        
        fig_scatter = px.scatter(
            df_historico, 
            x="t_avg", 
            y="v_avg", 
            color="Estado_IA",
            color_discrete_map={'Normal': '#8fce00', 'Riesgo': '#ffcc00', 'Falla': '#ff0000'},
            hover_data=["maquina", "timestamp_ventana"],
            labels={"t_avg": "Temperatura Media (°C)", "v_avg": "Vibración Media (Hz)"}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    with graf_der:
        st.subheader("Máquinas más Problemáticas")
        st.caption("Acumulado histórico de estados de Riesgo y Falla Crítica.")
        
        # Filtramos solo eventos anómalos
        df_fallas = df_historico[df_historico['decision_id'] > 0]
        conteo_fallas = df_fallas.groupby(['maquina', 'Estado_IA']).size().reset_index(name='Conteo')
        
        fig_barras = px.bar(
            conteo_fallas, 
            x="maquina", 
            y="Conteo", 
            color="Estado_IA",
            color_discrete_map={'Riesgo': '#ffcc00', 'Falla': '#ff0000'},
            barmode='stack'
        )
        st.plotly_chart(fig_barras, use_container_width=True)

    st.divider()
    
    st.subheader("Línea de Tiempo Global")
    # Selector multimaquina
    maquinas_disponibles = df_historico['maquina'].unique()
    maq_seleccionadas = st.multiselect("Filtrar por Máquinas:", maquinas_disponibles, default=maquinas_disponibles[:3] if len(maquinas_disponibles) > 3 else maquinas_disponibles)
    
    df_filtrado = df_historico[df_historico['maquina'].isin(maq_seleccionadas)]
    
    fig_line = px.line(
        df_filtrado, 
        x="timestamp_ventana", 
        y="v_avg", 
        color="maquina",
        labels={"timestamp_ventana": "Tiempo", "v_avg": "Vibración Media (Hz)"}
    )
    st.plotly_chart(fig_line, use_container_width=True)

else:
    st.info("Aún no hay suficientes datos históricos guardados en MinIO. El Data Lake se está poblando...")