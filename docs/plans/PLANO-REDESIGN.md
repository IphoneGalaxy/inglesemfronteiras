# PLANO — Redesign EnglishFlow "Inglês em Fronteiras"

> Data: 18/06/2026 | Revisor: reason (Qwen) | Build: DeepSeek Pro

## Contexto

- **Objetivo:** Redesign completo do site EnglishFlow com visual moderno (Dark Mode + Neon Gradients), foco em conversão via Telegram, e apenas o Professor Joab como instrutor
- **Origem dos arquivos:** Pasta `arquivos e instruções para nova modificação/`
- **Restrições:** Imagens via CDN externo (NÃO baixar), todos CTAs → `t.me/inglesemfronteiras_bot`

## Diagnóstico (reason/Qwen)

| Risco | Severidade | Solução |
|-------|-----------|---------|
| Login email/senha sem backend | 🔴 CRÍTICO | Manter access_code + Supabase JS |
| Painel estático sem dados reais | 🔴 CRÍTICO | Conectar Supabase JS no novo layout |
| `components.css` não existe | 🟡 ALTO | Criar com ~500 linhas |
| CSS path inconsistente | 🟡 ALTO | Padronizar `assets/css/` |
| Admin expõe código no HTML | 🟡 ALTO | Manter lógica Supabase |
| Bot mostra 4 professores | 🟢 MÉDIO | Atualizar pra só Joab |
| Imagens CDN podem expirar | 🟢 MÉDIO | `onerror` fallback |

## Delegação de Subagentes

| Fase | Tarefa | Subagente | Paralelo? |
|------|--------|-----------|-----------|
| 1 | Revisar o plano antes de executar | `review` (GLM 5.2) | ✅ Início |
| 2 | Criar `components.css` com +120 classes | Build (eu) | — |
| 3 | Adaptar `login.html` (visual novo + access_code + Supabase) | Build (eu) | — |
| 4 | Adaptar `painel.html` (visual novo + Supabase progresso) | Build (eu) | — |
| 5 | Adaptar `admin.html` (visual novo + Supabase) | Build (eu) | ✅ Paralelo com 4 |
| 6 | Adaptar `certificado.html` (dados Supabase) | Build (eu) | ✅ Paralelo com 5 |
| 7 | Atualizar `bot.py` (1 professor Joab) | Build (eu) | ✅ Paralelo com 5,6 |
| 8 | Atualizar `vercel.json` (cleanUrls) | Build (eu) | — |
| 9 | Substituir `style.css` pelo novo design | Build (eu) | — |
| 10 | Corrigir paths CSS no `index.html` | Build (eu) | — |
| 11 | Atualizar `privacidade.html` e `404.html` | Build (eu) | ✅ Paralelo com 10 |
| 12 | Revisão final pós-implementação | `review` (GLM 5.2) | ✅ Fim |

## Arquivos impactados

| Arquivo | Ação | Origem |
|---------|------|--------|
| `style.css` | 🔄 Substituir | `arquivos.../style.css` |
| `components.css` | 🆕 Criar | ~500 linhas |
| `index.html` | 🔄 Substituir + corrigir path CSS | `arquivos.../index.html` |
| `login.html` | 🔄 Adaptar (visual novo + access_code + Supabase) | Merge |
| `painel.html` | 🔄 Adaptar (visual novo + Supabase JS) | Merge |
| `admin.html` | 🔄 Adaptar (visual novo + Supabase JS) | Merge |
| `certificado.html` | 🔄 Adaptar (template + Supabase data) | Merge |
| `privacidade.html` | 🔄 Substituir | `arquivos.../privacidade.html` |
| `404.html` | 🔄 Substituir | `arquivos.../404.html` |
| `vercel.json` | ✏️ Atualizar (cleanUrls) | Novo formato |
| `bot.py` | ✏️ Atualizar professores | 4 → 1 (Joab) |
| `README.md` | ✏️ Atualizar | Nova estrutura |

## Fases que dependem do usuário

| # | Ação | Por quê |
|---|------|---------| 
| 1 | Nenhuma — arquivos já na pasta | — |
| 2 | Testar no celular após deploy | Responsividade, links Telegram |
| 3 | Trocar foto do Joab (opcional) | Imagem atual é CDN externo |

## O que NÃO muda

- Supabase (banco intacto)
- Bot Railway (continua rodando)
- Fluxo PIX (inalterado)
- Vercel deploy automático
- Imagens via CDN externo

## Definition of Done

- [ ] `style.css` substituído pelo novo design
- [ ] `components.css` criado com estilos de formulários, dashboard, admin, certificado
- [ ] `index.html` com novo visual, links corrigidos
- [ ] `login.html` adaptado: visual novo + access_code + Supabase JS
- [ ] `painel.html` adaptado: visual novo + Supabase progresso/materiais
- [ ] `admin.html` adaptado: visual novo + Supabase
- [ ] `certificado.html` adaptado: dados dinâmicos do Supabase
- [ ] `bot.py` com apenas Professor Joab
- [ ] `vercel.json` com cleanUrls
- [ ] `privacidade.html` e `404.html` atualizados
- [ ] Todos CTAs → `t.me/inglesemfronteiras_bot`
- [ ] Paths CSS padronizados `assets/css/`
- [ ] Deploy automático no Vercel via push
