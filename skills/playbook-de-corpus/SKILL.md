---
name: playbook-de-corpus
description: "Transformar um corpus colhido (transcrições de vídeo, posts de Instagram, artigos) em entregável — playbook, dossiê, deck de vendas, relatório — com cada afirmação rastreável à fonte, e exportar em PDF. Use quando pedirem 'monta um playbook em cima disso', 'cria um dossiê desse concorrente', 'vira um deck', 'gera o PDF', 'destila esse conteúdo', ou depois de rodar assistir-video / instagram-conteudo."
---

# Playbook a partir de um corpus

Colher é metade. A outra metade é destilar sem inventar — e o modo de errar aqui é caro: um playbook bonito cheio de afirmação que a fonte nunca fez parece mais confiável do que é.

## A regra que sustenta o resto

**Toda afirmação carrega sua fonte.** Vídeo + timestamp, ou post + data. Sem isso, o leitor não consegue conferir, e você não consegue defender.

Três marcações que fazem o documento honesto:

| Marcação | Quando usar |
|---|---|
| citação direta + `[timestamp]` | você está reproduzindo o que a fonte disse |
| **[alegação da fonte]** | a fonte afirma um dado sem apresentar origem — percentual de mercado, resultado de case, "uma pesquisa mostrou" |
| **[síntese]** | a estrutura é sua, derivada do material, não uma fala literal |

Sem a segunda marcação, você lava a reputação de um número inventado com a sua credibilidade. É o erro mais comum e o mais difícil de desfazer.

## Ferramenta

```bash
pb pdf <arquivo.md> [saida.pdf] [--modo doc|deck] [--acento "#B4472B"] [--guardar-html]
```

- `--modo doc` (padrão): A4, para playbook, dossiê, relatório.
- `--modo deck`: slides 16:9; **cada `---` do markdown vira um slide**.
- `--acento`: cor de destaque — escolha uma que combine com o assunto, não deixe no padrão por preguiça.

O PDF sai do motor de impressão do Chrome, então o texto continua selecionável e a tipografia não vira bitmap. Nunca gere PDF por screenshot ou html2canvas: some a busca, o copiar-colar e a nitidez.

## Processo

### 1. Inventariar antes de ler
Quantos itens, que tamanho, quanto de texto. Isso decide se você lê tudo ou faz varredura dirigida.

```bash
for f in transcricoes/*.md; do printf "%6sw  %s\n" "$(wc -w < "$f")" "$(head -1 "$f")"; done | sort -rn
```

### 2. Ler o núcleo, varrer o resto
Leia integralmente os itens centrais do tema. Para o resto, **varra por conceito** em vez de ler tudo:

```bash
for t in "objeção" "preço" "recompra" "funil"; do
  printf "%-12s %s\n" "$t" "$(grep -ril "$t" *.md | tr '\n' ' ')"
done
```

Isso encontra o que você não sabia procurar e evita construir o documento só com o que leu primeiro — o viés mais comum nesse trabalho.

### 3. Achar a estrutura no material, não no template
Um playbook genérico tem "introdução, desenvolvimento, conclusão". Um playbook útil tem a estrutura que o próprio material revela: se a fonte organiza tudo em torno de quatro pilares, o documento tem quatro pilares.

Camadas que costumam funcionar: **diagnóstico** (onde dói) → **sistema** (como funciona) → **execução** (o que fazer segunda-feira).

### 4. Escrever com matemática trabalhada
Onde a fonte dá números, refaça a conta e mostre o passo a passo. Uma cadeia de cálculo com exemplo real vale mais que dez parágrafos de conceito — é o que o leitor consegue aplicar no negócio dele.

### 5. Fechar com índice de fontes e nota de método
- **Índice de fontes**: id, título, duração/data, tamanho. Separe o que foi lido integralmente do que foi varrido.
- **Nota de método**: como foi colhido, o que pode estar errado (ASR erra vocabulário técnico), e o que o documento **não é**. Se parte do corpus é peça de venda, diga — muda como o leitor pesa o conteúdo.

### 6. Exportar
```bash
pb pdf playbook.md --modo doc --acento "#B4472B"
```

## Formatos além do playbook

| Pedido | Forma |
|---|---|
| **Dossiê de concorrente** | posicionamento, oferta, temas recorrentes, o que performa, brechas |
| **Deck de vendas** | `--modo deck`, um argumento por slide, `---` entre eles |
| **Carrossel** | 8–10 blocos: gancho, tensão, virada, prova, CTA |
| **Roteiro** | gancho nos 3 primeiros segundos, uma ideia só, CTA no fim |
| **Régua de conteúdo** | temas × formatos × frequência, tirados do que já funciona no corpus |

## Erros que já custaram caro

- **Reproduzir número da fonte como fato.** "90% das empresas não faturam 1M/ano" pode ser retórica. Marque como alegação.
- **Construir só com o que leu primeiro.** Sem a varredura por conceito, o documento vira resumo dos maiores arquivos.
- **Deck com `##` em vez de `---`.** O modo deck quebra em `---`; sem isso sai tudo num slide só.
- **Não dizer que parte do corpus é peça de venda.** Sem esse aviso, o leitor toma promessa de VSL por conclusão de pesquisa.
- **Gerar PDF por screenshot.** Perde texto selecionável, busca e nitidez. O `pb` usa o motor de impressão justamente para não cair nisso.
