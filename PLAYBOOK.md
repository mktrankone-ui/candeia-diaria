# Candeia Diária — Playbook

Manual que as tarefas automáticas seguem. Leia inteiro antes de produzir ou analisar.

## Objetivo

Crescer @candeiadiaria (Instagram e TikTok) com muitos seguidores, monetizar e, depois, usar os canais para vender a esse público. Cada vídeo precisa transmitir **paz**, ajudar quem precisa de oração e gerar comentários ("Amém"), salvamentos e compartilhamentos.

## Linha editorial — fé católica

O dono do perfil é **católico**. Todo conteúdo segue a fé e a teologia católica; na dúvida, a referência é o **Catecismo da Igreja Católica**.

- Bíblia católica (73 livros): pode usar também Sabedoria, Eclesiástico, Tobias, Judite, Baruc e Macabeus.
- Devoções bem-vindas: Nossa Senhora (sob seus títulos: Aparecida, das Graças, Desatadora dos Nós, de Fátima…), terço, Santo Anjo da Guarda, Sagrado Coração de Jesus, Espírito Santo, São José, São Miguel, santos do dia, Eucaristia, Adoração.
- Linguagem acolhedora, simples, de quem reza junto. Jesus, Maria e os santos com reverência.
- Use o calendário litúrgico quando fizer sentido (Advento, Natal, Quaresma, Páscoa, festas marianas, santos populares). Ex.: 2/11 Finados, 8/12 Imaculada Conceição, 12/10 Aparecida.

### Nunca

- Inventar frases e atribuí-las a Jesus, Maria, santos ou papas. Mensagens "de Nossa Senhora" inventadas também não. Orações **a** Maria, sim.
- Teologia da prosperidade ("digite amém e receba dinheiro"), promessas de milagre, correntes ("se não compartilhar…").
- Prometer cura física. Em ansiedade, depressão, luto e doença, a oração acompanha e conforta; quando couber, incentive procurar ajuda (médico, psicólogo, padre, CVV 188).
- Política, polêmicas, ataques a outras igrejas ou religiões.
- Repetir a mesma passagem bíblica em menos de 30 dias (ver `historico.json`).

### Citações bíblicas (padrão católico)

- Formato católico com vírgula: `João 14,27`, `Filipenses 4,6-7`, `Mateus 11,28`.
- Salmos: numeração hebraica com a grega entre parênteses quando diferirem: `Salmo 23(22),1`, `Salmo 91(90),11`, `Salmo 118(117),24`. Atenção aos versículos deslocados pelo título do salmo nas Bíblias católicas (ex.: `Salmo 4,9`, não 4:8).
- Na dúvida sobre o número exato, confira numa Bíblia católica online antes de usar.

### Direitos autorais

- Orações tradicionais são de domínio público e podem ser usadas inteiras: Pai-Nosso, Ave-Maria, Glória, Santo Anjo, Salve Rainha, Credo, Magnificat, Oração de São Francisco, Lembrai-vos (Memorare), Vinde Espírito Santo.
- Traduções católicas modernas da Bíblia (CNBB, Ave-Maria, Jerusalém, Pastoral) têm direitos. Para versículos, use uma frase curta ou uma paráfrase fiel e sempre a referência no campo `referencia`.
- Liturgia diária e Evangelho do dia: cite a referência e escreva uma reflexão própria; não copie o texto litúrgico.

## Banco de temas (explore infinitas possibilidades)

Varie sempre. Junte passagens bíblicas bonitas com textos originais que acolham quem precisa de oração.

**Manhã (bom dia, 08:00)** — tema leve e luminoso:
gratidão pelo novo dia · entregar o dia a Deus · oferecimento do dia · proteção ao sair de casa · trabalho e sustento · emprego · estudos e provas · família · filhos · marido/esposa · casamento · amigos · decisões importantes · força para recomeçar · esperança · coragem · fé que move montanhas · "Leão de Judá" (força) · Santo Anjo da Guarda · consagração a Nossa Senhora · Espírito Santo · Salmo do dia (Sl 23, 27, 91, 121, 139, 46, 34, 103, 62, 118) · santo do dia · domingo: alegria da ressurreição e missa.

**Noite (20:30)** — tema emocional e de cura:
ansiedade · medo · insônia e sono tranquilo · cura interior · cura de feridas emocionais · perdão (pedir e dar) · luto e saudade · solidão · tristeza e depressão (com cuidado) · doença na família · pessoa internada · crise no casamento · filho afastado · vícios na família · dívidas e aflição financeira · injustiça · cansaço · noite difícil · entrega das preocupações · exame de consciência · Salve Rainha · terço da noite · Nossa Senhora Desatadora dos Nós · Sagrado Coração · Salmos de confiança (Sl 4, 16, 31, 42, 46, 56, 63, 86, 130, 131).

**Formatos de série** (campo `serie`, curto — vira o título):
Oração da manhã · Oração da noite · Oração contra a ansiedade · Oração pela família · Oração pelos filhos · Oração de cura · Oração pelo trabalho · Salmo do dia · Oração a Nossa Senhora · Oração ao Santo Anjo · Oração de proteção · Oração para dormir em paz · Oração de entrega · Oração do perdão.

## Formato do roteiro (`roteiros/<id>.json`)

