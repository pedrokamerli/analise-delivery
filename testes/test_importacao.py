import pandas as pd
import pytest
from src.importacao import combinar_pedidos


def test_exportacao_parcial_preserva_historico_e_corrige_id():
    anterior = pd.DataFrame({"ID": [1, 2], "STATUS": ["Entregue", "Aberto"]})
    novos = pd.DataFrame({"ID": [2, 3], "STATUS": ["Entregue", "Retirado"]})
    resultado = combinar_pedidos(anterior, novos)
    assert resultado.ID.tolist() == [1, 2, 3]
    assert resultado.set_index("ID").loc[2, "STATUS"] == "Entregue"


def test_rejeita_ids_duplicados():
    base = pd.DataFrame({"ID": [1], "STATUS": ["Entregue"]})
    with pytest.raises(ValueError, match="duplicados"):
        combinar_pedidos(base, pd.concat([base, base]))
