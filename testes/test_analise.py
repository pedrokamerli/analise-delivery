import pandas as pd

from src.analise import calcular_segmentacao_rfm


def test_segmentacao_rfm_cria_quatro_notas_e_segmentos() -> None:
    clientes = pd.DataFrame(
        {
            "classificacao": ["Ativo"] * 8,
            "pedidos_historicos": [1, 2, 3, 4, 5, 6, 7, 8],
            "faturamento_historico": [10, 20, 30, 40, 50, 60, 70, 80],
            "dias_sem_comprar": [80, 70, 60, 50, 40, 30, 20, 10],
        }
    )

    rfm, segmentos = calcular_segmentacao_rfm(clientes)

    assert set(rfm["nota_recencia"]) == {1, 2, 3, 4}
    assert set(rfm["nota_frequencia"]) == {1, 2, 3, 4}
    assert segmentos["clientes"].sum() == len(clientes)
