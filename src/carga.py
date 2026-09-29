"""Leitura dos arquivos brutos da análise."""

from pathlib import Path

import pandas as pd


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
PASTA_DADOS_BRUTOS = RAIZ_PROJETO / "dados" / "brutos"


def localizar_arquivo(padrao: str) -> Path:
    """Localiza exatamente um arquivo dentro de dados/brutos."""
    arquivos = list(PASTA_DADOS_BRUTOS.glob(padrao))

    if len(arquivos) == 1:
        return arquivos[0]
    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum arquivo com o padrão '{padrao}' foi encontrado em {PASTA_DADOS_BRUTOS}."
        )
    raise ValueError(f"Foram encontrados vários arquivos para '{padrao}': {arquivos}")


def carregar_pedidos() -> pd.DataFrame:
    """Carrega a planilha de pedidos exportada pelo sistema."""
    return pd.read_excel(localizar_arquivo("Pedidos - *.xlsx"))


def carregar_clientes() -> pd.DataFrame:
    """Carrega a aba CLIENTES da planilha de clientes."""
    return pd.read_excel(localizar_arquivo("Planilha de clientes - *.xlsx"), sheet_name="CLIENTES")
