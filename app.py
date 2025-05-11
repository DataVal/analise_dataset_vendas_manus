import pandas as pd
import streamlit as st
import plotly.express as px
import requests
import numpy as np
import datetime

# ======================================
# CONFIGURAÇÃO DA PÁGINA
# ======================================
st.set_page_config(
    page_title="Dashboard E-Commerce DataSmart",
    page_icon="📊",
    layout="wide"
)

# ======================================
# FUNÇÃO PARA CARREGAR DADOS
# ======================================
@st.cache_data
def load_data():
    #Carrega a partir do .parquet
    df = pd.read_parquet("dataset_tratado.parquet")
    return df

# Carregar dados
df = load_data()
df = df[df["Estado"] != "Desconhecido"]

# Converter para datetime se ainda não for
df['Data_Venda'] = pd.to_datetime(df['Data_Venda'])

# ======================================
# BARRA LATERAL (FILTROS)
# ======================================
with st.sidebar:
    st.header("⚙️ Filtros")
    
    # Filtro de Estados
    # Lista real de estados
    estados_unicos = df['Estado'].unique().tolist()
    opcoes_estados = ['Todos'] + estados_unicos

    # Multiselect com "Todos" como padrão
    estado_selecionado = st.multiselect(
        label="Selecione os Estados:",
        options=opcoes_estados,
        default=['Todos']
    )

    # Lógica para aplicar o filtro
    if 'Todos' in estado_selecionado:
        estados_filtrados = estados_unicos
    else:
        estados_filtrados = estado_selecionado
    
    # Filtro de Categorias
    categorias = st.multiselect(
        label="Selecione as Categorias:",
        options=df['Categoria'].unique(),
        default=df['Categoria'].unique().tolist()
    )

    # Filtro de intervalo de datas com calendário
    inicio_fim = st.date_input(
        "Selecione o intervalo de datas:",
        value=(df['Data_Venda'].min().date(), df['Data_Venda'].max().date())
    )
    data_inicio, data_fim = inicio_fim

# ======================================
# APLICAR FILTROS
# ======================================
filtered_df = df[
    (df['Estado'].isin(estados_filtrados)) &
    (df['Categoria'].isin(categorias)) &
    (df['Data_Venda'].dt.date.between(data_inicio, data_fim))
]


# ======================================
# MÉTRICAS PRINCIPAIS
# ======================================
total_pedidos = filtered_df['ID_Pedido'].nunique()
vendas_totais = filtered_df['Valor_Total'].sum()
ticket_medio = filtered_df['Valor_Total'].mean()

# Layout em colunas para métricas
col1, col2, col3 = st.columns(3)
col1.metric("📦 Total de Pedidos", total_pedidos)
col2.metric("💰 Vendas Totais", f"R${vendas_totais:,.2f}")
col3.metric("💵 Ticket Médio", f"R${ticket_medio:,.2f}")

# ======================================
# GRÁFICOS PRINCIPAIS
# ======================================
tab1, tab2, tab3 = st.tabs(["📈 Análise Temporal", "🗺️ Análise Geográfica", "📦 Top Categorias"])

with tab1:
    # Gráfico de Vendas Mensais
    vendas_mensais = filtered_df.groupby(['Ano_Venda', 'Mes_Venda'])['Valor_Total'].sum().reset_index()

    # Criar coluna com data completa para eixo X
    vendas_mensais['Data'] = pd.to_datetime(
        vendas_mensais['Ano_Venda'].astype(str) + '-' + vendas_mensais['Mes_Venda'].astype(str)
    )

    fig1 = px.line(
        vendas_mensais,
        x='Data',
        y='Valor_Total',
        title='Vendas Mensais',
        markers=True,
        labels={'Data': 'Data', 'Valor_Total': 'Vendas (R$)'}
    )

    st.plotly_chart(fig1, use_container_width=True)


with tab2:
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    geojson_estados = requests.get(url).json()
    estados_counts = filtered_df[filtered_df["Estado"] != "Desconhecido"]
    estados_counts = estados_counts.groupby('Estado')["Valor_Total"].sum().reset_index()


    fig2 = px.choropleth(
    estados_counts,
    geojson=geojson_estados,
    locations="Estado",
    color="Valor_Total",
    color_continuous_scale="YlOrRd",
    range_color=(estados_counts["Valor_Total"].mean(), estados_counts["Valor_Total"].quantile(0.95)),  # até o percentil 95%
    featureidkey="properties.sigla",
    scope="south america",
    title="Vendas por Estado"
    )


    fig2.update_geos(fitbounds="locations", visible=False)
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    # Vendas por Categoria
    top_categorias = filtered_df['Categoria'].value_counts().nlargest(10).reset_index()
    top_categorias.columns = ['Categoria', 'Contagem']

    fig3 = px.bar(
        top_categorias,
        x='Categoria',
        y='Contagem',
        title='Vendas por Categoria',
        color='Contagem',
        color_continuous_scale="Tealrose",
        log_y=True

    )

    st.plotly_chart(fig3, use_container_width=True)

# ======================================
# TABELA DE DADOS
# ======================================
st.subheader("🔍 Dados Detalhados")
st.dataframe(
    filtered_df[["ID_Pedido",
         "Nome_Produto", 
         "Categoria", 
         "Nome_Cliente",
         "Email",
         "Estado",
         "Mes_Venda",
         "Ano_Venda", 
         "Quantidade", 
         "Preco_Unitario", 
         "Metodo_Pagamento",
         "Valor_Total"]],
    column_config={
        "ID_Pedido": "Pedido",
        "Preco_Unitario": "Preço (R$)",
        "Mes_Venda": "Mês da Compra",
        "Ano_Venda": "Ano da Compra"

    },
    use_container_width=True,
    hide_index=True
)