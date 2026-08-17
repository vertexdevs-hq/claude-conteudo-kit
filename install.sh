#!/usr/bin/env bash
# Instala o kit: dependencias externas + skills no Claude Code.
# Idempotente: rodar de novo nao quebra nada e nao reinstala o que ja existe.
set -uo pipefail

AQUI="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
FALTOU=0

azul()  { printf "\033[1;34m%s\033[0m\n" "$*"; }
ok()    { printf "  \033[0;32mok\033[0m    %s\n" "$*"; }
aviso() { printf "  \033[0;33maviso\033[0m %s\n" "$*"; }
erro()  { printf "  \033[0;31mfalta\033[0m %s\n" "$*"; FALTOU=1; }

tem() { command -v "$1" >/dev/null 2>&1; }

azul "1/4  Verificando o basico"

if [[ "$OSTYPE" == darwin* ]]; then
  if ! tem brew; then
    erro "Homebrew — instale em https://brew.sh e rode este script de novo"
    exit 1
  fi
  ok "Homebrew"
  GERENCIADOR="brew install"
elif tem apt-get; then
  ok "apt"
  GERENCIADOR="sudo apt-get install -y"
else
  aviso "gerenciador de pacotes nao reconhecido — instale ffmpeg, jq e yt-dlp na mao"
  GERENCIADOR=""
fi

tem python3 && ok "python3 ($(python3 --version 2>&1 | cut -d' ' -f2))" \
             || erro "python3"

azul "2/4  Dependencias de midia"

for pkg in ffmpeg jq yt-dlp; do
  if tem "$pkg"; then
    ok "$pkg"
  elif [ -n "$GERENCIADOR" ]; then
    echo "      instalando $pkg..."
    $GERENCIADOR "$pkg" >/dev/null 2>&1 && ok "$pkg (instalado)" || erro "$pkg"
  else
    erro "$pkg"
  fi
done

# Pillow desenha a hora dentro do frame. Sem isso a folha de contato vira
# mosaico sem referencia, porque o ffmpeg do Homebrew vem sem libfreetype.
if python3 -c "import PIL" 2>/dev/null; then
  ok "Pillow (python)"
else
  echo "      instalando Pillow..."
  python3 -m pip install --user --quiet Pillow 2>/dev/null \
    && ok "Pillow (instalado)" \
    || erro "Pillow — tente: python3 -m pip install --user Pillow"
fi

if tem uv; then
  ok "uv"
else
  echo "      instalando uv..."
  curl -LsSf https://astral.sh/uv/install.sh 2>/dev/null | sh >/dev/null 2>&1
  export PATH="$HOME/.local/bin:$PATH"
  tem uv && ok "uv (instalado)" || erro "uv — veja https://docs.astral.sh/uv/"
fi

azul "3/4  Ferramentas de coleta"

export PATH="$HOME/.local/bin:$PATH"
if tem gallery-dl; then
  ok "gallery-dl ($(gallery-dl --version 2>/dev/null))"
elif tem uv; then
  echo "      instalando gallery-dl..."
  uv tool install gallery-dl >/dev/null 2>&1 \
    && ok "gallery-dl (instalado)" || erro "gallery-dl"
else
  erro "gallery-dl (precisa do uv)"
fi

# whisper e opcional e pesado: so entra quando nao existe legenda pronta
if tem whisper; then
  ok "whisper (transcricao local)"
else
  aviso "whisper ausente — opcional. So faz falta em video SEM legenda."
  aviso "  instale depois com: uv tool install openai-whisper"
fi

if [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ] \
   || tem google-chrome || tem chromium; then
  ok "Chrome/Chromium (geracao de PDF)"
else
  aviso "Chrome nao encontrado — so o 'pb pdf' depende dele"
fi

azul "4/4  Instalando as skills no Claude Code"

mkdir -p "$SKILLS_DIR"
for skill in "$AQUI"/skills/*/; do
  nome="$(basename "$skill")"
  alvo="$SKILLS_DIR/$nome"
  if [ -L "$alvo" ] || [ -e "$alvo" ]; then
    rm -rf "$alvo"
  fi
  ln -s "${skill%/}" "$alvo"
  chmod +x "${skill%/}"/bin/* 2>/dev/null || true
  ok "$nome -> $alvo"
done

echo
if [ "$FALTOU" = 1 ]; then
  printf "\033[0;31mAlgo faltou.\033[0m Resolva os itens marcados e rode de novo.\n"
  exit 1
fi

cat <<'FIM'

Pronto. Reinicie a sessao do Claude Code para o catalogo de skills recarregar.

Comandos disponiveis (adicione ao PATH se quiser usar direto no terminal):
  vid   assistir video     ~/.claude/skills/assistir-video/bin/vid
  ig    ler Instagram      ~/.claude/skills/instagram-conteudo/bin/ig
  pb    markdown -> PDF    ~/.claude/skills/playbook-de-corpus/bin/pb

Para o Instagram, antes de qualquer coisa: faca login no navegador e rode
  ig sessao

FIM
