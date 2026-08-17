#!/usr/bin/env python3
"""Transforma os .json do gallery-dl num corpus markdown legivel pelo modelo.

Um diretorio com 200 arquivos JSON e ilegivel para um LLM. Um corpus.md com
legenda, metrica e link por post e exatamente o formato que ele consegue ler,
citar e ranquear.
"""
import json
import sys
from pathlib import Path

TIPOS = {
    "GraphImage": "imagem",
    "GraphVideo": "video",
    "GraphSidecar": "carrossel",
}


def milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def carregar(dir_posts: Path) -> list:
    """Um carrossel gera um JSON por midia; aqui vira um post so.

    Ao deduplicar, mantem a entrada que tem video: e a que interessa para
    mandar ao pipeline de assistir.
    """
    por_post = {}
    for f in sorted(dir_posts.glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        chave = d.get("post_shortcode") or d.get("shortcode") or f.stem
        d["_arquivo"] = f.with_suffix("").name
        anterior = por_post.get(chave)
        if anterior is None or (d.get("video_url") and not anterior.get("video_url")):
            por_post[chave] = d
    return list(por_post.values())


def tipo_de(p: dict) -> str:
    if p.get("video_url"):
        return "video/reel"
    t = p.get("typename") or p.get("type") or ""
    return TIPOS.get(t, t or "imagem")


def engajamento(p: dict) -> int:
    return int(p.get("likes") or 0)


def escrever_corpus(dir_saida: Path, posts: list) -> None:
    user = next((p.get("username") for p in posts if p.get("username")), "perfil")
    nome = next((p.get("fullname") for p in posts if p.get("fullname")), "")
    ordenados = sorted(posts, key=lambda p: str(p.get("date") or ""), reverse=True)

    linhas = [f"# Instagram @{user}" + (f" — {nome}" if nome else ""), ""]
    total_likes = sum(engajamento(p) for p in posts)
    com_video = sum(1 for p in posts if p.get("video_url"))
    linhas += [
        f"<!-- posts={len(posts)} videos={com_video} likes_somados={total_likes} -->",
        "",
        f"**{len(posts)} posts** · {com_video} com vídeo · "
        f"{milhar(total_likes)} curtidas somadas",
        "",
        "---",
        "",
    ]

    for p in ordenados:
        data = str(p.get("date") or "")[:16]
        tipo = tipo_de(p)
        url = p.get("post_url") or ""
        legenda = (p.get("description") or "").strip() or "_(sem legenda)_"
        linhas.append(f"## [{data}] {tipo} · {milhar(engajamento(p))} curtidas")
        linhas.append("")
        linhas.append(f"<{url}>")
        titulo_audio = p.get("audio_title")
        if titulo_audio and titulo_audio.lower() != "original audio":
            artista = p.get("audio_artist")
            sufixo = f" — {artista}" if artista else ""
            linhas.append(f"*áudio: {titulo_audio}{sufixo}*")
        if p.get("video_url"):
            linhas.append(f"*arquivo de mídia: `{p['_arquivo']}`*")
        linhas.append("")
        linhas.append(legenda)
        tags = p.get("tags") or []
        if tags:
            linhas.append("")
            linhas.append("`" + "` `".join(f"#{t}" for t in tags[:15]) + "`")
        linhas.append("")
        linhas.append("---")
        linhas.append("")

    (dir_saida / "corpus.md").write_text("\n".join(linhas), encoding="utf-8")


def escrever_ranking(dir_saida: Path, posts: list) -> None:
    top = sorted(posts, key=engajamento, reverse=True)
    linhas = ["# Ranking por engajamento", "",
              "| # | curtidas | tipo | data | primeiras palavras | link |",
              "|---|---|---|---|---|---|"]
    for i, p in enumerate(top, 1):
        # o pipe quebra a tabela; a legenda entra escapada
        legenda = " ".join((p.get("description") or "").split())[:70].replace("|", "\\|")
        linhas.append(
            f"| {i} | {milhar(engajamento(p))} | {tipo_de(p)} | "
            f"{str(p.get('date') or '')[:10]} | {legenda} | "
            f"[abrir]({p.get('post_url','')}) |"
        )
    (dir_saida / "ranking.md").write_text("\n".join(linhas), encoding="utf-8")


def main() -> None:
    dir_saida = Path(sys.argv[1])
    apenas_videos = "--videos" in sys.argv
    posts = carregar(dir_saida / "posts")
    if not posts:
        print("nenhum post encontrado", file=sys.stderr)
        sys.exit(1)

    if apenas_videos:
        for p in posts:
            if p.get("video_url"):
                caminho = dir_saida / "posts" / p["_arquivo"]
                existe = "OK " if caminho.exists() else "-- "
                print(f"{existe}{p.get('post_url','')}  {caminho}")
        return

    escrever_corpus(dir_saida, posts)
    escrever_ranking(dir_saida, posts)
    com_video = sum(1 for p in posts if p.get("video_url"))
    print(f"{dir_saida}/corpus.md   ({len(posts)} posts, {com_video} com vídeo)")
    print(f"{dir_saida}/ranking.md")


if __name__ == "__main__":
    main()
