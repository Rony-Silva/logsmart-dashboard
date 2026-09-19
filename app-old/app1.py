import os
import glob
import pandas as pd
import streamlit as st
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. Configuração da Página e Estilo CSS Moderno (SaaS/Modern Dark Theme)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="LogSmart - Gestão de Estoque",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Estilização Geral e Fontes */
    .main {
        background-color: #0e1117;
    }
    
    /* Card Container Moderno */
    .metric-card {
        background: linear-gradient(135deg, #1e222d 0%, #171a23 100%);
        border: 1px solid #2d313e;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        border-color: #4f46e5;
        transform: translateY(-2px);
    }
    
    .metric-title {
        color: #9ca3af;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .metric-value {
        color: #f3f4f6;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .metric-alert {
        color: #ef4444;
    }
    
    /* Alerta Customizado */
    .alert-box {
        background: rgba(239, 68, 68, 0.1);
        border-left: 4px solid #ef4444;
        padding: 15px;
        border-radius: 6px;
        color: #fca5a5;
        margin-bottom: 20px;
    }
    
    /* Customização de Abas e Tabelas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
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
# 2. Leitura e Processamento dos Arquivos da Pasta "dados"
# -----------------------------------------------------------------------------
FOLDER_PATH = "dados"
# Mapeamento por índice: Coluna I=8, J=9, L=11, N=13, O=14
COLUMNS_IDX = [8, 9, 11, 13, 14]

def get_cell_l3(df_raw):
    """
    Tenta obter o conteúdo da coordenada L3 (Linha index 2, Coluna index 11).
    Caso não exista ou esteja em branco, retorna um valor padrão.
    """
    try:
        if df_raw.shape[0] >= 3 and df_raw.shape[1] >= 12:
            val = str(df_raw.iloc[2, 11]).strip()
            if val and val.lower() != 'nan':
                return val
    except Exception:
        pass
    return "Categoria Não Definida"

def load_data_from_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        
    filepaths = glob.glob(os.path.join(folder_path, "*.[cC][sS][vV]")) + \
                glob.glob(os.path.join(folder_path, "*.[xX][lL][sS]*"))
                
    all_data = []
    
    for filepath in filepaths:
        filename = os.path.basename(filepath)
        try:
            # Leitura com fallback de delimitador
            if filepath.lower().endswith('.csv'):
                try:
                    df_raw = pd.read_csv(filepath, header=None, sep=';')
                except Exception:
                    df_raw = pd.read_csv(filepath, header=None, sep=None, engine='python')
            else:
                df_raw = pd.read_excel(filepath, header=None)
                
            # Extrai o nome/conteúdo presente na coordenada L3
            nome_conteudo_l3 = get_cell_l3(df_raw)
            
            # Validação das colunas
            max_idx = max(COLUMNS_IDX)
            if df_raw.shape[1] <= max_idx:
                continue
                
            # Filtra apenas as colunas I, J, L, N, O
            df_selected = df_raw.iloc[:, COLUMNS_IDX].copy()
            
            # Renomeia com rótulos descritivos usando o L3 para contextualização
            df_selected.columns = ['Coluna_I', 'Coluna_J', f'Conteudo_L3 ({nome_conteudo_l3})', 'Coluna_N', 'Quantidade_O']
            
            # Adiciona colunas de controle
            df_selected['Arquivo_Origem'] = filename
            df_selected['Nome_L3'] = nome_conteudo_l3
            
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
# 3. Construção da Interface Principal
# -----------------------------------------------------------------------------
st.title("📦 LogSmart - Dashboard de Controle de Itens")
st.caption("Importação automática da pasta `dados` com agrupamento dinâmico via célula L3.")

# Carrega os dados da pasta
df_main = load_data_from_folder(FOLDER_PATH)

if df_main.empty:
    st.warning(f"⚠️ NENHUM ARQUIVO ENCONTRADO NA PASTA `{FOLDER_PATH}`.")
    st.info(f"Por favor, insira os arquivos `.csv` ou `.xlsx` na pasta `{os.path.abspath(FOLDER_PATH)}` e atualize a página.")
else:
    # -------------------------------------------------------------------------
    # Barra Lateral: Filtros e Controles
    # -------------------------------------------------------------------------
    st.sidebar.header("⚙️ Painel de Controle")
    st.sidebar.markdown(f"**Arquivos Carregados:** `{len(df_main['Arquivo_Origem'].unique())}`")
    
    # Recarregar Dados Manualmente
    if st.sidebar.button("🔄 Recarregar Dados da Pasta"):
        st.cache_data.clear()
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Filtro de Coluna N")
    
    opcoes_n = df_main['Coluna_N'].dropna().astype(str).unique().tolist()
    opcoes_n.sort()
    
    selecionar_tudo = st.sidebar.checkbox("Selecionar Todos", value=True)
    
    if selecionar_tudo:
        selecao_n = st.sidebar.multiselect("Filtrar Seleção:", options=opcoes_n, default=opcoes_n)
    else:
        selecao_n = st.sidebar.multiselect("Filtrar Seleção:", options=opcoes_n, default=[])
        
    # Aplicação do Filtro
    if selecao_n:
        df_filtered = df_main[df_main['Coluna_N'].astype(str).isin(selecao_n)]
    else:
        df_filtered = df_main.iloc[0:0]

    # -------------------------------------------------------------------------
    # Métricas Globais em Cards Estilizados
    # -------------------------------------------------------------------------
    total_registros = len(df_filtered)
    soma_qtd = df_filtered['Quantidade_O'].sum()
    itens_zerados = df_filtered[df_filtered['Quantidade_O'] == 0]
    qtd_zerados = len(itens_zerados)
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total de Itens</div>
            <div class="metric-value">{total_registros:,}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Quantidade Total (Coluna O)</div>
            <div class="metric-value">{soma_qtd:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Itens Ativos (>0)</div>
            <div class="metric-value" style="color: #10b981;">{total_registros - qtd_zerados:,}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c4:
        color_class = "metric-alert" if qtd_zerados > 0 else ""
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Itens Zerados (=0)</div>
            <div class="metric-value {color_class}">{qtd_zerados:,}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Painel de Alerta Crítico
    # -------------------------------------------------------------------------
    if qtd_zerados > 0:
        st.markdown(f"""
        <div class="alert-box">
            🚨 <b>ATENÇÃO:</b> Foram identificados <b>{qtd_zerados}</b> item(ns) com quantidade igual a <b>ZERO</b> no filtro atual.
        </div>
        """, unsafe_allow_html=True)
        with st.expander("🚨 Clique para ver a lista completa de itens ZERADOS"):
            st.dataframe(
                itens_zerados[['Arquivo_Origem', 'Nome_L3', 'Coluna_I', 'Coluna_J', 'Coluna_N', 'Quantidade_O']],
                use_container_width=True
            )

    # -------------------------------------------------------------------------
    # Detalhamento por Conteúdo Extraído de L3 (Abas Modernas)
    # -------------------------------------------------------------------------
    st.subheader("📁 Visão Detalhada por Conteúdo da Célula L3")
    
    # Agrupa os arquivos/dados por cada nome extraído em L3
    categorias_l3 = df_filtered['Nome_L3'].unique()
    
    if len(categorias_l3) > 0:
        tabs = st.tabs([f"📌 {cat}" for cat in categorias_l3])
        
        for tab, cat in zip(tabs, categorias_l3):
            with tab:
                df_cat = df_filtered[df_filtered['Nome_L3'] == cat]
                zerados_cat = len(df_cat[df_cat['Quantidade_O'] == 0])
                
                # Indicadores locais da Categoria
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Arquivos nesta Categoria", len(df_cat['Arquivo_Origem'].unique()))
                mc2.metric("Total de Itens", len(df_cat))
                mc3.metric("Itens Zerados", zerados_cat, delta_color="inverse")
                
                # Estilização condicional de tabela para zeros
                def highlight_zeros(val):
                    return 'background-color: rgba(239, 68, 68, 0.2); color: #ef4444; font-weight: bold' if val == 0 else ''

                st.markdown("##### Itens Pertencentes a esta Categoria:")
                cols_to_show = [c for c in df_cat.columns if c not in ['Nome_L3']]
                
                st.dataframe(
                    df_cat[cols_to_show].style.map(highlight_zeros, subset=['Quantidade_O']),
                    use_container_width=True
                )
    else:
        st.info("Nenhum dado para exibir no filtro selecionado.")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # Gráficos e Analytics
    # -------------------------------------------------------------------------
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("📊 Quantidade Total por Valor da Coluna N")
        if not df_filtered.empty:
            df_g_n = df_filtered.groupby('Coluna_N', as_index=False)['Quantidade_O'].sum()
            fig_bar = px.bar(
                df_g_n,
                x='Coluna_N',
                y='Quantidade_O',
                text_auto='.2f',
                template="plotly_dark",
                color_discrete_sequence=['#6366f1']
            )
            fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_bar, use_container_width=True)

    with g2:
        st.subheader("🎯 Comparativo de Quantidades por Célula L3")
        if not df_filtered.empty:
            df_g_l3 = df_filtered.groupby('Nome_L3', as_index=False)['Quantidade_O'].sum()
            fig_pie = px.pie(
                df_g_l3,
                names='Nome_L3',
                values='Quantidade_O',
                hole=0.4,
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_pie, use_container_width=True)