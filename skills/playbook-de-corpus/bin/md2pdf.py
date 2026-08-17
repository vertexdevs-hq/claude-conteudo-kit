#!/usr/bin/env python3
"""Markdown -> HTML paginado -> PDF pelo Chrome headless.

Nao usa html2canvas nem screenshot: o PDF sai do motor de impressao do Chrome,
entao o texto continua selecionavel, as quebras respeitam CSS de impressao e a
tipografia nao vira bitmap.
"""
import argparse
import html as html_mod
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

CHROMES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
]

CSS_COMUM = """
*, *::before, *::after { box-sizing: border-box; }
:root {
  --tinta: #16161a;
  --tinta-2: #3d3d46;
  --fraco: #6f6f7a;
  --linha: #dcdae2;
  --fundo: #ffffff;
  --painel: #f6f5f8;
  --acento: %(acento)s;
  --serif: "Palatino", "Palatino Linotype", Georgia, serif;
  --sans: "Avenir Next", "Helvetica Neue", Helvetica, Arial, sans-serif;
  --mono: "SF Mono", "Menlo", "Consolas", monospace;
}
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body {
  margin: 0; background: var(--fundo); color: var(--tinta);
  font-family: var(--sans); font-size: 10.5pt; line-height: 1.62;
  font-kerning: normal;
}
h1, h2, h3, h4 { font-family: var(--serif); font-weight: 600; text-wrap: balance; }
h1 { font-size: 25pt; line-height: 1.15; letter-spacing: -0.015em; margin: 0 0 .5em; }
h2 {
  font-size: 16pt; line-height: 1.25; margin: 1.9em 0 .55em;
  padding-bottom: .28em; border-bottom: 2px solid var(--acento);
}
h3 { font-size: 12.5pt; margin: 1.5em 0 .4em; color: var(--tinta-2); }
h4 { font-size: 11pt; margin: 1.2em 0 .3em; color: var(--fraco);
     font-family: var(--sans); text-transform: uppercase;
     letter-spacing: .07em; font-size: 8.5pt; }
p { margin: 0 0 .85em; }
a { color: var(--acento); text-decoration: none; border-bottom: 1px solid var(--linha); }
strong { font-weight: 650; }
ul, ol { margin: 0 0 .9em; padding-left: 1.25em; }
li { margin-bottom: .3em; }
li::marker { color: var(--acento); }
hr { border: 0; border-top: 1px solid var(--linha); margin: 2em 0; }
blockquote {
  margin: 1.1em 0; padding: .7em 0 .7em 1.1em;
  border-left: 3px solid var(--acento); color: var(--tinta-2);
  font-family: var(--serif); font-size: 10.5pt; font-style: italic;
}
blockquote p:last-child { margin-bottom: 0; }
code {
  font-family: var(--mono); font-size: .87em;
  background: var(--painel); padding: .1em .35em; border-radius: 3px;
}
pre {
  background: var(--painel); padding: .85em 1em; border-radius: 6px;
  overflow-x: auto; border: 1px solid var(--linha);
}
pre code { background: none; padding: 0; font-size: 8.5pt; line-height: 1.45; }
table {
  width: 100%%; border-collapse: collapse; margin: 1em 0;
  font-size: 9pt; font-variant-numeric: tabular-nums;
}
th, td { text-align: left; padding: .48em .6em; border-bottom: 1px solid var(--linha);
         vertical-align: top; }
th { background: var(--painel); font-weight: 650; font-size: 8pt;
     text-transform: uppercase; letter-spacing: .05em; color: var(--fraco); }
tbody tr:nth-child(even) { background: #fbfafc; }
img { max-width: 100%%; height: auto; }
h1, h2, h3, h4 { break-after: avoid; page-break-after: avoid; }
table, pre, blockquote { break-inside: avoid; page-break-inside: avoid; }
"""

CSS_DOC = """
@page { size: A4; margin: 20mm 18mm 18mm; }
body { max-width: none; }
.conteudo { max-width: 165mm; margin: 0 auto; }
h1 { border-bottom: 3px solid var(--acento); padding-bottom: .35em; }
"""

