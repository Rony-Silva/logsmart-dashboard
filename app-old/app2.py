import os
import glob
import pandas as pd
import streamlit as st
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. Configuração da Página e Estilização Modern Dark
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="LogSmart - Gestão por Plataforma",
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
    
    /* Caixa de Alerta */
    .alert-box {
        background: rgba(239, 68, 68, 0.12);
        border-left: 5px solid #ef4444;
        padding: 14px 18px;
        border-radius: 8px;
        color: #fca5a5;
        margin-bottom: 20px;
    }

    /* Personalização de Abas */
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
# 2. Processamento e Leitura Dinâmica dos Arquivos na Pasta "dados"
# -----------------------------------------------------------------------------
FOLDER_PATH = "dados"

# Mapeamento fixo de colunas: I=8, J=9, L=11, N=13, O=14
COLUMNS_IDX = [8, 9, 11, 13, 14]

def extrair_nome_plataforma_l3(df_raw, filename):
    """
    Lê a célula L3 (linha 3 [índice 2], coluna L [índice 11]).
    Caso esteja vazia, utiliza o nome do arquivo (ex: P-38) como fallback.
    """
    try:
        if df_raw.shape[0] >= 3 and df_raw.shape[1] >= 12:
            val = str(df_raw.iloc[2, 11]).strip()
            if val and val.lower() != 'nan' and val != '':
                return val
    except Exception:
        pass
    return os.path.splitext(filename)[0]

