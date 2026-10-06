const REDUCED_MOTION = matchMedia('(prefers-reduced-motion: reduce)');
const COUNT_DURATION = 1600;
const COUNT_STAGGER = 120;

class ClinicalStats extends HTMLElement {
  /** @type {IntersectionObserver | undefined} */
  #observer;

  /** @type {ResizeObserver | undefined} */
  #resizeObserver;

  #width = 0;

  connectedCallback() {
    const list = this.firstElementChild;
    if (!(list instanceof HTMLElement)) return;

    this.#resizeObserver = new ResizeObserver(([entry]) => {
      if (!entry || entry.contentRect.width === this.#width) return;
      this.#width = entry.contentRect.width;
      this.#balanceCaptions();
    });
    this.#resizeObserver.observe(list);

    if (REDUCED_MOTION.matches) return;

    const numbers = Array.from(this.querySelectorAll('[data-count]')).filter((node) => node instanceof HTMLElement);
    for (const number of numbers) {
      number.style.inlineSize = `${number.getBoundingClientRect().width}px`;
      number.textContent = '0';
    }

    this.#observer = new IntersectionObserver(
      (entries) => {
        if (!entries.some((entry) => entry.isIntersecting)) return;
        this.#observer?.disconnect();
        this.#count(numbers);
      },
      { threshold: 0.35 }
    );
    this.#observer.observe(list);
  }

  disconnectedCallback() {
    this.#observer?.disconnect();
    this.#resizeObserver?.disconnect();
  }

  /** @param {HTMLElement[]} numbers */
  #count(numbers) {
    numbers.forEach((number, index) => {
      const target = Number(number.dataset.count) || 0;
      const delay = index * COUNT_STAGGER;
      /** @type {number | undefined} */
      let start;

      /** @param {number} now */
      const tick = (now) => {
        start ??= now;
        const progress = Math.min(Math.max((now - start - delay) / COUNT_DURATION, 0), 1);
        number.textContent = String(Math.round(target * (1 - Math.pow(1 - progress, 3))));
        if (progress < 1) {
          requestAnimationFrame(tick);
        } else {
          number.style.inlineSize = '';
        }
      };
      requestAnimationFrame(tick);
    });
  }

  #balanceCaptions() {
    for (const caption of this.querySelectorAll('[data-two-lines]')) {
      if (!(caption instanceof HTMLElement)) continue;
      caption.style.maxInlineSize = 'none';
      caption.style.whiteSpace = 'nowrap';
      const range = document.createRange();
      range.selectNodeContents(caption);
      const singleLine = range.getBoundingClientRect().width;
      caption.style.whiteSpace = '';
      const lineHeight = parseFloat(getComputedStyle(caption).lineHeight) || 24;
      let width = Math.ceil(singleLine / 2);
      caption.style.maxInlineSize = `${width}px`;
      while (caption.getBoundingClientRect().height > lineHeight * 2.5 && width < singleLine) {
        width += 4;
        caption.style.maxInlineSize = `${width}px`;
      }
    }
  }
}

if (!customElements.get('clinical-stats')) customElements.define('clinical-stats', ClinicalStats);
