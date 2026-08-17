# Kit de Conteúdo para Claude Code

Três skills que fazem o Claude Code **assistir vídeo, ler Instagram e virar isso em entregável** — playbook, dossiê, deck, PDF.

Não é um wrapper de API. É o encanamento que resolve o problema real: **o modelo não lê vídeo nem abre o Instagram.** Ele lê texto e imagem. Este kit converte um no outro, com controle de custo em tokens.

```
YouTube / arquivo de vídeo ─┐
                            ├──► corpus de texto + folhas de contato ──► playbook / deck / PDF
Instagram (posts e reels) ──┘
```

---

## Instalação

```bash
git clone git@github.com:vertexdevs-hq/claude-conteudo-kit.git
cd claude-conteudo-kit
./install.sh
```

Depois **reinicie a sessão do Claude Code** — o catálogo de skills só recarrega no start.

O `install.sh` verifica e instala o que falta, e é idempotente: rodar de novo não quebra nada.

### O que ele instala

| Peça | Para quê | Obrigatório |
|---|---|---|
| **ffmpeg** | extrair frames e áudio | sim |
| **yt-dlp** | baixar vídeo e legenda do YouTube | sim |
| **jq** | ler os metadados | sim |
| **Pillow** (python) | gravar a hora dentro do frame | sim |
| **uv** | rodar ferramentas isoladas | sim |
| **gallery-dl** | ler o Instagram | sim, para Instagram |
| **Chrome** | gerar o PDF | só para `pb pdf` |
| **whisper** | transcrever vídeo sem legenda | opcional, e pesado |

> **Por que Pillow e não o ffmpeg:** o ffmpeg do Homebrew vem **sem libfreetype**, ou seja, sem o filtro `drawtext`. Sem gravar a hora na imagem, uma folha de contato vira um mosaico que o modelo não consegue referenciar. O kit desenha o rótulo com Pillow e resolve isso sem exigir recompilar ffmpeg.

---

## As três skills

### `assistir-video` — o Claude vê o vídeo

Transcrição não é assistir: ela pega a fala e perde o que está escrito no slide, o número no dashboard, o produto que aparece.

```bash
vid prep "https://youtube.com/watch?v=..."   # sonda e sugere o plano de amostragem
vid ouvir <slug>                             # áudio -> transcrição com timestamps
vid frames <slug> && vid folhas <slug>       # frames -> folhas de contato
vid zoom <slug> 12:34                        # resolução cheia num instante específico
vid varrer "https://youtube.com/@canal/videos" ./saida   # canal inteiro
```

**Protocolo:** ficha técnica → ouvir → folhear → encarar → relatar.

**A economia que sustenta o kit:** 12 frames soltos custam ~1.400 tokens *cada*. A mesma dúzia numa folha de contato custa ~2.400 tokens *no total* — 7× mais barato. Frame em resolução cheia só depois que a folha localizou o instante.

### `instagram-conteudo` — o Claude lê o perfil

```bash
ig sessao                        # SEMPRE primeiro: testa a sessão do navegador
ig colher @perfil --n 60         # posts + legendas + métricas -> corpus.md + ranking.md
ig colher @perfil --com-midia    # também baixa foto e vídeo
ig videos <pasta>                # caminho dos .mp4, para mandar ao `vid`
```

**O Instagram exige sessão autenticada.** Não existe leitura anônima desde 2025. Os cookies saem do **seu** navegador (`IG_BROWSER`, padrão `chrome`) — nenhuma senha é digitada, guardada ou pedida. Faça login no Instagram no navegador e rode `ig sessao`.

### `playbook-de-corpus` — vira entregável

```bash
pb pdf playbook.md --modo doc                 # documento A4
pb pdf deck.md --modo deck --acento "#1F4D8F" # slides 16:9; cada `---` é um slide
```

O PDF sai do motor de impressão do Chrome: **texto continua selecionável**, sem screenshot nem html2canvas.

---

## Fluxo completo, na prática

Destilar um canal do YouTube inteiro em playbook:

```bash
vid varrer "https://www.youtube.com/@canal/videos" ./transcricoes
# o Claude lê as transcrições, encontra a estrutura e escreve o playbook
pb pdf playbook.md --modo doc
```

Estudar um concorrente no Instagram:

```bash
ig colher @concorrente --n 60
# leia ranking.md primeiro: o padrão do que performa aparece em 30 segundos
ig colher @concorrente --n 20 --com-midia
ig videos ~/.cache/instagram-conteudo/concorrente
vid prep <reel.mp4> reel-01 && vid frames reel-01 --cada 3 && vid folhas reel-01
pb pdf dossie.md --modo doc
```

---

## O que este kit **não** faz

Dito de frente, para ninguém descobrir no meio do trabalho:

- **Não publica nada.** É leitura. Para publicar, use outra ferramenta.
- **Não traz comentários do Instagram**, nem alcance, salvamentos ou compartilhamentos. Curtidas e legenda, sim.
- **Não lê stories** (expiram em 24h, outra rota).
- **Não abre perfil privado** que a conta logada não siga.
- **Não substitui assistir de verdade** quando o assunto é nuance de tom, ritmo ou edição. Ele extrai fato e estrutura muito bem; julgamento estético continua sendo seu.
- **Não valida o que colhe.** Se a fonte mente, o corpus reproduz a mentira fielmente. A skill `playbook-de-corpus` traz a disciplina de marcar `[alegação da fonte]` justamente por isso.

Detalhes de autenticação, limites de volume e o que quebra em cada ferramenta: [`docs/LIMITES.md`](docs/LIMITES.md).

---

## Cuidado com bloqueio

O Instagram bloqueia por volume, e o bloqueio cai **na conta que emprestou o cookie**. O `ig` já espaça as requisições em 7–12 segundos. Não baixe esse valor. 30 a 60 posts por sessão é confortável; centenas de uma vez, não. Se começar a dar erro, pare e espere horas — não minutos.

---

## Licença e uso

Ferramenta de pesquisa e análise de conteúdo público. Respeite os termos de uso das plataformas, a lei de direito autoral e a LGPD: colher conteúdo público para estudo é uma coisa, redistribuir obra de terceiro é outra.
