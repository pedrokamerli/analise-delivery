"""Reconstrói atributos de clientes no tempo, sem exportar identificadores."""

import json
from pathlib import Path
from io import BytesIO
import numpy as np
import pandas as pd

from src.tratamento import STATUS_CONCLUIDOS, _converter_data

COLUNAS_HISTORICO = ["historico_clientes_ativos_28d", "historico_clientes_repetiram_28d", "historico_frequencia_28d", "historico_ticket_28d"]


def validar_csv_historico(conteudo):
    if len(conteudo) > 5 * 1024 * 1024:
        raise ValueError("O arquivo deve ter no máximo 5 MB.")
    try:
        base = pd.read_csv(BytesIO(conteudo), sep=None, engine="python", encoding="utf-8-sig")
    except Exception as erro:
        raise ValueError("CSV inválido. Use UTF-8, datas AAAA-MM-DD e números com ponto decimal.") from erro
    obrigatorias = {"data", "pedidos", "faturamento"}
    permitidas = obrigatorias | set(COLUNAS_HISTORICO) | {"faturamento_registrado", "clientes_unicos", "clientes_recorrentes"}
    if not obrigatorias.issubset(base.columns) or not set(base.columns).issubset(permitidas):
        raise ValueError("Use data, pedidos e faturamento, e somente as colunas opcionais presentes no modelo. Remova dados pessoais.")
    if base.empty:
        raise ValueError("O CSV está vazio.")
    base["data"] = pd.to_datetime(base.data, format="%Y-%m-%d", errors="coerce")
    if base.data.isna().any() or base.data.duplicated().any():
        raise ValueError("Datas devem ser únicas, válidas e no formato AAAA-MM-DD.")
    for coluna in base.columns.drop("data"):
        base[coluna] = pd.to_numeric(base[coluna], errors="coerce")
        if not np.isfinite(base[coluna]).all() or (base[coluna] < 0).any():
            raise ValueError(f"Valores inválidos em {coluna}.")
    if (base.pedidos % 1 != 0).any():
        raise ValueError("Pedidos devem ser inteiros.")
    if ((base.pedidos == 0) & (base.faturamento > 0)).any():
        raise ValueError("Dias sem pedidos não podem ter faturamento positivo.")
    return base.sort_values("data").reset_index(drop=True)


def normalizar_telefone(serie):
    numeros = serie.fillna("").astype(str).str.replace(r"\.0$", "", regex=True).str.replace(r"\D", "", regex=True)
    numeros = numeros.where(~((numeros.str.len() >= 12) & numeros.str.startswith("55")), numeros.str[2:])
    return numeros.where(numeros.str.len().isin([10, 11]), "")


def construir_historico(pedidos, clientes):
    obrigatorias = {"ID", "DATA CADASTRAL", "TOTAL", "STATUS", "TELEFONE"}
    if not obrigatorias.issubset(pedidos.columns) or "TELEFONE" not in clientes:
        raise ValueError("As bases precisam de data, ID, total, status e telefone para reconstruir o histórico.")
    base = pd.DataFrame({"id": pedidos.ID, "data": _converter_data(pedidos["DATA CADASTRAL"]).dt.normalize(), "valor": pd.to_numeric(pedidos.TOTAL, errors="coerce"), "concluido": pedidos.STATUS.isin(STATUS_CONCLUIDOS), "cliente": normalizar_telefone(pedidos.TELEFONE)})
    if base.data.isna().any() or not np.isfinite(base.valor).all() or (base.valor < 0).any():
        raise ValueError("Existem datas ou valores inválidos nos pedidos; corrija a exportação antes de treinar.")
    if base.id.isna().any() or base.id.duplicated().any():
        raise ValueError("IDs de pedidos ausentes ou duplicados na exportação.")
    cadastro = set(normalizar_telefone(clientes.TELEFONE)) - {""}
    identificados = base.cliente.ne("")
    cobertura = float(100 * base.loc[identificados, "cliente"].isin(cadastro).mean()) if identificados.any() else 0
    primeiro = base[identificados].groupby("cliente").data.min()
    registros = []
    for data, dia in base.groupby("data", sort=True):
        # Somente pedidos anteriores ao dia que será previsto.
        passado = base[(base.data < data) & (base.data >= data - pd.Timedelta(days=28))]
        ativos = passado[passado.cliente.ne("")].groupby("cliente").size()
        concluidos = passado[passado.concluido]
        recorrentes = dia.loc[dia.cliente.ne("") & dia.cliente.map(primeiro).lt(data), "cliente"].nunique()
        registros.append({"data": data, "pedidos": len(dia), "faturamento": float(dia.loc[dia.concluido, "valor"].sum()), "faturamento_registrado": float(dia.valor.sum()), "clientes_unicos": dia.loc[dia.cliente.ne(""), "cliente"].nunique(), "clientes_recorrentes": recorrentes, "historico_clientes_ativos_28d": len(ativos), "historico_clientes_repetiram_28d": int((ativos > 1).sum()), "historico_frequencia_28d": float(ativos.mean()) if len(ativos) else 0, "historico_ticket_28d": float(concluidos.valor.mean()) if len(concluidos) else 0})
    resumo = {"pedidos": len(base), "clientes_identificados_nos_pedidos": int(base.loc[identificados, "cliente"].nunique()), "pedidos_sem_telefone_valido": int((~identificados).sum()), "cobertura_cadastro_pct": cobertura, "definicao_faturamento": "Soma de TOTAL dos pedidos com status Entregue, Retirado ou Avaliado na exportação, agrupada pela data do pedido. Não é lucro nem fluxo de caixa.", "limite_historico": "Recorrência reconstruída somente desde o primeiro pedido disponível. Totais atuais de pedidos e faturamento do cadastro não são usados no treino."}
    return pd.DataFrame(registros), resumo


def gerar_base_local(pasta):
    from src.carga import carregar_pedidos, carregar_clientes
    serie, resumo = construir_historico(carregar_pedidos(), carregar_clientes())
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    serie.to_csv(pasta / "historico_diario.csv", index=False)
    (pasta / "historico_resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    return serie, resumo
