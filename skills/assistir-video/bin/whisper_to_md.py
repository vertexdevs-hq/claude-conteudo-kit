#!/usr/bin/env python3
"""Converte o JSON do whisper em markdown com timestamps por bloco."""
import json
import sys
from pathlib import Path

BLOCK_S = 45.0


def ts(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def main():
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    title = sys.argv[2] if len(sys.argv) > 2 else "transcricao"
    segments = data.get("segments", [])
    if not segments:
        print(f"# {title}\n\n<!-- SEM FALA DETECTADA -->")
        return

    print(f"# {title}")
    print(f"\n<!-- idioma={data.get('language','?')} segmentos={len(segments)} -->\n")
    block, block_start = [], segments[0]["start"]
    for seg in segments:
        if seg["start"] - block_start >= BLOCK_S and block:
            print(f"**[{ts(block_start)}]** {' '.join(block).strip()}\n")
            block, block_start = [], seg["start"]
        block.append(seg["text"].strip())
    if block:
        print(f"**[{ts(block_start)}]** {' '.join(block).strip()}\n")


if __name__ == "__main__":
    main()
