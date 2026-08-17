---
name: assistir-video
description: "Fazer o Claude REALMENTE assistir um vídeo — ver a imagem e ouvir o áudio, não só ler a transcrição. Converte vídeo local, YouTube, gravação de tela, aula, reunião ou reel em frames com timestamp, folhas de contato e transcrição alinhada, que é o que o modelo consegue ler. Também varre canais/playlists inteiros. Use quando pedirem 'assiste esse vídeo', 'analisa esse vídeo', 'o que aparece na tela', 'resume essa aula/reunião', 'extrai o conteúdo desse canal', 'transcreve esse vídeo', watch/analyze this video."
---

# Assistir vídeo

O modelo não lê vídeo. Lê **imagem** e **texto**. Esta skill transforma um no outro, com controle explícito de custo.

O erro comum é achar que transcrever é assistir. Transcrição pega a fala e perde tudo que é visual: o que está escrito no slide, o número no dashboard, a expressão de quem fala, o produto que aparece, o erro na tela. Para *assistir* é preciso as duas trilhas — e é preciso saber quanto isso custa em tokens antes de pedir.

## Ferramenta

Um único script, `bin/vid`:

```bash
vid prep   <arquivo|url> [slug]        # ingere, sonda, sugere plano de amostragem
vid ouvir  <slug> [--modelo small]     # áudio -> transcript.md com timestamps
vid frames <slug> [--cada S|--cortes]  # frames com a hora gravada na imagem
vid folhas <slug>                      # folhas de contato (o que o Claude lê)
vid zoom   <slug> <mm:ss ...>          # frame em resolução cheia para ler detalhe
vid clipe  <slug> <ini> <fim>          # recorta trecho como evidência
vid custo  <imagens...>                # estima tokens de visão ANTES de ler
vid varrer <url-canal> [pasta]         # colhe transcrições de canal/playlist inteiro
vid status <slug> | vid ls
```

Adicione ao PATH ou chame direto: `~/.claude/skills/assistir-video/bin/vid`

Workdir padrão: `~/.cache/assistir-video/<slug>/` (mude com `VIDEO_HOME`). Reaproveita o que já foi feito — rodar de novo não re-baixa nem re-transcreve.

Dependências: `ffmpeg`, `ffprobe`, `jq`, `python3`; `yt-dlp` para URL; `whisper` só quando não há legenda.

## O protocolo — 5 passagens

Siga nesta ordem. Cada passagem é mais cara que a anterior; a maioria das perguntas se responde na 2ª ou 3ª.

### 1. Ficha técnica (custo zero)
```bash
vid prep "https://youtube.com/watch?v=..."
```
Devolve duração, resolução, fps, se tem áudio, e o **plano de amostragem sugerido**. Leia isso antes de decidir qualquer coisa: um vídeo de 3 min e um de 3 h pedem estratégias opostas.

### 2. Ouvir (barato, altíssima densidade)
```bash
vid ouvir <slug>
```
A fala é a espinha narrativa e custa quase nada em tokens comparada a imagem. **Faça sempre primeiro.** Muitas vezes já responde a pergunta e as passagens visuais viram desnecessárias.

Ordem de fontes, da melhor para a pior:
1. **Legenda do YouTube** (`vid varrer` ou `yt-dlp --write-auto-sub --sub-lang pt-orig --sub-format json3`) — instantânea, grátis, boa qualidade. Sempre tente isto primeiro em conteúdo do YouTube.
2. **ElevenLabs MCP** `speech_to_text` — rápido e com diarização (`diarize: true`) quando importa saber *quem* falou. Custa créditos: só com autorização explícita.
3. **whisper local** — grátis e offline, mas lento: medido em **~0,6× tempo real** com modelo `small` num Mac M-series. Uma hora de áudio leva perto de uma hora. Dispare em background e siga trabalhando.

### 3. Folhear (a passagem visual principal)
```bash
vid frames <slug>          # usa o plano sugerido
vid folhas <slug>          # monta as folhas e já imprime o custo
```
Frames viram **folhas de contato**: grades 3×4 com a hora gravada em cada quadro. Você lê as folhas com o Read e localiza os momentos que importam.

Por que grade em vez de frames soltos: 12 frames separados custam ~1.400 tokens **cada**. A mesma dúzia numa folha custa ~2.400 tokens **no total** — cerca de 200 por frame, 7× mais barato. Você perde resolução fina, que é exatamente o que a passagem seguinte recupera.

