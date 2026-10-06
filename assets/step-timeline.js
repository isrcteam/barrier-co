const REDUCED_MOTION = matchMedia('(prefers-reduced-motion: reduce)');
const STEP_GAP = 220;

class StepTimeline extends HTMLElement {
  /** @type {IntersectionObserver | undefined} */
  #observer;

  #nextReveal = 0;

  connectedCallback() {
    if (REDUCED_MOTION.matches || window.Shopify?.designMode) return;

    const list = this.querySelector('.step-timeline__steps');
    if (!(list instanceof HTMLElement)) return;

    const steps = Array.from(list.children).filter((step) => step instanceof HTMLElement);
    list.dataset.animate = '';

    this.#observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          this.#observer?.unobserve(entry.target);
          this.#reveal(entry.target);
        }
      },
      { rootMargin: '0px 0px -15% 0px' }
    );
    for (const step of steps) this.#observer.observe(step);
  }

  disconnectedCallback() {
    this.#observer?.disconnect();
  }

  /** @param {Element} step */
  #reveal(step) {
    const now = performance.now();
    const delay = Math.max(0, this.#nextReveal - now);
    this.#nextReveal = now + delay + STEP_GAP;
    setTimeout(() => step.classList.add('is-revealed'), delay);
  }
}

if (!customElements.get('step-timeline')) customElements.define('step-timeline', StepTimeline);
