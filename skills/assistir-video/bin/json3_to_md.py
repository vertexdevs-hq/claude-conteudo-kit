#!/usr/bin/env python3
"""Converte legenda json3 do YouTube em markdown com timestamps por bloco.

Legenda automatica vem em eventos curtos e sobrepostos. Aqui os eventos viram
uma sequencia unica de palavras com tempo, reagrupada em blocos de ~BLOCK_S
segundos, que e o formato que um LLM consegue citar por minuto.
"""
import json
import sys
from pathlib import Path

BLOCK_S = 45.0


def ts(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def words_from_json3(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for ev in data.get("events", []):
        base = ev.get("tStartMs", 0)
        for seg in ev.get("segs", []) or []:
            text = seg.get("utf8", "")
            if not text.strip():
                continue
            start = (base + seg.get("tOffsetMs", 0)) / 1000.0
            out.append((start, text.strip()))
    out.sort(key=lambda x: x[0])
    # auto-caption repete a mesma palavra no mesmo instante entre eventos vizinhos
    deduped = []
    for start, text in out:
        if deduped and abs(deduped[-1][0] - start) < 0.01 and deduped[-1][1] == text:
            continue
        deduped.append((start, text))
    return deduped


def to_blocks(words, block_s=BLOCK_S):
    blocks, cur, cur_start = [], [], None
    for start, text in words:
        if cur_start is None:
            cur_start = start
        if start - cur_start >= block_s and cur:
            blocks.append((cur_start, " ".join(cur)))
            cur, cur_start = [], start
        cur.append(text)
    if cur:
        blocks.append((cur_start or 0.0, " ".join(cur)))
    return blocks


def main():
    src = Path(sys.argv[1])
    title = sys.argv[2] if len(sys.argv) > 2 else src.stem
    vid = sys.argv[3] if len(sys.argv) > 3 else src.stem.split(".")[0]
    words = words_from_json3(src)
    if not words:
        print(f"<!-- SEM LEGENDA: {src.name} -->")
        return
    blocks = to_blocks(words)
    dur = words[-1][0]
    print(f"# {title}")
    print(f"\n<!-- id={vid} duracao={ts(dur)} palavras={len(words)} -->\n")
    for start, text in blocks:
        print(f"**[{ts(start)}]** {text}\n")


if __name__ == "__main__":
    main()