### 4. Encarar (caro, cirúrgico)
```bash
vid zoom <slug> 12:34 47:10
```
Resolução cheia, só nos instantes que a folha indicou. É aqui que se lê texto de slide, número de dashboard, código na tela, letra miúda. Nunca faça isso em varredura — só em alvo já localizado.

### 5. Relatar
Escreva com **timestamps**. Um achado sem `[mm:ss]` não é verificável e não serve para nada. Cruze o que a imagem mostra com o que o áudio diz: divergência entre as duas trilhas costuma ser o achado mais interessante.

## Orçamento de tokens

A conta da API: `tokens ≈ (largura × altura) / 750`, depois de reduzir o maior lado para 1568px.

| O que | Custo aproximado |
|---|---|
| 1 folha de contato (12 frames, 1560×1172) | ~2.400 tokens |
| 1 frame em zoom (1568×880) | ~1.800 tokens |
| 1 hora de transcrição (~9k palavras) | ~13.000 tokens |
| Vídeo de 1 h, varredura completa | ~5 folhas (~12k) + transcrição (~13k) = **~25k** |

`vid custo <imagens>` calcula antes de você ler. **Rode isso antes de dar Read em lote de imagem** — é a diferença entre gastar 20k e 200k tokens sem perceber.

Padrões de amostragem por duração (o `prep` já aplica):

| Duração | Intervalo | Frames | Folhas |
|---|---|---|---|
| ≤ 5 min | 10 s | ~30 | 3 |
| 5–20 min | 20 s | ~60 | 5 |
| 20–60 min | 45 s | ~80 | 7 |
| > 60 min | 90 s | teto de 120 | 10 |

`--cortes` troca amostragem uniforme por detecção de corte de cena — melhor para vídeo editado (reel, comercial, aula com slides), pior para plano fixo contínuo (palestra, reunião), onde não há corte para detectar.

## Varrer um canal inteiro

```bash
vid varrer "https://www.youtube.com/@canal/videos" ./transcricoes
```
Baixa a legenda original de cada vídeo e converte em markdown com timestamps. Pula o que já existe, então é seguro repetir. Para shorts, troque `/videos` por `/shorts`.

O que fazer quando falha:
- **"has no automatic captions"** → não existe legenda. Baixe o áudio (`yt-dlp -f ba -x --audio-format m4a`) e caia para whisper. Vale checar se o custo se justifica antes.
- **Legendas em dezenas de idiomas** → use sempre `pt-orig` (a faixa original), não `pt`, que pode ser tradução automática de outra língua.

## Receitas

**Gravação de tela / demo de produto** — `--cortes` não ajuda (tela muda continuamente sem corte). Use `--cada 15` e vá de zoom nos momentos de erro ou de tela cheia de texto. O que importa quase sempre está escrito, não falado.

**Aula com slides** — `--cortes` funciona bem: cada troca de slide é um corte. A folha de contato vira praticamente o índice da aula.

**Reunião gravada** — priorize áudio com diarização. Visual só se houver tela compartilhada; nesse caso, `--cada 60` já basta para pegar as trocas de tela.

**Reel / anúncio** — curto e denso. `--cada 2` ou `--cortes`, e leia todos os frames. Aqui o custo não é problema e o detalhe visual é o conteúdo.

**Vídeo longo com pergunta específica** — não assista tudo. Transcreva, faça `grep` do termo na transcrição, e dê `vid zoom` só nos timestamps que o grep devolveu.

**Vídeo sem fala** — pule `ouvir`. Aumente a densidade de frames, porque toda a informação está na imagem.

## Erros que já custaram caro

- **Ler 100 frames soltos.** ~140k tokens para o que 8 folhas resolvem por ~20k. Sempre folha antes de frame solto.
- **Transcrever com whisper sem checar legenda.** Uma hora de processamento para algo que o `yt-dlp` entrega em 3 segundos.
- **Usar a faixa `pt` em vez de `pt-orig`.** Você acaba lendo uma retradução do português para o português, com perda.
- **Relatar sem timestamp.** O achado fica não-verificável e o usuário não consegue conferir.
- **Confiar em legenda automática ao pé da letra.** O ASR erra nomes e termos técnicos ("cérebro"→"célebro", "leads"→"lids"). Para citação que vai ser publicada, confira no vídeo pelo timestamp.
- **Rodar detecção de cena em vídeo de 2 h sem necessidade.** Decodifica o arquivo inteiro. Em plano fixo, amostragem uniforme dá o mesmo resultado em segundos.
