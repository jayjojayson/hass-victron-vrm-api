/*

 switch auto theme clair/sombre ou choix manuel

 donc onglet param en plus

*/

// Version kommt aus der eigenen URL (?v=...), die die Integration aus manifest.json setzt.
// Sie wird an alle Unter-Dateien weitergereicht → nach jedem Update lädt der Browser
// garantiert die neuen Dateien (keine Pflege mehr an mehreren Stellen nötig).
const CARD_VERSION = new URL(import.meta.url).searchParams.get('v') || 'dev';

console.info(
  "%c 🗲 %c - %cVictron VRM API Card%c - %c 🗲 \n%c version " + CARD_VERSION + " ",
  "color: white; font-weight: bold; background: black",
  "color: orange; font-weight: bold; background: blue; font-weight: bold;",
  "color: white; font-weight: bold; background: blue; text-decoration: underline; text-decoration-color: orange; text-decoration-thickness: 5px; text-underline-offset: 2px;",
  "color: orange; font-weight: bold; background: blue; font-weight: bold;",
  "color: white; font-weight: bold; background: black",
  "color: white; font-weight: bold; background: grey"
);

const [{ EDITOR_TAG }, libVenus, { cssDataDark }, { cssDataLight }] = await Promise.all([
  import(`./editor.js?v=${CARD_VERSION}`),
  import(`./lib-venus.js?v=${CARD_VERSION}`),
  import(`./css-dark.js?v=${CARD_VERSION}`),
  import(`./css-light.js?v=${CARD_VERSION}`),
]);

// Fortlaufende ID pro Karteninstanz – wird zum Scopen des CSS genutzt,
// damit mehrere Karten (z.B. Dashboard + Editor-Vorschau, hell + dunkel)
// sich nicht gegenseitig die Styles überschreiben.
let cardInstanceCounter = 0;

/**
 * Stellt jedem Selektor einen Scope voran (z.B. `[data-vrm-card="3"] .box`).
 * Die Theme-CSS enthält keine @-Regeln, daher reicht ein einfacher Parser.
 */
function scopeCss(cssText, scope) {
  return cssText
    .split('}')
    .map((chunk) => {
      const idx = chunk.indexOf('{');
      if (idx === -1) return chunk;
      const selectors = chunk.slice(0, idx);
      const body = chunk.slice(idx);
      if (!selectors.trim()) return chunk;
      const scoped = selectors
        .split(',')
        .map((sel) => (sel.trim() ? `${scope} ${sel.trim()}` : sel))
        .join(', ');
      return `${scoped} ${body}`;
    })
    .join('}');
}

class VictronVrmApiCard extends HTMLElement {

  constructor() {
    super();
    this._instanceId = ++cardInstanceCounter;
    this._periodicTaskStarted = false;
    this._isDark = true;
  }

  setConfig(config) {

    if (!config || typeof config !== 'object') {
      throw new Error('Victron VRM API Card: ungültige Konfiguration');
    }

    this.config = config;

    if (this.content) {
      // Config wurde geändert (z.B. im Editor): laufende Animationen/Intervalle
      // dieser Karte stoppen und die Struktur (Boxen, Anker) neu aufbauen,
      // damit Änderungen an Spalten/Ankern sofort sichtbar werden.
      libVenus.clearAllIntervals(this.content);
      this._periodicTaskStarted = false;
    }

    this._createCardStructure();
    libVenus.razDashboardOldWidth(this.content);

    // Falls hass bereits vorhanden ist, direkt neu rendern
    if (this._hass) this.hass = this._hass;
  }

  _createCardStructure() {

    // Initialize the content if it's not there yet.
    if (!this.content) {

      this.setAttribute('data-vrm-card', String(this._instanceId));

      const cardElem = document.createElement('ha-card');
      this.appendChild(cardElem);

      const contElem = document.createElement('div');
      contElem.setAttribute('id', 'db-container');
      contElem.setAttribute('class', 'db-container');
      cardElem.appendChild(contElem);

      this.content = contElem;

    }

    // recuperation des parametres
    const param = this.config.param || {};

    // rendu de la structure de base de la carte (en mode normal ou demo "image")
    libVenus.baseRender(this.config, this.content);

    // recuperation des quantités de box a créer par colonne dans les parametres
    const boxCol1 = libVenus.getBoxCount(param, 1);
    const boxCol2 = libVenus.getBoxCount(param, 2);
    const boxCol3 = libVenus.getBoxCount(param, 3);

    // ajout des box
    if (this.config.demo !== true) libVenus.addBox(boxCol1, boxCol2, boxCol3, this.content);

    // ajout des ancres d'attache des lignes
    if (this.config.demo !== true) libVenus.addAnchors(this.config, this.content);

  }

