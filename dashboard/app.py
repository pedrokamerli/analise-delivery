"""Dashboard interativo com filtros temporais e comparações de períodos."""

import json
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_PROJETO))
from src.atualizacao import validar_csv, combinar_series, salvar_serie_local
from src.previsao import executar_previsao
PASTA_DADOS = RAIZ_PROJETO / "dados" / "publicos"
ARQUIVO_LOCAL = RAIZ_PROJETO / "dados" / "atualizacoes" / "serie_diaria.csv"
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
        dias_observados=("data", "size"),
        pedidos=("pedidos", "sum"),
        pedidos_concluidos=("pedidos_concluidos", "sum"),
        indice_faturamento=("indice_faturamento", "sum"),
        pontos_ticket_indice=("pontos_ticket_indice", "sum"),
    )
    resultado = resultado.rename(columns={coluna_periodo: "periodo"})
    resultado["taxa_conclusao"] = (
        100 * resultado["pedidos_concluidos"] / resultado["pedidos"].replace(0, float("nan"))
    ).fillna(0).round(1)
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
if "serie_atualizada" not in st.session_state and ARQUIVO_LOCAL.exists():
    try:
        st.session_state["serie_atualizada"] = validar_csv(ARQUIVO_LOCAL.read_bytes())
        st.session_state["fonte_atualizada"] = True
    except ValueError as erro:
        st.error(f"Base local inválida: {erro}")
with st.sidebar.expander("Atualizar dados por CSV"):
    st.caption("Envie agregações diárias sem nomes, telefones ou valores em reais. Aplique na sessão e, se quiser manter a atualização após reiniciar, salve a base local.")
    st.download_button("Baixar modelo CSV", dados["serie"].head(3).to_csv(index=False).encode("utf-8"), "modelo_serie_diaria.csv", "text/csv")
    arquivo = st.file_uploader("CSV diário (até 5 MB)", type=["csv"])
    modo = st.selectbox("Modo de atualização", ["Adicionar ou corrigir datas", "Substituir série completa"])
    if arquivo:
        try:
            nova = validar_csv(arquivo.getvalue())
            st.write(f"{len(nova)} dias validados. Datas coincidentes serão substituídas.")
            st.dataframe(nova.head(), hide_index=True)
            if st.button("Aplicar atualização"):
                st.session_state["serie_atualizada"] = combinar_series(st.session_state.get("serie_atualizada", dados["serie"]), nova, modo)
                st.session_state["fonte_atualizada"] = True
                st.rerun()
        except ValueError as erro:
            st.error(str(erro))
    if st.button("Restaurar base original nesta sessão"):
        st.session_state["serie_atualizada"] = dados["serie"].copy()
        st.session_state.pop("fonte_atualizada", None)
        st.rerun()
    if st.button("Salvar série ativa localmente"):
        try:
            salvar_serie_local(st.session_state.get("serie_atualizada", dados["serie"]), ARQUIVO_LOCAL)
            st.success("Base salva em dados/atualizacoes. A versão anterior é preservada em backup.")
        except (ValueError, OSError) as erro:
            st.error(f"Não foi possível salvar: {erro}")
serie = st.session_state.get("serie_atualizada", dados["serie"])
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
if serie_filtrada.empty:
    st.info("Não há dados neste intervalo. Selecione outro período.")
    st.stop()
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
    st.caption(f"Comparação na ordem selecionada: {primeiro['periodo']} → {segundo['periodo']}. Dias observados: {int(primeiro['dias_observados'])} e {int(segundo['dias_observados'])}. Períodos parciais podem distorcer a variação dos totais.")
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
    media_a = primeiro["pedidos"] / primeiro["dias_observados"]
    media_b = segundo["pedidos"] / segundo["dias_observados"]
    media_coluna, ticket_coluna = st.columns(2)
    media_coluna.metric("Pedidos por dia observado", f"{media_b:.1f}", calcular_delta(media_a, media_b))
    ticket_coluna.metric("Índice de ticket médio", f"{segundo['indice_ticket']:.1f}", calcular_delta(primeiro["indice_ticket"], segundo["indice_ticket"]))
    figura = px.bar(comparacao, x="periodo", y=["pedidos", "pedidos_concluidos"], barmode="group", title="Pedidos registrados x concluídos", color_discrete_sequence=[AZUL, VERDE])
    figura.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=55, b=20), legend_title_text="")
    st.plotly_chart(figura, use_container_width=True)
