"""Importa uma exportação de pedidos sem perder o histórico anterior."""

import argparse
from pathlib import Path
from src.importacao import importar_excel

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arquivo", type=Path, help="Exportação de pedidos .xlsx")
    args = parser.parse_args()
    print(importar_excel(args.arquivo.read_bytes()))
