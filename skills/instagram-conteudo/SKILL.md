---
name: instagram-conteudo
description: "Ler o conteúdo de um perfil do Instagram — posts, reels, vídeos, legendas, hashtags e métricas de engajamento — e transformar em corpus de texto analisável. Use quando pedirem 'analisa esse Instagram', 'extrai o conteúdo desse perfil', 'quais posts performam melhor', 'estuda a comunicação do @fulano', 'baixa esses reels', ou quando alguém quiser criar playbook, dossiê, carrossel ou conteúdo em cima do que um perfil publica."
---

# Conteúdo do Instagram

Colhe o que um perfil publica e devolve **texto que dá para ler, citar e ranquear** — mais os arquivos de vídeo, que seguem para a skill `assistir-video` quando o conteúdo estiver na imagem e não na legenda.

## O que muda tudo: o Instagram exige sessão

Desde 2025 não existe leitura anônima. Testado em 17/08/2026:

| Caminho | Resultado |
|---|---|
| `yt-dlp` num perfil | **quebrado** — o extractor `instagram:user` está marcado *CURRENTLY BROKEN* no próprio yt-dlp |
| `yt-dlp` num post | exige `--cookies-from-browser` |
| `instaloader` anônimo | **400 Bad Request** na API de perfil |
| `instaloader` com cookie | loga, mas o endpoint `web_profile_info` segue quebrado contra a API atual |
| **`gallery-dl` com cookie do navegador** | **funciona** — feed, legendas, métricas e mídia |

`gallery-dl` é a ferramenta. Os cookies saem do navegador de quem está rodando; nenhuma senha é digitada, guardada ou pedida.

## Ferramenta

```bash
ig sessao                              # testa se a sessão do navegador responde
ig colher <@perfil|url> [--n N]        # posts + legendas + métricas -> corpus.md + ranking.md
           [--com-midia] [--saida DIR]
ig baixar <url|@perfil> [--n N]        # baixa a mídia (para assistir reels)
ig indice <pasta>                      # remonta corpus.md e ranking.md
ig videos <pasta>                      # lista os vídeos baixados, com o caminho
```

Cache padrão: `~/.cache/instagram-conteudo/<perfil>/`. Navegador: `IG_BROWSER` (padrão `chrome`; aceita `firefox`, `safari`, `edge`, `brave`).

**Comece sempre por `ig sessao`.** Se ela falhar, todo o resto falha com erro confuso — a causa quase sempre é sessão expirada, e a correção é abrir o Instagram no navegador e logar.

## Protocolo

### 1. Colher o texto primeiro
```bash
ig colher @perfil --n 60
```
Gera dois arquivos:
- **`corpus.md`** — cada post com data, tipo, curtidas, link, legenda completa e hashtags. É o que você lê.
- **`ranking.md`** — os mesmos posts ordenados por engajamento. É onde se enxerga o padrão do que funciona.

Legenda de Instagram é densa: gancho, corpo e CTA num bloco só. Muitas vezes o corpus já responde a pergunta sem baixar um byte de vídeo.

### 2. Ler o ranking antes do corpus
O ranking responde "o que performa" em trinta segundos. Compare os cinco melhores com os cinco piores e o padrão aparece — formato, gancho, tema, presença de CTA.

**Cuidado ao interpretar:** post antigo teve mais tempo para acumular curtida, e um post de ontem com 87 curtidas pode estar performando melhor que um de um ano atrás com 400. Olhe a data junto do número, sempre.

### 3. Só então assistir os vídeos
```bash
ig colher @perfil --n 30 --com-midia
ig videos ~/.cache/instagram-conteudo/perfil     # pega o caminho do .mp4
vid prep <caminho.mp4> reel-01                   # segue na skill assistir-video
vid frames reel-01 --cada 3 && vid folhas reel-01
```
Reel curto pede amostragem densa (`--cada 2` ou `--cada 3`): são 30 a 60 segundos e a informação está na legenda gravada na tela, não na fala.

**Quando vale assistir:** reel com texto na tela, before/after, demonstração de produto, print de resultado. **Quando não vale:** post de foto com legenda longa — a legenda já é o conteúdo.

### 4. Produzir
Com corpus + ranking + o que se viu nos reels, siga para a skill `playbook-de-corpus`: playbook, dossiê de concorrente, carrossel, roteiro, PDF.

## Ritmo e bloqueio

O `ig` já espaça as requisições em 7 a 12 segundos (`IG_SLEEP`). **Não baixe esse valor.** O Instagram bloqueia por volume e o bloqueio cai sobre a conta que emprestou o cookie — a sua, ou a do seu colega.

Regras práticas:
- 30 a 60 posts por sessão é confortável. Centenas de uma vez, não.
- Se começar a vir erro, **pare** e espere horas, não minutos.
- Perfil privado só abre se a conta logada já seguir aquele perfil.
- Rode `ig colher` de novo mais tarde: ele reaproveita o que já baixou.

## Limites honestos

- **Não traz comentários.** O corpus tem legenda e curtidas; comentário exigiria outra rota e muito mais requisição.
- **Curtidas podem vir zeradas** em alguns perfis que ocultam a contagem. O campo existe mas vem `0` — não confunda com post sem engajamento.
- **Não traz alcance, salvamentos nem compartilhamentos.** Isso é dado de dono da conta, só via API oficial ou o painel do próprio perfil.
- **`--n` conta itens, não posts.** Um carrossel de 5 imagens gasta 5 itens e vira 1 post no corpus. Peça folgado quando o perfil tiver muitos carrosséis.
- **Story não é coberto** aqui — expira em 24h e exige outra rota.

## Erros que já custaram tempo

- **Interpretar ranking sem olhar a data.** Post velho acumula curtida; comparar cru premia o antigo e esconde o que está funcionando agora.
- **Rodar sem `ig sessao` antes.** O erro que aparece é sobre JSON vazio, e a causa real é login expirado.
- **Baixar mídia de tudo por padrão.** Um perfil de 200 posts vira gigabytes. Colha o texto primeiro; baixe só os vídeos que o ranking apontou.
- **Achar que legenda é tudo.** Em reel de venda, a promessa forte costuma estar *gravada na imagem*, não escrita na legenda — só a folha de contato mostra.