else:
    st.info("Selecione dois períodos para comparar o desempenho.")

st.subheader("Operação e retenção — retrato da base original")
st.caption("Estas agregações não têm dimensão de data. Os filtros e uploads alteram apenas a série temporal e suas métricas; preparo e RFM continuam referentes à exportação original.")
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

with st.expander("Explorar distribuição de status, horários e segmentos"):
    status_coluna, hora_coluna = st.columns(2)
    with status_coluna:
        st.plotly_chart(px.bar(dados["status"].sort_values("pedidos"), x="pedidos", y="status", orientation="h", title="Status registrados na exportação", labels={"pedidos": "Pedidos", "status": "Status"}, color_discrete_sequence=[AZUL]), use_container_width=True)
    with hora_coluna:
        st.plotly_chart(px.bar(dados["hora"], x="hora", y="pedidos", title="Demanda por hora do pedido", labels={"hora": "Hora", "pedidos": "Pedidos"}, color_discrete_sequence=[LARANJA]), use_container_width=True)
    st.dataframe(dados["rfm"].rename(columns={"segmento_rfm": "Segmento", "clientes": "Clientes", "mediana_dias_sem_comprar": "Dias sem comprar (mediana)", "mediana_pedidos": "Pedidos históricos (mediana)"}), hide_index=True)
    st.caption("Clientes fiéis: acompanhar recompra. Em risco: investigar queda de frequência. Clientes recentes: acompanhar segunda compra. Baixo engajamento e oportunidade: avaliar campanhas com teste e controle antes de concluir que uma ação funcionou.")

st.warning(f"Qualidade dos dados: {resumo['registros_tempo_final_invalido']} registros de finalização estão fora da faixa plausível de 0 a 180 minutos. O tempo de preparo é o indicador operacional mais confiável desta base.")
st.caption("Dados pessoais e valores financeiros absolutos foram removidos da camada pública.")

st.divider()
analise_tab, ml_tab, base_tab = st.tabs(["Diagnóstico da demanda", "Previsão e validação de ML", "Dados e exportação"])
with analise_tab:
    calendario = pd.date_range(serie_filtrada.data.min(), serie_filtrada.data.max()) if not serie_filtrada.empty else []
    ausentes = len(calendario) - len(serie_filtrada)
    st.info(f"{len(serie_filtrada)} dias observados e {ausentes} dias sem registro no intervalo. Dia sem registro não significa automaticamente zero pedidos.")
    if not serie_filtrada.empty:
        dias = serie_filtrada.assign(dia=serie_filtrada.data.dt.dayofweek).groupby("dia", as_index=False).agg(media=("pedidos", "mean"), dias_observados=("pedidos", "size"))
        dias["dia"] = dias.dia.map(dict(enumerate(["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"])))
        st.plotly_chart(px.bar(dias, x="dia", y="media", hover_data=["dias_observados"], title="Média de pedidos por dia observado"), use_container_width=True)
        evolucao = serie_filtrada.sort_values("data").assign(media_7_observacoes=lambda df: df.pedidos.rolling(7, min_periods=1).mean())
        st.plotly_chart(px.line(evolucao, x="data", y=["pedidos", "media_7_observacoes"], title="Demanda e média das últimas 7 observações"), use_container_width=True)
        st.caption("Comparações de meses ou semanas parciais exigem cuidado: o filtro pode conter quantidades diferentes de dias. A taxa de conclusão é calculada sobre todos os pedidos, incluindo os ainda em andamento.")

