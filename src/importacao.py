"""Atualização local de exportações Excel, preservando pedidos anteriores."""

from io import BytesIO
import json
from pathlib import Path
from datetime import datetime
import shutil

import pandas as pd

from src.carga import RAIZ_PROJETO, carregar_clientes, carregar_pedidos, localizar_arquivo
from src.historico_clientes import construir_historico
from src.tratamento import tratar_pedidos, tratar_clientes
from src.analise import calcular_metricas_principais, gerar_tabelas_analiticas
from src.publicacao import exportar_dados_publicos, exportar_historico_previsao


def combinar_pedidos(anterior, novos):
    if novos.empty or "ID" not in novos:
        raise ValueError("A exportação deve conter pedidos e a coluna ID.")
    if novos.ID.isna().any() or novos.ID.duplicated().any():
        raise ValueError("Existem IDs ausentes ou duplicados na nova exportação.")
    if set(anterior.columns) != set(novos.columns):
        raise ValueError("As colunas devem corresponder à exportação original de pedidos.")
    return pd.concat([anterior, novos], ignore_index=True).drop_duplicates("ID", keep="last").reset_index(drop=True)


def importar_excel(conteudo):
    """Lê o Excel somente localmente e regenera agregações públicas sem dados pessoais."""
    if len(conteudo) > 20 * 1024 * 1024:
        raise ValueError("A exportação deve ter no máximo 20 MB.")
    try:
        novos = pd.read_excel(BytesIO(conteudo))
    except Exception as erro:
        raise ValueError("Não foi possível ler o Excel. Envie a exportação de pedidos em .xlsx.") from erro
    anterior = carregar_pedidos()
    combinados = combinar_pedidos(anterior, novos)
    clientes_brutos = carregar_clientes()
    historico, resumo = construir_historico(combinados, clientes_brutos)
    pedidos = tratar_pedidos(combinados)
    tabelas = gerar_tabelas_analiticas(pedidos, tratar_clientes(clientes_brutos))
    metricas = calcular_metricas_principais(pedidos)
    pasta = RAIZ_PROJETO / "dados" / "tratados"
    pasta.mkdir(parents=True, exist_ok=True)
    # Mantém a exportação anterior recuperável antes de atualizar a base privada.
    origem = localizar_arquivo("Pedidos - *.xlsx")
    backup = RAIZ_PROJETO / "dados" / "atualizacoes" / "backups"
    backup.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origem, backup / f"pedidos-{datetime.now():%Y%m%d-%H%M%S-%f}.xlsx")
    if origem.with_suffix(".pkl").exists():
        shutil.copy2(origem.with_suffix(".pkl"), backup / f"consolidado-{datetime.now():%Y%m%d-%H%M%S-%f}.pkl")
    combinados.to_pickle(origem.with_suffix(".pkl"))
    # O pickle evita reescrever a planilha e preserva o arquivo original para auditoria.
    historico.to_csv(pasta / "historico_diario.csv", index=False)
    (pasta / "historico_resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    pedidos.to_csv(pasta / "pedidos_tratados.csv", index=False)
    for nome, tabela in tabelas.items():
        tabela.to_csv(pasta / f"{nome}.csv", index=False)
    exportar_dados_publicos(metricas, tabelas, RAIZ_PROJETO / "dados" / "publicos")
    exportar_historico_previsao(historico, RAIZ_PROJETO / "dados" / "publicos")
    serie_salva = RAIZ_PROJETO / "dados" / "atualizacoes" / "serie_diaria.csv"
    if serie_salva.exists():
        shutil.copy2(serie_salva, backup / f"serie-{datetime.now():%Y%m%d-%H%M%S-%f}.csv")
        shutil.copy2(RAIZ_PROJETO / "dados" / "publicos" / "serie_diaria.csv", serie_salva)
    return {"recebidos": len(novos), "novos": int((~novos.ID.isin(anterior.ID)).sum()), "corrigidos": int(novos.ID.isin(anterior.ID).sum()), "total": len(combinados), "ultima_data": historico.data.max().strftime("%d/%m/%Y")}
