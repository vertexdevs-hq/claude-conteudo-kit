# Comece aqui

Cinco minutos, do zero até funcionando. Se algo der errado, o passo 5 diz o que fazer.

---

## 1. Antes de tudo

Você precisa de duas coisas já instaladas:

- **Claude Code** — terminal, app de desktop ou extensão de IDE, tanto faz.
- **Homebrew** (só macOS) — se não tem: https://brew.sh

> **Windows:** instale o [WSL](https://learn.microsoft.com/windows/wsl/install) primeiro e faça **tudo** daqui pra frente dentro dele. Os scripts são bash.
>
> **Claude Code na web não funciona** com este kit — ele precisa de máquina local com ffmpeg e de um navegador logado. Use o app ou o terminal.

## 2. Instalar

```bash
git clone https://github.com/vertexdevs-hq/claude-conteudo-kit.git
cd claude-conteudo-kit
./install.sh
```

O script instala o que falta (ffmpeg, yt-dlp, gallery-dl e companhia) e liga as skills no Claude Code. Leva alguns minutos na primeira vez. Rodar de novo não quebra nada.

## 3. Reiniciar o Claude Code

**Feche e abra.** O catálogo de skills só recarrega no start — sem isso o Claude não sabe que as skills existem.

## 4. Conferir

```bash
~/.claude/skills/assistir-video/bin/vid doctor
```

Tem que terminar com `Ambiente ok.` Se aparecer algo com `FALTA`, rode o `./install.sh` de novo.

## 5. Para usar Instagram: emprestar sua sessão

O Instagram não deixa ninguém ler sem estar logado. O kit usa o cookie do **seu navegador** — nenhuma senha é digitada ou guardada.

1. Abra o **Chrome** e faça login no Instagram.
2. Rode:

```bash
~/.claude/skills/instagram-conteudo/bin/ig sessao
```

Tem que responder `OK - sessao valida`. Se falhar, é login expirado: volte ao Chrome, entre no Instagram e repita.

> Usa outro navegador? `IG_BROWSER=firefox` (ou `safari`, `edge`, `brave`) antes do comando.

---

## Pronto. Agora é só pedir

**Você não precisa decorar comando nenhum.** As skills disparam sozinhas quando você fala com o Claude Code em português. Abra o Claude Code na pasta que quiser e peça:

> "assiste esse vídeo e me diz o que aparece na tela: <link do YouTube>"

> "extrai o conteúdo do canal @igormelloeu e monta um playbook de vendas"

> "analisa o Instagram do @concorrente — quais posts performam melhor e por quê"

> "pega esses reels, vê o que eles têm em comum e me devolve um PDF"

O Claude escolhe a skill, roda os comandos e te entrega o resultado.

---

## Se quiser dirigir na mão

Os três comandos, caso você prefira rodar direto no terminal:

```bash
# atalho: coloque no seu .zshrc para não digitar o caminho todo
export PATH="$HOME/.claude/skills/assistir-video/bin:$HOME/.claude/skills/instagram-conteudo/bin:$HOME/.claude/skills/playbook-de-corpus/bin:$PATH"
```

```bash
vid prep "https://youtube.com/watch?v=..."   # baixa e sonda
vid ouvir <slug>                             # transcrição com timestamps
vid frames <slug> && vid folhas <slug>       # o que o Claude "vê"
vid varrer "https://youtube.com/@canal/videos" ./saida   # canal inteiro

ig sessao                                    # sempre primeiro
ig colher @perfil --n 60                     # corpus.md + ranking.md

pb pdf documento.md --modo doc               # PDF A4
pb pdf slides.md --modo deck                 # slides 16:9
```

---

## Duas coisas para não tomar susto

**O Instagram bloqueia por volume, e o bloqueio cai na sua conta** — é o cookie dela que está sendo usado. O kit já espaça as requisições; não mexa nisso. 30 a 60 posts por vez é confortável. Se começar a dar erro, pare e espere horas, não minutos.

**Colher vídeo custa tokens.** Uma hora de vídeo com varredura visual completa gasta uns 25 mil tokens. O comando `vid custo <imagens>` estima antes de você gastar.

O resto — o que cada ferramenta faz, onde quebra, e por quê — está no [README](README.md) e em [docs/LIMITES.md](docs/LIMITES.md).
