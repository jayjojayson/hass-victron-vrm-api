/**********************************************/
/* "variable" permettant de lister les panels */
/* qui sont "expended"                        */
/**********************************************/
let expandedPanelsState = new Set();

/**********************************************/
/* "variable" permettant de lister les events */
/* sur les objets et eviter de les recrer     */
/**********************************************/
export const eventHandlers = new WeakMap();

/**************************************/
/* fonctions permettant la traduction */
/* de l'editeur graphique             */
/**************************************/
let translations = {}; // Stocke les traductions chargées

export async function loadTranslations(appendTo) {
    const lang = appendTo._hass?.language || "en"; // Langue HA, ou "en" par défaut
    try {
        const response = await import(`./lang-${lang}.js`);
        translations = response.default;
    } catch (error) {
        console.error("Erreur de chargement de la langue :", error);
        const response = await import(`./lang-en.js`);
        translations = {};
    }
}

export function t(func, key) {
    return translations?.[func]?.[key] || `⚠️ ${func}.${key} ⚠️`; // Si absent, affiche une alerte visuelle
}

/***************************************/
/* fonction de rendu du tab pricipal : */
/***************************************/
export function tab1Render(appendTo) {
    
    const tabContent = appendTo.shadowRoot.querySelector('#tab-content');
    tabContent.innerHTML = '';
    
    // Ajout du contenu à l'élément appendTo
    const editorDiv = document.createElement('div');
    editorDiv.classList.add('editor');
    
    /*// Mode Demo
    const demoRow = document.createElement('div');
    demoRow.classList.add('row');
    const demoLabel = document.createElement('div');
    demoLabel.classList.add('cell', 'left');
    demoLabel.textContent = t("tab1Render", "demo_mode");//'Mode Demo';
    const demoSwitchContainer = document.createElement('div');
    demoSwitchContainer.classList.add('cell', 'right');
    const demoSwitch = document.createElement('ha-switch');
    demoSwitch.setAttribute('data-path', 'demo');
    if (appendTo._config.demo === true) demoSwitch.setAttribute('checked', '');
    demoSwitchContainer.appendChild(demoSwitch);
    demoRow.appendChild(demoLabel);
    demoRow.appendChild(demoSwitchContainer);
    editorDiv.appendChild(demoRow);*/
    
    // Choix du thème
    const themeRow = document.createElement('div');
    themeRow.classList.add('col');
    const themeLabel = document.createElement('div');
    themeLabel.classList.add('left');
    themeLabel.textContent = t("tab1Render", "theme_choice");//'Choix du theme de la carte :';
    const radioGroup = document.createElement('div');
    radioGroup.classList.add('radio-group', 'row');
    const themeOptions = [
      { label: t("tab1Render", "light"), value: 'light' }, // claire
      { label: t("tab1Render", "dark"), value: 'dark' }, // sombre
      { label: t("tab1Render", "auto"), value: 'auto' }, // auto
      { label: t("tab1Render", "transparent"), value: 'transparent' }, // transparent
    ];
    
    // Vérifiez si aucune option n'est définie dans le YAML
    const defaultTheme = appendTo._config.theme || 'auto';
    
    themeOptions.forEach(option => {
      const formfield = document.createElement('ha-formfield');
      formfield.setAttribute('label', option.label);
      formfield.classList.add('cell');
      const radio = document.createElement('ha-radio');
      radio.setAttribute('name', 'themeSelect');
      radio.setAttribute('data-path', 'theme');
      radio.setAttribute('value', option.value);
      if (defaultTheme  === option.value) radio.setAttribute('checked', '');
      formfield.appendChild(radio);
      radioGroup.appendChild(formfield);
    });
    
    themeRow.appendChild(themeLabel);
    themeRow.appendChild(radioGroup);
    editorDiv.appendChild(themeRow);
    
    // Nombre de "Devices" pour chaque colonne
    const devicesRow = document.createElement('div');
    devicesRow.classList.add('col');
    const devicesLabel = document.createElement('div');
    devicesLabel.classList.add('left');
    devicesLabel.textContent = t("tab1Render", "devices_per_column"); //'Nombre de "Devices" pour chaque colonne :';
    
    const devicesInputs = [
      { id: 'boxCol1', label: 'col. 1', value: appendTo._config.param?.boxCol1 ?? 1, min: 1, max: 4, step: 1 },
      { id: 'boxCol2', label: 'col. 2', value: appendTo._config.param?.boxCol2 ?? 1, min: 1, max: 2, step: 1 },
      { id: 'boxCol3', label: 'col. 3', value: appendTo._config.param?.boxCol3 ?? 1, min: 1, max: 4, step: 1 },
    ];
    
    const devicesRowContainer = document.createElement('div');
    devicesRowContainer.classList.add('row');
    devicesInputs.forEach(input => {
      const textfield = document.createElement('ha-textfield');
      textfield.classList.add('cell');
      textfield.setAttribute('id', input.id);
      textfield.setAttribute('data-path', `param.${input.id}`);
      textfield.setAttribute('label', input.label);
      textfield.setAttribute('value', input.value);
      textfield.setAttribute('type', 'number');
      textfield.setAttribute('min', input.min);
      textfield.setAttribute('max', input.max);
      textfield.setAttribute('step', input.step);
      devicesRowContainer.appendChild(textfield);
    });
    devicesRow.appendChild(devicesLabel);
    devicesRow.appendChild(devicesRowContainer);
    editorDiv.appendChild(devicesRow);
    
    // Taille de la font dans les zones des "Devices"
    const fontSizeRow = document.createElement('div');
    fontSizeRow.classList.add('col');
    const fontSizeLabel = document.createElement('div');
    fontSizeLabel.classList.add('row');
    fontSizeLabel.textContent = t("tab1Render", "font_size_zones");// 'Taille de la font dans les zones des "Devices" :';
    fontSizeRow.appendChild(fontSizeLabel);
    
    // Définit les sections
    const fontSizeSections = [
      { label: t("tab1Render", "in_header"), path: 'header', id: 'header' }, // 'dans le header'
      { label: t("tab1Render", "in_devices"), path: 'sensor', id: 'sensor' }, // 'dans le Devices'
      { label: t("tab1Render", "in_footer"), path: 'footer', id: 'footer' }, // 'dans le footer'
    ];
    
    // Boucle sur chaque section
    fontSizeSections.forEach(section => {
      const sectionRow = document.createElement('div');
      sectionRow.classList.add('row');
    
      const labelCell = document.createElement('div');
      labelCell.classList.add('row', 'cellx1-5');
      const labelText = document.createElement('div');
      labelText.classList.add('cell', 'left');
      labelText.textContent = `- ${section.label}`;
      labelCell.appendChild(labelText);
      sectionRow.appendChild(labelCell);
    
      const inputCell = document.createElement('div');
      inputCell.classList.add('cell', 'right');
      const textfield = document.createElement('ha-textfield');
      textfield.setAttribute('id', section.id);
      textfield.setAttribute('data-path', `styles.${section.path}`);
      textfield.setAttribute('data-group', section.path);
      textfield.setAttribute('label', t("tab1Render", "font_size"));
      textfield.setAttribute('type', 'number');
      textfield.setAttribute('min', 1);
      textfield.setAttribute('step', 1);
    
      // Vérifie si la clé existe avant de définir sa valeur ou d'activer le champ
      if (appendTo._config.styles && appendTo._config.styles[section.path]) {
        if (appendTo._config.styles[section.path] === 'auto') {
          textfield.setAttribute('disabled', '');
        } else {
          textfield.setAttribute('value', appendTo._config.styles[section.path]);
        }
      }
      
      inputCell.appendChild(textfield);
      sectionRow.appendChild(inputCell);
    
      const switchCell = document.createElement('div');
      switchCell.classList.add('row', 'cell');
      const switchContainer = document.createElement('div');
      switchContainer.classList.add('cell', 'right');
      const fontSwitch = document.createElement('ha-switch');
      fontSwitch.setAttribute('data-path', `styles.${section.path}`);
      fontSwitch.setAttribute('data-group', section.path);
    
      // Activer le switch uniquement si la clé existe et que sa valeur est "auto"
      if (appendTo._config.styles && appendTo._config.styles[section.path] === 'auto') {
        fontSwitch.setAttribute('checked', '');
      }
    
      switchContainer.appendChild(fontSwitch);
      switchCell.appendChild(switchContainer);
      sectionRow.appendChild(switchCell);
    
      fontSizeRow.appendChild(sectionRow);
    });
    
    editorDiv.appendChild(fontSizeRow);

    // Farbpicker
    const colorsRow = document.createElement('div');
    colorsRow.classList.add('col');
    const colorsLabel = document.createElement('div');
    colorsLabel.classList.add('left');
    colorsLabel.textContent = t("tab1Render", "colors_title");
    colorsRow.appendChild(colorsLabel);

    const colorOptions = [
      { label: t("tab1Render", "box_shadow_color"), path: 'colors.boxShadow',  defaultDark: '#38619b', defaultLight: '#38619b' },
      { label: t("tab1Render", "anchor_color"),     path: 'colors.anchor',    defaultDark: '#38619b', defaultLight: '#38619b' },
      { label: t("tab1Render", "graph_color"),      path: 'colors.graph',     defaultDark: '#4369a2', defaultLight: '#4369a2' },
      { label: t("tab1Render", "ball_color"),       path: 'colors.ball',      defaultDark: '#4369a2', defaultLight: '#4369a2' },
      { label: t("tab1Render", "text_main_color"),  path: 'colors.textMain',  defaultDark: '#ffffff',  defaultLight: '#484848' },
      { label: t("tab1Render", "text_sub_color"),   path: 'colors.textSub',   defaultDark: '#aaaaaa', defaultLight: '#aaaaaa' },
    ];

    const makeColorRow = (opts) => {
      const row = document.createElement('div');
      row.style.cssText = 'display:flex;gap:8px;margin-top:6px;';
      opts.forEach(opt => {
        const cell = document.createElement('div');
        cell.style.cssText = 'display:flex;flex-direction:column;align-items:center;width:56px;flex-shrink:0;';
        const lbl = document.createElement('div');
        lbl.style.cssText = 'font-size:0.75em;text-align:center;line-height:1.2;margin-bottom:3px;word-break:break-word;min-height:3em;display:flex;align-items:flex-end;justify-content:center;';
        lbl.textContent = opt.label;
        const pathParts = opt.path.split('.');
        const currentVal = appendTo._config?.[pathParts[0]]?.[pathParts[1]] || '';
        const input = document.createElement('input');
        input.type = 'color';
        input.dataset.path = opt.path;
        input.style.cssText = 'width:56px;height:32px;border:none;background:none;cursor:pointer;padding:0;box-sizing:border-box;';
        input.value = currentVal || opt.defaultDark;
        cell.appendChild(lbl);
        cell.appendChild(input);
        row.appendChild(cell);
      });
      return row;
    };
    colorsRow.appendChild(makeColorRow(colorOptions.slice(0, 3)));
    colorsRow.appendChild(makeColorRow(colorOptions.slice(3)));
    editorDiv.appendChild(colorsRow);

    // Ball-Größen-Slider
    const ballSizeRow = document.createElement('div');
    ballSizeRow.style.cssText = 'display:flex;align-items:center;gap:10px;margin-top:12px;';
    const ballSizeLbl = document.createElement('div');
    ballSizeLbl.classList.add('left');
    ballSizeLbl.textContent = t("tab1Render", "ball_size");
    ballSizeLbl.style.cssText = 'flex-shrink:0;min-width:120px;';
    const ballSizeVal = document.createElement('span');
    ballSizeVal.style.cssText = 'min-width:24px;text-align:right;font-weight:bold;';
    const currentBallSize = appendTo._config?.param?.ballSize ?? 4;
    ballSizeVal.textContent = currentBallSize;
    const ballSizeInput = document.createElement('input');
    ballSizeInput.type = 'range';
    ballSizeInput.min = '2';
    ballSizeInput.max = '15';
    ballSizeInput.step = '1';
    ballSizeInput.value = currentBallSize;
    ballSizeInput.dataset.path = 'param.ballSize';
    ballSizeInput.style.cssText = 'flex:1;cursor:pointer;';
    ballSizeInput.addEventListener('input', () => { ballSizeVal.textContent = ballSizeInput.value; });
    ballSizeRow.appendChild(ballSizeLbl);
    ballSizeRow.appendChild(ballSizeInput);
    ballSizeRow.appendChild(ballSizeVal);
    editorDiv.appendChild(ballSizeRow);

    // Ajouter le contenu au DOM
    tabContent.appendChild(editorDiv);

}

