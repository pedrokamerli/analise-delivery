"""Dashboard público do case, baseado apenas em dados agregados."""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
PASTA_DADOS = RAIZ_PROJETO / "dados" / "publicos"

st.set_page_config(page_title="Análise de Delivery", page_icon="📊", layout="wide")


@st.cache_data
def carregar_dados() -> dict[str, pd.DataFrame | dict]:
    return {
        "resumo": json.loads((PASTA_DADOS / "resumo.json").read_text(encoding="utf-8")),
        "mes": pd.read_csv(PASTA_DADOS / "pedidos_por_mes.csv"),
        "dia": pd.read_csv(PASTA_DADOS / "por_dia.csv"),
        "hora": pd.read_csv(PASTA_DADOS / "por_hora.csv"),
        "status": pd.read_csv(PASTA_DADOS / "por_status.csv"),
        "rfm": pd.read_csv(PASTA_DADOS / "segmentos_rfm.csv"),
    }


dados = carregar_dados()
resumo = dados["resumo"]

st.title("Análise de uma operação de delivery")
st.caption(f"Período analisado: {resumo['periodo']}")

coluna_1, coluna_2, coluna_3 = st.columns(3)
coluna_1.metric("Pedidos analisados", f"{resumo['total_pedidos']:,}".replace(",", "."))
coluna_2.metric("Taxa de conclusão", f"{resumo['taxa_conclusao']}%")
coluna_3.metric("Índice de ticket médio", resumo["ticket_medio_indice"])

esquerda, direita = st.columns(2)
with esquerda:
    figura = px.line(dados["mes"], x="mes", y="pedidos", markers=True, title="Pedidos por mês")
    st.plotly_chart(figura, use_container_width=True)
with direita:
    figura = px.line(dados["mes"], x="mes", y="indice_faturamento", markers=True, title="Índice de faturamento")
    figura.update_yaxes(title="Base do primeiro mês = 100")
    st.plotly_chart(figura, use_container_width=True)

esquerda, direita = st.columns(2)
with esquerda:
    figura = px.bar(dados["dia"], x="dia_semana", y="pedidos", title="Pedidos por dia")
    st.plotly_chart(figura, use_container_width=True)
with direita:
    figura = px.bar(dados["hora"], x="hora", y="pedidos", title="Pedidos por hora")
    st.plotly_chart(figura, use_container_width=True)

esquerda, direita = st.columns(2)
with esquerda:
    figura = px.bar(dados["status"], x="status", y="pedidos", title="Pedidos por status")
    st.plotly_chart(figura, use_container_width=True)
with direita:
    figura = px.bar(dados["rfm"], x="segmento_rfm", y="clientes", title="Segmentos RFM")
    st.plotly_chart(figura, use_container_width=True)

st.subheader("Recomendações")
st.markdown("""
- Ajustar a escala operacional para o horário e o dia de maior volume.
- Monitorar a taxa de conclusão separadamente do faturamento registrado.
- Priorizar ações de retenção para clientes em risco e clientes fiéis.
""")
st.info(resumo["observacao"])
