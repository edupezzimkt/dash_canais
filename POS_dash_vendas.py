import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

st.set_page_config(layout="wide")

@st.cache_data
def carregar_dados():
    return pd.read_parquet("dados_agregados.parquet")

# Carregar dados pré-processados
pivot_pedidos = carregar_dados()

# Cores fixas para cada canal
cores_canais = {
    'WhatsApp': '#98df8a',
    'Site': '#ff9896',
    'Telefone': '#ff7f0e',
    'Presencial': '#1f77b4',
    'E-mail': '#aec7e8',
    'Sem canal': '#e377c2',
    'Visita': '#bcbd22'
}

# Filtros disponíveis
meses_disponiveis = sorted(pivot_pedidos['ano_mes'].unique())
vendedoras_disponiveis = sorted(pivot_pedidos['vendedor_conclusao'].unique())

# Layout
st.title("📊 Análise de Pedidos por Canal e Vendedora")
modo_visualizacao = st.radio("Modo de visualização:", ["Comparar vendedoras em um mês", "Evolução de uma vendedora"])

if modo_visualizacao == "Comparar vendedoras em um mês":
    col1, col2 = st.columns([1, 4])
    with col1:
        mes_selecionado = st.selectbox("Selecione o mês:", meses_disponiveis, index=len(meses_disponiveis)-1)
        vendedoras_selecionadas = st.multiselect("Selecione vendedora(s):", vendedoras_disponiveis, default=vendedoras_disponiveis[:5])

    df_filtrado = pivot_pedidos[
        (pivot_pedidos['ano_mes'] == mes_selecionado) &
        (pivot_pedidos['vendedor_conclusao'].isin(vendedoras_selecionadas))
    ].copy()

    eixo_x = 'pct'
    eixo_y = 'vendedora'
    orientacao = 'h'
    label = mes_selecionado

else:  # Evolução de uma vendedora
    col1, col2 = st.columns([1, 4])
    with col1:
        vendedora_selecionada = st.selectbox("Selecione a vendedora:", vendedoras_disponiveis)

    df_filtrado = pivot_pedidos[
        pivot_pedidos['vendedor_conclusao'] == vendedora_selecionada
    ].copy()

    df_filtrado['mes_str'] = pd.to_datetime(df_filtrado['ano_mes']).dt.strftime('%Y-%m')
    df_filtrado = df_filtrado.sort_values('mes_str')

    eixo_x = 'mes'
    eixo_y = 'pct'
    orientacao = 'v'
    label = vendedora_selecionada

# Verificar se há dados
with col2:
    st.markdown("### ")
    if df_filtrado.empty:
        st.warning("Nenhum dado disponível com os filtros selecionados.")
    else:
        canais = [col for col in df_filtrado.columns if col.endswith('_pct')]
        canais_limpos = [col.replace('_pct', '') for col in canais]

        dados_plotly = pd.DataFrame()
        for canal_pct, canal_abs in zip(canais, canais_limpos):
            if modo_visualizacao == "Comparar vendedoras em um mês":
                temp = df_filtrado[['vendedor_conclusao', canal_pct, canal_abs]].copy()
                temp.columns = ['vendedora', 'pct', 'qtd']
            else:
                temp = df_filtrado[['mes_str', canal_pct, canal_abs]].copy()
                temp.columns = ['mes', 'pct', 'qtd']
                temp['vendedora'] = vendedora_selecionada
            temp['canal'] = canal_abs
            dados_plotly = pd.concat([dados_plotly, temp], ignore_index=True)

            dados_plotly['texto'] = dados_plotly.apply(lambda row: f"{row['pct']:.1f}% ({int(row['qtd'])})", axis=1)

            fig = px.bar(
                dados_plotly,
                x=eixo_x,
                y=eixo_y,
                color='canal',
                color_discrete_map=cores_canais,
                text='texto',  # Apenas o nome da coluna
                barmode='stack',
                orientation=orientacao,
                height=500 + (len(df_filtrado) * 25 if orientacao == 'h' else 0),
                title=f'Pedidos por Canal – {label}'
            )

        fig.update_layout(
            xaxis_title='Mês' if orientacao == 'v' else 'Percentual de Pedidos (%)',
            yaxis_title='Percentual de Pedidos (%)' if orientacao == 'v' else 'Vendedora',
            legend_title='Canal',
            margin=dict(l=40, r=40, t=60, b=40)
        )

        fig.update_traces(textposition='inside', insidetextanchor='middle')
        st.plotly_chart(fig, use_container_width=True)
