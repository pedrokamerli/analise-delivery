"""Dashboard interativo com filtros temporais e comparações de períodos."""

import json
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
PASTA_DADOS = RAIZ_PROJETO / "dados" / "publicos"
AZUL = "#2563EB"
LARANJA = "#F97316"
VERDE = "#16A34A"
ROXO = "#7C3AED"

st.set_page_config(page_title="Inteligência de Delivery", page_icon="📊", layout="wide")


@st.cache_data
def carregar_dados() -> dict[str, pd.DataFrame | dict]:
    serie = pd.read_csv(PASTA_DADOS / "serie_diaria.csv", parse_dates=["data"])
    return {
        "resumo": json.loads((PASTA_DADOS / "resumo.json").read_text(encoding="utf-8")),
        "serie": serie,
        "dia_semana": pd.read_csv(PASTA_DADOS / "por_dia.csv"),
        "hora": pd.read_csv(PASTA_DADOS / "por_hora.csv"),
        "status": pd.read_csv(PASTA_DADOS / "por_status.csv"),
        "preparo": pd.read_csv(PASTA_DADOS / "preparo_por_hora.csv"),
        "rfm": pd.read_csv(PASTA_DADOS / "segmentos_rfm.csv"),
    }


def agregar_periodo(serie: pd.DataFrame, granularidade: str) -> pd.DataFrame:
    coluna_periodo = {
        "Mês a mês": "mes",
        "Semana a semana": "semana",
        "Dia a dia": "data",
    }[granularidade]
    resultado = serie.groupby(coluna_periodo, as_index=False).agg(
        pedidos=("pedidos", "sum"),
        pedidos_concluidos=("pedidos_concluidos", "sum"),
        indice_faturamento=("indice_faturamento", "sum"),
        pontos_ticket_indice=("pontos_ticket_indice", "sum"),
    )
    resultado = resultado.rename(columns={coluna_periodo: "periodo"})
    resultado["taxa_conclusao"] = (
        100 * resultado["pedidos_concluidos"] / resultado["pedidos"]
    ).round(1)
    resultado["indice_ticket"] = (
        resultado["pontos_ticket_indice"] / resultado["pedidos_concluidos"]
    ).fillna(0).round(1)
    return resultado


def calcular_delta(valor_a: float, valor_b: float, sufixo: str = "%") -> str:
    if valor_a == 0:
        return "Sem base de comparação"
    variacao = 100 * (valor_b - valor_a) / valor_a
    return f"{variacao:+.1f}{sufixo}"


def formatar_periodo(valor: str, granularidade: str) -> str:
    data = pd.to_datetime(valor)
    if granularidade == "Mês a mês":
        return data.strftime("%m/%Y")
    return data.strftime("%d/%m/%Y")


dados = carregar_dados()
resumo = dados["resumo"]
serie = dados["serie"]
data_minima = serie["data"].min().date()
data_maxima = serie["data"].max().date()

st.title("Inteligência de Delivery")
st.caption("Case de portfólio com dados agregados e indicadores financeiros indexados.")

with st.sidebar:
    st.header("Filtros")
    granularidade = st.radio("Visualização", ["Mês a mês", "Semana a semana", "Dia a dia"])
    intervalo = st.date_input(
        "Período analisado",
        value=(data_minima, data_maxima),
        min_value=data_minima,
        max_value=data_maxima,
    )
    indicador = st.selectbox(
        "Indicador principal",
        ["Pedidos", "Taxa de conclusão", "Índice de faturamento", "Índice de ticket médio"],
    )
    st.divider()
    st.caption("Os filtros afetam os indicadores e a série temporal abaixo.")

if isinstance(intervalo, tuple) and len(intervalo) == 2:
    inicio, fim = intervalo
else:
    inicio = fim = intervalo if isinstance(intervalo, date) else data_minima

serie_filtrada = serie[(serie["data"].dt.date >= inicio) & (serie["data"].dt.date <= fim)].copy()
periodos = agregar_periodo(serie_filtrada, granularidade)

pedidos_periodo = int(serie_filtrada["pedidos"].sum())
concluidos_periodo = int(serie_filtrada["pedidos_concluidos"].sum())
taxa_periodo = 100 * concluidos_periodo / pedidos_periodo if pedidos_periodo else 0
pico = periodos.loc[periodos["pedidos"].idxmax()] if not periodos.empty else None