/**********************************************/
/* fonction de rendu du contenu de tabs col : */
/**********************************************/
export function tabColRender(col, appendTo) {
    
    const boxCol = appendTo._config.param[`boxCol${col}`] ?? 1;
    
    const tabContent = appendTo.shadowRoot.querySelector('#tab-content');
    tabContent.innerHTML = '';

    let tabsHTML = ''; // Initialise une variable pour stocker les onglets
    for (let i = 1; i <= boxCol; i++) {
        tabsHTML += `<sl-tab slot="nav" panel="anchor" label="1-${i}" data-tab="${i - 1}">${col}-${i}</sl-tab>`;
    }
            
    tabContent.innerHTML = `
        <div class="devices-editor">
            <sl-tab-group id="subTab-group">
                ${tabsHTML}
            </sl-tab-group>
        
            <sl-tab-panel id="sl-subTab-content" name="anchor">
              <div id="subTab-content" class="subTab-content">
                <!-- Le contenu de la section active sera affiché ici -->
              </div>
            </sl-tab-panel>
        </div>
    `;
            
    const tabBar = tabContent.querySelector('#subLink-container');
    if (tabBar && typeof appendTo._currentSubTab === 'number') {
        tabBar.activeIndex = appendTo._currentSubTab; // Définit l'onglet actif
    }
    
    attachSubLinkClick(appendTo);
    renderSubTabContent(col, appendTo);
}

