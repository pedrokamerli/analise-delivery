"""Cálculo dos indicadores e tabelas usadas nos gráficos."""

import pandas as pd


def calcular_metricas_principais(pedidos: pd.DataFrame) -> dict[str, float | int | str]:
    concluidos = pedidos[pedidos["pedido_concluido"]]
    return {
        "periodo_inicial": pedidos["data_pedido"].min().strftime("%d/%m/%Y"),
        "periodo_final": pedidos["data_pedido"].max().strftime("%d/%m/%Y"),
        "total_pedidos": len(pedidos),
        "pedidos_concluidos": len(concluidos),
        "taxa_conclusao": round(100 * len(concluidos) / len(pedidos), 1),
        "faturamento_registrado": round(pedidos["valor_total"].sum(), 2),
        "faturamento_concluido": round(concluidos["valor_total"].sum(), 2),
        "ticket_medio": round(concluidos["valor_total"].mean(), 2),
        "tempo_preparo_mediano": round(pedidos["tempo_preparo_min"].median(), 1),
        "registros_tempo_final_invalido": int(
            pedidos["tempo_finalizacao_min"].notna().sum()
            - pedidos["tempo_finalizacao_valido"].sum()
        ),
    }


def gerar_tabelas_analiticas(pedidos: pd.DataFrame, clientes: pd.DataFrame) -> dict[str, pd.DataFrame]:
    concluidos = pedidos[pedidos["pedido_concluido"]]

    por_mes = pedidos.groupby("mes", as_index=False).agg(
        pedidos=("id_pedido", "size"),
        pedidos_concluidos=("pedido_concluido", "sum"),
        faturamento_registrado=("valor_total", "sum"),
    )
    receita_concluida = concluidos.groupby("mes", as_index=False).agg(
        faturamento_concluido=("valor_total", "sum"),
        ticket_medio=("valor_total", "mean"),
    )
    por_mes = por_mes.merge(receita_concluida, on="mes", how="left").fillna(0)
    por_mes["taxa_conclusao"] = (100 * por_mes["pedidos_concluidos"] / por_mes["pedidos"]).round(1)
    base_faturamento = por_mes.loc[por_mes["faturamento_concluido"] > 0, "faturamento_concluido"].iloc[0]
    base_ticket = por_mes.loc[por_mes["ticket_medio"] > 0, "ticket_medio"].iloc[0]
    por_mes["indice_faturamento"] = (100 * por_mes["faturamento_concluido"] / base_faturamento).round(1)
    por_mes["indice_ticket"] = (100 * por_mes["ticket_medio"] / base_ticket).round(1)

    pedidos_com_data = pedidos.assign(data=pedidos["data_pedido"].dt.normalize())
    por_data = pedidos_com_data.groupby("data", as_index=False).agg(
        pedidos=("id_pedido", "size"),
        pedidos_concluidos=("pedido_concluido", "sum"),
    )
    receita_diaria = concluidos.assign(data=concluidos["data_pedido"].dt.normalize()).groupby(
        "data", as_index=False
    ).agg(faturamento_concluido=("valor_total", "sum"), ticket_medio=("valor_total", "mean"))
    por_data = por_data.merge(receita_diaria, on="data", how="left").fillna(0)
    por_data["taxa_conclusao"] = (100 * por_data["pedidos_concluidos"] / por_data["pedidos"]).round(1)
    por_data["indice_faturamento"] = (100 * por_data["faturamento_concluido"] / base_faturamento).round(3)
    por_data["indice_ticket"] = (100 * por_data["ticket_medio"] / base_ticket).round(3)
    por_data["pontos_ticket_indice"] = (
        por_data["indice_ticket"] * por_data["pedidos_concluidos"]
    ).round(3)
    por_data["semana"] = (
        por_data["data"] - pd.to_timedelta(por_data["data"].dt.dayofweek, unit="D")
    ).dt.strftime("%Y-%m-%d")
    por_data["mes"] = por_data["data"].dt.strftime("%Y-%m")
    por_data["data"] = por_data["data"].dt.strftime("%Y-%m-%d")

    por_dia = pedidos.groupby("dia_semana", observed=False, as_index=False).agg(
        pedidos=("id_pedido", "size"), faturamento=("valor_total", "sum")
    )
    por_hora = pedidos.groupby("hora", as_index=False).agg(
        pedidos=("id_pedido", "size"), faturamento=("valor_total", "sum")
    )
    por_status = pedidos.groupby("status", as_index=False).agg(pedidos=("id_pedido", "size"))
    por_pagamento = pedidos.groupby("forma_pagamento", as_index=False).agg(
        pedidos=("id_pedido", "size"), faturamento=("valor_total", "sum")
    ).sort_values("faturamento", ascending=False)
    por_tipo = pedidos.groupby("tipo_pedido", as_index=False).agg(
        pedidos=("id_pedido", "size"), taxa_conclusao=("pedido_concluido", "mean")
    )
    por_tipo["taxa_conclusao"] = (100 * por_tipo["taxa_conclusao"]).round(1)
    preparo_valido = pedidos[pedidos["tempo_preparo_min"].between(0, 180)]
    preparo_por_hora = preparo_valido.groupby("hora", as_index=False).agg(
        pedidos_com_tempo=("id_pedido", "size"),
        preparo_mediano_min=("tempo_preparo_min", "median"),
        preparo_p90_min=("tempo_preparo_min", lambda valores: valores.quantile(0.9)),
    )
    preparo_por_hora[["preparo_mediano_min", "preparo_p90_min"]] = preparo_por_hora[
        ["preparo_mediano_min", "preparo_p90_min"]
    ].round(1)
    por_cliente = clientes.groupby("classificacao", as_index=False).agg(
        clientes=("classificacao", "size"),
        mediana_pedidos=("pedidos_historicos", "median"),
        mediana_dias_sem_comprar=("dias_sem_comprar", "median"),
    )
    rfm, segmentos_rfm = calcular_segmentacao_rfm(clientes)
    return {
        "por_mes": por_mes,
        "por_data": por_data,
        "por_dia": por_dia,
        "por_hora": por_hora,
        "por_status": por_status,
        "por_pagamento": por_pagamento,
        "por_tipo": por_tipo,
        "preparo_por_hora": preparo_por_hora,
        "por_cliente": por_cliente,
        "rfm": rfm,
        "segmentos_rfm": segmentos_rfm,
    }