coluna_1, coluna_2, coluna_3, coluna_4 = st.columns(4)
coluna_1.metric("Pedidos no período", f"{pedidos_periodo:,}".replace(",", "."))
coluna_2.metric("Taxa de conclusão", f"{taxa_periodo:.1f}%")
coluna_3.metric(
    "Melhor período",
    formatar_periodo(str(pico["periodo"]), granularidade) if pico is not None else "-",
)
coluna_4.metric("Pedidos no pico", f"{int(pico['pedidos']):,}".replace(",", ".") if pico is not None else "-")

mapa_indicadores = {
    "Pedidos": ("pedidos", "Pedidos"),
    "Taxa de conclusão": ("taxa_conclusao", "% de pedidos concluídos"),
    "Índice de faturamento": ("indice_faturamento", "Índice: primeiro mês = 100"),
    "Índice de ticket médio": ("indice_ticket", "Índice: primeiro mês = 100"),
}
coluna, titulo_eixo = mapa_indicadores[indicador]

figura = px.line(
    periodos,
    x="periodo",
    y=coluna,
    markers=True,
    title=f"{indicador}: {granularidade.lower()}",
    color_discrete_sequence=[AZUL],
)
figura.update_traces(line_width=3, marker_size=7)
figura.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=55, b=20))
figura.update_yaxes(title=titulo_eixo, gridcolor="#E5E7EB")
figura.update_xaxes(title="", showgrid=False)
st.plotly_chart(figura, use_container_width=True)

st.subheader("Comparação entre períodos")
opcoes = periodos["periodo"].astype(str).tolist()
padrao = opcoes[-2:] if len(opcoes) >= 2 else opcoes
selecionados = st.multiselect(
    "Selecione até dois períodos para comparar",
    options=opcoes,
    default=padrao,
    max_selections=2,
)

if len(selecionados) == 2:
    comparacao = periodos[periodos["periodo"].astype(str).isin(selecionados)].copy()
    comparacao["periodo"] = pd.Categorical(comparacao["periodo"].astype(str), selecionados, ordered=True)
    comparacao = comparacao.sort_values("periodo")
    primeiro, segundo = comparacao.iloc[0], comparacao.iloc[1]
    coluna_1, coluna_2, coluna_3 = st.columns(3)
    coluna_1.metric(
        "Pedidos",
        f"{int(segundo['pedidos']):,}".replace(",", "."),
        calcular_delta(primeiro["pedidos"], segundo["pedidos"]),
    )
    coluna_2.metric(
        "Taxa de conclusão",
        f"{segundo['taxa_conclusao']:.1f}%",
        f"{segundo['taxa_conclusao'] - primeiro['taxa_conclusao']:+.1f} p.p.",
    )
    coluna_3.metric(
        "Índice de faturamento",
        f"{segundo['indice_faturamento']:.1f}",
        calcular_delta(primeiro["indice_faturamento"], segundo["indice_faturamento"]),
    )
    figura = px.bar(comparacao, x="periodo", y=["pedidos", "pedidos_concluidos"], barmode="group", title="Pedidos registrados x concluídos", color_discrete_sequence=[AZUL, VERDE])
    figura.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=55, b=20), legend_title_text="")
    st.plotly_chart(figura, use_container_width=True)
else:
    st.info("Selecione dois períodos para comparar o desempenho.")

st.subheader("Operação e retenção")
esquerda, direita = st.columns(2)
with esquerda:
    preparo = dados["preparo"]
    figura = px.line(preparo, x="hora", y=["preparo_mediano_min", "preparo_p90_min"], markers=True, title="Tempo de preparo por hora", color_discrete_sequence=[VERDE, LARANJA])
    figura.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=55, b=20), legend_title_text="")
    figura.update_yaxes(title="Minutos", gridcolor="#E5E7EB")
    st.plotly_chart(figura, use_container_width=True)
with direita:
    figura = px.bar(dados["rfm"].sort_values("clientes", ascending=False), x="segmento_rfm", y="clientes", title="Segmentos RFM", color="segmento_rfm", color_discrete_sequence=[ROXO, AZUL, LARANJA, VERDE])
    figura.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=55, b=20), showlegend=False)
    figura.update_yaxes(title="Clientes", gridcolor="#E5E7EB")
    st.plotly_chart(figura, use_container_width=True)

st.warning(f"Qualidade dos dados: {resumo['registros_tempo_final_invalido']} registros de finalização estão fora da faixa plausível de 0 a 180 minutos. O tempo de preparo é o indicador operacional mais confiável desta base.")
st.caption("Dados pessoais e valores financeiros absolutos foram removidos da camada pública.")
