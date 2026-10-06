const MOBILE = matchMedia('(max-width: 989px)');

class StickySpotlight extends HTMLElement {
  #observer = new IntersectionObserver(([entry]) => this.#update(entry), { threshold: 0 });

  /** @type {IntersectionObserverEntry | null} */
  #lastEntry = null;

  /** @type {HTMLElement | null} */
  #docked = null;

  connectedCallback() {
    this.#observer.observe(this);
    MOBILE.addEventListener('change', this.#handleBreakpoint);
  }

  disconnectedCallback() {
    this.#observer.disconnect();
    MOBILE.removeEventListener('change', this.#handleBreakpoint);
    this.#docked?.remove();
    this.#docked = null;
  }

  #handleBreakpoint = () => {
    if (this.#lastEntry) this.#update(this.#lastEntry);
  };

  /** @param {IntersectionObserverEntry} entry */
  #update(entry) {
    this.#lastEntry = entry;
    const passed = !entry.isIntersecting && entry.boundingClientRect.top < 0;
    const show = passed && MOBILE.matches;
    if (show && !this.#docked) {
      const card = this.firstElementChild;
      if (!(card instanceof HTMLElement)) return;
      this.#docked = document.createElement('div');
      this.#docked.className = `${this.className} sticky-spotlight__docked`;
      this.#docked.append(card.cloneNode(true));
      document.body.append(this.#docked);
    }
    this.#docked?.toggleAttribute('hidden', !show);
  }
}

if (!customElements.get('sticky-spotlight')) customElements.define('sticky-spotlight', StickySpotlight);