/************************************************/
/* fonction d'appel de la fonction de rendu des */
/* sous tabs                                    */
/* me demandez pas pourquoi j'ai fait deux      */
/* foncions, je ne saisplus                     */
/************************************************/
export function renderSubTabContent(col, appendTo) {
    const subTabContent = appendTo.shadowRoot.querySelector('#subTab-content');
    const boxId = `${col}-${appendTo._currentSubTab+1}`;
    subtabRender(boxId, appendTo._config, appendTo._hass, appendTo);
    attachInputs(appendTo); // Appeler la fonction attachInputs déjà présente
}

/************************************************/
/* fonction de rendu du contenu des sous-tabs : */
/* toutes les zones de conf des box en somme    */
/************************************************/
export function subtabRender(box, config, hass, appendTo) {
    
    const subTabContent = appendTo.shadowRoot.querySelector('#subTab-content');
    
    let leftQty = 0, topQty = 0, bottomQty = 0, rightQty = 0;
    
    // Vérifier si les ancres existent dans la configuration
    const anchors = config?.devices?.[box]?.anchors ? String(config?.devices?.[box]?.anchors).split(', ') : [];
    
    let thisAllAnchors = [];

    // Parcourir les ancres pour extraire les quantités par côté
    anchors.forEach((anchor) => {
        const [side, qtyStr] = anchor.split('-'); // Exemple : "L-2" devient ["L", "2"]
        const qty = parseInt(qtyStr, 10); // Convertir la quantité en nombre
    
        if (side === 'L') leftQty += qty;
        else if (side === 'T') topQty += qty;
        else if (side === 'B') bottomQty += qty;
        else if (side === 'R') rightQty += qty;
        
        for (let i = 1; i <= qty; i++) {
            thisAllAnchors.push(`${side}-${i}`);
        }
    });
    
    thisAllAnchors.sort();
    
    const OtherAllAnchors = getAllAnchorsExceptCurrent(config, box);
    //console.log(box + " : " + OtherAllAnchors);
    
    subTabContent.innerHTML = `
        
        <!-- ICON ET NOM -->
        <ha-expansion-panel expanded outlined id="subPanel_header" header="${t("subtabRender", "header_title")}">
            <div class="col inner">
                <div class="row">
                    <ha-icon-picker
                        class="cell"
                        label="${t("subtabRender", "icon_choice")}"
                        id="device_icon"
                        data-path="devices.${box}.icon"
                    >
                    </ha-icon-picker>
                    <ha-textfield 
                        class="cell"
                        label="${t("subtabRender", "name_choice")}"
                        id="device_name"
                        data-path="devices.${box}.name"
                    ></ha-textfield>
                </div>
            </div>
        </ha-expansion-panel>
        
        <!-- ENTITE 1 et 2-->
        <ha-expansion-panel expanded outlined id="subPanel_entities" header="${t("subtabRender", "sensor_title")}">
            <div class="col inner">
                <ha-selector
                    label="${t("subtabRender", "entity_choice")}"
                    id="device_sensor"
                    data-path="devices.${box}.entity"
                ></ha-selector>
                <ha-selector
                    label="${t("subtabRender", "entity2_choice")}"
                    id="device_sensor2"
                    data-path="devices.${box}.entity2"
                ></ha-selector>
    
                <!-- SWITCHS GRAPH ET GAUGE -->
                <div class="row">
                    <div class="row cell">
                        ${t("subtabRender", "enable_graph")} :
                        <ha-switch class="cell right" 
                            id="graph_switch"
                            data-path="devices.${box}.graph" 
                        ></ha-switch>
                    </div>
                    <div id="gauge_div" class="row cell">
                        ${t("subtabRender", "enable_gauge")} :
                        <ha-switch class="cell right"
                            id="gauge_switch"
                            data-path="devices.${box}.gauge" 
                        ></ha-switch>
                    </div>
                </div>
            </div>
        </ha-expansion-panel>
        
        <!-- HEADER ET FOOTER 1 -->
        <ha-expansion-panel expanded outlined id="subPanel_entities2" header="${t("subtabRender", "header_footer_title")}">
            <div class="col inner">
                <div class="row">
                    <ha-selector
                        label="${t("subtabRender", "entity_header")}"
                        id="header_sensor"
                        data-path="devices.${box}.headerEntity"
                    ></ha-selector>
                    <ha-selector
                        label="${t("subtabRender", "entity_footer")}"
                        id="footer1_sensor"
                        data-path="devices.${box}.footerEntity1"
                    ></ha-selector>
                </div>
                
                <!-- FOOTER 2 ET 3 -->
                <div class="row">
                    <ha-selector
                        label="${t("subtabRender", "entity2_footer")}"
                        id="footer2_sensor"
                        data-path="devices.${box}.footerEntity2"
                    ></ha-selector>
                    <ha-selector
                        label="${t("subtabRender", "entity3_footer")}"
                        id="footer3_sensor"
                        data-path="devices.${box}.footerEntity3"
                    ></ha-selector>
                </div>
            </div>
        </ha-expansion-panel>
        
        <!-- ANCHORS -->
        <ha-expansion-panel outlined id="subPanel_anchors" header="${t("subtabRender", "anchor_title")}">
            <div class="col inner">
                <div class="row">
                    <div class="col cell">
                        <label style="font-size:0.85em;color:var(--secondary-text-color);">${t("subtabRender", "left_qtyBox")}</label>
                        <input class="anchor" type="number" id="anchor_left"
                            data-path="devices.${box}.anchors"
                            value="${leftQty}" min="0" max="3" step="1"
                            style="width:100%;padding:6px 4px;background:var(--card-background-color,#1c2536);color:var(--primary-text-color);border:1px solid var(--divider-color,#404040);border-radius:4px;text-align:center;"
                        >
                    </div>
                    <div class="col cell">
                        <label style="font-size:0.85em;color:var(--secondary-text-color);">${t("subtabRender", "top_qtyBox")}</label>
                        <input class="anchor" type="number" id="anchor_top"
                            data-path="devices.${box}.anchors"
                            value="${topQty}" min="0" max="3" step="1"
                            style="width:100%;padding:6px 4px;background:var(--card-background-color,#1c2536);color:var(--primary-text-color);border:1px solid var(--divider-color,#404040);border-radius:4px;text-align:center;"
                        >
                        <label style="font-size:0.85em;color:var(--secondary-text-color);margin-top:6px;">${t("subtabRender", "bottom_qtyBox")}</label>
                        <input class="anchor" type="number" id="anchor_bottom"
                            data-path="devices.${box}.anchors"
                            value="${bottomQty}" min="0" max="3" step="1"
                            style="width:100%;padding:6px 4px;background:var(--card-background-color,#1c2536);color:var(--primary-text-color);border:1px solid var(--divider-color,#404040);border-radius:4px;text-align:center;"
                        >
                    </div>
                    <div class="col cell">
                        <label style="font-size:0.85em;color:var(--secondary-text-color);">${t("subtabRender", "right_qtyBox")}</label>
                        <input class="anchor" type="number" id="anchor_right"
                            data-path="devices.${box}.anchors"
                            value="${rightQty}" min="0" max="3" step="1"
                            style="width:100%;padding:6px 4px;background:var(--card-background-color,#1c2536);color:var(--primary-text-color);border:1px solid var(--divider-color,#404040);border-radius:4px;text-align:center;"
                        >
                    </div>
                </div>
            </div>
        </ha-expansion-panel>
        
        <!-- LINKS -->
        <div class="contMenu">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div class="headerMenu">${t("subtabRender", "add_links")}</div>
                <ha-icon-button id="add-link-button" aria-label="${t("subtabRender", "add_link")}">
                    <ha-icon icon="mdi:plus" style="display: flex;"></ha-icon>
                </ha-icon-button>
            </div>
            <div id="link-container" class="col noGap"></div>
        </div>
    `;
    
    // Réappliquer l'attribut "expanded" aux panneaux qui l'avaient avant
    // Sicherstellen dass die drei Haupt-Panels beim ersten Render im State sind
    ['subPanel_header', 'subPanel_entities', 'subPanel_entities2'].forEach(id => {
        expandedPanelsState.add(id);
    });
    expandedPanelsState.forEach(id => {
        const panel = subTabContent.querySelector(`ha-expansion-panel#${id}`);
        if (panel) {
            panel.setAttribute("expanded", "");
        }
    });
            
    const iconPicker = subTabContent.querySelector('#device_icon');
    const nameField = subTabContent.querySelector('#device_name');
    const entityPicker = subTabContent.querySelector('#device_sensor');
    entityPicker.selector = { entity: {} };
    entityPicker.required = false;
    const entity2Picker = subTabContent.querySelector('#device_sensor2');
    entity2Picker.selector = { entity: {} };
    entity2Picker.required = false;
    const graphSwitch = subTabContent.querySelector('#graph_switch');
    const gaugeSwitch = subTabContent.querySelector('#gauge_switch');
    const headerEntity = subTabContent.querySelector('#header_sensor');
    headerEntity.selector = { entity: {} };
    headerEntity.required = false;
    const footerEntity1 = subTabContent.querySelector('#footer1_sensor');
    footerEntity1.selector = { entity: {} };
    footerEntity1.required = false;
    const footerEntity2 = subTabContent.querySelector('#footer2_sensor');
    footerEntity2.selector = { entity: {} };
    footerEntity2.required = false;
    const footerEntity3 = subTabContent.querySelector('#footer3_sensor');
    footerEntity3.selector = { entity: {} };
    footerEntity3.required = false;
    // Werte sind jetzt direkt per value-Attribut im Template gesetzt – kein nachträgliches .value nötig
    
    // Après avoir inséré le contenu, configure les valeurs pour ha-icon-picker et ha-entity-picker
    nameField.value = config?.devices?.[box]?.name ?? "";
    iconPicker.value = config?.devices?.[box]?.icon ?? ""; 
    entityPicker.value = config?.devices?.[box]?.entity ?? "";
    entity2Picker.value = config?.devices?.[box]?.entity2 ?? "";
    headerEntity.value = config?.devices?.[box]?.headerEntity ?? "";
    footerEntity1.value = config?.devices?.[box]?.footerEntity1 ?? "";
    footerEntity2.value = config?.devices?.[box]?.footerEntity2 ?? "";
    footerEntity3.value = config?.devices?.[box]?.footerEntity3 ?? "";
    
    iconPicker.hass = hass; // Passe l'objet directement ici
    entityPicker.hass = hass; // Passe l'objet directement ici
    entity2Picker.hass = hass; // Passe l'objet directement ici
    headerEntity.hass = hass; // Passe l'objet directement ici  
    footerEntity1.hass = hass; // Passe l'objet directement ici
    footerEntity2.hass = hass; // Passe l'objet directement ici
    footerEntity3.hass = hass; // Passe l'objet directement ici
           
    if (config?.devices?.[box]?.graph === true) graphSwitch.setAttribute('checked', '');
    
    const entity = hass.states?.[entityPicker.value];
    const unit = entity?.attributes?.unit_of_measurement;

    if(unit !== '%' ) {
        gaugeSwitch.setAttribute('disabled', '');
        gaugeSwitch.setAttribute("title", t("subtabRender", "warning_gauge"));
    } else if (config.devices?.[box]?.gauge === true) gaugeSwitch.setAttribute('checked', '');
    
    
    const linkContainer = subTabContent.querySelector('#link-container');
    const addLinkButton = subTabContent.querySelector('#add-link-button');
    
    Object.entries(config.devices?.[box]?.link || {}).forEach(([linkKey, link]) => {
        
        addLink(linkKey, box, hass, thisAllAnchors, OtherAllAnchors, appendTo);

    });
    
    addLinkButton.addEventListener('click', (e) => {
        addLink(linkContainer.children.length+1, box, hass, thisAllAnchors, OtherAllAnchors, appendTo);
    });
    
    function trackExpansionState() {
    subTabContent.querySelectorAll("ha-expansion-panel").forEach(panel => {
            panel.addEventListener("expanded-changed", (event) => {
                if (event.detail.expanded) {
                    expandedPanelsState.add(panel.id);
                } else {
                    expandedPanelsState.delete(panel.id);
                }
            });
        });
    }
    
    // Appelle cette fonction au chargement initial pour capturer les événements
    trackExpansionState();
}