```json
{
  "id": "oracao-manha-02",
  "serie": "Oração da manhã",
  "tema": "amanhecer",
  "trilha_tema": "amanhecer",
  "fundo": "fotos",
  "busca": ["sunrise cross", "morning light church", "sunrise field"],
  "linhas": ["Frase com *palavra* em destaque.", "..."],
  "referencia": {"linha": 5, "texto": "Salmos 118:24"},
  "cta": ["Se você crê, escreva *AMÉM*", "Siga para orar todos os dias"],
  "cta_falado": "Se você crê, escreva amém nos comentários.",
  "legenda": "...",
  "slot": "manha",
  "data": "2026-10-30"
}
```

- `id`: `<serie-curta>-<AAAAMMDD>-<manha|noite>`, sem acento. Ex.: `oracao-20261031-noite`.
- `tema` (busca de fundo): amanhecer, gratidao, familia, trabalho, esperanca, forca, fe, nossa_senhora, noite, paz, ansiedade, cura, dificil. Pode trocar por `busca` com 4 a 7 termos em inglês.
- `trilha_tema`: amanhecer, esperanca, noite, paz, dificil, familia (ver `trilhas/lista.json`).
- `fundo`: `fotos` ou `videos`. Alterne.
- `linhas`: 7 a 9 frases curtas (até ~12 palavras), cada uma com **uma** palavra ou expressão entre `*asteriscos*`. A última costuma ser "Em nome de Jesus, *amém*." ou equivalente católico ("Por Cristo, nosso Senhor, *amém*.").
- Primeira frase é o gancho: fala direto com a dor ou o desejo de quem assiste ("Se hoje o seu coração está apertado…").
- `legenda`: 2 a 4 linhas acolhedoras + pedido de "AMÉM" + convite a compartilhar com quem precisa + 6 a 9 hashtags (sempre `#candeiadiaria`; misture amplas como `#oração #fé #Deus #Jesus` com católicas como `#catolico #igrejacatolica #nossasenhora #terço` e do tema).

## Horários

Definidos em `estrategia.json` (`horarios`). Padrão: manhã **08:00**, noite **20:30** (America/Sao_Paulo). Publica **todo dia**, inclusive sábado e domingo.

## Rotina diária de produção (seg a sex, horário comercial)

1. Clonar o repositório (`git clone https://github.com/mktrankone-ui/candeia-diaria`) e ler `PLAYBOOK.md`, `estrategia.json` e `historico.json`.
2. Ver quais datas ainda não têm os dois posts (manhã e noite) agendados: em geral o dia seguinte; na **sexta**, sábado, domingo e segunda. Conferir também no Metricool (`getScheduledPosts`, brand 7738266).
3. Escrever os roteiros que faltam, seguindo a linha editorial e os pesos de `estrategia.json` (temas que performam melhor aparecem mais; os da lista `evitar` não aparecem). Não repetir passagem bíblica dos últimos 30 dias nem o mesmo tema dois dias seguidos no mesmo horário.
4. Commit e push dos roteiros no `main` (isso dispara o workflow **Gerar vídeos**).
5. Acompanhar a execução (`gh api repos/mktrankone-ui/candeia-diaria/actions/runs?per_page=1`) até terminar. Ler `indice.json` e `gerar.log` no ramo `videos`. Se um roteiro falhar, corrigir e disparar de novo só ele (workflow_dispatch com `inputs[roteiros]=<id>`).
6. Agendar no Metricool cada vídeo novo (Reel no Instagram + TikTok), no horário do slot, com a legenda do roteiro e a mídia `https://raw.githubusercontent.com/mktrankone-ui/candeia-diaria/videos/<id>.mp4`. Usar `instagramData: {type: REEL, showReelOnFeed: true, isAiGenerated: true}` e `tiktokData: {privacyOption: PUBLIC_TO_EVERYONE, isAigc: true, title: <serie>}`.
7. Mover os roteiros agendados para `roteiros/publicados/` e registrar em `historico.json` (id, data, slot, serie, tema, referência, trilha, fundo, id do post no Metricool). Commit e push.
8. Relatar em poucas linhas o que foi agendado.

## Análise semanal (toda segunda)

1. Pegar no Metricool as métricas dos últimos 7 dias (e acumulado) por post: alcance/views, curtidas, comentários, compartilhamentos, salvamentos, seguidores ganhos — Instagram e TikTok.
2. Cruzar com `historico.json` (serie, tema, slot, fundo, trilha, duração).
3. Atualizar `estrategia.json`: aumentar o peso do que performa acima da mediana, reduzir o que fica abaixo, colocar em `evitar` o que ficou entre os piores por 2 semanas seguidas. Ajustar horários se os dados mostrarem algo melhor (`getBestTimeToPostByNetwork`).
4. Registrar o resumo em `relatorios/AAAA-MM-DD.md` (o que funcionou, o que não, decisões) e fazer commit.
5. Mandar um resumo curto ao Fernando com números e as mudanças feitas.

## Monetização (próximas etapas)

- TikTok (Creator Rewards) exige vídeos com mais de 1 minuto e 10 mil seguidores: quando chegar perto, produzir versões de 60–75 s (8–10 frases).
- Instagram: bônus/presentes e parcerias.
- Venda para o nicho (terço, livros de oração, produtos católicos, infoproduto): só depois de audiência formada; link na bio.
