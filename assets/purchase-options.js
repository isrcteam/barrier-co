import { Component } from '@theme/component';
import { StandardEvents } from '@shopify/events';

const LABEL_PROPERTY = '--purchase-options-button-label';

class PurchaseOptionsComponent extends Component {
  #abortController = new AbortController();

  connectedCallback() {
    super.connectedCallback();
    this.#abortController = new AbortController();
    const section = this.closest('.shopify-section, dialog');
    section?.addEventListener(StandardEvents.productSelect, this.#handleProductSelect, {
      signal: this.#abortController.signal,
    });
    this.#syncButtonLabel();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this.#abortController.abort();
  }

  select() {
    this.#syncButtonLabel();
  }

  #syncButtonLabel() {
    const form = document.getElementById(this.dataset.formId ?? '');
    if (!form) return;

    const checked = this.querySelector('input[data-button-label]:checked');
    const label =
      checked instanceof HTMLInputElement ? checked.dataset.buttonLabel ?? '' : this.dataset.oneTimeLabel ?? '';
    form.style.setProperty(LABEL_PROPERTY, JSON.stringify(label));
  }

  /** @param {Event & { promise?: Promise<any> }} event */
  #handleProductSelect = (event) => {
    if (!(event.target instanceof Element) || event.target.closest('product-card') || !event.promise) return;

    event.promise
      .then(({ detail }) => {
        const fresh = detail?.html?.querySelector(
          `purchase-options-component[data-block-id="${this.dataset.blockId}"]`
        );
        if (!fresh) return;

        const previous = this.querySelector('input[data-button-label]:checked');
        const previousValue = previous instanceof HTMLInputElement ? previous.value : null;

        this.replaceChildren(...fresh.childNodes);
        this.hidden = fresh.hasAttribute('hidden');
        this.dataset.oneTimeLabel = fresh.dataset.oneTimeLabel ?? '';

        if (previousValue !== null) {
          const match = Array.from(this.querySelectorAll('input[data-button-label]')).find(
            (input) => input instanceof HTMLInputElement && input.value === previousValue && !input.disabled
          );
          if (match instanceof HTMLInputElement) match.checked = true;
        }

        this.#syncButtonLabel();
      })
      .catch(() => {});
  };
}

if (!customElements.get('purchase-options-component')) {
  customElements.define('purchase-options-component', PurchaseOptionsComponent);
}