export function getAllAnchorsExceptCurrent(config, currentBox) {
    let allAnchors = [];

    Object.entries(config.devices || {}).forEach(([boxKey, device]) => {
        if (boxKey === currentBox || !device.anchors) return; // On saute le device en cours

        const anchors = String(device.anchors).split(', ');

        anchors.forEach((anchor) => {
            const [side, qtyStr] = anchor.split('-'); // Exemple : "L-2" → ["L", "2"]
            const qty = parseInt(qtyStr, 10);

            for (let i = 1; i <= qty; i++) {
                allAnchors.push(`${boxKey}_${side}-${i}`); // Associer l'ancre au device
            }
        });
    });

    allAnchors.sort();
    return allAnchors;
}

export function addLink(index, box, hass, thisAllAnchors, OtherAllAnchors, appendTo) {
    
    const subTabContent = appendTo.shadowRoot.querySelector('#subTab-content');
    const linkContainer = subTabContent.querySelector('#link-container');
    const addLinkButton = subTabContent.querySelector('#add-link-button');
    
    const panel = document.createElement('ha-expansion-panel');
    panel.setAttribute('outlined', '');
    panel.setAttribute('expanded', '');
    panel.setAttribute('style', 'margin: 0px 0px 8px 0px');
        
    const _curStart = appendTo._config.devices?.[box]?.link?.[index]?.start ?? "";
    const _curEnd   = appendTo._config.devices?.[box]?.link?.[index]?.end   ?? "";
    const _selStyle = 'width:100%;padding:8px 4px;background:var(--card-background-color,#1c2536);color:var(--primary-text-color);border:1px solid var(--divider-color,#404040);border-radius:4px;cursor:pointer;';
    const _startOpts = thisAllAnchors.map(a => `<option value="${a}"${a === _curStart ? ' selected' : ''}>${a}</option>`).join('');
    const _endOpts   = OtherAllAnchors.map(a => `<option value="${a}"${a === _curEnd   ? ' selected' : ''}>${a}</option>`).join('');

    panel.innerHTML = `
        <div slot="header" style="display: flex; justify-content: space-between; align-items: center;">
            <span>Lien ${index}</span>
            <ha-icon-button id="add-link-button" aria-label="Ajouter un lien">
                <ha-icon icon="mdi:trash-can" style="display: flex;"></ha-icon>
            </ha-icon-button>
        </div>
        <div id="link-container" class="inner">
            <div class="col">
                <div class="row">
                    <div class="col cell">
                        <div style="font-size:0.85em;margin-bottom:4px;color:var(--secondary-text-color);">${t("addLink", "start")}</div>
                        <select id="start_link_${index}" data-path="devices.${box}.link.${index}.start" style="${_selStyle}">
                            <option value="">--</option>
                            ${_startOpts}
                        </select>
                    </div>
                    <div class="col cell">
                        <div style="font-size:0.85em;margin-bottom:4px;color:var(--secondary-text-color);">${t("addLink", "end")}</div>
                        <select id="end_link_${index}" data-path="devices.${box}.link.${index}.end" style="${_selStyle}">
                            <option value="">--</option>
                            ${_endOpts}
                        </select>
                    </div>
                </div>
                
                <div class="row">
                    <ha-selector class="cell"
                        label="${t("addLink", "entity_picker")}"
                        id="entity_link_${index}"
                        data-path="devices.${box}.link.${index}.entity" 
                    ></ha-selector>
                    
                    <div class="row cell">
                        ${t("addLink", "reverse")} :
                        <ha-switch class="cell right" 
                            id="inv_link_${index}"
                            data-path="devices.${box}.link.${index}.inv" 
                        ></ha-switch>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const path = `devices.${box}.link.${index}`;

    const deleteButton = panel.querySelector('ha-icon-button');
    deleteButton.addEventListener('click', () => {
        appendTo._config = updateConfigRecursively(appendTo._config, path, null, true);
        notifyConfigChange(appendTo);
        panel.remove();
    });

    linkContainer.appendChild(panel);

    const entityLink = panel.querySelector(`#entity_link_${index}`);
    entityLink.selector = { entity: {} };
    entityLink.required = false;
    entityLink.hass = hass;
    entityLink.value = appendTo._config.devices[box]?.link?.[index]?.entity ?? "";

    const invLink = panel.querySelector(`#inv_link_${index}`);
    if (appendTo._config.devices[box]?.link?.[index]?.inv === true) invLink.setAttribute('checked', '');
    
    attachLinkInputs(appendTo)
        
}

