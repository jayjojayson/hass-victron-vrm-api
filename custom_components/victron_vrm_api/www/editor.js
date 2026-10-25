
// ?v=... verhindert, dass Browser nach einem Update alte Dateien aus dem Cache nutzen
import {css} from './css-editor.js?v=1.9';

import * as libEditor from './lib-editor.js?v=1.9';

class venusOsDashBoardEditor extends HTMLElement {

    async setConfig(config) {
        const incoming = { ...config, entities: { ...(config.entities || {}) } };

        // Kommt die Config von uns selbst zurück (nach notifyConfigChange), nicht
        // komplett neu rendern – sonst gehen Fokus, offene Panels und der
        // geöffnete Farbwähler bei jeder Änderung verloren.
        let incomingJson = null;
        try { incomingJson = JSON.stringify(config); } catch (e) { /* ignore */ }
        if (this.shadowRoot && incomingJson && incomingJson === this._lastEmittedConfig) {
            this._config = incoming;
            return;
        }

        this._config = incoming;

        await libEditor.loadTranslations(this);

        if (!this.shadowRoot) {

            this.attachShadow({ mode: 'open' });

            // Eigene Tab-Buttons statt sl-tab (Shoelace ist in HA nicht mehr enthalten)
            this.shadowRoot.innerHTML = `
              <div id="tab-group" class="vrm-tabs">
                <button type="button" class="vrm-tab" data-tab="0" active>Conf.</button>
                <button type="button" class="vrm-tab" data-tab="1">Col. 1</button>
                <button type="button" class="vrm-tab" data-tab="2">Col. 2</button>
                <button type="button" class="vrm-tab" data-tab="3">Col. 3</button>
              </div>
              <div id="tab-panel" class="vrm-tab-panel">
                <div id="tab-content" class="content"></div>
              </div>
            `;

            const style = document.createElement('style');
            style.textContent = css();
            this.shadowRoot.prepend(style);

            this._currentTab = 0;
            this._currentSubTab = 0;

            libEditor.attachLinkClick(this.renderTabContent.bind(this), this);

        }

        this.renderTabContent();
    }

    renderTabContent() {

        if (!this.shadowRoot || !this._config) return;

        if (this._currentTab === 1 || this._currentTab === 2 || this._currentTab === 3) {
            libEditor.tabColRender(this._currentTab, this);
        } else {
            libEditor.tab1Render(this);
        }

        libEditor.attachInputs(this);

    }

    set hass(hass) {
        const languageChanged = (hass?.language || 'en') !== (this._hass?.language || 'en');
        this._hass = hass;
        if (this.shadowRoot) {
            this.shadowRoot.querySelectorAll('ha-selector, ha-icon-picker').forEach(el => {
                el.hass = hass;
            });
        }
        // Beim ersten setConfig ist hass oft noch nicht gesetzt → Sprache fiel auf
        // Englisch zurück. Sobald hass da ist, ggf. in der richtigen Sprache neu rendern.
        if (this._config && this.shadowRoot && (languageChanged || !this._translationsForHass)) {
            this._translationsForHass = true;
            libEditor.loadTranslations(this).then(() => this.renderTabContent());
        }
    }

    get hass() {
        return this._hass;
    }

    get value() {
        return this._config;
    }
}

if (!customElements.get('venus-os-editor')) {
    customElements.define('venus-os-editor', venusOsDashBoardEditor);
}
