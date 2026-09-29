"""Limpeza e criação de variáveis analíticas."""

import pandas as pd


COLUNAS_PEDIDOS = {
    "ID": "id_pedido",
    "TIPO": "tipo_pedido",
    "TEMPO ESTIMADO": "tempo_estimado_min",
    "ORIGEM": "origem",
    "FORMA DE PAGAMENTO": "forma_pagamento",
    "SUB-TOTAL": "subtotal",
    "CUSTO DE ENTREGA": "custo_entrega",
    "DESCONTO": "desconto",
    "TOTAL": "valor_total",
    "STATUS": "status",
    "DATA CADASTRAL": "data_pedido",
    "DATA STATUS - ACEITO": "data_aceito",
    "DATA STATUS - PREPARADO": "data_preparado",
    "DATA STATUS - ENTREGUE": "data_entregue",
    "DATA STATUS - RETIRADO": "data_retirado",
}

STATUS_CONCLUIDOS = {"Entregue", "Retirado", "Avaliado"}
ORDEM_DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def _converter_data(serie: pd.Series) -> pd.Series:
    return pd.to_datetime(serie, format="%d/%m/%Y - %H:%M:%S", errors="coerce")


def tratar_pedidos(base_bruta: pd.DataFrame) -> pd.DataFrame:
    """Seleciona campos relevantes e gera variáveis para a análise."""
    colunas_faltantes = set(COLUNAS_PEDIDOS) - set(base_bruta.columns)
    if colunas_faltantes:
        raise ValueError(f"Colunas obrigatórias ausentes: {sorted(colunas_faltantes)}")

    pedidos = base_bruta[list(COLUNAS_PEDIDOS)].rename(columns=COLUNAS_PEDIDOS).copy()

    for coluna in ["data_pedido", "data_aceito", "data_preparado", "data_entregue", "data_retirado"]:
        pedidos[coluna] = _converter_data(pedidos[coluna])

    pedidos["pedido_concluido"] = pedidos["status"].isin(STATUS_CONCLUIDOS)
    pedidos["data_finalizacao"] = pedidos["data_entregue"].fillna(pedidos["data_retirado"])
    pedidos["tempo_preparo_min"] = (
        (pedidos["data_preparado"] - pedidos["data_aceito"]).dt.total_seconds() / 60
    )
    pedidos["tempo_finalizacao_min"] = (
        (pedidos["data_finalizacao"] - pedidos["data_pedido"]).dt.total_seconds() / 60
    )
    pedidos["tempo_finalizacao_valido"] = pedidos["tempo_finalizacao_min"].between(0, 180)
    pedidos["mes"] = pedidos["data_pedido"].dt.to_period("M").astype(str)
    pedidos["hora"] = pedidos["data_pedido"].dt.hour
    pedidos["dia_semana"] = pedidos["data_pedido"].dt.dayofweek.map(
        dict(enumerate(ORDEM_DIAS))
    )
    pedidos["dia_semana"] = pd.Categorical(
        pedidos["dia_semana"], categories=ORDEM_DIAS, ordered=True
    )
    return pedidos


def tratar_clientes(base_bruta: pd.DataFrame) -> pd.DataFrame:
    """Extrai métricas de clientes sem manter identificadores pessoais."""
    # O export possui caracteres corrompidos em alguns títulos. Estas posições
    # correspondem aos campos documentados pelo sistema de origem.
    clientes = pd.DataFrame(
        {
            "classificacao": base_bruta.iloc[:, 1],
            "pedidos_historicos": base_bruta.iloc[:, 8],
            "faturamento_historico": base_bruta.iloc[:, 9],
            "dias_sem_comprar": base_bruta.iloc[:, 10],
        }
    )
    clientes["dias_sem_comprar"] = pd.to_numeric(
        clientes["dias_sem_comprar"].astype(str).str.extract(r"(\d+)")[0], errors="coerce"
    )
    return clientes
