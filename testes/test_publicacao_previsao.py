import pandas as pd
import pytest
from src.publicacao import exportar_historico_previsao
from src.historico_clientes import COLUNAS_HISTORICO


def test_publicacao_remove_valores_em_reais(tmp_path):
    h = pd.DataFrame({"data": pd.to_datetime(["2026-01-01", "2026-01-02"]), "pedidos": [10, 20], "faturamento": [1000.0, 2000.0], "faturamento_registrado": [1200, 2300], "telefone": ["privado", "privado"], **{c: [10.0, 20.0] for c in COLUNAS_HISTORICO}})
    h["historico_ticket_28d"] = [50, 75]
    exportar_historico_previsao(h, tmp_path)
    publico = pd.read_csv(tmp_path / "historico_previsao.csv")
    assert publico.faturamento.sum() == pytest.approx(100)
    assert publico.historico_ticket_28d.tolist() == [100, 150]
    assert "faturamento_registrado" not in publico
    assert "telefone" not in publico
