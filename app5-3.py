import os
import glob
import pandas as pd
import streamlit as st
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. Configuração da Página e CSS Visual Premium (Dark Obsidian Fix)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="LogSmart - Control Tower Offshore",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Fundo Dark Obsidian Forçado no Conteúdo e Cabeçalho */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background: radial-gradient(circle at 20% 20%, #0f172a 0%, #080c14 100%) !important;
        color: #f8fafc !important;
    }

    /* Ocultar menus padrões */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Forçar cores de texto legíveis em rótulos e marcadores */
    label, p, span, h1, h2, h3, h4, h5, h6, [data-testid="stMarkdownContainer"] p {
        color: #f8fafc !important;
    }

    /* Customização dos componentes de filtro (Selectbox/Multiselect) */
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
        color: #f8fafc !important;
    }
    
    div[data-baseweb="tag"] {
        background-color: #3b82f6 !important;
    }

    /* Top Banner Hero */
    .hero-container {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.8) 100%);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 25px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 900;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        color: #94a3b8 !important;
        font-size: 0.95rem;
        margin-top: 6px;
        font-weight: 400;
    }

    /* Cards de Métricas com Glassmorphism */
    .metric-card {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(16px);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; width: 100%; height: 3px;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
    }
    .metric-card.alert::before {
        background: linear-gradient(90deg, #f43f5e, #fb7185);
    }
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(56, 189, 248, 0.4);
    }
    .metric-label {
        color: #94a3b8 !important;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .metric-val {
        color: #f8fafc !important;
        font-size: 1.9rem;
        font-weight: 900;
        margin-top: 8px;
        letter-spacing: -0.02em;
    }

    /* Banner Alerta Neon */
    .alert-banner {
        background: linear-gradient(90deg, rgba(244, 63, 94, 0.15) 0%, rgba(15, 23, 42, 0.6) 100%);
        border: 1px solid rgba(244, 63, 94, 0.2);
        border-left: 4px solid #f43f5e;
        backdrop-filter: blur(12px);
        border-radius: 12px;
        padding: 16px 20px;
        color: #fecdd3 !important;
        font-weight: 600;
        margin-bottom: 25px;
    }

    /* Barra Lateral Dark */
    [data-testid="stSidebar"] {
        background-color: #0b0f19 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Abas Futuristas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(15, 23, 42, 0.4);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        border-radius: 8px;
        color: #94a3b8 !important;
        font-weight: 600;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #38bdf8 0%, #6366f1 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.35);
    }

    /* Estilização de Botões */
    .stButton>button {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
        color: #38bdf8 !important;
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #38bdf8 0%, #6366f1 100%) !important;
        color: #ffffff !important;
        border-color: transparent !important;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. Conversor Numérico Seguro de Quantidades
# -----------------------------------------------------------------------------
def converter_quantidade(val):
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    
    s = str(val).strip()
    if not s or s.lower() in ["nan", "none", "null", ""]:
        return 0.0
    
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
        
    try:
        return float(s)
    except ValueError:
        return 0.0

# -----------------------------------------------------------------------------
# 3. Ingestão e Processamento dos Dados
# -----------------------------------------------------------------------------
@st.cache_data(ttl=5)
def carregar_dados_pasta(nome_pasta="dados"):
    diretorio_base = os.path.dirname(os.path.abspath(__file__))
    caminho_pasta = os.path.join(diretorio_base, nome_pasta)

    if not os.path.exists(caminho_pasta):
        return pd.DataFrame(), []

    padroes_busca = ['*.xlsx', '*.XLSX', '*.xls', '*.XLS', '*.csv', '*.CSV']
    arquivos = []
    for padrao in padroes_busca:
        arquivos.extend(glob.glob(os.path.join(caminho_pasta, padrao)))
    
    arquivos = list(set(arquivos))

    if not arquivos:
        return pd.DataFrame(), []

    lista_dfs = []
    alertas_leitura = []

    for arquivo in arquivos:
        nome_arquivo = os.path.basename(arquivo)
        nome_base_arquivo = os.path.splitext(nome_arquivo)[0]
        
        if os.path.getsize(arquivo) == 0:
            alertas_leitura.append(f"`{nome_arquivo}` está completamente vazio (0 bytes).")
            continue

        try:
            nome_plataforma = nome_base_arquivo
            is_excel = arquivo.lower().endswith(('.xlsx', '.xls'))
            
            if is_excel:
                df_raw_file = pd.read_excel(arquivo, header=None)
            else:
                with open(arquivo, 'r', encoding='utf-8', errors='ignore') as f:
                    primeiras_linhas = "".join([f.readline() for _ in range(5)])
                
                sep_detectado = ';' if primeiras_linhas.count(';') >= primeiras_linhas.count(',') else ','
                df_raw_file = pd.read_csv(arquivo, header=None, sep=sep_detectado, engine='python', on_bad_lines='skip')

            if df_raw_file.empty:
                alertas_leitura.append(f"`{nome_arquivo}` não possui linhas de dados.")
                continue

            # Captura da Plataforma (Célula L2 -> Linha índice 1, Coluna L [11])
            if df_raw_file.shape[0] >= 2 and df_raw_file.shape[1] >= 12:
                val_l2 = df_raw_file.iloc[1, 11]
                if pd.notna(val_l2) and str(val_l2).strip().lower() not in ["", "nan", "none", "plataforma", "unidade"]:
                    nome_plataforma = str(val_l2).strip()

            # Padding para garantir 15 colunas (A até O -> Índice 0 até 14)
            if df_raw_file.shape[1] < 15:
                for c in range(df_raw_file.shape[1], 15):
                    df_raw_file[c] = None

            # Captura dos dados a partir da LINHA 2 (O2 em diante)
            df_dados = df_raw_file.iloc[1:].copy()

            # Mapeamento: I(8)=Código, J(9)=Item, L(11)=Localização, N(13)=Categoria, O(14)=Quantidade
            df_selecionado = df_dados.iloc[:, [8, 9, 11, 13, 14]].copy()
            df_selecionado.columns = ["Código", "Item", "Localização", "Categoria", "Quantidade"]
            df_selecionado["Plataforma"] = nome_plataforma

            for col in ["Código", "Item", "Localização", "Categoria"]:
                df_selecionado[col] = df_selecionado[col].astype(str).str.strip()

            termos_cabecalho = [
                "item", "descrição", "descricao", "descriçao", "código", "codigo", 
                "code", "material", "especificação", "especificacao", "nome", 
                "equipamento", "produto", "denominacao", "denominação", "quantidade", 
                "qtd", "qty", "categoria", "localização", "localizacao", "nan", "none", "", "null"
            ]

            categorias_invalidas = ["nan", "none", "", "0", "geral", "não especificada", "nao especificada", "categoria"]

            is_valido = (
                (~df_selecionado["Item"].str.lower().isin(termos_cabecalho)) &
                (~df_selecionado["Código"].str.lower().isin(termos_cabecalho)) &
                (~df_selecionado["Quantidade"].astype(str).str.strip().str.lower().isin(termos_cabecalho)) &
                (~df_selecionado["Categoria"].str.lower().isin(categorias_invalidas))
            )
            df_selecionado = df_selecionado[is_valido].copy()

            df_selecionado["Quantidade"] = df_selecionado["Quantidade"].apply(converter_quantidade)

            if not df_selecionado.empty:
                lista_dfs.append(df_selecionado)
            else:
                alertas_leitura.append(f"`{nome_arquivo}` não continha itens de dados válidos.")

        except Exception as e:
            alertas_leitura.append(f"Erro ao processar `{nome_arquivo}`: {e}")

    if lista_dfs:
        df_final = pd.concat(lista_dfs, ignore_index=True)
        cols_texto = ["Código", "Item", "Localização", "Categoria", "Plataforma"]
        for col in cols_texto:
            df_final[col] = df_final[col].astype(str).str.strip()

        categorias_invalidas = ["nan", "none", "", "0", "geral", "não especificada", "nao especificada", "categoria"]
        df_final = df_final[~df_final["Categoria"].str.lower().isin(categorias_invalidas)]
        df_final["Status_Estoque"] = df_final["Quantidade"].apply(lambda q: "🔴 ZERADO" if q == 0 else "🟢 DISPONÍVEL")

        return df_final, alertas_leitura
    else:
        return pd.DataFrame(), alertas_leitura

# -----------------------------------------------------------------------------
# 4. Interface Principal e Barra Lateral
# -----------------------------------------------------------------------------
st.markdown("""
<div class="hero-container">
    <div class="hero-title">⚓ LogSmart — Control Tower Offshore</div>
    <div class="hero-subtitle">Sistema Integrado de Monitoramento de Suprimentos & Rastreabilidade de Estoque</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("### ⚙️ Painel de Operações")

if st.sidebar.button("🔄 Recarregar Dados do Disco", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

df_raw, lista_alertas = carregar_dados_pasta("dados")

if lista_alertas:
    with st.sidebar.expander("⚠️ Alertas de Leitura de Arquivos"):
        for alert in lista_alertas:
            st.caption(f"• {alert}")

if df_raw.empty:
    st.error("❌ Nenhum dado válido pôde ser carregado da pasta `dados/`.")
    st.stop()

st.sidebar.markdown("---")
plataformas_disponiveis = sorted(list(df_raw["Plataforma"].unique()))
plataformas_sel = st.sidebar.multiselect(
    "🚢 Selecionar Plataformas:",
    options=plataformas_disponiveis,
    default=plataformas_disponiveis
)

categorias_disponiveis = sorted(list(df_raw["Categoria"].unique()))
categorias_sel = st.sidebar.multiselect(
    "🏷️ Selecionar Categorias:",
    options=categorias_disponiveis,
    default=categorias_disponiveis
)

df_filtrado = df_raw[
    (df_raw["Plataforma"].isin(plataformas_sel)) &
    (df_raw["Categoria"].isin(categorias_sel))
].copy()

# -----------------------------------------------------------------------------
# 5. Dashboard de Métricas
# -----------------------------------------------------------------------------
total_itens = len(df_filtrado)
total_qtd = float(df_filtrado["Quantidade"].sum())
itens_zero = df_filtrado[df_filtrado["Quantidade"] == 0]
qtd_zero = len(itens_zero)
plats_ativas = df_filtrado["Plataforma"].nunique()

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Registros Exibidos</div>
        <div class="metric-val">{total_itens:,}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Volume em Estoque</div>
        <div class="metric-val" style="color: #38bdf8;">{total_qtd:,.0f} <span style="font-size:1rem; color:#64748b;">un</span></div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Unidades Ativas</div>
        <div class="metric-val" style="color: #c084fc;">{plats_ativas}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    alert_class = "alert" if qtd_zero > 0 else ""
    color_val = "#f43f5e" if qtd_zero > 0 else "#34d399"
    st.markdown(f"""
    <div class="metric-card {alert_class}">
        <div class="metric-label">Itens Zerados (Crítico)</div>
        <div class="metric-val" style="color: {color_val};">{qtd_zero}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if qtd_zero > 0:
    st.markdown(f"""
    <div class="alert-banner">
        🚨 <b>ATENÇÃO OPERACIONAL:</b> Foram detectados <b>{qtd_zero}</b> itens com saldo NULO/ZERADO no escopo selecionado.
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("🔍 Clique para inspecionar a lista discriminada de itens Zerados"):
        st.dataframe(
            itens_zero[["Plataforma", "Código", "Item", "Categoria", "Localização"]],
            use_container_width=True,
            hide_index=True
        )

# -----------------------------------------------------------------------------
# 6. Análise Visual Grafica (Plotly Dark Customizado)
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("### 📊 Analytics de Suprimentos")

col_g1, col_g2 = st.columns(2)

with col_g1:
    df_cat = df_filtrado.groupby("Categoria")["Quantidade"].sum().reset_index().sort_values(by="Quantidade", ascending=False)
    fig_cat = px.bar(
        df_cat,
        x="Categoria",
        y="Quantidade",
        text_auto=".0f",
        title="Volume em Estoque por Categoria",
        color="Categoria",
        color_discrete_sequence=["#38bdf8", "#818cf8", "#c084fc", "#34d399", "#f43f5e", "#fbbf24"]
    )
    fig_cat.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"),
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)")
    )
    st.plotly_chart(fig_cat, use_container_width=True)

with col_g2:
    df_plat = df_filtrado.groupby("Plataforma")["Quantidade"].sum().reset_index().sort_values(by="Quantidade", ascending=False)
    fig_plat = px.pie(
        df_plat,
        names="Plataforma",
        values="Quantidade",
        title="Distribuição por Unidade / Plataforma",
        hole=0.5,
        color_discrete_sequence=["#00f2fe", "#4f46e5", "#c084fc", "#38bdf8", "#f43f5e", "#34d399"]
    )
    fig_plat.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8")
    )
    st.plotly_chart(fig_plat, use_container_width=True)

# -----------------------------------------------------------------------------
# 7. Central de Relatórios e Exportação
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("### 🖨️ Central de Relatórios e Exportação")

opcao_escopo = st.radio(
    "Defina o escopo para geração do relatório:",
    options=[
        "Relatório Filtrado (Apenas Seleção da Barra Lateral)",
        "Relatório Completo (Todas as Categorias e Plataformas)"
    ],
    horizontal=True
)

if opcao_escopo.startswith("Relatório Filtrado"):
    df_relatorio = df_filtrado.copy()
    titulo_escopo = "Relatório Personalizado por Categoria/Plataforma"
else:
    df_relatorio = df_raw.copy()
    titulo_escopo = "Relatório Geral de Estoque Completo"

tab_zerados, tab_disponiveis, tab_todos = st.tabs([
    "🚨 Itens Zerados por Unidade",
    "📦 Itens Disponíveis por Unidade",
    "📄 Visão Geral Unificada"
])

with tab_zerados:
    df_rel_zero = df_relatorio[df_relatorio["Quantidade"] == 0].sort_values(by=["Plataforma", "Categoria", "Item"])
    if not df_rel_zero.empty:
        st.dataframe(
            df_rel_zero[["Plataforma", "Código", "Item", "Categoria", "Localização", "Status_Estoque"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("🎉 Nenhum item zerado no escopo selecionado!")

with tab_disponiveis:
    df_rel_disp = df_relatorio[df_relatorio["Quantidade"] > 0].sort_values(by=["Plataforma", "Categoria", "Item"])
    st.dataframe(
        df_rel_disp[["Plataforma", "Código", "Item", "Categoria", "Localização", "Quantidade", "Status_Estoque"]],
        use_container_width=True,
        hide_index=True
    )

with tab_todos:
    st.dataframe(
        df_relatorio.sort_values(by=["Plataforma", "Categoria", "Item"])[
            ["Plataforma", "Código", "Item", "Categoria", "Localização", "Quantidade", "Status_Estoque"]
        ],
        use_container_width=True,
        hide_index=True
    )

# -----------------------------------------------------------------------------
# 8. Gerador de Relatório HTML Estilizado para Impressão
# -----------------------------------------------------------------------------
def gerar_html_relatorio_discriminado(df, titulo):
    tot_itens = len(df)
    tot_quant = int(df["Quantidade"].sum())
    tot_zerados = int((df["Quantidade"] == 0).sum())
    
    plataformas = sorted(df["Plataforma"].unique())
    html_unidades = ""

    for plat in plataformas:
        df_p = df[df["Plataforma"] == plat]
        df_p_zero = df_p[df_p["Quantidade"] == 0]
        df_p_disp = df_p[df_p["Quantidade"] > 0]

        linhas_zerados = ""
        if not df_p_zero.empty:
            for _, r in df_p_zero.iterrows():
                linhas_zerados += f"""
                <tr class="row-zero">
                    <td>{r['Código']}</td>
                    <td><strong>{r['Item']}</strong></td>
                    <td>{r['Categoria']}</td>
                    <td>{r['Localização']}</td>
                    <td class="badge-zero">0 un</td>
                </tr>
                """
            bloco_zerados = f"""
            <div class="sub-section">
                <h4 class="title-zero">🚨 ITENS ZERADOS / ESTOQUE CRÍTICO ({len(df_p_zero)})</h4>
                <table>
                    <thead>
                        <tr class="th-zero">
                            <th>Código</th>
                            <th>Item / Descrição</th>
                            <th>Categoria</th>
                            <th>Localização</th>
                            <th>Qtd</th>
                        </tr>
                    </thead>
                    <tbody>{linhas_zerados}</tbody>
                </table>
            </div>
            """
        else:
            bloco_zerados = '<p class="clean-unit">✅ Nenhum item zerado nesta unidade.</p>'

        linhas_disp = ""
        if not df_p_disp.empty:
            for _, r in df_p_disp.iterrows():
                linhas_disp += f"""
                <tr>
                    <td>{r['Código']}</td>
                    <td>{r['Item']}</td>
                    <td>{r['Categoria']}</td>
                    <td>{r['Localização']}</td>
                    <td class="qtd-disp">{int(r['Quantidade'])} un</td>
                </tr>
                """
            bloco_disp = f"""
            <div class="sub-section">
                <h4 class="title-disp">📦 ITENS DISPONÍVEIS EM ESTOQUE ({len(df_p_disp)})</h4>
                <table>
                    <thead>
                        <tr class="th-disp">
                            <th>Código</th>
                            <th>Item / Descrição</th>
                            <th>Categoria</th>
                            <th>Localização</th>
                            <th>Qtd</th>
                        </tr>
                    </thead>
                    <tbody>{linhas_disp}</tbody>
                </table>
            </div>
            """
        else:
            bloco_disp = '<p class="clean-unit">Nenhum item com estoque positivo nesta unidade.</p>'

        html_unidades += f"""
        <div class="unit-card">
            <div class="unit-header">
                <span>🚢 UNIDADE / PLATAFORMA: <strong>{plat}</strong></span>
                <span class="unit-stats">Total: {len(df_p)} itens | Volume: {int(df_p['Quantidade'].sum()):,} un | Zerados: {len(df_p_zero)}</span>
            </div>
            <div class="unit-body">
                {bloco_zerados}
                {bloco_disp}
            </div>
        </div>
        """

    html_code = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>{titulo}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 25px; color: #222; background-color: #fff; }}
            .header {{ text-align: center; border-bottom: 3px solid #0066cc; padding-bottom: 12px; margin-bottom: 20px; }}
            .header h1 {{ margin: 0; color: #0066cc; font-size: 24px; }}
            .header p {{ margin: 4px 0 0 0; color: #555; font-size: 13px; }}
            .btn-print {{ display: block; width: 260px; margin: 10px auto 20px auto; padding: 12px; background-color: #0066cc; color: white; text-align: center; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 14px; box-shadow: 0 4px 10px rgba(0,0,0,0.15); }}
            .summary-cards {{ display: flex; justify-content: space-around; margin-bottom: 25px; }}
            .card {{ background: #f8f9fa; border: 1px solid #dcdcdc; border-radius: 6px; padding: 10px 18px; text-align: center; width: 22%; }}
            .card h3 {{ margin: 0; font-size: 12px; color: #555; }}
            .card p {{ margin: 4px 0 0 0; font-size: 18px; font-weight: bold; color: #0066cc; }}
            .card.alert p {{ color: #cc0000; }}
            .unit-card {{ border: 1px solid #0066cc; border-radius: 8px; margin-bottom: 25px; overflow: hidden; page-break-inside: avoid; }}
            .unit-header {{ background-color: #0066cc; color: white; padding: 10px 15px; font-size: 15px; display: flex; justify-content: space-between; align-items: center; }}
            .unit-stats {{ font-size: 12px; background: rgba(255,255,255,0.2); padding: 3px 8px; border-radius: 4px; }}
            .unit-body {{ padding: 15px; background: #fff; }}
            .sub-section {{ margin-bottom: 15px; }}
            .title-zero {{ color: #cc0000; margin: 0 0 8px 0; font-size: 13px; border-bottom: 2px solid #ffcccc; padding-bottom: 4px; }}
            .title-disp {{ color: #0066cc; margin: 0 0 8px 0; font-size: 13px; border-bottom: 2px solid #cce5ff; padding-bottom: 4px; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 10px; }}
            th {{ text-align: left; padding: 6px 8px; }}
            .th-zero {{ background-color: #d9534f; color: white; }}
            .th-disp {{ background-color: #4682b4; color: white; }}
            td {{ padding: 6px 8px; border-bottom: 1px solid #eee; }}
            .row-zero {{ background-color: #ffe6e6; }}
            .badge-zero {{ color: #cc0000; font-weight: bold; }}
            .qtd-disp {{ color: #28a745; font-weight: bold; }}
            .clean-unit {{ font-size: 12px; color: #28a745; margin: 5px 0 15px 0; font-weight: bold; }}
            .footer {{ margin-top: 30px; text-align: center; font-size: 11px; color: #777; border-top: 1px solid #ddd; padding-top: 8px; }}
            @media print {{ body {{ margin: 0; }} .btn-print {{ display: none; }} .unit-card {{ page-break-inside: avoid; }} }}
        </style>
    </head>
    <body>
        <a href="#" class="btn-print" onclick="window.print(); return false;">🖨️ Imprimir / Salvar em PDF</a>
        <div class="header">
            <h1>LogSmart — {titulo}</h1>
            <p>Relatório Operacional Discriminado por Unidade (Zerados vs. Disponíveis)</p>
        </div>
        <div class="summary-cards">
            <div class="card">
                <h3>Unidades Avaliadas</h3>
                <p>{len(plataformas)}</p>
            </div>
            <div class="card">
                <h3>Total de Registros</h3>
                <p>{tot_itens:,}</p>
            </div>
            <div class="card alert">
                <h3>Itens Zerados</h3>
                <p>{tot_zerados:,}</p>
            </div>
            <div class="card">
                <h3>Volume Disponível</h3>
                <p>{tot_quant:,} un</p>
            </div>
        </div>
        
        {html_unidades}

        <div class="footer">
            <p>Gerado pelo Sistema LogSmart • Documento para Auditoria e Controle de Suprimentos Offshore</p>
        </div>
    </body>
    </html>
    """
    return html_code

# Botões de Exportação
st.markdown("<br>", unsafe_allow_html=True)
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    df_exp = df_relatorio.sort_values(by=["Plataforma", "Categoria", "Item"])[
        ["Plataforma", "Status_Estoque", "Código", "Item", "Categoria", "Localização", "Quantidade"]
    ]
    data_csv = df_exp.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label="📥 Baixar Dados Organizados em CSV (Separado por Status/Unidade)",
        data=data_csv,
        file_name="relatorio_logsmart_discriminado.csv",
        mime="text/csv",
        use_container_width=True
    )

with col_btn2:
    conteudo_html = gerar_html_relatorio_discriminado(df_relatorio, titulo_escopo)
    st.download_button(
        label="🖨️ Baixar Relatório Formatado para Impressão (HTML Setorizado)",
        data=conteudo_html,
        file_name="relatorio_logsmart_impressao.html",
        mime="text/html",
        use_container_width=True
    )