  set hass(hass) {

    this._hass = hass;

    if (!hass || !this.config || !this.content) return;

    const haCard = this.querySelector('ha-card');

    // Check the selected theme
    const isDarkTheme = !!hass.themes?.darkMode;

    // Include color config in the cache key so color changes trigger a re-render
    const colors = this.config.colors || {};
    const colorKey = JSON.stringify(colors);
    const themeKey = (this.config.theme || 'auto') + '-' + isDarkTheme + '-' + colorKey;

    // Only re-inject theme CSS when the effective theme/colors actually change.
    if (themeKey !== this._appliedThemeKey && haCard) {
      this._appliedThemeKey = themeKey;

      let style = haCard.querySelector('style#victron-theme');
      if (!style) {
        style = document.createElement('style');
        style.id = 'victron-theme';
        haCard.appendChild(style);
      }

      // Build override block from editor color config
      const colorOverrides = `
        ha-card {
          ${colors.boxShadow ? `--box-shadow-color: ${colors.boxShadow};` : ''}
          ${colors.anchor    ? `--anchor-color: ${colors.anchor};`        : ''}
        }
        ${colors.graph    ? `.line g path { stroke: ${colors.graph} !important; }` : ''}
        ${colors.ball     ? `.ball { fill: ${colors.ball} !important; }` : ''}
        ${colors.textMain ? `.boxSensor1, .boxSensor1 * { color: ${colors.textMain} !important; }` : ''}
        ${colors.textSub  ? `.boxSensor2, .boxSensor2 *, .headerEntity, .headerEntity *, .boxTitle, .boxTitle * { color: ${colors.textSub} !important; }` : ''}
      `;

      let cssText;
      if (this.config.theme === 'transparent') {
        const baseCSS = isDarkTheme ? cssDataDark() : cssDataLight();
        cssText = baseCSS + `
          ha-card { background: transparent !important; box-shadow: none !important; }
          .dashboard { background-color: transparent !important; }
        ` + colorOverrides;
        haCard.style.background = 'transparent';
        haCard.style.boxShadow = 'none';
        this._isDark = isDarkTheme;
      } else if ((isDarkTheme && (this.config.theme || 'auto') === 'auto') || this.config.theme === 'dark') {
        cssText = cssDataDark() + colorOverrides;
        haCard.style.background = '';
        haCard.style.boxShadow = '';
        this._isDark = true;
      } else {
        cssText = cssDataLight() + colorOverrides;
        haCard.style.background = '';
        haCard.style.boxShadow = '';
        this._isDark = false;
      }

      // CSS auf diese Karteninstanz begrenzen
      style.textContent = scopeCss(cssText, `[data-vrm-card="${this._instanceId}"]`);

      // Farbe der Kugeln/Linien hängt vom Theme ab → Linien neu zeichnen
      libVenus.razDashboardOldWidth(this.content);
    }

    // mise en pause (ou ne pas aller plus loin) si mode demo
    if (this.config.demo === true) return;

    // recuperation des parametres de la carte
    const devices = this.config.devices || {};
    const styles = this.config.styles || {};

    // remplissage des box avec les parametres donnés
    libVenus.fillBox(this.config, styles, this._isDark, hass, this.content);

    // verification de changement de taille... si oui re-creation des lignes
    libVenus.checkReSize(devices, this._isDark, this.content, this.config);

    // verification des valeurs pour inversion de l'anim path
    libVenus.checkForReverse(devices, hass, this.content);

    // Lancement initial de startPeriodicTask (Historie für Graphen)
    if (!this._periodicTaskStarted) {
      this._periodicTaskStarted = true; // sofort setzen → kein Mehrfachstart
      libVenus.startPeriodicTask(this.config, hass, this.content)
        .then((ok) => { if (!ok) this._periodicTaskStarted = false; })
        .catch(() => { this._periodicTaskStarted = false; });
    }
  }

  get hass() {
    return this._hass;
  }

  // Méthode pour générer l'élément de configuration
  static getConfigElement(hass) {
    const editor = document.createElement(EDITOR_TAG);
    if (hass) editor.hass = hass;
    return editor;
  }

  static getStubConfig(hass) {
    // get available power entities
    return libVenus.getDefaultConfig(hass);
  }

  // Höhe der Karte ≈ 60 % der Breite → ca. 6 Masonry-Einheiten
  getCardSize() {
    return 6;
  }

  // Sections-Dashboard: volle Breite als Standard
  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  // Wenn die Karte wieder in den DOM eingehängt wird (z.B. Tab-Wechsel), Animation neu starten
  connectedCallback() {
    if (this.content) libVenus.razDashboardOldWidth(this.content);
    if (this._hass && this.config) this.hass = this._hass;
  }

  // Fonction de nettoyage si la carte est retirée
  disconnectedCallback() {
    if (this.content) libVenus.clearAllIntervals(this.content); // Arrêter toutes les tâches
    this._periodicTaskStarted = false;
  }

}

if (!customElements.get('victron-vrm-api-card')) {
  customElements.define('victron-vrm-api-card', VictronVrmApiCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === 'victron-vrm-api-card')) {
  window.customCards.push({
    type: 'victron-vrm-api-card',
    name: 'Victron VRM API Card',
    preview: true,
    description: 'A Dashboard that replicates Venus OS GUI v2 for Victron VRM Integration.',
  });
}
