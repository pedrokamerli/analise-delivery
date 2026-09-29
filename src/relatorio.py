"""Criação do relatório textual com os indicadores calculados."""

from pathlib import Path

import pandas as pd


def criar_relatorio(
    metricas: dict[str, float | int | str],
    tabelas: dict[str, pd.DataFrame],
    auditoria_avaliacoes: dict[str, int | bool],
    pasta_saida: Path,
) -> Path:
    pasta_saida.mkdir(parents=True, exist_ok=True)
    caminho = pasta_saida / "relatorio_analitico.md"
    pico_hora = tabelas["por_hora"].sort_values("pedidos", ascending=False).iloc[0]
    pico_dia = tabelas["por_dia"].sort_values("pedidos", ascending=False).iloc[0]
    maior_segmento = tabelas["segmentos_rfm"].sort_values("clientes", ascending=False).iloc[0]

    conteudo = f"""# Relatório analítico da operação de delivery

## Período analisado

{metricas['periodo_inicial']} a {metricas['periodo_final']}.

## Indicadores principais

- Pedidos registrados: {metricas['total_pedidos']:,}
- Pedidos concluídos: {metricas['pedidos_concluidos']:,}
- Taxa de conclusão: {metricas['taxa_conclusao']}%
- Faturamento registrado: R$ {metricas['faturamento_registrado']:,.2f}
- Faturamento de pedidos concluídos: R$ {metricas['faturamento_concluido']:,.2f}
- Ticket médio dos pedidos concluídos: R$ {metricas['ticket_medio']:,.2f}
- Tempo mediano entre aceite e preparo: {metricas['tempo_preparo_mediano']} minutos

## Qualidade dos dados

Foram identificados {metricas['registros_tempo_final_invalido']} registros com duração final fora da regra de plausibilidade de 0 a 180 minutos. Esses registros não devem ser usados para medir SLA de entrega até que a captura dos eventos seja revisada.

## Leitura de negócio

1. **Capacidade operacional:** o maior pico ocorre às {int(pico_hora['hora'])}h, com {int(pico_hora['pedidos'])} pedidos. O dia de maior demanda é {pico_dia['dia_semana']}, com {int(pico_dia['pedidos'])} pedidos.
2. **Conclusão de pedidos:** a taxa de conclusão é {metricas['taxa_conclusao']}%. Acompanhar rejeições e desistências ajuda a identificar perdas antes da etapa de faturamento concluído.
3. **Retenção:** o maior segmento RFM é "{maior_segmento['segmento_rfm']}", com {int(maior_segmento['clientes'])} clientes. Esse grupo deve receber uma estratégia compatível com sua recência, frequência e valor histórico.

## Avaliações de clientes

O PDF de avaliações possui {auditoria_avaliacoes['paginas']} páginas. A extração automática de texto está definida como `{auditoria_avaliacoes['possui_texto_extraivel']}`. Como o arquivo é uma impressão visual e não uma tabela estruturada, a análise de comentários precisa de OCR ou de uma exportação original em CSV/XLSX antes de ser automatizada.
"""
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho
