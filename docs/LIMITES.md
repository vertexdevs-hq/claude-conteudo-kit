# Limites, autenticação e o que quebra

Tudo aqui foi testado em **17/08/2026**, macOS (Apple Silicon). Plataforma muda; se algo parar de funcionar, comece por esta página.

---

## YouTube

### O que funciona sem autenticação

Legenda automática e download de vídeo funcionam anônimos. É o caminho barato e deve ser sempre o primeiro.

```bash
yt-dlp --write-auto-sub --sub-lang pt-orig --sub-format json3 --skip-download <url>
```

### Peça `pt-orig`, nunca `pt`

O YouTube oferece legenda automática em dezenas de idiomas — quase todas **traduções automáticas** da faixa original. Pedir `pt` num vídeo em português pode devolver uma retradução do próprio português, com perda de sentido.

`pt-orig` é a faixa original. É a única que vale.

### `json3` em vez de `vtt`

O `vtt` de legenda automática vem com linhas rolantes duplicadas — cada frase aparece duas ou três vezes em quadros sucessivos. O `json3` traz timing por palavra e limpa direto.

### Quando não existe legenda

Alguns vídeos simplesmente não têm. O diagnóstico é claro:

```
$ yt-dlp --list-subs <url>
<id> has no automatic captions
```

Aí só resta transcrição local (whisper). **Meça o custo antes:** whisper `small` roda a ~**0,6× tempo real** num Mac M-series — 16 minutos de áudio levam 10,5 minutos; uma hora de vídeo leva perto de uma hora. Sempre em background.

### ASR erra vocabulário técnico

Tanto a legenda do YouTube quanto o whisper erram de forma sistemática em nome próprio e jargão: *cérebro* → "célebro", *leads* → "lids", *Hormozi* → "ormos". Para citação que vai ser publicada, confira no vídeo pelo timestamp.

---

## Instagram

### Não existe leitura anônima

Testado, com o resultado de cada caminho:

| Caminho | Resultado em 17/08/2026 |
|---|---|
| `yt-dlp` num perfil | **quebrado** — o próprio yt-dlp marca `instagram:user` como *CURRENTLY BROKEN* |
| `yt-dlp` num post único | exige `--cookies-from-browser` |
| `instaloader` anônimo | **400 Bad Request** na API de perfil |
| `instaloader` com cookie | loga com sucesso, mas o endpoint `web_profile_info` segue quebrado contra a API atual |
| **`gallery-dl` com cookie do navegador** | **funciona** — feed, legendas, métricas e mídia |

Por isso o kit usa `gallery-dl`. Se ele quebrar um dia, o teste diagnóstico é este:

```bash
gallery-dl --cookies-from-browser chrome --simulate --range 1-3 -v "https://www.instagram.com/instagram/"
```

### Como a sessão funciona

Os cookies são lidos do navegador local. No macOS isso passa pelo Keychain (o sistema pode pedir autorização na primeira vez).

- Nenhuma senha é digitada, pedida ou gravada pelo kit.
- Troque de navegador com `IG_BROWSER=firefox|safari|edge|brave`.
- Sessão expira. Quando expirar, o erro aparece como "nada colhido" ou JSON vazio — a correção é abrir o Instagram no navegador e logar.

> **Nota sobre o instaloader:** se você chegar a rodá-lo com `--load-cookies`, ele grava um arquivo de sessão em `~/.config/instaloader/session-<usuario>`. É a sua sessão autenticada em disco. Apague se não for usar.

### Bloqueio por volume

O bloqueio cai **na conta que emprestou o cookie**, não na ferramenta.

- O `ig` espaça requisições em **7–12 segundos** (`IG_SLEEP`). Não baixe isso.
- 30 a 60 posts por sessão é confortável.
- Erros em sequência = pare e espere **horas**, não minutos.
- `ig colher` reaproveita o que já baixou; rodar de novo mais tarde é barato.

### O que o Instagram entrega e o que não entrega

**Entrega:** legenda completa, curtidas, data, link, hashtags, usuários marcados, coautores, título e artista do áudio do reel, e a mídia.

**Não entrega:**
- **Comentários** — exigiria outra rota e muito mais requisição.
- **Alcance, salvamentos, compartilhamentos** — dado de dono da conta, só via API oficial ou o painel do perfil.
- **Stories** — expiram em 24h, rota diferente.
- **Perfil privado** que a conta logada não segue.

**Curtidas podem vir `0`** em perfis que ocultam a contagem. O campo existe e vem zerado — não confunda com post sem engajamento.

**`--n` conta itens, não posts.** Um carrossel de 5 imagens gasta 5 itens e vira 1 post no corpus. Peça folgado em perfis com muito carrossel.

---

## Custo em tokens

A conta da API: `tokens ≈ (largura × altura) / 750`, depois de reduzir o maior lado para 1568px.

