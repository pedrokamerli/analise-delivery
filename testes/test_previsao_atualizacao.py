import numpy as np
import pandas as pd
import pytest
from src.atualizacao import validar_csv, combinar_series, salvar_serie_local
from src.previsao import executar_previsao


def conteudo():
    return b"data,pedidos,pedidos_concluidos,indice_faturamento,pontos_ticket_indice\n2026-01-01,10,8,1,800\n"


def test_csv_valida_e_corrige_datas_sem_duplicar():
    atual = validar_csv(conteudo())
    nova = validar_csv(conteudo().replace(b",10,8,", b",12,9,"))
    resultado = combinar_series(atual, nova, "Adicionar ou corrigir datas")
    assert len(resultado) == 1
    assert resultado.iloc[0].pedidos == 12
    assert resultado.iloc[0].taxa_conclusao == 75


@pytest.mark.parametrize("arquivo", [
    conteudo().replace(b",10,8,", b",2,8,"),
    conteudo().replace(b",10,8,", b",10.5,8,"),
    conteudo().replace(b",10,8,", b",inf,8,"),
    conteudo().replace(b"2026-01-01", b"data-invalida"),
    conteudo().replace(b"pontos_ticket_indice", b"telefone"),
])
def test_csv_rejeita_dados_invalidos(arquivo):
    with pytest.raises(ValueError):
        validar_csv(arquivo)


def test_previsao_cronologica_e_futuro_sem_vazamento():
    datas = pd.date_range("2026-01-01", periods=150)
    serie = pd.DataFrame({"data": datas, "pedidos": 10 + datas.dayofweek * 2})
    resultado = executar_previsao(serie, 14)
    assert len(resultado["previsao"]) == 14
    assert resultado["previsao"].data.min() > serie.data.max()
    assert (resultado["avaliacao"].treino_ate < resultado["avaliacao"].teste_de).all()
    assert np.isfinite(resultado["previsao"].pedidos_previstos).all()
    assert (resultado["previsao"].limite_inferior >= 0).all()
    assert resultado["modelo"] == "Média por dia da semana"


def test_modelo_recusa_historico_curto():
    with pytest.raises(ValueError):
        executar_previsao(pd.DataFrame({"data": pd.date_range("2026-01-01", periods=10), "pedidos": [1] * 10}))


def test_salvamento_persiste_e_preserva_backup(tmp_path):
    destino = tmp_path / "serie_diaria.csv"
    original = validar_csv(conteudo())
    salvar_serie_local(original, destino)
    nova = validar_csv(conteudo().replace(b",10,8,", b",12,9,"))
    salvar_serie_local(nova, destino)
    assert validar_csv(destino.read_bytes()).iloc[0].pedidos == 12
    backups = list(tmp_path.glob("serie_backup_*.csv"))
    assert len(backups) == 1
    assert validar_csv(backups[0].read_bytes()).iloc[0].pedidos == 10
