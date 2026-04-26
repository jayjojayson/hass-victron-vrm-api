/*

 switch auto theme clair/sombre ou choix manuel
 
 donc onglet param en plus

*/

console.info(
  "%c 🗲 %c - %cVictron VRM API Card%c - %c 🗲 \n%c version 0.1.18 ",
  "color: white; font-weight: bold; background: black",
  "color: orange; font-weight: bold; background: blue; font-weight: bold;",
  "color: white; font-weight: bold; background: blue; text-decoration: underline; text-decoration-color: orange; text-decoration-thickness: 5px; text-underline-offset: 2px;",
  "color: orange; font-weight: bold; background: blue; font-weight: bold;",
  "color: white; font-weight: bold; background: black",
  "color: white; font-weight: bold; background: grey"
);

import './editor.js';
import * as libVenus from './lib-venus.js';

import { cssDataDark } from './css-dark.js';
import { cssDataLight } from './css-light.js';

class VictronVrmApiCard extends HTMLElement {

  static isDark = true;

  static periodicTaskStarted = false;

  static cycle = 0;

  constructor() {
    super();
  }

  setConfig(config) {

    this.config = config;

    // Crée la structure statique après avoir reçu la configuration
    if (!this.content) {
      this._createCardStructure();
    } else {
      // Config wurde geändert (z.B. Editor-Save): Linien neu zeichnen
      libVenus.razDashboardOldWidth(this.content);
    }
  }

  _createCardStructure() {

    // Initialize the content if it's not there yet.
    if (!this.content) {

      const cardElem = document.createElement('ha-card');
      this.appendChild(cardElem);

      const contElem = document.createElement('div');
      contElem.setAttribute('id', 'db-container');
      contElem.setAttribute('class', 'db-container');
      cardElem.appendChild(contElem);

      this.content = this.querySelector("div");

      window.contElem = this.content;

    }

    // recuperation des parametres
    const param = this.config.param || [];

    // rendu de la structure de base de la carte (en mode normal ou demo "image")
    libVenus.baseRender(this.config, this.content);

    // recuperation des quantités de box a créer par colonne dans les parametres
    const boxCol1 = param.boxCol1 ? Math.min(Math.max(param.boxCol1, 1), 4) : 1;
    const boxCol2 = param.boxCol2 ? Math.min(Math.max(param.boxCol2, 1), 2) : 1;
    const boxCol3 = param.boxCol3 ? Math.min(Math.max(param.boxCol3, 1), 4) : 1;

    // ajout des box
    if (this.config.demo !== true) libVenus.addBox(boxCol1, boxCol2, boxCol3, this.content);

    // ajout des ancres d'attache des lignes
    if (this.config.demo !== true) libVenus.addAnchors(this.config, this.content);

  }

  set hass(hass) {

    this._hass = hass;

    if (this._hass) {

      // Check the selected theme
      const isDarkTheme = this._hass.themes.darkMode;

      // Include color config in the cache key so color changes trigger a re-render
      const colors = this.config.colors || {};
      const colorKey = JSON.stringify(colors);
      const themeKey = (this.config.theme || 'auto') + '-' + isDarkTheme + '-' + colorKey;

      // Only re-inject theme CSS when the effective theme/colors actually change.
      if (themeKey !== this._appliedThemeKey) {
        this._appliedThemeKey = themeKey;

        let style = this.querySelector('style#victron-theme');
        if (!style) {
          style = document.createElement('style');
          style.id = 'victron-theme';
          this.querySelector('ha-card').appendChild(style);
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

        if (this.config.theme === 'transparent') {
          const baseCSS = isDarkTheme ? cssDataDark() : cssDataLight();
          style.textContent = baseCSS + `
            ha-card { background: transparent !important; box-shadow: none !important; }
            .dashboard { background-color: transparent !important; }
          ` + colorOverrides;
          this.querySelector('ha-card').style.background = 'transparent';
          this.querySelector('ha-card').style.boxShadow = 'none';
          VictronVrmApiCard.isDark = isDarkTheme;
        } else if ((isDarkTheme && this.config.theme === 'auto') || this.config.theme === 'dark') {
          style.textContent = cssDataDark() + colorOverrides;
          this.querySelector('ha-card').style.background = '';
          this.querySelector('ha-card').style.boxShadow = '';
          VictronVrmApiCard.isDark = true;
        } else {
          style.textContent = cssDataLight() + colorOverrides;
          this.querySelector('ha-card').style.background = '';
          this.querySelector('ha-card').style.boxShadow = '';
          VictronVrmApiCard.isDark = false;
        }
      }
    }

    // mise en pause (ou ne pas aller plus loin) si mode demo
    if (this.config.demo === true) return;

    // mise en pause (ou ne pas aller plus loin) si debug
    if (VictronVrmApiCard.cycle >= 10) return;

    // recuperation des parametres de la carte
    const devices = this.config.devices || [];
    const styles = this.config.styles || "";

    // remplissage des box avec les parametres donnés
    libVenus.fillBox(this.config, styles, VictronVrmApiCard.isDark, hass, this.content);

    // verification de changement de taille... si oui re-creation des lignes
    libVenus.checkReSize(devices, VictronVrmApiCard.isDark, this.content, this.config);

    // verification des valeurs pour inversion de l'anim path
    libVenus.checkForReverse(devices, hass, this.content);

    // Lancement initial de startPeriodicTask
    if (!this.periodicTaskStarted) {
      // console.log('Tentative de démarrage de startPeriodicTask...');
      const taskStarted = libVenus.startPeriodicTask(this.config, hass);

      if (taskStarted) {
        // console.log('startPeriodicTask démarré avec succès.');
        this.periodicTaskStarted = true; // Marquer comme démarrée
      } else {
        // console.warn('startPeriodicTask a échoué. Elle sera relancée lors de la prochaine itération.');
        this.periodicTaskStarted = false; // Rester sur false pour retenter
      }
    }

    // VictronVrmApiCard.cycle++;
  }

  // Méthode pour générer l'élément de configuration
  static getConfigElement(hass) {
    const editor = document.createElement('venus-os-editor');
    editor.hass = hass; // Passe explicitement l'instance de hass à l'éditeur
    return editor;
  }

  static getStubConfig(hass) {
    // get available power entities
    return libVenus.getDefaultConfig(hass);
  }

  // Méthode pour récupérer la taille de la carte
  getCardSize() {
    return 1;
  }

  // Wenn die Karte wieder in den DOM eingehängt wird (z.B. Tab-Wechsel), Animation neu starten
  connectedCallback() {
    if (this.content) libVenus.razDashboardOldWidth(this.content);
  }

  // Fonction de nettoyage si la carte est retirée
  disconnectedCallback() {
    libVenus.clearAllIntervals(this.content); // Arrêter toutes les tâches
  }

}
customElements.define('victron-vrm-api-card', VictronVrmApiCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'victron-vrm-api-card',
  name: 'Victron VRM API Card',
  preview: true,
  description: 'A Dashboard that replicates Venus OS GUI v2 for Victron VRM Integration.',
});