export function attachLinkInputs(appendTo) {
        
    // Listener pour les <select> start/end (remplace ha-combo-box)
    appendTo.shadowRoot.querySelectorAll('select[data-path]').forEach((selectEl) => {
        if (eventHandlers.has(selectEl)) return;
        const handleChange = (e) => {
            const key = selectEl.dataset.path;
            const value = e.target.value || null;
            if (key) {
                appendTo._config = updateConfigRecursively(appendTo._config, key, value, true);
                notifyConfigChange(appendTo);
            }
            document.dispatchEvent(new CustomEvent('config-changed', { detail: { redrawRequired: true } }));
        };
        selectEl.addEventListener('change', handleChange);
        eventHandlers.set(selectEl, handleChange);
    });
    
    // Listener pour les `ha-textfield` sauf les champs "anchor"
    appendTo.shadowRoot.querySelectorAll('ha-textfield').forEach((textField) => {
        
        if (eventHandlers.has(textField)) {
            //console.log("Événement déjà attaché à cet élément ha-textfield :", textField);
            return; // Ne rien faire si l'événement est déjà attaché
        }
        
        // Créer un nouveau gestionnaire d'événements
        const handleChange = (e) => {
            const key = textField.dataset.path;
            let value = e.target.value;
    
            // Gestion des valeurs en fonction du type de champ
            if (e.target.type === 'number') {
                // Si c'est un champ numérique
                if (!value || isNaN(parseInt(value, 10))) {
                    value = null; // Déclenche la suppression de la clé dans le YAML
                } else {
                    value = parseInt(value, 10); // Convertir en entier si valide
                }
            } else {
                // Si c'est un champ texte, on garde la valeur telle quelle
                value = value.trim(); // Supprime les espaces inutiles
                if (value === "") {
                    value = null; // Si le champ est vide, suppression dans YAML
                }
            }
        
            // Mise à jour de la config si une clé est définie
            if (key) {
                appendTo._config = updateConfigRecursively(appendTo._config, key, value, true);
                notifyConfigChange(appendTo);
            }
            
            // Émettre un événement personnalisé pour signaler que la configuration a changé
            const event = new CustomEvent('config-changed', {
                detail: { redrawRequired: true }
            });
            document.dispatchEvent(event);
        };
        
        // Ajouter l'événement
        textField.addEventListener("change", handleChange);
        
        // Enregistrer le gestionnaire dans le WeakMap
        eventHandlers.set(textField, handleChange);
        
    });
    
    // Listener pour les `ha-switch`
    appendTo.shadowRoot.querySelectorAll('ha-switch').forEach((toggle) => {
        
        if (eventHandlers.has(toggle)) {
            //console.log("Événement déjà attaché à cet élément ha-switch :", toggle);
            return; // Ne rien faire si l'événement est déjà attaché
        }
        
        // Créer un nouveau gestionnaire d'événements
        const handleChange = (e) => {
            const key = toggle.dataset.path;
            const value = e.target.checked ? true : null; // `true` si activé, `null` pour suppression
            
            if (key) {
                appendTo._config = updateConfigRecursively(appendTo._config, key, value, true); // Suppression si désactivé
                notifyConfigChange(appendTo);
            }
            
            // Émettre un événement personnalisé pour signaler que la configuration a changé
            const event = new CustomEvent('config-changed', {
                detail: { redrawRequired: true }
            });
            document.dispatchEvent(event);
        };
        
        // Ajouter l'événement
        toggle.addEventListener("change", handleChange);
        
        // Enregistrer le gestionnaire dans le WeakMap
        eventHandlers.set(toggle, handleChange);
        
    });
}

