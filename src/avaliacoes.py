"""Auditoria da fonte de avaliações."""

from pathlib import Path

from pypdf import PdfReader


def auditar_pdf_avaliacoes(caminho: Path) -> dict[str, int | bool]:
    """Verifica se o PDF permite análise textual automatizada."""
    leitor = PdfReader(caminho)
    texto = "".join(pagina.extract_text() or "" for pagina in leitor.pages).strip()
    return {
        "paginas": len(leitor.pages),
        "possui_texto_extraivel": bool(texto),
        "caracteres_extraidos": len(texto),
    }