def _pontuar_quartis(serie: pd.Series, menor_e_melhor: bool = False) -> pd.Series:
    """Atribui notas de 1 a 4 sem falhar quando há valores repetidos."""
    ranking = serie.rank(method="first", ascending=not menor_e_melhor)
    return pd.qcut(ranking, q=4, labels=[1, 2, 3, 4]).astype(int)


def calcular_segmentacao_rfm(clientes: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cria segmentos por recência, frequência e valor histórico."""
    rfm = clientes.dropna(subset=["dias_sem_comprar"]).copy()
    rfm = rfm[(rfm["pedidos_historicos"] > 0) & (rfm["faturamento_historico"] > 0)].copy()

    rfm["nota_recencia"] = _pontuar_quartis(rfm["dias_sem_comprar"], menor_e_melhor=True)
    rfm["nota_frequencia"] = _pontuar_quartis(rfm["pedidos_historicos"])
    rfm["nota_valor"] = _pontuar_quartis(rfm["faturamento_historico"])

    rfm["segmento_rfm"] = "Em desenvolvimento"
    rfm.loc[
        (rfm["nota_recencia"] >= 3)
        & (rfm["nota_frequencia"] >= 3)
        & (rfm["nota_valor"] >= 3),
        "segmento_rfm",
    ] = "Clientes fiéis"
    rfm.loc[
        (rfm["nota_recencia"] <= 2) & (rfm["nota_valor"] >= 3), "segmento_rfm"
    ] = "Em risco"
    rfm.loc[
        (rfm["nota_recencia"] >= 3) & (rfm["nota_frequencia"] <= 2), "segmento_rfm"
    ] = "Clientes recentes"
    rfm.loc[
        (rfm["nota_recencia"] <= 2)
        & (rfm["nota_frequencia"] <= 2)
        & (rfm["nota_valor"] <= 2),
        "segmento_rfm",
    ] = "Baixo engajamento"

    segmentos = rfm.groupby("segmento_rfm", as_index=False).agg(
        clientes=("segmento_rfm", "size"),
        mediana_dias_sem_comprar=("dias_sem_comprar", "median"),
        mediana_pedidos=("pedidos_historicos", "median"),
    ).sort_values("clientes", ascending=False)
    return rfm, segmentos