/************************************************/
/* fonction de creation des events attachés aux */
/* differents inputs de l'interface puis tri et */
/* envoi pour mise a jour du yaml               */
/************************************************/
export function attachInputs(appendTo) {
        
    // Listener pour les `ha-textfield` sauf les champs "anchor"
    appendTo.shadowRoot.querySelectorAll('ha-textfield:not(.anchor)').forEach((textField) => {
        
        if (eventHandlers.has(textField)) {
            //console.log("Événement déjà attaché à cet élément ha-textfield :", textField);
            return; // Ne rien faire si l'événement est déjà attaché
        }
        
        // Créer un nouveau gestionnaire d'événements
        const handleChange = (e) => {
            const key = textField.dataset.path;
            let value = e.target.value;
    
            // Gestion des valeurs en fonction du type de champ
            if (e.target.type === 'number') {
                // Si c'est un champ numérique
                if (!value || isNaN(parseInt(value, 10))) {
                    value = null; // Déclenche la suppression de la clé dans le YAML
                } else {
                    value = parseInt(value, 10); // Convertir en entier si valide
                }
            } else {
                // Si c'est un champ texte, on garde la valeur telle quelle
                value = value.trim(); // Supprime les espaces inutiles
                if (value === "") {
                    value = null; // Si le champ est vide, suppression dans YAML
                }
            }
        
            // Mise à jour de la config si une clé est définie
            if (key) {
                appendTo._config = updateConfigRecursively(appendTo._config, key, value, true);
                notifyConfigChange(appendTo);
            }
        };
        
        // Ajouter l'événement
        textField.addEventListener("change", handleChange);
        
        // Enregistrer le gestionnaire dans le WeakMap
        eventHandlers.set(textField, handleChange);
        
    });

    // Listener pour les champs "anchor" (native input[type=number])
    appendTo.shadowRoot.querySelectorAll('input.anchor').forEach((inputEl) => {
        
        if (eventHandlers.has(inputEl)) {
            return;
        }
        
        const handleChange = (e) => {
            const key = inputEl.dataset.path;
    
            // Récupérer les valeurs des champs "left", "top", "bottom", "right"
            const anchorLeft   = appendTo.shadowRoot.querySelector('#anchor_left')?.value   ?? '0';
            const anchorTop    = appendTo.shadowRoot.querySelector('#anchor_top')?.value    ?? '0';
            const anchorBottom = appendTo.shadowRoot.querySelector('#anchor_bottom')?.value ?? '0';
            const anchorRight  = appendTo.shadowRoot.querySelector('#anchor_right')?.value  ?? '0';
            
            let anchors = [];
            
            if (anchorLeft   && anchorLeft   !== '0') anchors.push(`L-${anchorLeft}`);
            if (anchorTop    && anchorTop    !== '0') anchors.push(`T-${anchorTop}`);
            if (anchorBottom && anchorBottom !== '0') anchors.push(`B-${anchorBottom}`);
            if (anchorRight  && anchorRight  !== '0') anchors.push(`R-${anchorRight}`);
        
            if (anchors.length > 0) {
                appendTo._config = updateConfigRecursively(appendTo._config, key, anchors.join(', '), true);
            } else {
                appendTo._config = updateConfigRecursively(appendTo._config, key, null, true);
            }
            notifyConfigChange(appendTo);
        };
        
        inputEl.addEventListener('change', handleChange);
        eventHandlers.set(inputEl, handleChange);
        
    });
 
    // Listener pour les `ha-switch`
    appendTo.shadowRoot.querySelectorAll('ha-switch').forEach((toggle) => {
        
        if (eventHandlers.has(toggle)) {
            //console.log("Événement déjà attaché à cet élément ha-switch :", toggle);
            return; // Ne rien faire si l'événement est déjà attaché
        }
        
        // Créer un nouveau gestionnaire d'événements
        const handleChange = (e) => {
            const key = toggle.dataset.path;
            const value = e.target.checked ? true : null; // `true` si activé, `null` pour suppression
            const group = toggle.dataset.group;
            const isChecked = e.target.checked;
            
            if (group) {
                // Trouver le champ texte associé au switch
                const textField = appendTo.shadowRoot.querySelector(`ha-textfield[data-group="${group}"]`);
                const key2 = textField.dataset.path;
        
                if (isChecked) {
                  appendTo._config = updateConfigRecursively(appendTo._config, key2, "auto"); // Définir sur "auto"
                } else {

                    const value = textField.value && !isNaN(parseInt(textField.value, 10)) 
                    ? parseInt(textField.value, 10) 
                    : null;
                    
                    appendTo._config = updateConfigRecursively(appendTo._config, key2, value, true);

                }
                notifyConfigChange(appendTo);
                
            } else {
                if (key) {
                    appendTo._config = updateConfigRecursively(appendTo._config, key, value, true); // Suppression si désactivé
                    notifyConfigChange(appendTo);
                }
            }
        };
        
        // Ajouter l'événement
        toggle.addEventListener("change", handleChange);
        
        // Enregistrer le gestionnaire dans le WeakMap
        eventHandlers.set(toggle, handleChange);
        
    });
    
    // Listener pour les `ha-radio`
    appendTo.shadowRoot.querySelectorAll('ha-radio').forEach((radio) => {
        
        if (eventHandlers.has(radio)) {
            //console.log("Événement déjà attaché à cet élément ha-radio :", radio);
            return; // Ne rien faire si l'événement est déjà attaché
        }
        
        // Créer un nouveau gestionnaire d'événements
        const handleChange = (e) => {
            const key = radio.dataset.path; // Assurez-vous que le `name` correspond à la clé dans la config
            const value = e.target.value; // 'light', 'dark', 'auto'
    
            if (key) {
                appendTo._config = updateConfigRecursively(appendTo._config, key, value, true);
                notifyConfigChange(appendTo);
            }
        };
        
        // Ajouter l'événement
        radio.addEventListener("change", handleChange);
        
        // Enregistrer le gestionnaire dans le WeakMap
        eventHandlers.set(radio, handleChange);
        
    });
          
    // Listener pour les `ha-icon-picker`
    appendTo.shadowRoot.querySelectorAll('ha-icon-picker').forEach((iconPicker) => {
        
        if (eventHandlers.has(iconPicker)) {
            //console.log("Événement déjà attaché à cet élément ha-icon-picker :", iconPicker);
            return; // Ne rien faire si l'événement est déjà attaché
        }
        
        // Créer un nouveau gestionnaire d'événements
        const handleChange = (e) => {
            const key = iconPicker.dataset.path; // Assurez-vous que le `name` correspond à la clé dans la config
            let value = e.detail.value;
            
            // Si la valeur est une chaîne vide, traiter comme suppression de l'icône
            if (value === "") {
                value = null; // Marquer pour suppression dans le YAML
            }
            
            if (key) {
                appendTo._config = updateConfigRecursively(appendTo._config, key, value, true);
                notifyConfigChange(appendTo);
            }
        }
            
        // Ajouter l'événement
        iconPicker.addEventListener("value-changed", handleChange);
        
        // Enregistrer le gestionnaire dans le WeakMap
        eventHandlers.set(iconPicker, handleChange);
        
    });
    
    // Listener pour les color pickers
    appendTo.shadowRoot.querySelectorAll('input[type="color"]').forEach((colorInput) => {
        if (eventHandlers.has(colorInput)) return;
        const handleChange = (e) => {
            const key = colorInput.dataset.path;
            const value = e.target.value;
            if (key) {
                appendTo._config = updateConfigRecursively(appendTo._config, key, value, false);
                notifyConfigChange(appendTo);
            }
        };
        colorInput.addEventListener('input', handleChange);
        eventHandlers.set(colorInput, handleChange);
    });

    // Listener pour les range sliders
    appendTo.shadowRoot.querySelectorAll('input[type="range"]').forEach((rangeInput) => {
        if (eventHandlers.has(rangeInput)) return;
        const handleChange = (e) => {
            const key = rangeInput.dataset.path;
            const value = parseInt(e.target.value, 10);
            if (key) {
                appendTo._config = updateConfigRecursively(appendTo._config, key, value, true);
                notifyConfigChange(appendTo);
            }
        };
        rangeInput.addEventListener('change', handleChange);
        eventHandlers.set(rangeInput, handleChange);
    });

    // Listener pour les `ha-selector` (entity type)
    appendTo.shadowRoot.querySelectorAll('ha-selector[data-path]').forEach((entityPicker) => {
        
        if (eventHandlers.has(entityPicker)) {
            //console.log("Événement déjà attaché à cet élément ha-entity-picker :", entityPicker);
            return; // Ne rien faire si l'événement est déjà attaché
        }
            
        // Créer un nouveau gestionnaire d'événements
        const handleChange = (e) => {
            const key = entityPicker.dataset.path; // Assurez-vous que le `name` correspond à la clé dans la config
            let value = e.detail.value;
            
            // Si la valeur est une chaîne vide, traiter comme suppression de l'icône
            if (!value || value.trim() === "") {
                value = null; // Marquer pour suppression dans le YAML
            }
            
            if (key) {
                appendTo._config = updateConfigRecursively(appendTo._config, key, value, true);
                notifyConfigChange(appendTo);
            }
        }
        
        // Ajouter l'événement
        entityPicker.addEventListener("value-changed", handleChange);
        
        // Enregistrer le gestionnaire dans le WeakMap
        eventHandlers.set(entityPicker, handleChange);
        
    });
    
}