with ml_tab:
    st.write("Previsão experimental do número de pedidos diários. Random Forest usa variáveis de calendário e é comparado à média histórica por dia da semana em três janelas cronológicas. O método com menor MAE médio gera a projeção.")
    horizonte = st.slider("Horizonte de previsão (dias)", 7, 28, 14)
    zeros = st.checkbox("Confirmo que todos os dias ausentes representam zero pedidos", value=False)
    if not zeros:
        st.warning("Sem essa confirmação, o treino usa somente dias observados. A previsão descreve demanda condicionada a um dia registrado e não estima a probabilidade de a loja abrir.")
    st.caption("O treino usa toda a série ativa, independentemente do filtro de visualização. Datas importadas são consideradas históricas; a projeção começa após a última data da série.")
    assinatura = (int(pd.util.hash_pandas_object(serie[["data", "pedidos"]], index=False).sum()), horizonte, zeros)
    if st.session_state.get("assinatura_previsao") != assinatura:
        st.session_state.pop("resultado_previsao", None)
    if st.button("Treinar e avaliar previsão"):
        try:
            with st.spinner("Avaliando três janelas futuras e treinando o modelo..."):
                resultado = executar_previsao(serie, horizonte, zeros)
            st.session_state["resultado_previsao"] = resultado
            st.session_state["assinatura_previsao"] = assinatura
        except ValueError as erro:
            st.error(str(erro))
    if "resultado_previsao" in st.session_state:
        resultado = st.session_state["resultado_previsao"]
        st.success(f"Método escolhido: {resultado['modelo']}")
        medias = resultado["avaliacao"].groupby("modelo")[["MAE", "RMSE"]].mean().round(2)
        st.dataframe(medias)
        with st.expander("Ver resultados por janela de validação"):
            st.dataframe(resultado["avaliacao"], hide_index=True)
        st.caption("MAE: erro absoluto médio em pedidos/dia. RMSE penaliza erros maiores. Todas as previsões de teste usam apenas dados anteriores à respectiva janela.")
        st.plotly_chart(px.line(resultado["validacao"].rename(columns={"pedidos": "Pedidos reais", "ml": "Random Forest", "referencia": "Referência semanal"}), x="data", y=["Pedidos reais", "Random Forest", "Referência semanal"], title="Dados reais e previsões fora do treino", labels={"data": "Data", "value": "Pedidos", "variable": "Método"}), use_container_width=True)
        st.plotly_chart(px.line(resultado["previsao"].rename(columns={"pedidos_previstos": "Previsão", "limite_inferior": "Limite inferior", "limite_superior": "Limite superior"}), x="data", y=["Previsão", "Limite inferior", "Limite superior"], title="Projeção de demanda e faixa de erro histórico", labels={"data": "Data", "value": "Pedidos", "variable": "Série"}), use_container_width=True)
        st.caption("A faixa usa o percentil 90 do erro absoluto de validação. É uma faixa empírica de referência, sem garantia de cobertura futura. Não incorpora feriados, promoções, clima ou mudanças na operação.")
        st.dataframe(resultado["importancia"], hide_index=True)
        st.caption("Importâncias do Random Forest indicam uso das variáveis pelo modelo, não relações de causa e efeito.")
        st.download_button("Baixar previsão CSV", resultado["previsao"].to_csv(index=False).encode("utf-8"), "previsao_demanda.csv", "text/csv")

with base_tab:
    st.write("Fonte: " + ("CSV aplicado nesta sessão" if st.session_state.get("fonte_atualizada") else "Agregações originais do projeto"))
    st.dataframe(serie_filtrada, hide_index=True)
    st.download_button("Baixar série ativa", serie.to_csv(index=False).encode("utf-8"), "serie_diaria.csv", "text/csv")
    st.caption("Mantenha a mesma base de indexação financeira em todos os CSVs adicionados. A importação recalcula mês, semana e taxa de conclusão. O botão de salvar mantém a série no computador, em uma pasta ignorada pelo Git.")
