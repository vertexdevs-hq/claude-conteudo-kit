#!/usr/bin/env python3
"""Rotula frames com o timestamp e monta folhas de contato.

Existe porque o ffmpeg do Homebrew vem sem libfreetype, ou seja, sem o filtro
drawtext. Sem a hora gravada na imagem, uma folha de contato vira um mosaico
de quadros que o modelo nao consegue referenciar.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTS = [
    # macOS
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    # Windows
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arial.ttf",
]

LABEL_PAD = 6
BG = (17, 17, 17)


def load_font(size: int):
    for path in FONTS:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def ts_from_name(name: str) -> str:
    """000_00h01m30s.jpg -> 00:01:30"""
    stem = Path(name).stem
    part = stem.split("_", 1)[-1]
    try:
        h = part.split("h")[0]
        m = part.split("h")[1].split("m")[0]
        s = part.split("m")[1].split("s")[0]
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
    except (IndexError, ValueError):
        return part


def draw_label(img: Image.Image, text: str) -> Image.Image:
    draw = ImageDraw.Draw(img)
    size = max(14, int(img.width * 0.055))
    font = load_font(size)
    box = draw.textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    x0, y0 = 8, 8
    draw.rectangle(
        [x0, y0, x0 + w + LABEL_PAD * 2, y0 + h + LABEL_PAD * 2 + 4],
        fill=(0, 0, 0),
    )
    draw.text((x0 + LABEL_PAD, y0 + LABEL_PAD - box[1]), text,
              font=font, fill=(255, 255, 255))
    return img


def cmd_rotular(scan_dir: Path) -> None:
    frames = sorted(scan_dir.glob("*.jpg"))
    for f in frames:
        img = Image.open(f).convert("RGB")
        draw_label(img, ts_from_name(f.name))
        img.save(f, quality=88)
    print(f"{len(frames)} frames rotulados")


def estimar_tokens(w: int, h: int) -> int:
    """A API reduz o maior lado para 1568px antes de contar tokens."""
    maior = max(w, h)
    if maior > 1568:
        fator = 1568 / maior
        w, h = w * fator, h * fator
    return int(w * h / 750)


MAX_LADO = 1568  # acima disso a API reduz a imagem por conta propria


def melhor_grade(tile_w: int, tile_h: int, alvo: int) -> tuple:
    """Escolhe cols x rows cuja folha fique o mais quadrada possivel.

    Folha quadrada aproveita melhor o teto de 1568px: um mosaico muito alto ou
    muito largo e reduzido no lado maior e os quadros ficam ilegiveis.
    """
    melhor, desvio_min = (alvo, 1), float("inf")
    for rows in range(1, alvo + 1):
        cols = -(-alvo // rows)  # teto da divisao
        if cols * rows > alvo + max(0, rows - 1):
            continue
        aspecto = (cols * tile_w) / (rows * tile_h)
        desvio = abs(aspecto - 1.0) if aspecto >= 1 else abs(1 / aspecto - 1.0)
        if desvio < desvio_min:
            melhor, desvio_min = (cols, rows), desvio
    return melhor


def cmd_folhas(scan_dir: Path, out_dir: Path, cols: int, rows: int) -> None:
    frames = sorted(scan_dir.glob("*.jpg"))
    if not frames:
        print("nenhum frame para montar", file=sys.stderr)
        sys.exit(1)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.jpg"):
        old.unlink()

    amostra = Image.open(frames[0])
    tile_w, tile_h = amostra.size
    alvo = cols * rows
    cols, rows = melhor_grade(tile_w, tile_h, alvo)

    per = cols * rows
    gap = 6
    sheets = [frames[i:i + per] for i in range(0, len(frames), per)]
    print(f"grade {cols}x{rows} (frame {tile_w}x{tile_h}), "
          f"{len(sheets)} folha(s)")

    for idx, group in enumerate(sheets, start=1):
        sheet_w = cols * tile_w + (cols + 1) * gap
        sheet_h = rows * tile_h + (rows + 1) * gap
        sheet = Image.new("RGB", (sheet_w, sheet_h), BG)
        linhas = []
        for pos, f in enumerate(group):
            r, c = divmod(pos, cols)
            x = gap + c * (tile_w + gap)
            y = gap + r * (tile_h + gap)
            img = Image.open(f).convert("RGB")
            if img.size != (tile_w, tile_h):
                img = img.resize((tile_w, tile_h))
            sheet.paste(img, (x, y))
            linhas.append(f"{pos + 1:>2}. {ts_from_name(f.name)}")

        # reduz aqui em vez de deixar a API reduzir: assim o resultado e previsivel
        maior = max(sheet.size)
        if maior > MAX_LADO:
            fator = MAX_LADO / maior
            sheet = sheet.resize(
                (int(sheet.width * fator), int(sheet.height * fator)),
                Image.LANCZOS,
            )
        out = out_dir / f"folha-{idx:02d}.jpg"
        sheet.save(out, quality=88)
        print(f"\n{out}  ({sheet.width}x{sheet.height}, "
              f"~{estimar_tokens(*sheet.size)} tokens)")
        print("   ordem de leitura: esquerda->direita, cima->baixo")
        print("   " + " | ".join(linhas))


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "rotular":
        cmd_rotular(Path(sys.argv[2]))
    elif cmd == "folhas":
        cmd_folhas(Path(sys.argv[2]), Path(sys.argv[3]),
                   int(sys.argv[4]), int(sys.argv[5]))
    else:
        print("uso: frames_tool.py rotular <scan_dir>", file=sys.stderr)
        print("     frames_tool.py folhas <scan_dir> <out_dir> <cols> <rows>",
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
