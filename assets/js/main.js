/**
 * EnglishFlow — Stars & Messages
 * Vanilla JS: Theme, Observer, Typing, Count-Up, Chat Demo, Particles, Counter, FAQ
 */

(function () {
  'use strict';

  /* ---------- UTILS ---------- */
  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

  /** Check for reduced motion preference */
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ============================================================
     1. THEME TOGGLE
     ============================================================ */
  (function initTheme() {
    const html = document.documentElement;
    const toggle = $('#themeToggle');

    // Detect saved or system preference
    const saved = localStorage.getItem('englishflow-theme');
    if (saved) {
      html.setAttribute('data-theme', saved);
    } else {
      html.setAttribute('data-theme',
        window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    }

    toggle?.addEventListener('click', () => {
      const current = html.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      localStorage.setItem('englishflow-theme', next);
    });
  })();

  /* ============================================================
     2. INTERSECTION OBSERVER (Scroll Reveal)
     ============================================================ */
  (function initObserver() {
    if (prefersReducedMotion) return;

    // Add .reveal class to sections and cards
    const revealTargets = $$('section > *, .prof-card, .plano-card, .depo-card, .step');
    revealTargets.forEach(el => {
      if (!el.classList.contains('reveal')) {
        el.classList.add('reveal');
      }
    });

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('reveal--visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
    );

    $$('.reveal').forEach(el => observer.observe(el));
  })();

  /* ============================================================
     3. TYPING EFFECT (Hero Headline)
     ============================================================ */
  (function initTypingEffect() {
    if (prefersReducedMotion) return;

    const headline = $('#hero-headline');
    if (!headline) return;

    const fullText = headline.textContent.trim();
    headline.textContent = '';

    let i = 0;
    const speed = 50;

    function type() {
      if (i < fullText.length) {
        headline.textContent += fullText.charAt(i);
        i++;
        setTimeout(type, speed);
      }
    }

    // Start typing after a short delay
    setTimeout(type, 600);
  })();

  /* ============================================================
     4. COUNT-UP ANIMATION (Hero Badge)
     ============================================================ */
  (function initCountUp() {
    const counterEl = $('#heroCounter');
    if (!counterEl) return;

    const target = 10000;
    const duration = 2000;
    const startTime = performance.now();

    function update(now) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(eased * target);
      counterEl.textContent = '+' + current.toLocaleString('pt-BR');

      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        counterEl.textContent = '+10 mil';
      }
    }

    // Start when hero is visible
    const heroObserver = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          requestAnimationFrame(update);
          heroObserver.disconnect();
        }
      },
      { threshold: 0.5 }
    );

    heroObserver.observe($('#hero'));
  })();

  /* ============================================================
     5. CHAT DEMO INTERACTIVE
     ============================================================ */
  (function initChatDemo() {
    const messages = $('#chatMessages');
    const suggestions = $('#chatSuggestions');
    const input = $('#chatInput');
    const sendBtn = $('#chatSend');

    if (!messages || !input || !sendBtn) return;

    // Response database
    const responses = {
      'como funcionam as aulas': 'As aulas são pelo Telegram! 🎓 Você agenda um horário, recebe o link e conversa diretamente com um professor nativo americano. Pode ser por chat, áudio ou chamada. Simples, rápido e sem burocracia!',
      'quanto custa': 'Temos 3 planos: 💚 Básico (R$30/mês — 4 aulas), ⭐ Pro (R$55/mês — 8 aulas, o mais popular!), e 👑 Premium (R$80/mês — 12 aulas individuais). A primeira aula é gratuita em todos os planos!',
      'os professores são nativos': 'Sim! 🇺🇸 Todos os nossos professores são americanos nativos, com formação universitária e experiência comprovada no ensino de inglês. Você escolhe com quem quer aprender!',
      'posso fazer uma aula teste': 'Claro! 🎉 A primeira aula é 100% gratuita em qualquer plano. Sem compromisso. Se não gostar, não paga nada. É só agendar!',
      'qual o horário das aulas': 'Você escolhe! 📅 Temos horários de segunda a sábado, das 7h às 22h (horário de Brasília). Basta selecionar o professor e o slot que melhor encaixa na sua rotina.'
    };

    const fallback = 'Hmm, ótima pergunta! 🤔 Para essa eu recomendo falar direto com um professor no Telegram. É rapidinho e você já resolve! 💬';

    function addMessage(text, isUser) {
      const msgDiv = document.createElement('div');
      msgDiv.className = 'chat-msg ' + (isUser ? 'chat-msg--user' : 'chat-msg--bot');
      msgDiv.innerHTML = `
        <div class="chat-msg__avatar">${isUser ? '👤' : '🤖'}</div>
        <div class="chat-msg__body">
          <p>${escapeHTML(text)}</p>
          <span class="chat-msg__time">Agora</span>
        </div>
      `;
      messages.appendChild(msgDiv);
      messages.scrollTop = messages.scrollHeight;
      return msgDiv;
    }

    function addBotResponse(text) {
      // Simulate typing delay
      const typingDelay = 800 + Math.random() * 600;

      // Add typing indicator
      const typingDiv = document.createElement('div');
      typingDiv.className = 'chat-msg chat-msg--bot';
      typingDiv.innerHTML = `
        <div class="chat-msg__avatar">🤖</div>
        <div class="chat-msg__body">
          <p style="color: var(--color-text-muted); font-style: italic;">digitando...</p>
        </div>
      `;
      typingDiv.setAttribute('aria-label', 'Assistente está digitando');
      messages.appendChild(typingDiv);
      messages.scrollTop = messages.scrollHeight;

      setTimeout(() => {
        // Remove typing indicator
        typingDiv.remove();
        addMessage(text, false);
      }, typingDelay);
    }

    function getResponse(question) {
      const q = question.toLowerCase().trim().replace(/[?!.,]/g, '');
      // Check for matches
      for (const [key, response] of Object.entries(responses)) {
        if (q.includes(key) || key.includes(q)) {
          return response;
        }
      }
      return fallback;
    }

    function sendQuestion(text) {
      if (!text.trim()) return;
      addMessage(text, true);
      input.value = '';
      const response = getResponse(text);
      addBotResponse(response);
    }

    // Suggestion buttons
    suggestions?.addEventListener('click', (e) => {
      const btn = e.target.closest('.chat-suggestion');
      if (!btn) return;
      const question = btn.dataset.question;
      if (question) sendQuestion(question);
    });

    // Send button
    sendBtn.addEventListener('click', () => {
      sendQuestion(input.value);
    });

    // Enter key
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        sendQuestion(input.value);
      }
    });
  })();

  /* ============================================================
     6. EMOJI PARTICLES (Hero Background)
     ============================================================ */
  (function initParticles() {
    if (prefersReducedMotion) return;

    const container = $('#heroParticles');
    if (!container) return;

    const emojis = ['💬', '🇺🇸', '⭐', '✈️', '🎓', '📱', '✨', '💡'];
    const maxParticles = 8;

    function createParticle() {
      const currentCount = container.querySelectorAll('.particle').length;
      if (currentCount >= maxParticles) return;

      const span = document.createElement('span');
      span.className = 'particle';
      span.textContent = emojis[Math.floor(Math.random() * emojis.length)];
      span.style.left = Math.random() * 90 + '%';
      span.style.bottom = Math.random() * 40 + '%';
      span.style.fontSize = (1 + Math.random() * 1.5) + 'rem';
      span.style.animationDuration = (5 + Math.random() * 5) + 's';
      span.style.animationDelay = Math.random() * 2 + 's';

      container.appendChild(span);

      // Clean up after animation
      span.addEventListener('animationend', () => {
        span.remove();
      });
    }

    // Create particles periodically
    setInterval(createParticle, 2500);

    // Initial burst
    for (let i = 0; i < 4; i++) {
      setTimeout(createParticle, i * 600);
    }
  })();

  /* ============================================================
     7. LIVE COUNTER (Background)
     ============================================================ */
  (function initLiveCounter() {
    const badgeEl = $('.badge__text');
    if (!badgeEl) return;

    // Periodically show "live counter" text
    const liveTexts = [
      '+10 mil aulas realizadas*',
      '23 aulas agora',
      '12 professores online',
      '+10 mil aulas realizadas*'
    ];

    let idx = 0;
    setInterval(() => {
      idx = (idx + 1) % liveTexts.length;
      // Smooth text swap
      badgeEl.style.opacity = '0';
      setTimeout(() => {
        badgeEl.textContent = liveTexts[idx];
        badgeEl.style.opacity = '1';
      }, 200);
    }, 8000);

    // Add transition to badge text
    badgeEl.style.transition = 'opacity 0.2s ease';
  })();

  /* ============================================================
     8. FAQ SEARCH
     ============================================================ */
  (function initFaqSearch() {
    const searchInput = $('#faqSearch');
    const faqList = $('#faqList');
    if (!searchInput || !faqList) return;

    const items = $$('.faq-item', faqList);

    searchInput.addEventListener('input', () => {
      const query = searchInput.value.toLowerCase().trim();

      items.forEach(item => {
        const question = ($('.faq-item__question', item)?.textContent || '').toLowerCase();
        const answer = ($('.faq-item__answer', item)?.textContent || '').toLowerCase();

        if (!query || question.includes(query) || answer.includes(query)) {
          item.classList.remove('faq-item--hidden');
        } else {
          item.classList.add('faq-item--hidden');
        }
      });
    });
  })();

  /* ============================================================
     9. FAB (Floating Action Button) Behavior
     ============================================================ */
  (function initFab() {
    const fab = $('#fab');
    if (!fab) return;

    let lastScroll = 0;
    const hideThreshold = 300;

    window.addEventListener('scroll', () => {
      const currentScroll = window.scrollY;

      if (currentScroll > hideThreshold && currentScroll > lastScroll) {
        // Scrolling down — hide
        fab.classList.add('fab--hidden');
      } else {
        // Scrolling up or at top — show
        fab.classList.remove('fab--hidden');
      }

      lastScroll = currentScroll;
    }, { passive: true });
  })();

  /* ============================================================
     10. SMOOTH SECTION HIGHLIGHT ON HASH NAVIGATION
     ============================================================ */
  (function initHashNavigation() {
    window.addEventListener('hashchange', () => {
      const target = document.querySelector(location.hash);
      if (target) {
        target.setAttribute('tabindex', '-1');
        target.focus({ preventScroll: true });
      }
    });
  })();

  /* ---------- HELPER: Escape HTML ---------- */
  function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

})();