/**********************************************/
/* fonction de modification de la config yaml */
/* en local (en fait l'array local)           */
/* renvoi la nouvelle confif pour mod du yaml */
/* via la fonction notifyConfigChange         */
/**********************************************/
export function updateConfigRecursively(obj, path, value, removeIfNull = false) {
    const cloneObject = (o) => {
        return Array.isArray(o)
            ? o.map(cloneObject)
            : o && typeof o === "object"
            ? { ...o }
            : o;
    };

    const keys = path.split('.');
    let clonedObj = cloneObject(obj);
    let current = clonedObj;

    for (let i = 0; i < keys.length; i++) {
        const key = keys[i];

        if (i === keys.length - 1) {
            if (value === null && removeIfNull) {
                delete current[key]; // Supprime la clé si `null` et `removeIfNull` est vrai
            } else {
                current[key] = value; // Définit la nouvelle valeur
            }
            break;
        }

        if (!current[key]) {
            current[key] = {};
        }

        current[key] = cloneObject(current[key]);
        current = current[key];
    }

    // Suppression des clés vides (supprime les objets vides récursivement)
    const removeEmptyKeys = (obj) => {
        for (const key in obj) {
            if (obj[key] && typeof obj[key] === 'object') {
                if (Object.keys(obj[key]).length === 0) {
                    delete obj[key];
                } else {
                    removeEmptyKeys(obj[key]);
                }
            }
        }
    };

    removeEmptyKeys(clonedObj);
    return clonedObj;
}

