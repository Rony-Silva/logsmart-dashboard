import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Dashboard LogSmart - Controle de Estoque", layout="wide")

st.title("📊 Relatório e Controle de Estoque de Itens")
st.markdown("Importação multiarquivos, filtro pela **Coluna N** e alertas de itens zerados.")

# Colunas por índice: I=8, J=9, L=11, N=13, O=14
COLUMNS_IDX = [8, 9, 11, 13, 14]

@st.cache_data
def process_uploaded_files(uploaded_files):
    all_data = []
    
    for file in uploaded_files:
        try:
            # Tenta ler com ';' (padrão regional Excel) ou autodetecção
            if file.name.endswith('.csv'):
                try:
                    df_raw = pd.read_csv(file, header=None, sep=';')
                except Exception:
                    file.seek(0)
                    df_raw = pd.read_csv(file, header=None, sep=None, engine='python')
            else:
                df_raw = pd.read_excel(file, header=None)
            
            # Validação do número de colunas
            max_idx = max(COLUMNS_IDX)
            if df_raw.shape[1] <= max_idx:
                st.warning(f"⚠️ O arquivo `{file.name}` possui apenas {df_raw.shape[1]} colunas (mínimo necessário: {max_idx + 1}).")
                continue
            
            # Extração das colunas I, J, L, N, O
            df_selected = df_raw.iloc[:, COLUMNS_IDX].copy()
            df_selected.columns = ['Coluna_I', 'Coluna_J', 'Coluna_L', 'Coluna_N', 'Quantidade_O']
            
            # Identificação do arquivo de origem (ex: P-38.csv, UMLI.csv)
            df_selected['Arquivo_Origem'] = file.name
            
            # Tratamento numérico para a quantidade (Coluna O)
            df_selected['Quantidade_O'] = (
                df_selected['Quantidade_O']
                .astype(str)
                .str.replace(',', '.', regex=False)
                .str.strip()
            )
            df_selected['Quantidade_O'] = pd.to_numeric(df_selected['Quantidade_O'], errors='coerce').fillna(0)
            
            all_data.append(df_selected)
            
        except Exception as e:
            st.error(f"❌ Erro ao ler o arquivo `{file.name}`: {e}")
            
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()

# 1. Menu Lateral de Importação e Filtros
st.sidebar.header("📂 Importação de Arquivos")
uploaded_files = st.sidebar.file_uploader(
    "Carregue os arquivos (P-38, UMLI, P-09, etc.):", 
    type=["csv", "xlsx", "xls"], 
    accept_multiple_files=True
)

