"""Cria dados agregados seguros para demonstrar o projeto no portfólio."""

import json
from pathlib import Path

import pandas as pd


def exportar_dados_publicos(
    metricas: dict[str, float | int | str], tabelas: dict[str, pd.DataFrame], pasta_saida: Path
) -> None:
    """Exporta somente agregações, sem identificadores ou valores monetários absolutos."""
    pasta_saida.mkdir(parents=True, exist_ok=True)

    por_mes = tabelas["por_mes"].copy()
    base_faturamento = por_mes.loc[por_mes["faturamento_concluido"] > 0, "faturamento_concluido"].iloc[0]
    por_mes_publico = por_mes[
        ["mes", "pedidos", "pedidos_concluidos", "taxa_conclusao", "indice_ticket"]
    ].copy()
    por_mes_publico["indice_faturamento"] = (100 * por_mes["faturamento_concluido"] / base_faturamento).round(1)
    por_mes_publico.to_csv(pasta_saida / "pedidos_por_mes.csv", index=False)

    tabelas["por_data"][
        [
            "data",
            "semana",
            "mes",
            "pedidos",
            "pedidos_concluidos",
            "taxa_conclusao",
            "indice_faturamento",
            "pontos_ticket_indice",
        ]
    ].to_csv(pasta_saida / "serie_diaria.csv", index=False)

    tabelas["por_dia"][["dia_semana", "pedidos"]].to_csv(
        pasta_saida / "por_dia.csv", index=False
    )
    tabelas["por_hora"][["hora", "pedidos"]].to_csv(
        pasta_saida / "por_hora.csv", index=False
    )
    tabelas["por_status"][["status", "pedidos"]].to_csv(
        pasta_saida / "por_status.csv", index=False
    )
    tabelas["por_tipo"].to_csv(pasta_saida / "por_tipo.csv", index=False)
    tabelas["preparo_por_hora"].to_csv(pasta_saida / "preparo_por_hora.csv", index=False)

    tabelas["segmentos_rfm"].to_csv(pasta_saida / "segmentos_rfm.csv", index=False)

    resumo = {
        "periodo": f"{metricas['periodo_inicial']} a {metricas['periodo_final']}",
        "total_pedidos": metricas["total_pedidos"],
        "taxa_conclusao": metricas["taxa_conclusao"],
        "ticket_medio_indice": 100,
        "registros_tempo_final_invalido": metricas["registros_tempo_final_invalido"],
        "observacao": "Faturamento e ticket médio foram indexados ou omitidos para proteção comercial.",
    }
    (pasta_saida / "resumo.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8"
    )
