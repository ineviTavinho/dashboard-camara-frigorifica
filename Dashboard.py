import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import datetime
import os
import sys
import base64

# 1. Configuração da Página
st.set_page_config(page_title="Dashboard - Câmara Frigorífica", layout="wide")

# ==========================================
# FUNÇÃO INTELIGENTE DE CAMINHOS (PYINSTALLER)
# ==========================================
def obter_caminho_arquivo(nome_arquivo):
    """Encontra o arquivo tanto no modo de desenvolvimento quanto no .exe gerado"""
    if getattr(sys, 'frozen', False):
        # Se estiver rodando como executável (PyInstaller)
        pasta_base = sys._MEIPASS
    else:
        # Se estiver rodando como script Python normal
        pasta_base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(pasta_base, nome_arquivo)

# ==========================================
# BARRA LATERAL (SIDEBAR) & LOGO
# ==========================================

caminho_logo = obter_caminho_arquivo("logo.png")

# A caixa protetora branca da Logo da Instituição
if os.path.exists(caminho_logo):
    with open(caminho_logo, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    
    st.sidebar.markdown(
        f"""
        <div style="background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; display: flex; justify-content: center; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
            <img src="data:image/png;base64,{encoded_string}" style="max-width: 100%;">
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.sidebar.warning("📌 Logo não encontrada. Verifique se 'logo.png' foi empacotada corretamente.")

st.sidebar.markdown("---")
st.sidebar.header("📁 Carregar Arquivos")
uploaded_files = st.sidebar.file_uploader("Selecione os arquivos Excel (.xlsx)", type=['xlsx'], accept_multiple_files=True)

# ==========================================
# CORPO PRINCIPAL
# ==========================================
st.title(" Análise Interativa de Consumo e Refrigeração")

# Função para carregar e tratar os dados (com cache para ficar rápido)
@st.cache_data
def load_data(file):
    try:
        df = pd.read_excel(file, engine='openpyxl')
        time_col = df.columns[2]
        
        try:
            if isinstance(df[time_col].dropna().iloc[0], datetime.time):
                df['Tempo'] = pd.to_datetime(df[time_col].astype(str), format='%H:%M:%S', errors='coerce')
            else:
                df['Tempo'] = pd.to_datetime(df[time_col], format='%H:%M:%S', errors='coerce')
        except:
            df['Tempo'] = pd.to_datetime(df[time_col], errors='coerce')
            
        if df['Tempo'].isna().all():
            df['Tempo_Minutos'] = pd.to_timedelta(df[time_col].astype(str)).dt.total_seconds() / 60.0
            eixo_x = 'Tempo_Minutos'
        else:
            eixo_x = 'Tempo'

        df.columns = [str(c).lower().strip() for c in df.columns]
        df = df.rename(columns={eixo_x.lower(): eixo_x})
        
        for col in df.columns:
            if df[col].dtype == 'object' and col != eixo_x:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

        return df, eixo_x
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
        return None, None

if uploaded_files:
    file_dict = {file.name: file for file in uploaded_files}
    tab1, tab2 = st.tabs([" Análise Individual", " Comparação entre Experimentos"])

    # ==========================================
    # ABA 1: ANÁLISE INDIVIDUAL
    # ==========================================
    with tab1:
        st.sidebar.header(" Filtro - Análise Individual")
        selected_file = st.sidebar.selectbox("Selecione o Experimento:", list(file_dict.keys()))
        
        df, eixo_x = load_data(file_dict[selected_file])
        
        if df is not None:
            st.subheader(f" Resultados: {selected_file.split('.')[0]}")
            
            cols = df.columns.tolist()
            def find_col(keywords):
                for k in keywords:
                    for c in cols:
                        if k in c: return c
                return None

            col_t_amb = find_col(['temperatura ambiente'])
            col_t_sup = find_col(['temperatura de superaquecimento'])
            col_t_ext = find_col(['temperatura externa'])
            col_v_a = find_col(['tensão a'])
            col_v_b = find_col(['tensão b'])
            col_v_c = find_col(['tensão c'])
            col_c_a = find_col(['corrente a'])
            col_c_b = find_col(['corrente b'])
            col_c_c = find_col(['corrente c'])
            col_energia = find_col(['energia ativa'])

            opcoes_variaveis = {}
            if col_t_amb: opcoes_variaveis["Temperatura Ambiente"] = col_t_amb
            if col_t_ext: opcoes_variaveis["Temperatura Externa"] = col_t_ext
            if col_t_sup: opcoes_variaveis["Temp. Superaquecimento"] = col_t_sup
            if col_v_a: opcoes_variaveis["Tensão A"] = col_v_a
            if col_v_b: opcoes_variaveis["Tensão B"] = col_v_b
            if col_v_c: opcoes_variaveis["Tensão C"] = col_v_c
            if col_c_a: opcoes_variaveis["Corrente A"] = col_c_a
            if col_c_b: opcoes_variaveis["Corrente B"] = col_c_b
            if col_c_c: opcoes_variaveis["Corrente C"] = col_c_c
            if col_energia: opcoes_variaveis["Energia Ativa"] = col_energia

            def plot_chart(df, x_col, y_col, title, color, y_label):
                if y_col:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=df[x_col], y=df[y_col], name=title, line=dict(color=color)))
                    fig.update_layout(title=title, height=300, margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified", yaxis_title=y_label)
                    if x_col == 'Tempo':
                        fig.update_xaxes(tickformat="%H:%M:%S", hoverformat="%H:%M:%S")
                    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

            st.markdown("###  Análise Térmica")
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1: plot_chart(df, eixo_x, col_t_amb, "Temperatura Ambiente", "blue", "°C")
            with col_t2: plot_chart(df, eixo_x, col_t_ext, "Temperatura Externa", "red", "°C")
            with col_t3: plot_chart(df, eixo_x, col_t_sup, "Temp. Superaquecimento", "orange", "°C")
            st.divider()

            st.markdown("###  Parâmetros Elétricos: Tensão")
            col_v1, col_v2, col_v3 = st.columns(3)
            with col_v1: plot_chart(df, eixo_x, col_v_a, "Tensão - Fase A", "#1f77b4", "Volts (V)")
            with col_v2: plot_chart(df, eixo_x, col_v_b, "Tensão - Fase B", "#ff7f0e", "Volts (V)")
            with col_v3: plot_chart(df, eixo_x, col_v_c, "Tensão - Fase C", "#2ca02c", "Volts (V)")
            st.divider()

            st.markdown("###  Parâmetros Elétricos: Corrente")
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1: plot_chart(df, eixo_x, col_c_a, "Corrente - Fase A", "#9467bd", "Amperes (A)")
            with col_c2: plot_chart(df, eixo_x, col_c_b, "Corrente - Fase B", "#e377c2", "Amperes (A)")
            with col_c3: plot_chart(df, eixo_x, col_c_c, "Corrente - Fase C", "#8c564b", "Amperes (A)")
            st.divider()

            st.markdown("###  Consumo Energético")
            if col_energia:
                fig_energia = go.Figure()
                fig_energia.add_trace(go.Scatter(x=df[eixo_x], y=df[col_energia], fill='tozeroy', name="Energia Ativa", line=dict(color='green')))
                fig_energia.update_layout(height=400, xaxis_title="Tempo", yaxis_title="Energia (kWh)", hovermode="x unified")
                if eixo_x == 'Tempo': fig_energia.update_xaxes(tickformat="%H:%M:%S", hoverformat="%H:%M:%S")
                st.plotly_chart(fig_energia, use_container_width=True, theme="streamlit")
                consumo_total = df[col_energia].max() - df[col_energia].min()
                st.success(f"**Consumo Total no Período:** {consumo_total:.3f} kWh")
            st.divider()

            st.markdown("###  Comparativo Personalizado (Sobreposição Interna)")
            col_filtro1, col_filtro2 = st.columns([3, 1])
            with col_filtro1: selecionadas = st.multiselect("Variáveis para sobrepor:", list(opcoes_variaveis.keys()), default=[])
            with col_filtro2:
                st.write("")
                normalizar = st.checkbox("Normalizar dados (Escala 0 a 1)")

            if selecionadas:
                st.markdown("** Escolha as cores para cada curva:**")
                col_cores = st.columns(len(selecionadas))
                cores_escolhidas = {}
                cores_padrao = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
                
                for idx, var_nome in enumerate(selecionadas):
                    with col_cores[idx]:
                        cor_default = cores_padrao[idx % len(cores_padrao)]
                        cor = st.color_picker(var_nome, cor_default, key=f"color_{var_nome}")
                        cores_escolhidas[var_nome] = cor
                        
                fig_custom = go.Figure()
                for var_nome in selecionadas:
                    coluna_real = opcoes_variaveis[var_nome]
                    y_data = df[coluna_real]
                    if normalizar:
                        val_min = y_data.min()
                        val_max = y_data.max()
                        if val_max != val_min: y_data = (y_data - val_min) / (val_max - val_min)
                        else: y_data = y_data - val_min
                            
                    fig_custom.add_trace(go.Scatter(x=df[eixo_x], y=y_data, name=var_nome, line=dict(color=cores_escolhidas[var_nome])))
                    
                titulo_eixo_y = "Valores Normalizados (0 a 1)" if normalizar else "Valores Brutos"
                fig_custom.update_layout(height=500, xaxis_title="Tempo", yaxis_title=titulo_eixo_y, hovermode="x unified")
                if eixo_x == 'Tempo': fig_custom.update_xaxes(tickformat="%H:%M:%S", hoverformat="%H:%M:%S")
                st.plotly_chart(fig_custom, use_container_width=True, theme="streamlit")

    # ==========================================
    # ABA 2: COMPARAÇÃO ENTRE EXPERIMENTOS
    # ==========================================
    with tab2:
        st.markdown("###  Sobreposição de Múltiplos Experimentos")
        st.write("Selecione os experimentos que deseja comparar.")
        
        experimentos_selecionados = st.multiselect(
            "Selecione os experimentos para comparar:", 
            list(file_dict.keys()), 
            default=list(file_dict.keys())[:2] if len(file_dict) >= 2 else list(file_dict.keys())
        )

        if experimentos_selecionados:
            st.markdown("** Escolha uma cor para identificar cada experimento:**")
            
            col_cores_exp = st.columns(len(experimentos_selecionados))
            cores_escolhidas_exp = {}
            cores_padrao_exp = ['#1f77b4', '#d62728', '#2ca02c', '#ff7f0e', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            
            for idx, exp_name in enumerate(experimentos_selecionados):
                with col_cores_exp[idx]:
                    cor_default = cores_padrao_exp[idx % len(cores_padrao_exp)]
                    nome_legenda = exp_name.split('.')[0]
                    cor = st.color_picker(nome_legenda, cor_default, key=f"color_exp_{exp_name}")
                    cores_escolhidas_exp[exp_name] = cor

            st.divider()

            dados_comp = {}
            for exp in experimentos_selecionados:
                df_c, eixo_x_c = load_data(file_dict[exp])
                if df_c is not None:
                    dados_comp[exp] = (df_c, eixo_x_c)

            def get_col_real(df_c, keywords):
                cols_c = df_c.columns.tolist()
                for k in keywords:
                    for c in cols_c:
                        if k in c: return c
                return None

            def plot_comparison_chart(title, keywords, y_label):
                fig = go.Figure()
                adicionou_algo = False
                
                for exp_name, (df_exp, eixo_x_exp) in dados_comp.items():
                    col_real = get_col_real(df_exp, keywords)
                    if col_real:
                        nome_legenda = exp_name.split('.')[0]
                        fig.add_trace(go.Scatter(
                            x=df_exp[eixo_x_exp], 
                            y=df_exp[col_real], 
                            name=nome_legenda,
                            line=dict(color=cores_escolhidas_exp[exp_name])
                        ))
                        adicionou_algo = True
                        
                if adicionou_algo:
                    fig.update_layout(title=title, height=350, margin=dict(l=20, r=20, t=40, b=20), hovermode="x unified", yaxis_title=y_label)
                    if eixo_x_exp == 'Tempo': 
                        fig.update_xaxes(tickformat="%H:%M:%S", hoverformat="%H:%M:%S")
                    st.plotly_chart(fig, use_container_width=True, theme="streamlit")
                else:
                    st.warning(f"Dados não encontrados para {title} nos arquivos selecionados.")

            st.markdown("####  Térmica")
            col_comp_t1, col_comp_t2, col_comp_t3 = st.columns(3)
            with col_comp_t1: plot_comparison_chart("Temperatura Ambiente", ['temperatura ambiente'], "°C")
            with col_comp_t2: plot_comparison_chart("Temperatura Externa", ['temperatura externa'], "°C")
            with col_comp_t3: plot_comparison_chart("Temp. Superaquecimento", ['temperatura de superaquecimento'], "°C")
            st.divider()

            st.markdown("####  Tensão")
            col_comp_v1, col_comp_v2, col_comp_v3 = st.columns(3)
            with col_comp_v1: plot_comparison_chart("Tensão - Fase A", ['tensão a'], "Volts (V)")
            with col_comp_v2: plot_comparison_chart("Tensão - Fase B", ['tensão b'], "Volts (V)")
            with col_comp_v3: plot_comparison_chart("Tensão - Fase C", ['tensão c'], "Volts (V)")
            st.divider()

            st.markdown("####  Corrente")
            col_comp_c1, col_comp_c2, col_comp_c3 = st.columns(3)
            with col_comp_c1: plot_comparison_chart("Corrente - Fase A", ['corrente a'], "Amperes (A)")
            with col_comp_c2: plot_comparison_chart("Corrente - Fase B", ['corrente b'], "Amperes (A)")
            with col_comp_c3: plot_comparison_chart("Corrente - Fase C", ['corrente c'], "Amperes (A)")
            st.divider()

            st.markdown("####  Consumo Energético")
            plot_comparison_chart("Energia Ativa (Acumulada)", ['energia ativa'], "Energia (kWh)")

        else:
            st.info("Selecione pelo menos um experimento para visualizar a comparação.")

else:
    st.info("👈 Por favor, carregue um ou mais arquivos .xlsx na barra lateral para iniciar a análise.")