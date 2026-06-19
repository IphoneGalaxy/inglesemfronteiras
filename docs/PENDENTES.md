# Pendências Futuras — EnglishFlow

> Itens que serão implementados depois.
> Criado em 17/06/2026.

---

## 5. Imagens reais no site

**O que:** Substituir emojis por fotos reais dos professores e assets visuais.

**Por quê:** Emojis dão aspecto amador. Fotos reais passam credibilidade.

**O que precisa:**
- [ ] Fotos de perfil dos professores (400x400px, webp)
- [ ] OG Image personalizada (1200x630, webp)
- [ ] Substituir `.prof-card__emoji` por `<img>` com foto real
- [ ] Ajustar CSS para imagens circulares

---

## 9. Verificação automática de PIX

**O que:** Bot verifica automaticamente se o PIX foi recebido, sem precisar de aprovação manual.

**Por quê:** Agiliza o processo, elimina trabalho manual.

**Como:**
- [ ] Integrar com API do banco (webhook de notificação PIX)
- [ ] Ou usar serviço terceiro (ex: Mercado Pago, Efí)
- [ ] Bot escuta confirmação e libera acesso automaticamente
- [ ] Fallback: manter aprovação manual como backup

**Desafio:** Requer conta PJ ou gateway de pagamento. Avaliar custo x benefício.
