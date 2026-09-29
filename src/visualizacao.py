"""Geração dos gráficos do case."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def configurar_estilo() -> None:
    sns.set_theme(style="whitegrid", palette="deep")
    plt.rcParams["figure.dpi"] = 130
    plt.rcParams["axes.titleweight"] = "bold"


def salvar_graficos(tabelas: dict[str, pd.DataFrame], pasta_saida: Path) -> list[Path]:
    """Cria os principais gráficos e devolve os caminhos gerados."""
    configurar_estilo()
    pasta_saida.mkdir(parents=True, exist_ok=True)
    arquivos = []

    por_mes = tabelas["por_mes"]
    fig, eixo = plt.subplots(figsize=(10, 5))
    sns.lineplot(data=por_mes, x="mes", y="pedidos", marker="o", ax=eixo)
    eixo.set_title("Evolução mensal dos pedidos")
    eixo.set_xlabel("Mês")
    eixo.set_ylabel("Quantidade de pedidos")
    eixo.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    caminho = pasta_saida / "pedidos_por_mes.png"
    fig.savefig(caminho, bbox_inches="tight")
    plt.close(fig)
    arquivos.append(caminho)

    por_hora = tabelas["por_hora"]
    fig, eixo = plt.subplots(figsize=(10, 5))
    sns.barplot(data=por_hora, x="hora", y="pedidos", color="#4C78A8", ax=eixo)
    eixo.set_title("Concentração de pedidos por hora")
    eixo.set_xlabel("Hora do dia")
    eixo.set_ylabel("Quantidade de pedidos")
    fig.tight_layout()
    caminho = pasta_saida / "pedidos_por_hora.png"
    fig.savefig(caminho, bbox_inches="tight")
    plt.close(fig)
    arquivos.append(caminho)

    por_dia = tabelas["por_dia"]
    fig, eixo = plt.subplots(figsize=(10, 5))
    sns.barplot(data=por_dia, x="dia_semana", y="pedidos", color="#F58518", ax=eixo)
    eixo.set_title("Concentração de pedidos por dia da semana")
    eixo.set_xlabel("")
    eixo.set_ylabel("Quantidade de pedidos")
    eixo.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    caminho = pasta_saida / "pedidos_por_dia.png"
    fig.savefig(caminho, bbox_inches="tight")
    plt.close(fig)
    arquivos.append(caminho)

    por_status = tabelas["por_status"].sort_values("pedidos", ascending=False)
    fig, eixo = plt.subplots(figsize=(10, 5))
    sns.barplot(data=por_status, x="status", y="pedidos", color="#54A24B", ax=eixo)
    eixo.set_title("Pedidos por status")
    eixo.set_xlabel("")
    eixo.set_ylabel("Quantidade de pedidos")
    eixo.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    caminho = pasta_saida / "pedidos_por_status.png"
    fig.savefig(caminho, bbox_inches="tight")
    plt.close(fig)
    arquivos.append(caminho)

    segmentos = tabelas["segmentos_rfm"].sort_values("clientes", ascending=False)
    fig, eixo = plt.subplots(figsize=(10, 5))
    sns.barplot(data=segmentos, x="segmento_rfm", y="clientes", color="#B279A2", ax=eixo)
    eixo.set_title("Segmentação RFM de clientes")
    eixo.set_xlabel("")
    eixo.set_ylabel("Quantidade de clientes")
    eixo.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    caminho = pasta_saida / "segmentacao_rfm.png"
    fig.savefig(caminho, bbox_inches="tight")
    plt.close(fig)
    arquivos.append(caminho)

    return arquivos
