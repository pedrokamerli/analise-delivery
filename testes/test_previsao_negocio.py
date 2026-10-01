import numpy as np
import pandas as pd
import pytest
from src.historico_clientes import construir_historico, validar_csv_historico
from src.previsao_negocio import prever_pedidos_faturamento


def test_historico_clientes_usa_apenas_pedidos_anteriores():
    pedidos = pd.DataFrame({"ID": [1, 2, 3], "DATA CADASTRAL": ["01/01/2026 - 18:00:00", "02/01/2026 - 18:00:00", "03/01/2026 - 18:00:00"], "TOTAL": [100, 200, 300], "STATUS": ["Entregue", "Entregue", "Rejeitado"], "TELEFONE": ["5511999999999"] * 3})
    clientes = pd.DataFrame({"TELEFONE": ["11999999999"], "PEDIDOS": [999], "FATURADO": [999999]})
    serie, resumo = construir_historico(pedidos, clientes)
    assert serie.iloc[0].historico_clientes_ativos_28d == 0
    assert serie.iloc[1].historico_ticket_28d == 100
    assert serie.iloc[2].historico_ticket_28d == 150
    assert serie.iloc[2].faturamento == 0
    assert serie.iloc[2].clientes_recorrentes == 1
    assert resumo["cobertura_cadastro_pct"] == 100
    assert not any("telefone" in c.lower() or c == "cliente" for c in serie.columns)


def base_sintetica():
    datas = pd.date_range("2026-01-01", periods=100)
    return pd.DataFrame({"data": datas, "pedidos": 10 + datas.dayofweek, "faturamento": (10 + datas.dayofweek) * 50, "historico_clientes_ativos_28d": [30] * 100})


def test_previsao_ambos_alvos_e_sem_consultar_futuro():
    base = base_sintetica()
    resultado = prever_pedidos_faturamento(base, 7)
    alterada = base.copy()
    alterada.loc[alterada.index[-7:], ["pedidos", "faturamento", "historico_clientes_ativos_28d"]] = 100000
    outro = prever_pedidos_faturamento(alterada, 7)
    # Mesmo mudando os valores reais da última janela, suas previsões de teste não mudam.
    np.testing.assert_allclose(resultado["validacao"].ml, outro["validacao"].ml)
    np.testing.assert_allclose(resultado["validacao"].referencia, outro["validacao"].referencia)
    assert set(resultado["modelos"]) == {"pedidos", "faturamento"}
    assert len(resultado["previsao"]) == 7
    assert resultado["previsao"].data.min() > base.data.max()
    assert (resultado["avaliacao"].treino_ate < resultado["avaliacao"].teste_de).all()
    assert (resultado["previsao"].filter(like="inferior") >= 0).all().all()


def test_csv_historico_rejeita_identificadores_e_quantidades_invalidas():
    valido = b"data,pedidos,faturamento\n2026-01-01,10,500\n"
    assert validar_csv_historico(valido).iloc[0].faturamento == 500
    for invalido in [valido.replace(b",10,", b",-1,"), valido.replace(b",10,", b",1.5,"), valido.replace(b"faturamento", b"telefone")]:
        with pytest.raises(ValueError):
            validar_csv_historico(invalido)
