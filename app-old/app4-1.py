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
# 2. Processamento e Limpeza dos Arquivos da Pasta "dados"
# -----------------------------------------------------------------------------
FOLDER_PATH = "dados"
# Mapeamento fixo das colunas por índice: I=8, J=9, L=11, N=13, O=14
COLUMNS_IDX = [8, 9, 11, 13, 14]

def extrair_plataforma(df_raw, filename):
    """Lê a coordenada da Plataforma na célula L3 ou usa o nome do arquivo."""
    try:
        if df_raw.shape[0] >= 3 and df_raw.shape[1] >= 12:
            val = str(df_raw.iloc[2, 11]).strip()
            if val and val.lower() not in ['nan', 'none', '']:
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
                    df_raw = pd.read_csv(filepath, header=None, sep=';', dtype=str)
                except Exception:
                    df_raw = pd.read_csv(filepath, header=None, sep=None, engine='python', dtype=str)
            else:
                df_raw = pd.read_excel(filepath, header=None, dtype=str)
                
            plataforma = extrair_plataforma(df_raw, filename)
            
            max_idx = max(COLUMNS_IDX)
            if df_raw.shape[1] <= max_idx:
                continue
                
            df_selected = df_raw.iloc[:, COLUMNS_IDX].copy()
            df_selected.columns = ['Codigo_Item', 'Descricao', 'Localizacao', 'Categoria', 'Quantidade']
            
            # Limpeza de strings
            for col in ['Codigo_Item', 'Descricao', 'Localizacao', 'Categoria']:
                df_selected[col] = (
                    df_selected[col]
                    .astype(str)
                    .str.strip()
                    .replace({'nan': '', 'None': '', '<NA>': ''})
                )
            
            # Converte Quantidade para numérico
            df_selected['Quantidade_Num'] = pd.to_numeric(
                df_selected['Quantidade']
                .astype(str)
                .str.replace(',', '.', regex=False)
                .str.strip(),
                errors='coerce'
            )
            
            # Filtro de Validação de linhas
            palavras_cabecalho = ['codigo', 'código', 'code', 'item', 'descrição', 'descricao', 'quantidade', 'qtd']
            is_valid_row = (
                (df_selected['Codigo_Item'] != '') | (df_selected['Descricao'] != '')
            ) & (
                ~df_selected['Codigo_Item'].str.lower().isin(palavras_cabecalho)
            ) & (
                ~df_selected['Descricao'].str.lower().isin(palavras_cabecalho)
            )
            
            df_selected = df_selected[is_valid_row].copy()
            df_selected['Quantidade'] = df_selected['Quantidade_Num'].fillna(0)
            df_selected.drop(columns=['Quantidade_Num'], inplace=True)
            
            df_selected['Plataforma'] = plataforma
            df_selected['Arquivo_Origem'] = filename
            
            all_data.append(df_selected)
            
        except Exception as e:
            st.sidebar.error(f"Erro ao processar {filename}: {e}")
            
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()