@st.cache_data
def carregar_dados_plataformas(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        
    filepaths = glob.glob(os.path.join(folder_path, "*.[cC][sS][vV]")) + \
                glob.glob(os.path.join(folder_path, "*.[xX][lL][sS]*"))
                
    all_data = []
    
    for filepath in filepaths:
        filename = os.path.basename(filepath)
        try:
            # Tenta ler CSV com ';' ou autodetecção
            if filepath.lower().endswith('.csv'):
                try:
                    df_raw = pd.read_csv(filepath, header=None, sep=';')
                except Exception:
                    df_raw = pd.read_csv(filepath, header=None, sep=None, engine='python')
            else:
                df_raw = pd.read_excel(filepath, header=None)
                
            # Identifica a Plataforma pela célula L3
            plataforma = extrair_nome_plataforma_l3(df_raw, filename)
            
            # Valida número de colunas
            max_idx = max(COLUMNS_IDX)
            if df_raw.shape[1] <= max_idx:
                continue
                
            # Extrai colunas I, J, L, N, O
            df_selected = df_raw.iloc[:, COLUMNS_IDX].copy()
            df_selected.columns = ['Coluna_I', 'Coluna_J', 'Coluna_L', 'Coluna_N', 'Quantidade_O']
            
            # Adiciona informações da Plataforma e do Arquivo
            df_selected['Plataforma'] = plataforma
            df_selected['Arquivo_Origem'] = filename
            
            # Tratamento numérico para a Quantidade (Coluna O)
            df_selected['Quantidade_O'] = (
                df_selected['Quantidade_O']
                .astype(str)
                .str.replace(',', '.', regex=False)
                .str.strip()
            )
            df_selected['Quantidade_O'] = pd.to_numeric(df_selected['Quantidade_O'], errors='coerce').fillna(0)
            
            all_data.append(df_selected)
            
        except Exception as e:
            st.sidebar.error(f"Erro ao ler {filename}: {e}")
            
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()

# -----------------------------------------------------------------------------
# 3. Execução Principal e Filtros Reativos
# -----------------------------------------------------------------------------
st.title("⚓ LogSmart - Painel de Controle de Plataformas")
st.caption("Importação automática da pasta `dados` | Identificação por Célula L3 (Plataforma)")

df_main = carregar_dados_plataformas(FOLDER_PATH)

if df_main.empty:
    st.warning(f"⚠️ Nenhum arquivo foi encontrado na pasta `{FOLDER_PATH}`.")
    st.info(f"Insira os arquivos (`P-38.csv`, `UMLI.csv`, etc.) dentro do diretório local `{os.path.abspath(FOLDER_PATH)}` e recarregue a página.")
else:
    # --- Sidebar: Filtros de Plataforma e Coluna N ---
    st.sidebar.header("⚙️ Filtros de Pesquisa")
    
    # Lista de Plataformas encontradas via L3
    lista_plataformas = df_main['Plataforma'].dropna().unique().tolist()
    lista_plataformas.sort()
    
    plataformas_selecionadas = st.sidebar.multiselect(
        "🚢 Selecionar Plataforma(s) (L3):",
        options=lista_plataformas,
        default=lista_plataformas
    )
    
    st.sidebar.markdown("---")
    
    # Lista de valores da Coluna N
    lista_n = df_main['Coluna_N'].dropna().astype(str).unique().tolist()
    lista_n.sort()
    
    selecionar_tudo_n = st.sidebar.checkbox("Selecionar Todos da Coluna N", value=True)
    
    if selecionar_tudo_n:
        selecao_n = st.sidebar.multiselect("🔍 Filtrar Coluna N:", options=lista_n, default=lista_n)
    else:
        selecao_n = st.sidebar.multiselect("🔍 Filtrar Coluna N:", options=lista_n, default=[])

    if st.sidebar.button("🔄 Recarregar Dados da Pasta"):
        st.cache_data.clear()
        st.rerun()

    # --- Aplicação dos Filtros Cruzados ---
    df_filtered = df_main[
        (df_main['Plataforma'].isin(plataformas_selecionadas)) &
        (df_main['Coluna_N'].astype(str).isin(selecao_n))
    ]

    # --- Métricas Principais ---
    total_registros = len(df_filtered)
    soma_qtd = df_filtered['Quantidade_O'].sum()
    itens_zerados = df_filtered[df_filtered['Quantidade_O'] == 0]
    qtd_zerados = len(itens_zerados)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Total Registros</div><div class="metric-value">{total_registros:,}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Quantidade Total (O)</div><div class="metric-value">{soma_qtd:,.2f}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Itens Ativos (>0)</div><div class="metric-value" style="color:#10b981;">{total_registros - qtd_zerados:,}</div></div>', unsafe_allow_html=True)
    with c4:
        alert_cls = "metric-alert" if qtd_zerados > 0 else ""
        st.markdown(f'<div class="metric-card"><div class="metric-title">Itens Zerados (=0)</div><div class="metric-value {alert_cls}">{qtd_zerados:,}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Alerta Crítico Global ---
    if qtd_zerados > 0:
        st.markdown(f"""
        <div class="alert-box">
            🚨 <b>ALERTA CRÍTICO:</b> Existem <b>{qtd_zerados}</b> item(ns) com <b>quantidade 0</b> nas plataformas selecionadas!
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 4. Detalhamento Estrito por Plataforma (L3)
    # -------------------------------------------------------------------------
    st.subheader("📋 Itens Pertencentes por Plataforma")
    
    plataformas_no_filtro = df_filtered['Plataforma'].unique()
    
    if len(plataformas_no_filtro) > 0:
        tabs = st.tabs([f"🚢 {plat}" for plat in plataformas_no_filtro])
        
        for tab, plat in zip(tabs, plataformas_no_filtro):
            with tab:
                # Isola estritamente os dados desta plataforma
                df_plat = df_filtered[df_filtered['Plataforma'] == plat]
                zerados_plat = df_plat[df_plat['Quantidade_O'] == 0]
                num_zerados_plat = len(zerados_plat)
                
                # Indicadores locais da plataforma
                col_p1, col_p2, col_p3 = st.columns(3)
                col_p1.metric("Plataforma", plat)
                col_p2.metric("Total de Itens", len(df_plat))
                col_p3.metric("Itens Zerados", num_zerados_plat, delta_color="inverse")
                
                if num_zerados_plat > 0:
                    st.error(f"⚠️ A plataforma **{plat}** possui **{num_zerados_plat}** item(ns) com quantidade zerada!")

                st.markdown(f"**Tabela de Itens - Plataforma {plat}:**")
                
                def highlight_zeros(val):
                    return 'background-color: rgba(239, 68, 68, 0.25); color: #ef4444; font-weight: bold' if val == 0 else ''

                tabela_exibicao = df_plat[['Coluna_I', 'Coluna_J', 'Coluna_L', 'Coluna_N', 'Quantidade_O', 'Arquivo_Origem']]
                
                st.dataframe(
                    tabela_exibicao.style.map(highlight_zeros, subset=['Quantidade_O']),
                    use_container_width=True
                )
    else:
        st.info("Nenhuma plataforma encontrada para os filtros aplicados.")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 5. Gráficos Analíticos
    # -------------------------------------------------------------------------
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("📊 Quantidade por Coluna N (Filtro Ativo)")
        if not df_filtered.empty:
            df_g_n = df_filtered.groupby('Coluna_N', as_index=False)['Quantidade_O'].sum()
            fig_bar = px.bar(
                df_g_n, x='Coluna_N', y='Quantidade_O',
                text_auto='.2f', template="plotly_dark",
                color_discrete_sequence=['#6366f1']
            )
            fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_bar, use_container_width=True)

    with g2:
        st.subheader("🚢 Distribuição de Quantidade por Plataforma (L3)")
        if not df_filtered.empty:
            df_g_plat = df_filtered.groupby('Plataforma', as_index=False)['Quantidade_O'].sum()
            fig_pie = px.pie(
                df_g_plat, names='Plataforma', values='Quantidade_O',
                hole=0.4, template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pie, use_container_width=True)