CSS_DECK = """
@page { size: 338.7mm 190.5mm; margin: 0; }
body { font-size: 13pt; }
.slide {
  width: 338.7mm; height: 190.5mm; padding: 20mm 24mm;
  display: flex; flex-direction: column; justify-content: center;
  break-after: page; page-break-after: always; overflow: hidden;
  position: relative; background: var(--fundo);
}
.slide:last-child { break-after: auto; page-break-after: auto; }
.slide::after {
  content: counter(pagina); counter-increment: pagina;
  position: absolute; right: 24mm; bottom: 12mm;
  font-size: 8pt; color: var(--fraco); font-variant-numeric: tabular-nums;
}
body { counter-reset: pagina; }
.slide h1 { font-size: 34pt; }
.slide h2 { font-size: 22pt; margin-top: 0; }
.slide h3 { font-size: 15pt; }
.slide table { font-size: 10pt; }
.slide > :first-child { margin-top: 0; }
.slide.capa { justify-content: center; align-items: flex-start;
              border-left: 10mm solid var(--acento); }
"""


def achar_chrome() -> str:
    for c in CHROMES:
        if Path(c).exists():
            return c
    for nome in ("google-chrome", "chromium", "chromium-browser"):
        achado = shutil.which(nome)
        if achado:
            return achado
    sys.exit("erro: Chrome/Chromium nao encontrado — necessario para gerar o PDF")


def montar_html(md_texto: str, modo: str, titulo: str, acento: str) -> str:
    corpo = markdown.markdown(
        md_texto,
        extensions=["tables", "fenced_code", "attr_list", "sane_lists", "toc"],
    )
    if modo == "deck":
        partes = re.split(r"\n?<hr\s*/?>\n?", corpo)
        blocos = []
        for i, parte in enumerate(partes):
            if not parte.strip():
                continue
            classe = "slide capa" if i == 0 else "slide"
            blocos.append(f'<section class="{classe}">{parte}</section>')
        corpo = "\n".join(blocos)
        css_modo = CSS_DECK
    else:
        corpo = f'<div class="conteudo">{corpo}</div>'
        css_modo = CSS_DOC

    return (
        "<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>"
        f"<title>{html_mod.escape(titulo)}</title>"
        f"<style>{CSS_COMUM % {'acento': acento}}{css_modo}</style>"
        f"</head><body>{corpo}</body></html>"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="markdown -> PDF")
    ap.add_argument("entrada")
    ap.add_argument("saida", nargs="?")
    ap.add_argument("--modo", choices=["doc", "deck"], default="doc")
    ap.add_argument("--acento", default="#B4472B",
                    help="cor de destaque (padrao: terracota)")
    ap.add_argument("--guardar-html", action="store_true")
    args = ap.parse_args()

    entrada = Path(args.entrada)
    if not entrada.exists():
        sys.exit(f"erro: {entrada} nao existe")
    saida = Path(args.saida) if args.saida else entrada.with_suffix(".pdf")

    md_texto = entrada.read_text(encoding="utf-8")
    titulo = next(
        (l.lstrip("# ").strip() for l in md_texto.splitlines() if l.startswith("# ")),
        entrada.stem,
    )
    doc = montar_html(md_texto, args.modo, titulo, args.acento)

    tmp = Path(tempfile.mkdtemp()) / "doc.html"
    tmp.write_text(doc, encoding="utf-8")
    if args.guardar_html:
        destino = saida.with_suffix(".html")
        destino.write_text(doc, encoding="utf-8")
        print(f"html: {destino}")

    subprocess.run(
        [achar_chrome(), "--headless", "--disable-gpu", "--no-pdf-header-footer",
         f"--print-to-pdf={saida.resolve()}", tmp.as_uri()],
        check=True, capture_output=True,
    )
    tamanho = saida.stat().st_size / 1024
    print(f"{saida}  ({tamanho:.0f} KB, modo {args.modo})")


if __name__ == "__main__":
    main()
