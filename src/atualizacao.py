"""Importação de agregações diárias: validação antes de substituir dados."""

from io import BytesIO
import os
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd

COLUNAS = ["data", "pedidos", "pedidos_concluidos", "indice_faturamento", "pontos_ticket_indice"]


def validar_csv(conteudo):
    if len(conteudo) > 5 * 1024 * 1024:
        raise ValueError("O CSV deve ter no máximo 5 MB.")
    try:
        dados = pd.read_csv(BytesIO(conteudo), sep=None, engine="python", encoding="utf-8-sig")
    except Exception as erro:
        raise ValueError("Não foi possível ler o CSV. Use UTF-8 e separador vírgula ou ponto e vírgula.") from erro
    faltantes = set(COLUNAS) - set(dados.columns)
    if faltantes:
        raise ValueError("Colunas ausentes: " + ", ".join(sorted(faltantes)))
    extras = set(dados.columns) - set(COLUNAS) - {"semana", "mes", "taxa_conclusao"}
    if extras:
        raise ValueError("Remova colunas extras para evitar importar dados pessoais: " + ", ".join(sorted(extras)))
    dados = dados[COLUNAS].copy()
    if dados.empty:
        raise ValueError("O arquivo está vazio.")
    dados["data"] = pd.to_datetime(dados.data, format="%Y-%m-%d", errors="coerce")
    if dados.data.isna().any() or dados.data.duplicated().any():
        raise ValueError("As datas devem ser únicas e válidas, no formato AAAA-MM-DD.")
    for coluna in COLUNAS[1:]:
        dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce")
        if not np.isfinite(dados[coluna]).all() or (dados[coluna] < 0).any():
            raise ValueError(f"{coluna}: use números finitos e não negativos.")
    for coluna in ["pedidos", "pedidos_concluidos"]:
        if (dados[coluna] % 1 != 0).any():
            raise ValueError("As quantidades de pedidos devem ser inteiras.")
    if (dados.pedidos_concluidos > dados.pedidos).any():
        raise ValueError("Pedidos concluídos não podem superar o total.")
    if ((dados.pedidos_concluidos == 0) & ((dados.indice_faturamento > 0) | (dados.pontos_ticket_indice > 0))).any():
        raise ValueError("Dias sem pedidos concluídos devem ter índices financeiros iguais a zero.")
    dados["taxa_conclusao"] = 100 * dados.pedidos_concluidos / dados.pedidos.replace(0, np.nan)
    dados["taxa_conclusao"] = dados.taxa_conclusao.fillna(0)
    dados["semana"] = (dados.data - pd.to_timedelta(dados.data.dt.dayofweek, unit="D")).dt.strftime("%Y-%m-%d")
    dados["mes"] = dados.data.dt.strftime("%Y-%m")
    return dados.sort_values("data").reset_index(drop=True)


def combinar_series(atual, nova, modo):
    if modo == "Substituir série completa":
        return nova.copy()
    # Em datas sobrepostas a nova linha substitui a antiga; nunca soma duas vezes.
    return pd.concat([atual, nova], ignore_index=True).drop_duplicates("data", keep="last").sort_values("data").reset_index(drop=True)


def salvar_serie_local(serie, destino):
    """Valida, preserva a versão anterior e troca o arquivo atomicamente."""
    destino = Path(destino)
    conteudo = serie.to_csv(index=False).encode("utf-8")
    validar_csv(conteudo)
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        backup = destino.with_name(f"serie_backup_{datetime.now():%Y%m%d_%H%M%S_%f}.csv")
        backup.write_bytes(destino.read_bytes())
    temporario = destino.with_suffix(".tmp")
    temporario.write_bytes(conteudo)
    os.replace(temporario, destino)
