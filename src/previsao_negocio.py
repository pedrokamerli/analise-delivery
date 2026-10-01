"""Prevê pedidos e faturamento com histórico disponível na origem da previsão."""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from src.previsao import atributos


def linha_atributos(data, origem, historico, contexto):
    linha = atributos([data], origem)
    # Janelas em dias corridos; ausências não são preenchidas sem confirmação.
    for janela in (7, 28):
        valores = historico.loc[(historico.index >= data - pd.Timedelta(days=janela)) & (historico.index < data)]
        linha[f"media_{janela}d"] = float(valores.mean()) if len(valores) else 0.0
        linha[f"observacoes_{janela}d"] = len(valores)
    linha["ultimo_valor"] = float(historico.iloc[-1]) if len(historico) else 0.0
    for nome, valor in contexto.items():
        linha[nome] = float(valor)
    return linha


def matriz_treino(base, alvo, origem, colunas_contexto):
    linhas = []
    for i, linha in base.iterrows():
        passado = base.loc[base.data < linha.data].set_index("data")[alvo]
        linhas.append(linha_atributos(linha.data, origem, passado, linha[colunas_contexto].to_dict()))
    return pd.concat(linhas, ignore_index=True)


def projetar(modelo, treino, datas, alvo, origem, contexto):
    historia = treino.set_index("data")[alvo].copy()
    valores = []
    for data in datas:
        previsto = max(0.0, float(modelo.predict(linha_atributos(data, origem, historia, contexto))[0]))
        valores.append(previsto)
        # Somente estimativas são acrescentadas, nunca os valores reais do teste.
        historia.loc[data] = previsto
    return np.array(valores)


def prever_pedidos_faturamento(serie, horizonte=14, preencher_zeros=False):
    if not {"data", "pedidos", "faturamento"}.issubset(serie.columns):
        raise ValueError("A série precisa de data, pedidos e faturamento.")
    base = serie.sort_values("data").reset_index(drop=True).copy()
    base["data"] = pd.to_datetime(base.data)
    if base.data.isna().any() or base.data.duplicated().any():
        raise ValueError("Datas inválidas ou repetidas na série.")
    contexto_cols = [c for c in base if c.startswith("historico_")]
    for coluna in ["pedidos", "faturamento"] + contexto_cols:
        base[coluna] = pd.to_numeric(base[coluna], errors="coerce")
        if not np.isfinite(base[coluna]).all() or (base[coluna] < 0).any():
            raise ValueError(f"Valores inválidos em {coluna}.")
    if not 7 <= horizonte <= 28:
        raise ValueError("O horizonte deve estar entre 7 e 28 dias.")
    if preencher_zeros:
        base = base.set_index("data").reindex(pd.date_range(base.data.min(), base.data.max())).rename_axis("data")
        base[["pedidos", "faturamento"]] = base[["pedidos", "faturamento"]].fillna(0)
        # Contexto é do passado; não se usa preenchimento para trás.
        base[contexto_cols] = base[contexto_cols].ffill().fillna(0)
        base = base.reset_index()
    if len(base) < 90:
        raise ValueError("São necessários pelo menos 90 dias observados.")
    origem = base.data.min()
    datas_futuras = pd.date_range(base.data.max() + pd.Timedelta(days=1), periods=horizonte)
    previsao = pd.DataFrame({"data": datas_futuras})
    avaliacoes, validacoes, importancias, escolhidos = [], [], [], {}
    for alvo in ["pedidos", "faturamento"]:
        x = matriz_treino(base, alvo, origem, contexto_cols)
        registros = []
        # Validação da mesma extensão em dias corridos do horizonte escolhido.
        for janela in range(3, 0, -1):
            fim = base.data.max() - pd.Timedelta(days=(janela - 1) * horizonte)
            inicio = fim - pd.Timedelta(days=horizonte - 1)
            treino = base[base.data < inicio]
            teste = base[base.data.between(inicio, fim)]
            if len(treino) < 30 or teste.empty:
                raise ValueError("Histórico insuficiente para três janelas cronológicas neste horizonte.")
            modelo = RandomForestRegressor(n_estimators=150, min_samples_leaf=5, random_state=42, n_jobs=1)
            modelo.fit(x.loc[treino.index], treino[alvo])
            # O contexto de clientes fica congelado na origem: o futuro é desconhecido.
            contexto = treino.iloc[-1][contexto_cols].to_dict()
            calendario = pd.date_range(inicio, fim)
            ml_calendario = projetar(modelo, treino, calendario, alvo, origem, contexto)
            ml = pd.Series(ml_calendario, index=calendario).reindex(teste.data).to_numpy()
            medias = treino.groupby(treino.data.dt.dayofweek)[alvo].mean()
            simples = np.array([medias.get(d.dayofweek, treino[alvo].mean()) for d in teste.data])
            for nome, estimado in [("Random Forest com histórico", ml), ("Média por dia da semana", simples)]:
                avaliacoes.append({"alvo": alvo, "janela": 4 - janela, "modelo": nome, "MAE": mean_absolute_error(teste[alvo], estimado), "RMSE": np.sqrt(mean_squared_error(teste[alvo], estimado)), "treino_ate": treino.data.max(), "teste_de": inicio, "teste_ate": fim, "dias_avaliados": len(teste)})
            registros.append(pd.DataFrame({"data": teste.data, "alvo": alvo, "real": teste[alvo], "ml": ml, "referencia": simples}))
        avaliacao_alvo = pd.DataFrame([v for v in avaliacoes if v["alvo"] == alvo])
        vencedor = avaliacao_alvo.groupby("modelo").MAE.mean().idxmin()
        escolhidos[alvo] = vencedor
        modelo.fit(x, base[alvo])
        contexto = base.iloc[-1][contexto_cols].to_dict()
        if vencedor.startswith("Random Forest"):
            previsto = projetar(modelo, base, datas_futuras, alvo, origem, contexto)
        else:
            medias = base.groupby(base.data.dt.dayofweek)[alvo].mean()
            previsto = np.array([medias.get(d.dayofweek, base[alvo].mean()) for d in datas_futuras])
        validacao = pd.concat(registros, ignore_index=True)
        erro = abs(validacao.real - validacao["ml" if vencedor.startswith("Random Forest") else "referencia"])
        margem = float(erro.quantile(0.9))
        previsao[f"{alvo}_previstos"] = previsto
        previsao[f"{alvo}_inferior"] = np.maximum(0, previsto - margem)
        previsao[f"{alvo}_superior"] = previsto + margem
        validacoes.append(validacao)
        importancias.append(pd.DataFrame({"alvo": alvo, "variavel": x.columns, "importancia": modelo.feature_importances_}))
    return {"previsao": previsao, "avaliacao": pd.DataFrame(avaliacoes), "validacao": pd.concat(validacoes, ignore_index=True), "modelos": escolhidos, "importancia": pd.concat(importancias, ignore_index=True)}
