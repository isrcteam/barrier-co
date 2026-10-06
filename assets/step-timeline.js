const REDUCED_MOTION = matchMedia('(prefers-reduced-motion: reduce)');
const DURATION = 1500;

/** @param {number} t */
const easeInOut = (t) => -(Math.cos(Math.PI * t) - 1) / 2;

class StepTimeline extends HTMLElement {
  /** @type {IntersectionObserver | undefined} */
  #observer;

  /** @type {ResizeObserver | undefined} */
  #resizeObserver;

  /** @type {HTMLElement | undefined} */
  #list;

  /** @type {HTMLElement[]} */
  #steps = [];

  /** @type {number[]} */
  #stops = [];

  #length = 0;

  #frame = 0;

  connectedCallback() {
    if (REDUCED_MOTION.matches || window.Shopify?.designMode) return;

    const list = this.querySelector('.step-timeline__steps');
    if (!(list instanceof HTMLElement)) return;

    const steps = Array.from(list.children).filter((step) => step instanceof HTMLElement);
    if (steps.length < 2) return;

    this.#list = list;
    this.#steps = steps;
    list.dataset.animate = '';
    this.#measure();

    this.#resizeObserver = new ResizeObserver(() => this.#measure());
    this.#resizeObserver.observe(list);

    this.#observer = new IntersectionObserver(([entry]) => {
      if (!entry?.isIntersecting) return;
      this.#observer?.disconnect();
      this.#play();
    });
    this.#observer.observe(this);
  }

  disconnectedCallback() {
    this.#observer?.disconnect();
    this.#resizeObserver?.disconnect();
    cancelAnimationFrame(this.#frame);
  }

  #measure() {
    const first = this.#steps[0];
    const last = this.#steps[this.#steps.length - 1];
    if (!this.#list || !first || !last) return;

    this.#length = last.offsetTop - first.offsetTop;
    this.#stops = this.#steps.map((step) => (this.#length > 0 ? (step.offsetTop - first.offsetTop) / this.#length : 0));
    this.#list.style.setProperty('--step-rail-length', `${this.#length}px`);
  }

  #play() {
    const list = this.#list;
    if (!list) return;

    /** @type {number | undefined} */
    let start;

    /** @param {number} now */
    const tick = (now) => {
      start ??= now;
      const elapsed = Math.min((now - start) / DURATION, 1);
      const progress = easeInOut(elapsed);
      list.style.setProperty('--step-progress', progress.toFixed(4));
      this.#steps.forEach((step, index) => {
        if (progress >= (this.#stops[index] ?? 1) - 0.001) step.classList.add('is-reached');
      });
      if (elapsed < 1) this.#frame = requestAnimationFrame(tick);
    };
    this.#frame = requestAnimationFrame(tick);
  }
}

if (!customElements.get('step-timeline')) customElements.define('step-timeline', StepTimeline);
