# PLANO — Telegram English Landing (Stars & Messages)

> Revisado por GLM 5.2 (review subagent) em 17/06/2026

## Contexto

- **Objetivo:** Landing page estática para venda de cursos de inglês com professores nativos que conectam via Telegram com horário marcado
- **Repo:** `projetos locais/TelegramBot/`
- **Restrições:** HTML/CSS/JS puro · sem backend · sem pagamento · sem login · bot Telegram apenas conceitual
- **Conceito:** "Stars & Messages" — Tech-first, conversacional, limpo como o app Telegram

| Decisão | Escolha |
|---------|---------|
| Contador | Exibido com disclaimer "valores ilustrativos" |
| README do bot | Sim — descrevendo comandos e fluxo conceitual |
| CTA Telegram | Placeholder `t.me/inglesemfronteiras_bot` com `<!-- TODO -->` |

## Paleta de Cores

| Cor | Hex | Uso |
|-----|-----|-----|
| Telegram Blue | `#3390EC` | Fundo, CTAs, links |
| Dark | `#0F172A` | Textos, fundo dark mode |
| USA Red | `#DC2626` | Acentos, hover CTAs |
| Gold | `#FFD700` | Estrelas, badges |
| Light bg | `#F1F5F9` | Fundo alternado |

## Tipografia

- Display: **Space Grotesk** 700 (headlines)
- Body: **Inter** 400/500/600
- Mono: `ui-monospace, SFMono-Regular, monospace` (timestamps — stack do sistema)

## Seções (One-Page Long-Scroll)

1. **Header** — Sticky glass-effect, logo, dark mode toggle, CTA Telegram
2. **Hero** — Headline com typing effect, mock de chat, badge com count-up, disclaimer
3. **Chat Demo** — 5 perguntas sugeridas + input livre com fallback + ARIA `role="log"`
4. **Professores** — 4 cards estilo chat (avatar, rating, badge "Online", última msg)
5. **Como Funciona** — 4 passos em bolhas com timestamps
6. **Planos** — 3 cards (Básico/Pro/Premium) — sem valores finais
7. **Depoimentos** — Feed chat com nomes, cidades, estrelas
8. **FAQ** — Busca + acordeão em bolhas com details/summary
9. **CTA Final** — Bolha escura com botão Telegram gigante
10. **Footer** — Logo, links, privacidade

## Estrutura de Arquivos

```
TelegramBot/
├── index.html
├── privacidade.html
├── 404.html
├── README.md
├── docs/plans/PLANO-telegram-english-bot.md
└── assets/
    ├── css/style.css    (BEM + Custom Properties + Dark Mode)
    ├── js/main.js       (Theme, Observer, Typing, Count-Up, Chat, Particles, FAQ)
    ├── fonts/           (woff2 — produção)
    └── img/             (favicons, manifest, OG image)
```

## Animações & Efeitos

| Animação | Implementação | Guards |
|----------|--------------|--------|
| Typing effect | `setTimeout` char-by-char | `prefers-reduced-motion` |
| Count-up | `requestAnimationFrame` + easing | `prefers-reduced-motion` |
| Chat demo | Inline keyboard + fallback | ARIA `role="log"` `aria-live="polite"` |
| Emoji particles | `setInterval` + CSS `@keyframes` | `prefers-reduced-motion`, max 8 |
| Scroll reveal | Intersection Observer + `.reveal` classes | `prefers-reduced-motion` |
| FAB behavior | Scroll listener com throttling | N/A |
| FAQ search | Input listener + CSS hide | N/A |

## Acessibilidade (WCAG 2.1 AA)

- [x] HTML semântico (`<header>`, `<main>`, `<section>`, `<nav>`, `<footer>`)
- [x] `lang="pt-BR"` no `<html>`
- [x] `role="log"` + `aria-live="polite"` no chat demo
- [x] `role="feed"` nos depoimentos
- [x] `:focus-visible` em todos elementos interativos
- [x] `prefers-reduced-motion` respeitado em TODAS animações
- [x] Labels ARIA em botões flutuantes
- [x] Contrast ratio adequado em ambos os temas

## SEO

- [x] Meta description
- [x] Open Graph (og:title, og:description, og:image, og:url, og:locale)
- [x] Twitter Card (summary_large_image)
- [x] JSON-LD Schema.org (`@type: Course` + `CourseInstance`)
- [x] Favicon SVG + PNG placeholders
- [x] Web manifest para PWA
- [x] `theme-color` para mobile
- [x] `apple-mobile-web-app-capable`

## Definition of Done

- [x] Página carrega sem erros de console
- [ ] Lighthouse ≥ 90 Performance (a verificar)
- [x] WCAG 2.1 AA
- [x] `prefers-reduced-motion` respeitado
- [x] Dark mode funcional
- [x] 100% responsivo (320px–1920px)
- [x] Chat demo funcional com ARIA
- [x] Contador com disclaimer
- [x] 10 seções + 404 + privacidade
- [x] README do bot conceitual
- [ ] Deploy no ar

## Notas

- Zero dependências externas (exceto Google Fonts CDN durante desenvolvimento)
- Para produção: self-host fonts (woff2) com `font-display: swap`
- CTA Telegram placeholder: `https://t.me/inglesemfronteiras_bot` (TODO: substituir pelo handle real)
- Analytics não implementado por enquanto (documentado no README)

---

**Revisor:** GLM 5.2 (review subagent) — 17/06/2026  
**Build:** DeepSeek Pro — 17/06/2026
