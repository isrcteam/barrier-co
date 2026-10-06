const DESKTOP = matchMedia('(min-width: 990px)');
const REDUCED_MOTION = matchMedia('(prefers-reduced-motion: reduce)');

class CarouselFocus extends HTMLElement {
  #active = 0;

  /** @type {HTMLElement[]} */
  #slides = [];

  connectedCallback() {
    this.#slides = Array.from(this.querySelectorAll('slideshow-slide'));
    this.#active = Math.min(Number(this.dataset.start ?? 0), Math.max(this.#slides.length - 1, 0));
    this.addEventListener('click', this.#handleClick);
    DESKTOP.addEventListener('change', this.#render);
    this.#render();
  }

  disconnectedCallback() {
    this.removeEventListener('click', this.#handleClick);
    DESKTOP.removeEventListener('change', this.#render);
  }

  /** @param {MouseEvent} event */
  #handleClick = (event) => {
    const button = event.target instanceof Element ? event.target.closest('[data-focus-step]') : null;
    if (!(button instanceof HTMLElement)) return;
    this.#step(Number(button.dataset.focusStep));
  };

  /** @param {number} delta */
  #step(delta) {
    const count = this.#slides.length;
    if (count < 2) return;
    const before = new Map(this.#slides.map((slide) => [slide, slide.getBoundingClientRect()]));
    this.#active = (this.#active + delta + count) % count;
    this.#render();
    this.#animate(before);
  }

  #render = () => {
    const count = this.#slides.length;
    this.#slides.forEach((slide, index) => {
      if (!DESKTOP.matches) {
        delete slide.dataset.focus;
        slide.classList.toggle('image-carousel__slide--middle', slide.hasAttribute('data-middle'));
        return;
      }
      let offset = (index - this.#active + count) % count;
      if (offset > count / 2) offset -= count;
      const position = offset === 0 ? 'active' : offset === -1 ? 'previous' : offset === 1 ? 'next' : 'hidden';
      slide.dataset.focus = position;
      slide.classList.toggle('image-carousel__slide--middle', position === 'active');
      slide.setAttribute('aria-hidden', String(position === 'hidden'));
    });
  };

  /** @param {Map<HTMLElement, DOMRect>} before */
  #animate(before) {
    if (!DESKTOP.matches || REDUCED_MOTION.matches) return;
    const duration = parseFloat(getComputedStyle(this).getPropertyValue('--duration-slow')) || 600;
    for (const slide of this.#slides) {
      const from = before.get(slide);
      const to = slide.getBoundingClientRect();
      if (!to.width) continue;
      if (!from || !from.width) {
        slide.animate([{ opacity: 0 }, { opacity: 1 }], { duration, easing: 'ease-out' });
        continue;
      }
      const scale = from.width / to.width;
      slide.animate(
        [
          {
            transformOrigin: 'top left',
            transform: `translate(${from.left - to.left}px, ${from.top - to.top}px) scale(${scale})`,
          },
          { transformOrigin: 'top left', transform: 'none' },
        ],
        { duration, easing: 'cubic-bezier(0.2, 0, 0, 1)' }
      );
    }
  }
}

if (!customElements.get('carousel-focus')) customElements.define('carousel-focus', CarouselFocus);