/***********************************/
/* fonction de mise à jour du yaml */
/***********************************/
export function notifyConfigChange(appendTo) {
    const event = new Event('config-changed', {
        bubbles: true,
        composed: true,
    });
    
    //console.log(appendTo._config);
    
    event.detail = { config: appendTo._config };
    appendTo.dispatchEvent(event);
}

/********************************/
/* fonction de gestion du click */
/* dans les onglets principaux  */
/********************************/
export function attachLinkClick(renderTabContent, appendTo) {
    appendTo.shadowRoot.querySelectorAll('#tab-group sl-tab').forEach((link) => {
        if (eventHandlers.has(link)) {
            console.log("Événement déjà attaché à cet élément #link-container mwc-tab :", link);
            return;
        }

        const handleClick = (e) => {
            const tab = parseInt(e.currentTarget.getAttribute('data-tab'), 10);
            appendTo._currentTab = tab;
            appendTo._currentSubTab = 0;
            renderTabContent(appendTo); // Appelle la fonction passée en paramètre
        };

        link.addEventListener("click", handleClick);
        eventHandlers.set(link, handleClick);
    });
}

/********************************/
/* fonction de gestion du click */
/* dans les onglets secondaires */
/********************************/
export function attachSubLinkClick(appendTo) {
    appendTo.shadowRoot.querySelectorAll('#subTab-group sl-tab').forEach((sublink) => {
        if (eventHandlers.has(sublink)) {
            console.log("Événement déjà attaché à cet élément #sublink-container mwc-tab :", sublink);
            return;
        }

        const handleClick = (e) => {
            const tab = parseInt(e.currentTarget.getAttribute('data-tab'), 10);
            appendTo._currentSubTab = tab;
            renderSubTabContent(appendTo._currentTab, appendTo);
        };

        sublink.addEventListener("click", handleClick);
        eventHandlers.set(sublink, handleClick);
    });
}
