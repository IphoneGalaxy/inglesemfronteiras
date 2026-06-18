# EnglishFlow — Landing Page

> **Conceito:** "Stars & Messages" — Tech-first, conversacional, limpo como o Telegram.
> **Site:** Landing page estática para venda de cursos de inglês com professores nativos via Telegram.

---

## Sobre o Projeto

EnglishFlow conecta brasileiros a professores americanos nativos diretamente pelo Telegram. Sem apps novos, sem burocracia — o aprendizado acontece onde você já está.

**Tech Stack:** HTML5 + CSS3 (BEM, Custom Properties) + Vanilla JS | Zero frameworks | Zero dependências

---

## Bot Telegram — Conceito

O bot do Telegram (`@englishflow_bot`) é a peça central da operação. Abaixo, o conceito completo para implementação futura.

### Comandos Principais

| Comando | Descrição |
|---------|-----------|
| `/start` | Menu principal com teclado inline (Agendar, Professores, Planos, Minhas Aulas) |
| `/agendar` | Inicia fluxo de agendamento de aula |
| `/professores` | Lista professores disponíveis com inline keyboard |
| `/planos` | Mostra planos com opção de checkout |
| `/minhasaulas` | Próximas aulas agendadas + histórico |
| `/reagendar` | Menu de reagendamento de aula |
| `/cancelar` | Cancelamento com confirmação |
| `/ajuda` | FAQ e suporte |

### Fluxo de Agendamento

```
1. /agendar → Bot envia inline keyboard com perfis dos professores:
   ┌─────────────────────────────┐
   │ 👩‍💼 Sarah J. — Business Eng  │
   │ 🧔 Michael T. — Conversação  │
   │ 👩‍🏫 Emily P. — Preparatório   │
   │ 🧑‍💻 David C. — Viagem         │
   └─────────────────────────────┘

2. Após escolher → Calendário inline (próximos 14 dias)

3. Seleção de slot → Confirmação:
   "✅ Agendado! Sarah Johnson · 20/06 às 19:00 BRT"

4. Lembretes automáticos:
   - 24h antes: "🔔 Você tem aula amanhã com Sarah às 19h!"
   - 1h antes: "⏰ Sua aula começa em 1 hora!"
   - 15min antes: "🚀 Sarah está online! Clique para entrar."
```

### Funcionalidades Avançadas (Conceito)

- **Onboarding conversacional:** Bot faz perguntas (nível, objetivo, disponibilidade) e sugere professores
- **Quiz diagnóstico:** 5 perguntas rápidas para avaliar nível (A1→C2)
- **Daily Vocabulary Push:** Mensagem matinal 7h com frase do dia + áudio do professor
- **Voice Notes:** Professores enviam áudios curtos para prática de listening
- **Reações:** Aluno avalia aula com ⭐ (1-5) via inline keyboard
- **Gamificação:** Níveis (Tourist → Business → Native Soul), badges, streak de dias consecutivos
- **Indicação:** `/indicar` gera link personalizado com 1 aula grátis para indicado e indicador

### Stack Sugerida para o Bot

| Camada | Recomendação |
|--------|-------------|
| Linguagem | **Node.js** com **Grammy.js** (ou Python com python-telegram-bot) |
| Hospedagem | **Railway** (grátis) ou **Render** |
| Banco | **Supabase** (Postgres + Auth + Realtime) |
| Agendamento | **Cal.com API** (open source) ou nativo no bot |
| Pagamento | **Kiwify** ou **Stripe** |

---

## Estrutura do Projeto

```
TelegramBot/
├── index.html              # Landing page principal
├── privacidade.html        # Política de privacidade (LGPD)
├── 404.html                # Página de erro personalizada
├── README.md               # Este arquivo
├── docs/
│   └── plans/
│       └── PLANO-telegram-english-bot.md
└── assets/
    ├── css/
    │   └── style.css       # Estilos (BEM + Custom Properties + Dark Mode)
    ├── js/
    │   └── main.js         # Animações e interações
    ├── fonts/              # Fontes self-hosted (woff2)
    └── img/                # Imagens e favicons
```

---

## Funcionalidades do Site

- ✅ 10 seções (Hero, Chat Demo, Professores, Como Funciona, Planos, Depoimentos, FAQ, CTA Final, Footer)
- ✅ Dark/Light mode com toggle + `prefers-color-scheme`
- ✅ Chat demo interativo (5 perguntas sugeridas + input livre)
- ✅ Typing effect no headline
- ✅ Count-up animado no badge
- ✅ Emoji particles no background do hero
- ✅ FAQ com busca em tempo real
- ✅ Scroll reveal animations (Intersection Observer)
- ✅ `prefers-reduced-motion` respeitado
- ✅ Acessibilidade: ARIA roles, focus-visible, semantic HTML, `lang="pt-BR"`
- ✅ SEO: Open Graph, Twitter Card, JSON-LD Schema.org, meta tags
- ✅ Responsivo: 320px–1920px
- ✅ PWA-ready: manifest, theme-color, apple-mobile-web-app

---

## Como Rodar Localmente

1. Clone o repositório
2. Abra `index.html` no navegador
3. Pronto! Zero dependências, zero build step.

```bash
# Ou com qualquer servidor estático:
npx serve .
# ou
python -m http.server 8080
```

---

## Deploy

- **GitHub Pages:** Push para branch `main` (ou `gh-pages`)
- **Netlify:** Arrasta a pasta `TelegramBot/` para o dashboard
- **Vercel:** `vercel` no diretório raiz

---

## Como Rodar o Bot

```bash
# Instalar dependências
pip install python-telegram-bot qrcode[pil] crcmod

# Rodar o bot (token já configurado em bot.py)
python bot.py
```

O bot ficará online e responderá comandos no Telegram.

**Comandos implementados:**
| Comando | Função |
|---------|--------|
| `/start` | Menu principal com teclado inline |
| `/agendar` | Fluxo de agendamento (professor → dia → horário) |
| `/professores` | Lista professores com avaliações |
| `/planos` | Planos e preços → PIX com QR Code |
| `/minhasaulas` | Aulas agendadas |
| `/ajuda` | FAQ e comandos |

**Pagamento PIX:**
- Usuário escolhe plano → bot gera QR Code + código copia-e-cola
- Pagamento via PIX para chave `guilhermenduwe@gmail.com`
- Usuário envia comprovante por foto
- Valores: Básico R$30 | Pro R$55 | Premium R$80

## TODO

- [x] Substituir `https://t.me/seubot` pelo handle real @inglesemfronteiras_bot
- [x] Gerar favicon PNGs (32, 180, 512)
- [x] Implementar bot Telegram funcional com todos os comandos
- [ ] Adicionar analytics (Plausible/Umami) se necessário
- [ ] Implementar self-host de fontes (woff2) para produção
- [ ] Testar cross-browser (Chrome, Firefox, Safari, Edge)
- [ ] Auditoria Lighthouse (meta: 90+)

---

## Licença

Projeto privado — EnglishFlow © 2026
