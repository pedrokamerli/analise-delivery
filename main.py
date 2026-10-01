"""Executa todas as etapas da análise da operação de delivery."""

from pathlib import Path

from src.analise import calcular_metricas_principais, gerar_tabelas_analiticas
from src.carga import RAIZ_PROJETO, carregar_clientes, carregar_pedidos
from src.avaliacoes import auditar_pdf_avaliacoes
from src.publicacao import exportar_dados_publicos
from src.relatorio import criar_relatorio
from src.tratamento import tratar_clientes, tratar_pedidos
from src.visualizacao import salvar_graficos
from src.historico_clientes import construir_historico
import json


def salvar_tabelas(tabelas: dict, pasta_saida: Path) -> None:
    """Salva as tabelas agregadas para consulta posterior."""
    pasta_saida.mkdir(parents=True, exist_ok=True)
    for nome, tabela in tabelas.items():
        tabela.to_csv(pasta_saida / f"{nome}.csv", index=False, encoding="utf-8-sig")


def main() -> None:
    print("Carregando dados...")
    pedidos_brutos = carregar_pedidos()
    clientes_brutos = carregar_clientes()

    print("Tratando dados...")
    pedidos = tratar_pedidos(pedidos_brutos)
    clientes = tratar_clientes(clientes_brutos)

    print("Calculando indicadores...")
    metricas = calcular_metricas_principais(pedidos)
    tabelas = gerar_tabelas_analiticas(pedidos, clientes)

    pasta_dados_tratados = RAIZ_PROJETO / "dados" / "tratados"
    pedidos.to_csv(pasta_dados_tratados / "pedidos_tratados.csv", index=False, encoding="utf-8-sig")
    clientes.to_csv(pasta_dados_tratados / "clientes_tratados.csv", index=False, encoding="utf-8-sig")
    salvar_tabelas(tabelas, pasta_dados_tratados)

    graficos = salvar_graficos(tabelas, RAIZ_PROJETO / "imagens" / "geradas")
    pdf_avaliacoes = next((RAIZ_PROJETO / "dados" / "brutos").glob("*.pdf"))
    auditoria_avaliacoes = auditar_pdf_avaliacoes(pdf_avaliacoes)
    relatorio = criar_relatorio(
        metricas, tabelas, auditoria_avaliacoes, RAIZ_PROJETO / "relatorios" / "gerados"
    )
    exportar_dados_publicos(metricas, tabelas, RAIZ_PROJETO / "dados" / "publicos")
    historico, resumo_historico = construir_historico(pedidos_brutos, clientes_brutos)
    historico.to_csv(pasta_dados_tratados / "historico_diario.csv", index=False)
    (pasta_dados_tratados / "historico_resumo.json").write_text(
        json.dumps(resumo_historico, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\nAnálise concluída.")
    print(f"Período: {metricas['periodo_inicial']} a {metricas['periodo_final']}")
    print(f"Pedidos: {metricas['total_pedidos']}")
    print(f"Taxa de conclusão: {metricas['taxa_conclusao']}%")
    print(f"Ticket médio: R$ {metricas['ticket_medio']:,.2f}")
    print(f"Gráficos gerados: {len(graficos)}")
    print(f"Relatório salvo em: {relatorio}")


if __name__ == "__main__":
    main()
