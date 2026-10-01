"""Previsão diária com validação cronológica e referência por dia da semana."""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


def atributos(datas, origem):
    datas = pd.DatetimeIndex(datas)
    return pd.DataFrame({
        "dia_semana": datas.dayofweek,
        "mes": datas.month,
        "dia_mes": datas.day,
        "tendencia": (datas - origem).days,
        "semana_seno": np.sin(2 * np.pi * datas.dayofweek / 7),
        "semana_cosseno": np.cos(2 * np.pi * datas.dayofweek / 7),
    })


def referencia(treino, datas):
    medias = treino.groupby(treino.data.dt.dayofweek).pedidos.mean()
    return np.array([medias.get(d.dayofweek, treino.pedidos.mean()) for d in datas])


def executar_previsao(serie, horizonte=14, preencher_zeros=False):
    base = serie[["data", "pedidos"]].sort_values("data").copy()
    base["data"] = pd.to_datetime(base.data)
    if preencher_zeros:
        base = base.set_index("data").reindex(pd.date_range(base.data.min(), base.data.max())).fillna(0).rename_axis("data").reset_index()
    if len(base) < 90:
        raise ValueError("São necessários pelo menos 90 dias observados para avaliar a previsão.")
    origem = base.data.min()
    tamanho = min(28, len(base) // 5)
    registros = []
    metricas = []
    for rodada in range(3, 0, -1):
        corte = len(base) - rodada * tamanho
        treino = base.iloc[:corte]
        teste = base.iloc[corte:corte + tamanho]
        modelo = RandomForestRegressor(n_estimators=150, min_samples_leaf=5, random_state=42, n_jobs=1)
        modelo.fit(atributos(treino.data, origem), treino.pedidos)
        estimado = modelo.predict(atributos(teste.data, origem))
        simples = referencia(treino, teste.data)
        for nome, valores in [("Random Forest", estimado), ("Média por dia da semana", simples)]:
            metricas.append({"janela": 4 - rodada, "modelo": nome, "MAE": mean_absolute_error(teste.pedidos, valores), "RMSE": np.sqrt(mean_squared_error(teste.pedidos, valores)), "treino_ate": treino.data.max(), "teste_de": teste.data.min(), "teste_ate": teste.data.max()})
        registros.append(teste.assign(ml=estimado, referencia=simples))
    avaliacao = pd.DataFrame(metricas)
    medias = avaliacao.groupby("modelo")[["MAE", "RMSE"]].mean()
    escolhido = medias.MAE.idxmin()
    modelo.fit(atributos(base.data, origem), base.pedidos)
    futuras = pd.date_range(base.data.max() + pd.Timedelta(days=1), periods=horizonte)
    valores = modelo.predict(atributos(futuras, origem)) if escolhido == "Random Forest" else referencia(base, futuras)
    validacao = pd.concat(registros, ignore_index=True)
    erros = abs(validacao.pedidos - validacao["ml" if escolhido == "Random Forest" else "referencia"])
    margem = float(erros.quantile(0.9))
    previsao = pd.DataFrame({"data": futuras, "pedidos_previstos": valores, "limite_inferior": np.maximum(0, valores - margem), "limite_superior": valores + margem})
    return {"previsao": previsao, "avaliacao": avaliacao, "validacao": validacao, "modelo": escolhido, "importancia": pd.DataFrame({"variavel": atributos(base.data, origem).columns, "importancia": modelo.feature_importances_}).sort_values("importancia", ascending=False)}
