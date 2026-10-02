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
    this.#syncSticky(checked instanceof HTMLInputElement ? checked : null, label);
  }

  /**
   * Mirrors the selected plan in the sticky add to cart bar: button label, price, savings and a plan select
   * that checks the same radios, so the sticky button (which clicks the main one) adds the chosen plan.
   * @param {HTMLInputElement | null} checked
   * @param {string} label
   */
  #syncSticky(checked, label) {
    const sticky = this.closest('.shopify-section')?.querySelector('sticky-add-to-cart');
    if (!(sticky instanceof HTMLElement)) return;

    sticky.style.setProperty(LABEL_PROPERTY, JSON.stringify(label));

    const inputs = Array.from(this.querySelectorAll('input[data-button-label]')).filter(
      (input) => input instanceof HTMLInputElement
    );
    const planPrice = sticky.querySelector('[data-sticky-plan-price]');
    const savings = sticky.querySelector('[data-sticky-plan-savings]');
    const planField = sticky.querySelector('[data-sticky-plan]');
    const select = sticky.querySelector('[data-sticky-plan-select]');
    const hasPlans = inputs.length > 1 && checked !== null;

    sticky.toggleAttribute('data-has-plans', hasPlans);
    if (planField instanceof HTMLElement) planField.hidden = !hasPlans;
    if (planPrice instanceof HTMLElement) {
      planPrice.hidden = !hasPlans;
      planPrice.textContent = checked?.dataset.price ?? '';
    }
    if (savings instanceof HTMLElement) {
      savings.hidden = !hasPlans || !checked?.dataset.savings;
      savings.textContent = checked?.dataset.savings ?? '';
    }
    if (!hasPlans || !(select instanceof HTMLSelectElement)) return;

    select.replaceChildren(
      ...inputs.map((input) => {
        const name = this.querySelector(`label[for="${CSS.escape(input.id)}"]`)?.textContent?.trim() ?? input.value;
        const option = new Option(name, input.id, false, input.checked);
        option.disabled = input.disabled;
        return option;
      })
    );

    if (!select.dataset.bound) {
      select.dataset.bound = 'true';
      select.addEventListener(
        'change',
        () => {
          const input = this.querySelector(`#${CSS.escape(select.value)}`);
          if (!(input instanceof HTMLInputElement)) return;
          input.checked = true;
          input.dispatchEvent(new Event('change', { bubbles: true }));
          this.#syncButtonLabel();
        },
        { signal: this.#abortController.signal }
      );
    }
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