def gerar_html_impressao(df_export):
    """Gera um arquivo HTML com layout limpo e botão automático de impressão."""
    linhas_tabela = ""
    for _, row in df_export.iterrows():
        estilo_zero = "color: red; font-weight: bold;" if row['Quantidade'] == 0 else ""
        linhas_tabela += f"""
        <tr>
            <td>{row['Plataforma']}</td>
            <td>{row['Nome_Item']}</td>
            <td style="text-align: right; {estilo_zero}">{row['Quantidade']:,.2f}</td>
        </tr>
        """
        
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Relatório de Estoque por Plataforma</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 30px; color: #333; }}
            h1 {{ text-align: center; color: #1e293b; border-bottom: 2px solid #0f172a; padding-bottom: 10px; }}
            .info {{ margin-bottom: 20px; font-size: 14px; color: #64748b; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ border: 1px solid #cbd5e1; padding: 10px; text-align: left; font-size: 13px; }}
            th {{ background-color: #f1f5f9; color: #0f172a; font-weight: bold; }}
            tr:nth-child(even) {{ background-color: #f8fafc; }}
            .btn-print {{
                display: block; width: 200px; margin: 0 auto 20px auto; padding: 10px;
                background-color: #2563eb; color: white; text-align: center;
                text-decoration: none; border-radius: 5px; font-weight: bold;
            }}
            @media print {{
                .btn-print {{ display: none; }}
            }}
        </style>
    </head>
    <body>
        <a href="#" class="btn-print" onclick="window.print(); return false;">🖨️ Imprimir Relatório</a>
        <h1>⚓ Relatório de Estoque - LogSmart</h1>
        <div class="info">
            <p><b>Total de Registros:</b> {len(df_export):,}</p>
            <p><b>Quantidade Total em Estoque:</b> {df_export['Quantidade'].sum():,.2f}</p>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Plataforma</th>
                    <th>Nome do Item (Descrição)</th>
                    <th style="text-align: right;">Quantidade</th>
                </tr>
            </thead>
            <tbody>
                {linhas_tabela}
            </tbody>
        </table>
    </body>
    </html>
    """
    return html

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
    # --- Sidebar: Filtros ---
    st.sidebar.header("⚙️ Filtros de Pesquisa")
    
    lista_plataformas = [p for p in df_main['Plataforma'].dropna().unique().tolist() if p != '']
    lista_plataformas.sort()
    
    plataformas_selecionadas = st.sidebar.multiselect(
        "🚢 Selecionar Plataforma(s):",
        options=lista_plataformas,
        default=lista_plataformas
    )
    
    st.sidebar.markdown("---")
    
    lista_categorias = [c for c in df_main['Categoria'].dropna().astype(str).unique().tolist() if c != '']
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
    # 4. Alertas e Lista de Itens Zerados
    # -------------------------------------------------------------------------
    if qtd_zerados > 0:
        st.markdown(f"""
        <div class="alert-box">
            🚨 <b>ALERTA DE ESTOQUE CRÍTICO:</b> Foram detectados <b>{qtd_zerados}</b> item(ns) com <b>quantidade 0</b> nas plataformas selecionadas!
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("🚨 Detalhamento dos Itens Zerados (Alerta)")
        
        tabela_alerta = itens_zerados[['Plataforma', 'Codigo_Item', 'Descricao', 'Categoria', 'Quantidade', 'Arquivo_Origem']].copy()
        tabela_alerta.columns = ['Plataforma', 'Código do Item', 'Descrição do Item', 'Categoria', 'Qtd em Estoque', 'Arquivo Fonte']
        
        st.dataframe(
            tabela_alerta.style.map(lambda v: 'background-color: rgba(239, 68, 68, 0.25); color: #ef4444; font-weight: bold;' if v == 0 else '', subset=['Qtd em Estoque']),
            use_container_width=True
        )
        st.markdown("---")

    # -------------------------------------------------------------------------
    # 5. Exportação e Impressão do Relatório (Nome, Quantidade e Plataforma)
    # -------------------------------------------------------------------------
    st.subheader("🖨️ Exportar e Imprimir Relatório")
    st.markdown("Gere um relatório contendo apenas **Nome do Item**, **Quantidade** e **Plataforma** dos dados selecionados.")

    # DataFrame específico solicitado
    df_export = df_filtered[['Descricao', 'Quantidade', 'Plataforma']].copy()
    df_export.columns = ['Nome_Item', 'Quantidade', 'Plataforma']
    df_export = df_export[['Plataforma', 'Nome_Item', 'Quantidade']]

    exp_col1, exp_col2 = st.columns(2)

    with exp_col1:
        csv_bytes = df_export.to_csv(index=False, sep=';').encode('utf-8-sig')
        st.download_button(
            label="📥 Baixar Relatório para Excel (CSV)",
            data=csv_bytes,
            file_name="relatorio_estoque_plataformas.csv",
            mime="text/csv",
            use_container_width=True
        )

    with exp_col2:
        html_print = gerar_html_impressao(df_export)
        st.download_button(
            label="🖨️ Baixar Relatório Imprimível (HTML)",
            data=html_print,
            file_name="relatorio_impressao.html",
            mime="text/html",
            use_container_width=True
        )

    with st.expander("👁️ Visualizar Prévia da Tabela de Exportação/Impressão"):
        st.dataframe(df_export, use_container_width=True)

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 6. Relatórios por Categoria
    # -------------------------------------------------------------------------
    st.subheader("📊 Relatórios Detalhados por Categoria")
    
    cats_validas = sorted([c for c in df_filtered['Categoria'].astype(str).unique() if c != ''])
    if cats_validas:
        col_sel, _ = st.columns([1, 2])
        with col_sel:
            cat_relatorio = st.selectbox("Selecione uma Categoria para Analisar:", options=cats_validas)
            
        df_cat_especifica = df_filtered[df_filtered['Categoria'].astype(str) == cat_relatorio]
        zerados_cat_esp = df_cat_especifica[df_cat_especifica['Quantidade'] == 0]
        
        r1, r2, r3 = st.columns(3)
        r1.metric(f"Itens em '{cat_relatorio}'", len(df_cat_especifica))
        r2.metric("Total em Estoque", f"{df_cat_especifica['Quantidade'].sum():,.2f}")
        r3.metric("Itens Zerados na Categoria", len(zerados_cat_esp), delta_color="inverse")
        
        tabela_cat_view = df_cat_especifica[['Plataforma', 'Codigo_Item', 'Descricao', 'Quantidade', 'Arquivo_Origem']].copy()
        tabela_cat_view.columns = ['Plataforma', 'Código do Item', 'Descrição / Especificação', 'Quantidade em Estoque', 'Arquivo Fonte']
        
        st.dataframe(
            tabela_cat_view.style.map(lambda v: 'background-color: rgba(239, 68, 68, 0.25); color: #ef4444; font-weight: bold' if v == 0 else '', subset=['Quantidade em Estoque']),
            use_container_width=True
        )

    # -------------------------------------------------------------------------
    # 7. Estudo por Plataforma (Abas)
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("📋 Estudo do Estoque por Plataforma")
    
    plataformas_no_filtro = [p for p in df_filtered['Plataforma'].unique() if p != '']
    
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