if uploaded_files:
    df_main = process_uploaded_files(uploaded_files)
    
    if not df_main.empty:
        st.sidebar.markdown("---")
        st.sidebar.header("🔍 Filtros de Visualização")
        
        # Filtro de Escolha da Coluna N
        opcoes_n = df_main['Coluna_N'].dropna().astype(str).unique().tolist()
        opcoes_n.sort()
        
        # Opções de Selecionar Todos / Desmarcar Todos
        selecionar_tudo = st.sidebar.checkbox("Selecionar Todos na Coluna N", value=True)
        
        if selecionar_tudo:
            selecao_n = st.sidebar.multiselect(
                "Filtrar por Coluna N:",
                options=opcoes_n,
                default=opcoes_n
            )
        else:
            selecao_n = st.sidebar.multiselect(
                "Filtrar por Coluna N:",
                options=opcoes_n,
                default=[]
            )
            
        # Aplicação do Filtro nos dados consolidados
        if selecao_n:
            df_filtered = df_main[df_main['Coluna_N'].astype(str).isin(selecao_n)]
        else:
            df_filtered = df_main.iloc[0:0]

        # 2. Resumo de Métricas Principais
        col1, col2, col3, col4 = st.columns(4)
        
        total_itens = len(df_filtered)
        total_qtd = df_filtered['Quantidade_O'].sum()
        itens_zerados = df_filtered[df_filtered['Quantidade_O'] == 0]
        qtd_zerados = len(itens_zerados)
        
        col1.metric("Total de Registros", f"{total_itens:,}")
        col2.metric("Soma das Quantidades", f"{total_qtd:,.2f}")
        col3.metric("Itens com Estoque (>0)", f"{total_itens - qtd_zerados:,}")
        col4.metric("🚨 Itens Zerados (=0)", f"{qtd_zerados:,}", delta_color="inverse")
        
        st.markdown("---")

        # 3. Alerta Crítico para Itens com Quantidade Zero
        if qtd_zerados > 0:
            st.error(f"⚠️ **ALERTA DE ESTOQUE ZERADO:** Foram localizados **{qtd_zerados}** itens com **quantidade 0** para a seleção atual da Coluna N!")
            with st.expander("🚨 Ver detalhe dos itens com quantidade ZERADA"):
                st.dataframe(
                    itens_zerados[['Arquivo_Origem', 'Coluna_I', 'Coluna_J', 'Coluna_L', 'Coluna_N', 'Quantidade_O']],
                    use_container_width=True
                )
        else:
            st.success("✅ Nenhum item zerado para os filtros aplicados.")

        # 4. Detalhamento por Arquivo de Origem (P-38, UMLI, P-09, etc.)
        st.subheader("📂 Detalhamento dos Itens por Arquivo")
        
        arquivos_presentes = df_filtered['Arquivo_Origem'].unique()
        
        if len(arquivos_presentes) > 0:
            for arq in arquivos_presentes:
                df_arq = df_filtered[df_filtered['Arquivo_Origem'] == arq]
                zerados_arq = df_arq[df_arq['Quantidade_O'] == 0]
                num_zerados = len(zerados_arq)
                
                # Título do bloco por arquivo com indicativo visual de alerta
                status_alerta = f"🚨 ({num_zerados} ZERADOS)" if num_zerados > 0 else "✅ (OK)"
                
                with st.expander(f"📄 Arquivo: **{arq}** — Total de Itens: {len(df_arq)} | Status: {status_alerta}"):
                    if num_zerados > 0:
                        st.warning(f"Atenção: O arquivo **{arq}** contém **{num_zerados}** item(ns) com quantidade igual a zero.")
                    
                    # Tabela individual estilizada por arquivo
                    def highlight_zeros(val):
                        return 'background-color: #ffcccc; color: red; font-weight: bold' if val == 0 else ''

                    st.dataframe(
                        df_arq[['Coluna_I', 'Coluna_J', 'Coluna_L', 'Coluna_N', 'Quantidade_O']]
                        .style.map(highlight_zeros, subset=['Quantidade_O']),
                        use_container_width=True
                    )
        else:
            st.info("Nenhum item para exibir no filtro selecionado.")

        st.markdown("---")

        # 5. Visualização Gráfica
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("📊 Quantidades Agrupadas por Coluna N")
            if not df_filtered.empty:
                df_grouped = df_filtered.groupby('Coluna_N', as_index=False)['Quantidade_O'].sum()
                fig_bar = px.bar(
                    df_grouped,
                    x='Coluna_N',
                    y='Quantidade_O',
                    text_auto='.2f',
                    title="Total da Coluna O agrupado por valor de N",
                    labels={'Coluna_N': 'Coluna N', 'Quantidade_O': 'Quantidade (Coluna O)'}
                )
                st.plotly_chart(fig_bar, use_container_width=True)
                
        with col_g2:
            st.subheader("🚨 Proporção de Itens Zerados vs Ativos")
            if not df_filtered.empty:
                status_df = pd.DataFrame({
                    'Status': ['Estoque (>0)', 'Zerados (=0)'],
                    'Quantidade': [total_itens - qtd_zerados, qtd_zerados]
                })
                fig_pie = px.pie(
                    status_df,
                    names='Status',
                    values='Quantidade',
                    color='Status',
                    color_discrete_map={'Estoque (>0)': '#2ca02c', 'Zerados (=0)': '#d62728'},
                    hole=0.4,
                    title="Proporção de Status no Filtro Selecionado"
                )
                st.plotly_chart(fig_pie, use_container_width=True)

else:
    st.info("👆 Por favor, faça o upload de um ou mais arquivos na barra lateral para carregar a análise.")