| O que | Custo aproximado |
|---|---|
| 1 folha de contato (12 frames) | ~2.400 tokens |
| 1 frame em resolução cheia | ~1.800 tokens |
| 1 hora de transcrição (~9k palavras) | ~13.000 tokens |
| **Vídeo de 1 h, varredura completa** | **~25.000 tokens** |
| 12 frames soltos (o jeito errado) | **~17.000 tokens** |

`vid custo <imagens>` calcula antes de você ler. Rode isso antes de dar Read em lote — é a diferença entre gastar 20k e 200k tokens sem perceber.

### Amostragem por duração

| Duração | Intervalo | Frames | Folhas |
|---|---|---|---|
| ≤ 5 min | 10 s | ~30 | 3 |
| 5–20 min | 20 s | ~60 | 5 |
| 20–60 min | 45 s | ~80 | 7 |
| > 60 min | 90 s | teto de 120 | 10 |

`--cortes` (detecção de cena) serve para vídeo editado — reel, comercial, aula com slides. Em plano fixo contínuo (palestra, reunião) não há corte para detectar e ele decodifica o arquivo inteiro à toa.

---

## ffmpeg sem `drawtext`

O ffmpeg do Homebrew (8.0.1_4) vem **sem libfreetype**. Diagnóstico:

```bash
ffmpeg -filters | grep drawtext     # volta vazio
ffmpeg -version | grep freetype     # volta vazio
```

Sem `drawtext` não dá para gravar a hora dentro do frame, e folha de contato sem hora é um mosaico que o modelo não consegue referenciar. O kit resolve desenhando o rótulo com **Pillow**, o que também dá controle de fonte e margem. Não é preciso recompilar ffmpeg.

## Grade da folha de contato

A API reduz o maior lado da imagem para 1568px. Uma grade fixa 3×4 num vídeo **vertical** (9:16) gera folha de 1584×3726 → reduzida a 667px de largura → quadros ilegíveis.

O kit escolhe automaticamente `cols × rows` que deixem a folha **o mais quadrada possível** e reduz a folha para 1568 no maior lado antes de salvar. Assim o resultado é previsível em vez de ser refeito pela API.

---

## PDF

Gerado pelo **motor de impressão do Chrome** (`--print-to-pdf`), não por screenshot. O texto continua selecionável e buscável, e a tipografia não vira bitmap.

Nunca use html2canvas ou captura de tela para gerar PDF de documento: perde busca, copiar-colar e nitidez.

O modo `--modo deck` quebra os slides em `---` (regra horizontal do markdown). Sem `---` no arquivo, sai tudo num slide só.

---

## App de desktop e PATH

O Claude Code roda os comandos na máquina local em todas as superfícies (terminal, app de desktop, extensão de IDE). O que muda é o **ambiente herdado**.

Aplicativo lançado pela interface gráfica no macOS não lê `.zshrc`/`.bash_profile`. Resultado com PATH mínimo, antes do tratamento:

```
$ env -i PATH="/usr/bin:/bin:/usr/sbin:/sbin" bash -c 'command -v ffmpeg yt-dlp uv gallery-dl'
(nada)
```

Os três scripts prefixam o PATH na inicialização:

```
/opt/homebrew/bin  →  Homebrew (Apple Silicon)
~/.local/bin       →  ferramentas do uv e pipx (gallery-dl mora aqui)
/usr/local/bin     →  Homebrew (Intel)
/opt/local/bin     →  MacPorts
~/.cargo/bin       →  Rust
/home/linuxbrew/.linuxbrew/bin
```

**A ordem importa.** Numa primeira versão o loop prefixava um por um, o que invertia a precedência: `/usr/local/bin` acabava na frente de `/opt/homebrew/bin`, e `python3` resolvia para um interpretador **sem Pillow**. O diagnóstico enganava — dizia "Pillow FALTA" numa máquina onde o Pillow estava instalado, só que em outro Python.

Por isso existe `escolher_python()`: ele não aceita o primeiro `python3` do PATH, testa `import PIL` e usa o que passar.

Diagnóstico: `vid doctor` mostra o PATH efetivo, onde cada ferramenta foi encontrada e qual Python está sendo usado para o Pillow.

## Windows

Os scripts são bash. No Windows é preciso **WSL**, com o kit instalado dentro dele.

O `frames_tool.py` já procura fonte em `C:/Windows/Fonts` (arialbd, segoeuib, arial), então o rótulo de tempo funciona se alguém rodar o Python nativamente. Mas `install.sh` só conhece `brew` e `apt`, e os três executáveis são shell script — sem WSL ou Git Bash, não rodam.

## Claude Code na web

Não funciona, e a razão é estrutural: não existe máquina local com ffmpeg instalado nem navegador logado no Instagram para emprestar cookie. Este kit é local por natureza.
