import os
import glob
import pandas as pd
import streamlit as st
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. Configuração da Página e Estilização Visual
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="LogSmart - Gestão de Estoque e Plataformas",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    
    /* Cards de Métricas */
    .metric-card {
        background: linear-gradient(135deg, #1e222d 0%, #171a23 100%);
        border: 1px solid #2d313e;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        text-align: center;
    }
    .metric-title {
        color: #9ca3af;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .metric-value {
        color: #f3f4f6;
        font-size: 1.7rem;
        font-weight: 700;
    }
    .metric-alert { color: #ef4444; }
    
    /* Caixa de Alerta de Estoque */
    .alert-box {
        background: rgba(239, 68, 68, 0.12);
        border-left: 5px solid #ef4444;
        padding: 14px 18px;
        border-radius: 8px;
        color: #fca5a5;
        margin-bottom: 20px;
    }

    /* Personalização das Abas */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        background-color: #1a1d24;
        border-radius: 8px;
        color: #9ca3af;
        font-weight: 600;
        border: 1px solid #2d313e;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4f46e5 !important;
        color: #ffffff !important;
        border-color: #6366f1 !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. Processamento dos Arquivos da Pasta "dados"
# -----------------------------------------------------------------------------
FOLDER_PATH = "dados"
# Mapeamento por índice: I=8, J=9, L=11, N=13, O=14
COLUMNS_IDX = [8, 9, 11, 13, 14]

def extrair_plataforma(df_raw, filename):
    """Lê a coordenada da Plataforma na célula L3 ou usa o nome do arquivo."""
    try:
        if df_raw.shape[0] >= 3 and df_raw.shape[1] >= 12:
            val = str(df_raw.iloc[2, 11]).strip()
            if val and val.lower() != 'nan' and val != '':
                return val
    except Exception:
        pass
    return os.path.splitext(filename)[0]

@st.cache_data
def carregar_dados_estoque(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        
    filepaths = glob.glob(os.path.join(folder_path, "*.[cC][sS][vV]")) + \
                glob.glob(os.path.join(folder_path, "*.[xX][lL][sS]*"))
                
    all_data = []
    
    for filepath in filepaths:
        filename = os.path.basename(filepath)
        try:
            if filepath.lower().endswith('.csv'):
                try:
                    df_raw = pd.read_csv(filepath, header=None, sep=';')
                except Exception:
                    df_raw = pd.read_csv(filepath, header=None, sep=None, engine='python')
            else:
                df_raw = pd.read_excel(filepath, header=None)
                
            plataforma = extrair_plataforma(df_raw, filename)
            
            max_idx = max(COLUMNS_IDX)
            if df_raw.shape[1] <= max_idx:
                continue
                
            # Extrai as colunas e atribui nomes de negócios claros
            df_selected = df_raw.iloc[:, COLUMNS_IDX].copy()
            df_selected.columns = ['Codigo_Item', 'Descricao', 'Localizacao', 'Categoria', 'Quantidade']
            
            df_selected['Plataforma'] = plataforma
            df_selected['Arquivo_Origem'] = filename
            
            # Tratamento numérico da Quantidade
            df_selected['Quantidade'] = (
                df_selected['Quantidade']
                .astype(str)
                .str.replace(',', '.', regex=False)
                .str.strip()
            )
            df_selected['Quantidade'] = pd.to_numeric(df_selected['Quantidade'], errors='coerce').fillna(0)
            
            all_data.append(df_selected)
            
        except Exception as e:
            st.sidebar.error(f"Erro ao processar {filename}: {e}")
            
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()

# -----------------------------------------------------------------------------
# 3. Painel Principal
# -----------------------------------------------------------------------------
st.title("⚓ LogSmart - Controle de Estoque por Plataforma")
st.caption("Importação automática e monitoramento contínuo de itens e suprimentos.")

df_main = carregar_dados_estoque(FOLDER_PATH)

if df_main.empty:
    st.warning(f"⚠️ Nenhum arquivo foi localizado na pasta `{FOLDER_PATH}`.")
    st.info(f"Insira os arquivos de dados na pasta local `{os.path.abspath(FOLDER_PATH)}` e recarregue a página.")
else:
    # --- Sidebar: Filtros Amigáveis ---
    st.sidebar.header("⚙️ Filtros de Pesquisa")
    
    # 1. Filtro de Plataforma
    lista_plataformas = df_main['Plataforma'].dropna().unique().tolist()
    lista_plataformas.sort()
    
    plataformas_selecionadas = st.sidebar.multiselect(
        "🚢 Selecionar Plataforma(s):",
        options=lista_plataformas,
        default=lista_plataformas
    )
    
    st.sidebar.markdown("---")
    
    # 2. Filtro de Categoria
    lista_categorias = df_main['Categoria'].dropna().astype(str).unique().tolist()
    lista_categorias.sort()
    
    selecionar_tudo_cat = st.sidebar.checkbox("Selecionar Todas as Categorias", value=True)
    
    if selecionar_tudo_cat:
        categorias_selecionadas = st.sidebar.multiselect("🔍 Categorias de Itens:", options=lista_categorias, default=lista_categorias)
    else:
        categorias_selecionadas = st.sidebar.multiselect("🔍 Categorias de Itens:", options=lista_categorias, default=[])

    if st.sidebar.button("🔄 Recarregar Pasta de Dados"):
        st.cache_data.clear()
        st.rerun()

    # --- Aplicação dos Filtros ---
    df_filtered = df_main[
        (df_main['Plataforma'].isin(plataformas_selecionadas)) &
        (df_main['Categoria'].astype(str).isin(categorias_selecionadas))
    ]

    # --- Resumo Executivo ---
    total_registros = len(df_filtered)
    soma_qtd = df_filtered['Quantidade'].sum()
    itens_zerados = df_filtered[df_filtered['Quantidade'] == 0]
    qtd_zerados = len(itens_zerados)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Total de Registros</div><div class="metric-value">{total_registros:,}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Volume em Estoque</div><div class="metric-value">{soma_qtd:,.2f}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Itens Com Estoque</div><div class="metric-value" style="color:#10b981;">{total_registros - qtd_zerados:,}</div></div>', unsafe_allow_html=True)
    with c4:
        alert_cls = "metric-alert" if qtd_zerados > 0 else ""
        st.markdown(f'<div class="metric-card"><div class="metric-title">Itens Zerados</div><div class="metric-value {alert_cls}">{qtd_zerados:,}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 4. Alertas com Detalhamento Exato dos Itens Afetados
    # -------------------------------------------------------------------------
    if qtd_zerados > 0:
        st.markdown(f"""
        <div class="alert-box">
            🚨 <b>ALERTA DE ESTOQUE CRÍTICO:</b> Foram detectados <b>{qtd_zerados}</b> item(ns) com <b>quantidade 0</b> nas plataformas selecionadas!
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("🚨 Detalhamento dos Itens Zerados (Alerta)")
        
        # Mapeamento e exibição amigável da tabela de alertas
        tabela_alerta = itens_zerados[['Plataforma', 'Codigo_Item', 'Descricao', 'Categoria', 'Quantidade', 'Arquivo_Origem']].copy()
        tabela_alerta.columns = ['Plataforma', 'Código do Item', 'Descrição do Item', 'Categoria', 'Qtd em Estoque', 'Arquivo Fonte']
        
        def highlight_alert_row(val):
            return 'background-color: rgba(239, 68, 68, 0.25); color: #ef4444; font-weight: bold;' if val == 0 else ''

        st.dataframe(
            tabela_alerta.style.map(highlight_alert_row, subset=['Qtd em Estoque']),
            use_container_width=True
        )
        st.markdown("---")

    # -------------------------------------------------------------------------
    # 5. Relatórios Específicos por Categoria de Item
    # -------------------------------------------------------------------------
    st.subheader("📊 Relatórios Detalhados por Categoria de Item")
    
    if not df_filtered.empty:
        col_sel, col_empty = st.columns([1, 2])
        with col_sel:
            cat_relatorio = st.selectbox("Selecione uma Categoria para Analisar:", options=sorted(df_filtered['Categoria'].astype(str).unique()))
            
        df_cat_especifica = df_filtered[df_filtered['Categoria'].astype(str) == cat_relatorio]
        zerados_cat_esp = df_cat_especifica[df_cat_especifica['Quantidade'] == 0]
        
        r1, r2, r3 = st.columns(3)
        r1.metric(f"Itens em '{cat_relatorio}'", len(df_cat_especifica))
        r2.metric("Total em Estoque", f"{df_cat_especifica['Quantidade'].sum():,.2f}")
        r3.metric("Itens Zerados na Categoria", len(zerados_cat_esp), delta_color="inverse")
        
        st.markdown(f"**Tabela de Itens da Categoria: `{cat_relatorio}`**")
        
        tabela_cat_view = df_cat_especifica[['Plataforma', 'Codigo_Item', 'Descricao', 'Quantidade', 'Arquivo_Origem']].copy()
        tabela_cat_view.columns = ['Plataforma', 'Código do Item', 'Descrição / Especificação', 'Quantidade em Estoque', 'Arquivo Fonte']
        
        st.dataframe(
            tabela_cat_view.style.map(lambda v: 'background-color: rgba(239, 68, 68, 0.25); color: #ef4444; font-weight: bold' if v == 0 else '', subset=['Quantidade em Estoque']),
            use_container_width=True
        )
    else:
        st.info("Nenhum item localizado para a seleção atual.")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 6. Visão Geral por Plataforma (Abas)
    # -------------------------------------------------------------------------
    st.subheader("📋 Estudo do Estoque por Plataforma")
    
    plataformas_no_filtro = df_filtered['Plataforma'].unique()
    
    if len(plataformas_no_filtro) > 0:
        tabs = st.tabs([f"🚢 {plat}" for plat in plataformas_no_filtro])
        
        for tab, plat in zip(tabs, plataformas_no_filtro):
            with tab:
                df_plat = df_filtered[df_filtered['Plataforma'] == plat]
                zerados_plat = df_plat[df_plat['Quantidade'] == 0]
                
                col_p1, col_p2, col_p3 = st.columns(3)
                col_p1.metric("Plataforma", plat)
                col_p2.metric("Total de Registros", len(df_plat))
                col_p3.metric("Itens Zerados", len(zerados_plat), delta_color="inverse")
                
                tabela_plat_exibicao = df_plat[['Codigo_Item', 'Descricao', 'Categoria', 'Quantidade', 'Arquivo_Origem']].copy()
                tabela_plat_exibicao.columns = ['Código do Item', 'Descrição', 'Categoria', 'Quantidade em Estoque', 'Arquivo Fonte']
                
                st.dataframe(
                    tabela_plat_exibicao.style.map(lambda v: 'background-color: rgba(239, 68, 68, 0.25); color: #ef4444; font-weight: bold' if v == 0 else '', subset=['Quantidade em Estoque']),
                    use_container_width=True
                )

    # -------------------------------------------------------------------------
    # 7. Gráficos Analíticos Integrados
    # -------------------------------------------------------------------------
    st.markdown("---")
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("📊 Quantidade Total por Categoria")
        if not df_filtered.empty:
            df_g_cat = df_filtered.groupby('Categoria', as_index=False)['Quantidade'].sum()
            fig_bar = px.bar(
                df_g_cat, x='Categoria', y='Quantidade',
                text_auto='.2f', template="plotly_dark",
                color_discrete_sequence=['#6366f1'],
                labels={'Categoria': 'Categoria do Item', 'Quantidade': 'Quantidade em Estoque'}
            )
            fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_bar, use_container_width=True)

    with g2:
        st.subheader("🚢 Distribuição do Volume por Plataforma")
        if not df_filtered.empty:
            df_g_plat = df_filtered.groupby('Plataforma', as_index=False)['Quantidade'].sum()
            fig_pie = px.pie(
                df_g_plat, names='Plataforma', values='Quantidade',
                hole=0.4, template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Set3,
                labels={'Plataforma': 'Plataforma', 'Quantidade': 'Quantidade em Estoque'}
            )
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pie, use_container_width=True)