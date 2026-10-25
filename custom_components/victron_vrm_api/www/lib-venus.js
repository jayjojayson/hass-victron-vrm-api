export let intervals = new Map();

export let historicData = new Map();

export let updateGraphTriggers = new Map();

// Version der Historie pro Entität (wird bei jedem erfolgreichen Abruf erhöht).
// Jede Karte merkt sich, welche Version sie gezeichnet hat → mehrere Karten
// (Dashboard + Editor-Vorschau) können denselben Graphen zeichnen.
const historicVersion = new Map();

/* Anzahl Boxen pro Spalte (gleiche Grenzen wie im Editor) */
export function getBoxCount(param, col) {
    const max = col === 2 ? 2 : 4;
    const raw = parseInt(param?.[`boxCol${col}`], 10);
    if (isNaN(raw)) return 1;
    return Math.min(Math.max(raw, 1), max);
}

/* "true"/true → true (YAML/Editor liefern teils Strings) */
function isTrue(value) {
    return value === true || value === "true";
}

/* Anker-String "L-1, B-2" robust zerlegen (auch "L-1,B-2") */
export function parseAnchors(anchorsValue) {
    if (!anchorsValue) return [];
    return String(anchorsValue)
        .split(/\s*,\s*/)
        .map((a) => a.trim())
        .filter((a) => /^[LTBR]-\d+$/.test(a))
        .map((a) => {
            const [type, qtyStr] = a.split('-');
            return { type, qty: parseInt(qtyStr, 10) };
        });
}

/* Schriftgröße: Zahl → px, sonst unverändert (z.B. "1.2em") */
function toFontSize(value) {
    if (value === undefined || value === null || value === "") return "";
    return /^\d+(\.\d+)?$/.test(String(value)) ? `${value}px` : String(value);
}

/* HTML-Sonderzeichen maskieren (Namen/Werte kommen aus Config/States) */
function esc(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

/**
 * Wert + Einheit einer Entität formatieren. Nutzt (falls vorhanden) die
 * HA-Formatierung → Anzeigegenauigkeit, Sprache/Locale und übersetzte
 * Zustände wie "Nicht verfügbar".
 */
export function formatEntity(hass, entityId, fallback = "") {
    const stateObj = entityId ? hass?.states?.[entityId] : undefined;
    if (!stateObj) return { value: fallback, unit: "", raw: undefined };
    const unit = stateObj.attributes?.unit_of_measurement || "";
    let value = stateObj.state;
    if (typeof hass.formatEntityState === "function") {
        try {
            let formatted = hass.formatEntityState(stateObj);
            if (typeof formatted === "string") {
                if (unit && formatted.endsWith(unit)) {
                    formatted = formatted.slice(0, -unit.length).trim();
                }
                value = formatted;
            }
        } catch (e) {
            // Fallback auf Rohwert
        }
    }
    return { value, unit, raw: stateObj.state };
}

// Per-Karteninstanz-State (Schlüssel: appendTo-Element).
// So teilen Hauptkarte und Editor-Vorschaukarte KEINEN gemeinsamen Zustand mehr.
const perCard = new WeakMap();

function getState(appendTo) {
    if (!perCard.has(appendTo)) {
        perCard.set(appendTo, {
            pathControls: new Map(),
            directionControls: new Map(),
            dashboardOldWidth: undefined,
            mustRedrawLine: true,
            checkReadyRafId: null,
            intervals: new Map(),
            graphDrawn: new Map(),
            hass: null,
        });
    }
    return perCard.get(appendTo);
}

/************************************************/
/* fonction de rendu du squelette de la carte : */
/* rend une image si dans le YAML, mode = DEMO  */
/************************************************/
export function baseRender(config, appendTo) {
    
    appendTo.innerHTML = `
	    <div id="dashboard" class="dashboard">
    		<svg id="svg_container" class="line" viewBox="0 0 1000 600" width="100%" height="100%">
    			<defs>
    				<filter id="blurEffect">
    					<feGaussianBlur in="SourceGraphic" stdDeviation="1"/> <!-- Ajuste stdDeviation pour plus ou moins de flou -->
    				</filter>
    				<radialGradient id="gradientDark" cx="50%" cy="50%" r="50%">
    					<stop offset="0%" stop-color="#ffffff" stop-opacity="1"></stop>
    					<stop offset="90%" stop-color="#ffffff" stop-opacity="0"></stop>
    				</radialGradient>
    				<radialGradient id="gradientLight" cx="50%" cy="50%" r="50%">
    					<stop offset="0%" stop-color="#000000" stop-opacity="1"></stop>
    					<stop offset="90%" stop-color="#000000" stop-opacity="0"></stop>
    				</radialGradient>
    			</defs>
        		<g id="path_container" class="balls"></g>
    			<g id="circ_container" class="lines"></g>
    		</svg>
            <div id="column-1" class="column column-1"></div>
            <div id="column-2" class="column column-2"></div>
            <div id="column-3" class="column column-3"></div>
        </div>
	`;

}

/**********************************/
/* fonction de creation des box : */
/* qty par col                    */
/**********************************/
export function addBox(col1, col2, col3, appendTo) {
    
    const boxCounts = [col1, col2, col3];
    
    boxCounts.forEach((count, columnIndex) => {
        const column = appendTo.querySelector(`#dashboard > #column-${columnIndex + 1}`); // Accède aux colonnes via querySelector

        if (column) {
            const gapPercentage = count === 3 ? '5%' : count === 2 ? '10%' : '0';
            column.style.gap = gapPercentage; // Applique le gap à la colonne

            for (let i = 1; i <= count; i++) {
                
                const content = document.createElement('div'); // Crée un nouvel élément div
                content.id = `content_${columnIndex + 1}-${i}`; // Définit l'id de la box
                content.className = 'content'; // Applique la classe 'content'
                
                const graph = document.createElement('div'); // Crée un nouvel élément div
                graph.id = `graph_${columnIndex + 1}-${i}`;
                graph.className = 'graph';
                
                const gauge = document.createElement('div'); // Crée un nouvel élément div
                gauge.id = `gauge_${columnIndex + 1}-${i}`;
                gauge.className = 'gauge';
                gauge.style.height = `0px`;
                
                const box = document.createElement('div'); // Crée un nouvel élément div
                box.id = `box_${columnIndex + 1}-${i}`; // Définit l'id de la box
                box.className = 'box'; // Applique la classe 'box'
                box.appendChild(graph);
                box.appendChild(gauge);
                box.appendChild(content);
                column.appendChild(box); // Ajoute la box à la colonne
            }
        } else {
            console.warn(`Colonne ${columnIndex + 1} introuvable.`);
        }
    });
}

/****************************************/
/* fonction d'ajout des ancres :        */
/* liste les ancres a créer das les box */
/* puis lance la fonction creatAnchors  */
/* en fonction des param du YAML        */
/****************************************/
export function addAnchors(config, appendTo) {
    
    // Parcourir tous les devices dans la configuration
    Object.entries(config.devices || {}).forEach(([boxKey, device]) => {
        if (device?.anchors) {
            // Extraire les ancres définies pour le device
            const anchors = parseAnchors(device.anchors);

            // Traiter chaque ancre
            anchors.forEach(({ type, qty }) => {
                const col = parseInt(boxKey[0], 10); // Première partie du boxKey (colonne)
                const box = parseInt(boxKey[2], 10); // Troisième partie du boxKey (box)
                
                // Appeler la fonction creatAnchors
                creatAnchors(col, box, qty, type, appendTo);
            });
        }
    });
}

/****************************************/
/* fonction de creation des ancres :    */
/* recoit en param la colonne, la box,  */
/* le nombre à créer par coté, et       */
/* le coté(position)                    */
/****************************************/
function creatAnchors(colNbrs, boxNbrs, numAnchors, type, appendTo) {
	const box = appendTo.querySelector(`#dashboard > #column-${colNbrs} > #box_${colNbrs}-${boxNbrs}`); // Accède aux colonnes via querySelector
	
	if (!box) {
		console.error(`Boîte avec l'ID "box_${colNbrs}-${boxNbrs}" introuvable.`);
		return;
	}

	// Ajouter les nouveaux anchors
	for (let i = 0; i < numAnchors; i++) {
		const anchor = document.createElement('div');
		
		anchor.className = 'anchor anchor-'+type;
		anchor.id = `anchor_${colNbrs}-${boxNbrs}_${type}-${i+1}`;
		
		// Calculer la position de chaque anchor
		const positionPercent = ((i + 1) / (numAnchors + 1)) * 100; // Uniformément réparti
		
		if(type === "T" ||  type === "B")
			anchor.style.left = `${positionPercent}%`;
		else {
			anchor.style.top = `${positionPercent}%`;
		}
		
		// Ajouter l'anchor à la boîte
		box.appendChild(anchor);
	}
}

/**********************************************/
/* fonction de remplissage des box :          */
/* recoit en param les diferents devices,     */
/* le style eventuel ou la taille des strings */
/* (defini ou auto),                          */
/**********************************************/
export function fillBox(config, styles, isDark, hass, appendTo) {
    
    const devices = config.devices || {};
    styles = styles && typeof styles === "object" ? styles : {};

    // aktuelles hass für die periodischen Historien-Abrufe merken
    getState(appendTo).hass = hass;
    
    for (const boxId in devices) {
        
        // Box-ID muss das Format "Spalte-Box" haben (z.B. "1-2")
        if (!/^[1-3]-[1-4]$/.test(boxId)) continue;

        const boxIdtest = parseInt(boxId[2], 10);
        const boxIdmax = getBoxCount(config.param, parseInt(boxId[0], 10));
        
        // Box existiert in dieser Konfiguration nicht → überspringen (nicht abbrechen!)
        if(boxIdtest > boxIdmax) continue;
            
        const device = devices[boxId] || {};
            
        const divGauge = appendTo.querySelector(`#dashboard > #column-${boxId[0]} > #box_${boxId} > #gauge_${boxId}`);
        const innerContent = appendTo.querySelector(`#dashboard > #column-${boxId[0]} > #box_${boxId} > #content_${boxId}`);

        if (!innerContent || !divGauge) continue;
                
        const main = formatEntity(hass, device.entity, device.entity ? 'N/C' : '');
        let value = main.value;
        let unit = main.unit;
            
        let addGauge = "";
        let addHeaderEntity = "";
        let addEntity2 = "";
        let addFooter = "";
        let addHeaderStyle = "";
        let addSensorStyle = "";
        let addSensor2Style = "";
        let addFooterStyle = "";
        
        if(isTrue(device.graph)) creatGraph(boxId, device, isDark, appendTo);
        
        if(isTrue(device.gauge)) {
            const pct = parseFloat(main.raw);
            divGauge.style.height = isNaN(pct) ? `0px` : `${Math.min(Math.max(pct, 0), 100)}%`;
        }
        else divGauge.style.height = `0px`;
            
        if(styles.header) {
            if(styles.header == "auto") {
                
                let dynSizeHeader = "";
                
                if(boxId[0] == "2") dynSizeHeader = Math.round(0.0693*innerContent.offsetWidth+1.9854);
                else dynSizeHeader = Math.round(0.0945*innerContent.offsetWidth+2.209);

                addHeaderStyle = ` style="font-size: ${dynSizeHeader}px;"`;
                
            } else {
                addHeaderStyle = ` style="font-size: ${toFontSize(styles.header)};"`;
            }
        } 
        
        if(styles.sensor) {
            if(styles.sensor == "auto") {
                    
                let dynSizeSensor = "";
                    
                if(boxId[0] == "2") dynSizeSensor = Math.round(0.1065*innerContent.offsetWidth+8.7929);
                else dynSizeSensor = Math.round(0.1452*innerContent.offsetWidth+9.0806);
                    
                addSensorStyle = ` style="font-size: ${dynSizeSensor}px;"`;
                    
            } else {
                addSensorStyle = ` style="font-size: ${toFontSize(styles.sensor)};"`;
            }
        }
        
        if(styles.sensor2) {
            if(styles.sensor2 == "auto") {
                    
                let dynSizeSensor2 = "";
                    
                if(boxId[0] == "2") dynSizeSensor2 = Math.round(0.0693*innerContent.offsetWidth+1.9854);
                else dynSizeSensor2 = Math.round(0.0945*innerContent.offsetWidth+2.209);
                    
                addSensor2Style = ` style="font-size: ${dynSizeSensor2}px;"`;
                    
            } else {
                addSensor2Style = ` style="font-size: ${toFontSize(styles.sensor2)};"`
            }
        }
            
        if(styles.footer) {
            if(styles.footer == "auto") {
                    
                let dynSizeFooter = "";
                    
                if(boxId[0] == "2") dynSizeFooter = Math.round(0.0803*innerContent.offsetWidth-2.438);
                else dynSizeFooter = Math.round(0.1095*innerContent.offsetWidth-2.1791);
                    
                addFooterStyle = ` style="font-size: ${dynSizeFooter}px;"`;
                    
            } else {
                addFooterStyle = ` style="font-size: ${toFontSize(styles.footer)};"`;
            }
        }
            
        if(device.headerEntity) {
            const h = formatEntity(hass, device.headerEntity);
                
            addHeaderEntity = `
                <div class="headerEntity">${esc(h.value)}<div class="boxUnit">${esc(h.unit)}</div></div>
            `;
        }
        
        if(device.entity2) {
            const e2 = formatEntity(hass, device.entity2);
                
            addEntity2 = `
                <div class="boxSensor2"${addSensor2Style}>${esc(e2.value)}<div class="boxUnit">${esc(e2.unit)}</div></div>
            `;
        }
            
        if(device.footerEntity1) {
                
            const f1 = formatEntity(hass, device.footerEntity1);
            const f2 = formatEntity(hass, device.footerEntity2);
            const f3 = formatEntity(hass, device.footerEntity3);
            
            addFooter = `
                <div class="boxFooter"${addFooterStyle}>
                    <div class="footerCell">${esc(f1.value)}<div class="boxUnit">${esc(f1.unit)}</div></div>
                    <div class="footerCell">${esc(f2.value)}<div class="boxUnit">${esc(f2.unit)}</div></div>
                    <div class="footerCell">${esc(f3.value)}<div class="boxUnit">${esc(f3.unit)}</div></div>
                </div>
            `;
        }
            
        const html = `
            <div class="boxHeader"${addHeaderStyle}>
                ${device.icon ? `<ha-icon icon="${esc(device.icon)}" class="boxIcon"></ha-icon>` : ''}
                <div class="boxTitle">${esc(device.name)}</div>
                ${addHeaderEntity}
            </div>
            <div class="boxSensor1"${addSensorStyle}>${esc(value)}<div class="boxUnit">${esc(unit)}</div></div>
            ${addEntity2}
            ${addFooter}
        `;

        // Nur neu schreiben, wenn sich etwas geändert hat (set hass wird bei JEDER
        // Zustandsänderung in HA aufgerufen → sonst ständiges Neu-Rendern/Flackern)
        if (innerContent._vrmHtml !== html) {
            innerContent._vrmHtml = html;
            innerContent.innerHTML = html;
        }

        // Entität für den Klick aktuell halten (Config kann sich ändern)
        innerContent.dataset.entity = device.entity || "";
        
        if (!innerContent.dataset.listener) {
            innerContent.dataset.listener = "true"; // Marque comme ayant un listener
        
            innerContent.addEventListener('click', () => {
                const entityId = innerContent.dataset.entity;
                if (!entityId) return;
        
                // Déclenche l'événement "more-info" de Home Assistant
                innerContent.dispatchEvent(new CustomEvent('hass-more-info', {
                    bubbles: true,
                    composed: true,
                    detail: { entityId },
                }));
            });
        }
    }
}

function creatGraph (boxId, device, isDark, appendTo) {
    
    const state = getState(appendTo);
    const version = historicVersion.get(device.entity);

    // Nur zeichnen, wenn neue Daten vorliegen (pro Karte und Box)
    if (version === undefined || state.graphDrawn.get(boxId) === `${device.entity}#${version}`) return;
    
    const divGraph = appendTo.querySelector(`#dashboard > #column-${boxId[0]} > #box_${boxId} > #graph_${boxId}`);
    const data = historicData.get(device.entity);
    
    if (!divGraph || !data || data.length < 2) return;
    
    // Générer le path SVG
    const pathD = generatePath(data, 500, 99); // Dimensions SVG fixées pour cet exemple

    let colorPath = "#00000077";
    if(isDark) {
        colorPath = "#ffffff77";
    } 
    
    if (!pathD || pathD.includes("NaN")) return;

    divGraph.innerHTML = `
        <svg viewBox="0 0 500 100" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" style="width: 100%; height: 100%;">
            <path fill="none" stroke="${colorPath}" stroke-width="3" d="${pathD}" />
        </svg>
    `;

    state.graphDrawn.set(boxId, `${device.entity}#${version}`);
}

function generatePath(data, svgWidth = 500, svgHeight = 100) {
    if (!data || data.length < 2) return '';

    // Étape 1 : Calculer min/max pour normalisation
    const minY = Math.min(...data.map(d => d.value));
    let maxY = Math.max(...data.map(d => d.value));
    // Konstante Werte → Division durch 0 vermeiden (flache Linie in der Mitte)
    if (maxY === minY) maxY = minY + 1;

    // Étape 2 : Normalisation des points
    const normalizedData = data.map((d, index) => ({
        x: (index / (data.length - 1)) * svgWidth, // Répartition uniforme des X
        y: svgHeight - ((d.value - minY) / (maxY - minY)) * svgHeight, // Normalisation Y inversée (SVG : 0 en haut)
    }));

    // Étape 3 (optionnel) : Simplification des points
    //const simplifiedData = simplifyPath(normalizedData, 3); // Tolérance à ajuster
    const simplifiedData = normalizedData;
    
    // Étape 4 : Construction du path
    let path = `M${simplifiedData[0].x},${simplifiedData[0].y}`; // Point de départ
    for (let i = 1; i < simplifiedData.length; i++) {
        const prev = simplifiedData[i - 1];
        const curr = simplifiedData[i];
        const midX = (prev.x + curr.x) / 2; // Point médian pour une courbe fluide
        path += ` Q${prev.x},${prev.y} ${midX},${curr.y}`;
    }
    path += ` T${simplifiedData[simplifiedData.length - 1].x},${simplifiedData[simplifiedData.length - 1].y}`; // Dernier point

    return path;
}

function simplifyPath(points, tolerance) {
    if (points.length <= 2) return points; // Pas besoin de simplification si 2 points ou moins

    const sqTolerance = tolerance * tolerance;

    // Fonction pour calculer la distance au carré d'un point à une ligne
    function getSqSegmentDistance(p, p1, p2) {
        let x = p1.x, y = p1.y;
        let dx = p2.x - x, dy = p2.y - y;

        if (dx !== 0 || dy !== 0) {
            const t = ((p.x - x) * dx + (p.y - y) * dy) / (dx * dx + dy * dy);
            if (t > 1) {
                x = p2.x;
                y = p2.y;
            } else if (t > 0) {
                x += dx * t;
                y += dy * t;
            }
        }

        dx = p.x - x;
        dy = p.y - y;

        return dx * dx + dy * dy;
    }

    // Fonction récursive principale
    function simplifyRecursive(start, end, sqTolerance, simplified) {
        let maxSqDist = sqTolerance;
        let index;

        for (let i = start + 1; i < end; i++) {
            const sqDist = getSqSegmentDistance(points[i], points[start], points[end]);
            if (sqDist > maxSqDist) {
                index = i;
                maxSqDist = sqDist;
            }
        }

        if (maxSqDist > sqTolerance) {
            if (index - start > 1) simplifyRecursive(start, index, sqTolerance, simplified);
            simplified.push(points[index]);
            if (end - index > 1) simplifyRecursive(index, end, sqTolerance, simplified);
        }
    }

    const simplified = [points[0]];
    simplifyRecursive(0, points.length - 1, sqTolerance, simplified);
    simplified.push(points[points.length - 1]);

    return simplified;
}

/******************************************************/
/* fonction d'ajout des liens entre les box :     */
/* compare les tailles d'une boucle "set hass" à      */
/* l'autre et si il y a changement lance la           */
/* fonction addLine (donc a la premiere boucle aussi) */
/******************************************************/
export function checkReSize(devices, isDarkTheme, appendTo, config) {

    const state = getState(appendTo);
    
    // recuperation de la taille de la carte pour recalcul des path si necessaire
    const rect = appendTo.querySelector(`#dashboard`).getBoundingClientRect();

    // Element nicht gerendert (z.B. Tab nicht aktiv) → überspringen
    if (rect.width === 0) return;

    // Gerundete Breite verwenden (vermeidet Subpixel-Float-Variationen die fälschlicherweise
    // einen Neuzeichnen auslösen würden, z.B. 557.333 vs 557.334 nach einem DOM-Update)
    const roundedWidth = Math.round(rect.width);
    
    // si largeur differente de precedemment OU redessinage demandé : recalcul
    if(state.dashboardOldWidth !== roundedWidth || state.mustRedrawLine) {

        // Marquer immédiatement pour éviter les doubles redessins entre deux hass successifs
        const wasRedraw = state.mustRedrawLine;
        state.mustRedrawLine = false;
        state.dashboardOldWidth = roundedWidth;

        // Annuler un éventuel checkReady déjà en attente
        if (state.checkReadyRafId !== null) {
            cancelAnimationFrame(state.checkReadyRafId);
            state.checkReadyRafId = null;
        }

        // conteneur des path et des circles
        const circContainer = appendTo.querySelector(`#dashboard > #svg_container > #circ_container`);
        const pathContainer = appendTo.querySelector(`#dashboard > #svg_container > #path_container`);
            
        // si le DOM est fini...
        const checkReady = () => {
            state.checkReadyRafId = null;
            const dashboard = appendTo.querySelector("#dashboard");
        
            if (dashboard) {

                // Annuler toutes les animations RAF en cours avant de vider les conteneurs
                state.pathControls.forEach(ctrl => { if (ctrl && ctrl.cancel) ctrl.cancel(); });
                state.pathControls.clear();
                state.directionControls.clear();

                circContainer.innerHTML = "";
                pathContainer.innerHTML = "";
                addLine(devices, isDarkTheme, appendTo, config);
                
                return; // Arrête la boucle
            }
        
            // Sinon, replanifie la vérification
            state.checkReadyRafId = requestAnimationFrame(checkReady);
        };
        
        // Lancer la vérification initiale
        state.checkReadyRafId = requestAnimationFrame(checkReady);
        
    }
}

export function razDashboardOldWidth(appendTo) {
    if (appendTo) getState(appendTo).mustRedrawLine = true;
}

/********************************************************/
/* fonction de lancement de creation de liens entre     */
/* les box :                                            */
/* recupere les params de creation et lance la fonction */
/* creatLine en concequence                             */
/********************************************************/
function addLine(devices, isDarkTheme, appendTo, config) {
	for (const boxId in devices) {
        const device = devices[boxId];
        
        // Parcours des liens numérotés
        const links = device.link;
        
        if(links !== "nolink") {
            for (const linkId in links) {
                const link = links[linkId];
                
                if(link == "nolink") continue;
                
                if (!link || typeof link !== "object") continue;
                const inv = isTrue(link.inv) ? -1 : 1;          // Par défaut, "inv" est 1 s'il n'est pas défini
                        
                // Affichage des informations du lien
                if (link.start && link.end) creatLine(`${boxId}_${link.start}`, link.end, inv, isDarkTheme, appendTo, config);
                                
            }
    	}
    }
}

/*********************************************************/
/* fonction de creation des liens entre les box :        */
/* recoit en param l'ancre de depart, l'ancre d'arrivée, */
/* le sens initial de deplacement de l'animation         */
/*********************************************************/
function creatLine(anchorId1, anchorId2, direction_init, isDarkTheme, appendTo, config) {
    
    const circContainer = appendTo.querySelector(`#dashboard > #svg_container > #circ_container`);
    const pathContainer = appendTo.querySelector(`#dashboard > #svg_container > #path_container`);

    if (!circContainer) {
		console.error("circContainer container introuvable.");
		return;
	}
	
	if (!pathContainer) {
		console.error("pathContainer container introuvable.");
		return;
	}
	
	var coords1 = getAnchorCoordinates(anchorId1, appendTo);
	var coords2 = getAnchorCoordinates(anchorId2, appendTo);
	
	if (!coords1 || !coords2) {
		console.error("Impossible de calculer les coordonnées.");
		return;
	}
	
	let pathData = "";
	
	if (coords1.x === coords2.x || coords1.y === coords2.y) {
        pathData = `M ${coords1.x} ${coords1.y} L ${coords2.x} ${coords2.y}`;
    } else {
	
    	const anchor1isH = anchorId1.includes("L") || anchorId1.includes("R");
    	const anchor2isH = anchorId2.includes("L") || anchorId2.includes("R");

    	if (anchor1isH && anchor2isH) {
    		const midX = (coords1.x + coords2.x) / 2;
    		// Définition du chemin avec deux courbes symétriques
    		pathData = `
    			M ${coords1.x} ${coords1.y}
    			C ${midX} ${coords1.y}, ${midX} ${coords1.y}, ${midX} ${(coords1.y + coords2.y) / 2}
    			C ${midX} ${coords2.y}, ${midX} ${coords2.y}, ${coords2.x} ${coords2.y}
    		`;
    	} else if (!anchor1isH && !anchor2isH) {
    		const midY = (coords1.y + coords2.y) / 2;
    		// Définition du chemin avec deux courbes : vertical -> horizontal -> vertical
    		pathData = `
    			M ${coords1.x} ${coords1.y} 
    			C ${coords1.x} ${midY}, ${coords1.x} ${midY}, ${(coords1.x + coords2.x)/2} ${midY} 
    			C ${coords2.x} ${midY}, ${coords2.x} ${midY}, ${coords2.x} ${coords2.y}
    		`;
    	} else {
    		if (anchor1isH) {
    			coords1 = getAnchorCoordinates(anchorId2, appendTo);
    			coords2 = getAnchorCoordinates(anchorId1, appendTo);
    		}
    		const midY = (coords1.y + coords2.y) / 2;
    		// Définition du chemin avec un seul virage
    		pathData = `
    			M ${coords1.x} ${coords1.y} 
    			C ${coords1.x} ${coords2.y}, ${coords1.x} ${coords2.y}, ${coords2.x} ${coords2.y}
    		`;
    	}
    }
    
	// Création de l'élément SVG <path>
	const path = document.createElementNS("http://www.w3.org/2000/svg", "path");

	if (!pathData.includes("NaN")) {
        path.setAttribute("d", pathData);
    } else {
        console.warn("Chemin SVG ignoré car pathData contient NaN");
        return;
    }
    
    path.setAttribute("fill", "none");
	path.setAttribute("stroke-width", "2");
	//path.setAttribute("filter", "url(#blurEffect)"); // Utilisation du dégradé
	
	// Créer la boule avec le dégradé
	const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
	circle.setAttribute("class", "ball");
	circle.setAttribute("cx", coords1.x); // Départ de la boule
	circle.setAttribute("cy", coords1.y); // Départ de la boule
	circle.setAttribute("r", String(config?.param?.ballSize ?? 4));
	if(isDarkTheme) circle.setAttribute("fill", "url(#gradientDark)"); // Utilisation du dégradé
	else circle.setAttribute("fill", "url(#gradientLight)"); // Utilisation du dégradé
	
	// Ajouter le path et le circle au groupe
	pathContainer.appendChild(path);
	circContainer.appendChild(circle);
	
	const state = getState(appendTo);

	// Stocker la direction AVANT de lancer l'animation pour que la closure l'ait dès le départ
	state.directionControls.set(anchorId1, direction_init);

	// Animer la boule le long du path et recuperation du pointeur de fonction "reverse"
	const controls = animateBallAlongPath(anchorId1, path, circle, appendTo);
	
	// ajout du pointeur "reverse" (et "cancel") dans un "map" pour exploitation ulterieur
	state.pathControls.set(anchorId1, controls);
}

/*********************************************************/
/* fonction de recuperation des coordonnées des ancres : */
/* recoit en param l'ancre recherché                     */
/*********************************************************/
function getAnchorCoordinates(anchorId, appendTo) {
	
	const columnIndex = anchorId[0];
	const boxIndex = anchorId.substring(0, 3);
	
	const anchor = appendTo.querySelector(`#dashboard > #column-${columnIndex} > #box_${boxIndex} > #anchor_${anchorId}`);
	const container = appendTo.querySelector(`#dashboard`);
	
	if (!anchor || !container) {
		console.error("Anchor ou container introuvable : " + anchorId);
		return null;
	}
	
	// Position de l'anchor dans le document
	const anchorRect = anchor.getBoundingClientRect();
	
	// Position du container dans le document
	const containerRect = container.getBoundingClientRect();
	
	// Calcul des coordonnées relatives
	const relativeX = (anchorRect.left - containerRect.left + anchorRect.width / 2)*1000/containerRect.width;
	const relativeY = (anchorRect.top - containerRect.top + anchorRect.height / 2)*600/containerRect.height;
	
	//const relativeX = anchorRect.left - containerRect.left + anchorRect.width / 2;
	//const relativeY = anchorRect.top - containerRect.top + anchorRect.height / 2;
	
	return { x: parseFloat(relativeX.toFixed(2)), y: parseFloat(relativeY.toFixed(2)) };
}

/******************************************************************/
/* fonction de lancement de l'animation sur les liens :           */
/* recoit en param l'id du lien dans le map (son ancre d'origine) */
/* necessaire pour recuperer le sens de base de circulation du    */
/* circle, le path pour le deplacement du circle, et le circle à  */
/* deplacer                                                       */
/******************************************************************/
function animateBallAlongPath(anchorId1, path, circle, appendTo) {

	const state = getState(appendTo);
	let direction = state.directionControls.get(anchorId1);
	
	const pathLength = path.getTotalLength(); // Longueur totale du path
	
	const box = appendTo.querySelector(`#dashboard`);
	const boxWidth = box.offsetWidth;

	const speed = boxWidth/10; // Vitesse de la boule en pixels par seconde 100/900
	const duration = pathLength / speed * 1000; // Durée de l'animation (en ms)
	let startTime;
	let rafId = null;

	// Externe Referenz für Self-Recovery-Prüfung (wird in checkForReverse gelesen)
	const controls = {
		reverse: reverseDirection,
		cancel: cancel,
		lastTick: performance.now(),
	};
	
	function reverseDirection(cmd) {
	    const directionInit = getState(appendTo).directionControls.get(anchorId1);
		direction = directionInit*cmd; // Inverser la direction
	}

	function cancel() {
		if (rafId !== null) {
			cancelAnimationFrame(rafId);
			rafId = null;
		}
	}
	
	function moveBall(time) {
		// Element nicht im DOM: Loop am Leben halten (HA kann Karte
		// temporär aus dem DOM nehmen), aber nichts zeichnen.
		// disconnectedCallback → clearAllIntervals beendet den Loop bei echter Entfernung.
		if (!circle.isConnected) {
			rafId = requestAnimationFrame(moveBall);
			return;
		}
		controls.lastTick = time;
		try {
			if (!startTime) startTime = time;
			
			const elapsed = time - startTime;
			var progress = duration > 0 ? (elapsed % duration) / duration : 0;
			
			if (direction == -1) {
				progress = 1 - progress;
			} else if (direction == 0) {
				progress = 0; 
			}
			
			const point = path.getPointAtLength(progress * pathLength);
			
			circle.setAttribute("cx", point.x);
			circle.setAttribute("cy", point.y);
		} catch(e) {
			// Fehler ignorieren damit der Loop nie abbricht
		}
		
		rafId = requestAnimationFrame(moveBall);
	}
	
	// Démarrer l'animation
	rafId = requestAnimationFrame(moveBall);
	
	return controls;
}

/******************************************************/
/* fonction de d'invertion de l'animation :           */
/* verifie la valeur de l'entité et change le sens si */
/* necessaire                                         */
/******************************************************/
export function checkForReverse(devices, hass, appendTo) {

    const state = getState(appendTo);
    const { pathControls } = state;

    // Self-Recovery: Karte ist gerendert, kein Redraw läuft,
    // aber entweder keine Circles im DOM oder Animationen sind "tot" (lastTick älter als 3s)
    if (state.dashboardOldWidth !== undefined && !state.mustRedrawLine && state.checkReadyRafId === null) {
        const cc = appendTo.querySelector('#dashboard > #svg_container > #circ_container');
        if (cc && cc.children.length === 0 && pathControls.size > 0) {
            state.mustRedrawLine = true;
            return;
        }
        // Prüfe ob irgendein Animations-Loop nicht mehr tickt
        const now = performance.now();
        let anyStale = false;
        pathControls.forEach(ctrl => {
            if (ctrl && ctrl.lastTick && (now - ctrl.lastTick) > 3000) {
                anyStale = true;
            }
        });
        if (anyStale) {
            state.mustRedrawLine = true;
            return;
        }
    }
    
    for (const boxId in devices) {
            const device = devices[boxId];
            
            // Parcours des liens numérotés
            const links = device.link;
            
            if(links !== "nolink") {
                for (const linkId in links) {
                    
                    const link = links[linkId];
                    if (!link || typeof link !== "object") continue;
                    
                    const stateLinkEnt = link.entity ? hass.states[link.entity] : undefined;
                    const rawValue = stateLinkEnt ? stateLinkEnt.state : undefined;
                    const valueLinkEnt = parseFloat(rawValue);
                    
                    const pathControl = pathControls.get(`${boxId}_${link.start}`);
                    
                    if (pathControl && typeof pathControl.reverse === "function") {
                        // Nur setzen wenn der Wert eine gültige Zahl ist
                        if (!isNaN(valueLinkEnt)) {
                            if(valueLinkEnt < -0.5) pathControl.reverse(-1); 
                            else if(valueLinkEnt > 0.5) pathControl.reverse(1); 
                            else pathControl.reverse(0);
                        }
                    } 
                }
        	}
        }
}

/******************************************************/
/* groupe de fonctions permettant de lancer la recup  */
/* de l'historique a interval regulier                */
/******************************************************/
export async function startPeriodicTask(config, hass, appendTo) {
    
    // Nur die Intervalle DIESER Karte stoppen (früher wurden global alle
    // Intervalle gelöscht → Editor-Vorschau stoppte die Graphen der Hauptkarte)
    clearCardIntervals(appendTo);
    
    const devices = config.devices || {};
    const state = appendTo ? getState(appendTo) : null;
    const cardIntervals = state ? state.intervals : intervals;
    const intervalMinutes = 15;
    let allOk = true;
    
    for (const boxId in devices) {
        
        const device = devices[boxId];
            
        if(device && isTrue(device.graph) && device.entity && !cardIntervals.has(device.entity)) {
            
            // Vérifie si la première exécution réussit
            const firstExecutionSuccessful = await performTask(device.entity, hass);
            
            if (!firstExecutionSuccessful) {
                // Kein Abbruch für alle anderen Graphen – nur diese Entität überspringen
                console.warn(`Victron VRM API Card: Historie für ${device.entity} nicht verfügbar.`);
                allOk = false;
                continue;
            }
            
            // Planifier la tâche périodique pour cette entité (immer mit aktuellem hass)
            const intervalId = setInterval(() => {
                performTask(device.entity, (state && state.hass) || hass);
            }, intervalMinutes * 60 * 1000);
    
            // Stocker l'intervalle dans la Map
            cardIntervals.set(device.entity, intervalId);
        }
    }
    return allOk;
}

function clearCardIntervals(appendTo) {
    const map = appendTo ? getState(appendTo).intervals : intervals;
    map.forEach((intervalId) => clearInterval(intervalId));
    map.clear();
}

export function clearAllIntervals(appendTo) {
    // Animationen und RAFs dieser Karteninstanz stoppen
    if (appendTo) {
        const state = getState(appendTo);
        if (state.checkReadyRafId !== null) {
            cancelAnimationFrame(state.checkReadyRafId);
            state.checkReadyRafId = null;
        }
        state.pathControls.forEach(ctrl => { if (ctrl && ctrl.cancel) ctrl.cancel(); });
        state.pathControls.clear();
        state.directionControls.clear();
        state.graphDrawn.clear();
        state.mustRedrawLine = true;
        clearCardIntervals(appendTo);
        return;
    }
    // Ohne Karten-Referenz (Altverhalten): alle globalen Intervalle stoppen
    clearCardIntervals(null);
}

async function performTask(entityId, hass) {
    // Historie der letzten 24h abrufen (wartet jetzt korrekt auf das Ergebnis)
    try {
        return (await fetchHistoricalData(entityId, 24, hass)) === true;
    } catch (e) {
        return false;
    }
}

async function fetchHistoricalData(entityId, periodInHours = 24, hass, numSegments = 6) {
    const now = new Date();
    const startTime = new Date(now.getTime() - periodInHours * 60 * 60 * 1000); // Période spécifiée

    if (!hass || !hass.states || !hass.states[entityId] || typeof hass.callApi !== "function") {
        return false;
    }

    // URL pour l'API Home Assistant
    const url = `history/period/${startTime.toISOString()}?filter_entity_id=${encodeURIComponent(entityId)}&minimal_response=true&no_attributes=true&significant_changes_only=true`;

    try {
        const response = await hass.callApi('GET', url);

        if (!Array.isArray(response) || response.length === 0 || !Array.isArray(response[0]) || response[0].length === 0) {
            console.log(`Aucune donnée disponible pour "${entityId}" dans la période de ${periodInHours} heure(s).`);
            return false;
        }

        const rawData = response[0];

        // Étape 1 : Transformer les données en un format exploitable
        const formattedData = rawData
            .map((item) => ({
                // minimal_response: last_changed (ISO) bzw. lu (Sekunden) je nach HA-Version
                time: new Date(item.last_changed ?? item.last_updated ?? (item.lu ? item.lu * 1000 : undefined)),
                state: parseFloat(item.state ?? item.s), // Conversion en nombre
            }))
            .filter((item) => !isNaN(item.state) && !isNaN(item.time.getTime())); // Filtrer les données invalides

        if (formattedData.length === 0) {
            console.log(`Aucune donnée valide formatée pour "${entityId}".`);
            return false;
        }

        // Étape 2 : Réduire les données en segments tout en maintenant l'échelle Y constante
        const interval = 30 * 60 * 1000; // 15 minutes en millisecondes
                const totalIntervals = (periodInHours * 60 * 60 * 1000) / interval; // Calcul du nombre d'intervalles pour la période donnée
                const startTimestamp = Math.floor(startTime.getTime() / interval) * interval;
            
                const reducedData = [];
                for (let i = 0; i < totalIntervals; i++) {
                    const targetTime = new Date(startTimestamp + i * interval);
                    const closest = formattedData.reduce((prev, curr) => {
                        return Math.abs(curr.time - targetTime) < Math.abs(prev.time - targetTime) ? curr : prev;
                    });
                    reducedData.push({ time: targetTime, value: closest.state });
                }
        
        // Étape 2bis : Ajouter les points min et max dans le tableau reducedData
        const segmentSize = Math.ceil(formattedData.length / numSegments);
        for (let i = 0; i < formattedData.length; i += segmentSize) {
            const segment = formattedData.slice(i, i + segmentSize);
        
            let minPoint = { value: Infinity, time: null };
            let maxPoint = { value: -Infinity, time: null };
        
            segment.forEach((point) => {
                if (point.state < minPoint.value) minPoint = { value: point.state, time: point.time };
                if (point.state > maxPoint.value) maxPoint = { value: point.state, time: point.time };
            });
        
            // Ajouter les min et max au tableau réduit
            reducedData.push({ time: minPoint.time, value: minPoint.value });
            reducedData.push({ time: maxPoint.time, value: maxPoint.value });
        }

        // Étape 3 : Trier par ordre chronologique
        reducedData.sort((a, b) => a.time - b.time);
        
        //console.log(reducedData);

        // Étape 4 : Stocker les données réduites
        historicData.set(
            entityId,
            reducedData.map((point) => ({
                time: point.time,
                value: point.value,
            }))
        );
        
        updateGraphTriggers.set(entityId, true);
        historicVersion.set(entityId, (historicVersion.get(entityId) || 0) + 1);

        return true;
    } catch (error) {
        console.error('Erreur lors de la récupération de l’historique :', error);
        return false;
    }
}





export const getEntityNames = (entities) => {
  return entities?.split("|").map((p) => p.trim());
};

export const getFirstEntityName = (entities) => {
  const names = getEntityNames(entities);
  return names.length > 0 ? names[0] : "";
};


export function getDefaultConfig(hass) {
    
    // --- CUSTOM LOGIC FOR VICTRON VRM API INTEGRATION ---
    // Die Integration erzeugt entity_ids nach dem Schema "sensor.vrm_<name>"
    // (z.B. sensor.vrm_state_of_charge, sensor.vrm_ac_input_power_l1).
    // Bei mehreren Geräten hängt HA "_2", "_3" ... an.
    const states = hass?.states || {};
    const vrmEntities = Object.keys(states).filter(id => id.startsWith("sensor.vrm_"));
    const pickVrm = (...names) => {
        for (const name of names) {
            const re = new RegExp(`^sensor\\.vrm_${name}(_\\d+)?$`);
            const found = vrmEntities.filter(id => re.test(id)).sort()[0];
            if (found) return found;
        }
        return undefined;
    };

    // Battery SOC
    const vrmBatterySoc = pickVrm("state_of_charge", "system_state_of_charge");
    // Battery Power (Total or Summary)
    const vrmBatteryPower = pickVrm("batteries_power_total", "battery_power");
    // Battery Current (Richtung der Animation)
    const vrmBatteryCurrent = pickVrm("current");
    // Grid Power (Grid Meter gesamt, sonst MultiPlus AC In)
    const vrmGrid = pickVrm("grid_total_power", "ac_input_power_l1");
    // Home Power (MultiPlus AC Out)
    const vrmHome = pickVrm("ac_output_power_l1");
    // Solar Power (Summen-Sensoren bevorzugt)
    const vrmSolar = pickVrm("solar_chargers_power_total", "pv_inverters_power_total", "battery_watts", "l1_power");
    // --- END CUSTOM LOGIC ---
      
    const powerEntities = Object.keys(states).filter((entityId) => {
        const stateObj = states[getFirstEntityName(entityId)];
        if (!stateObj) return false;
        const isAvailable =
          (stateObj.state && stateObj.attributes && stateObj.attributes.device_class === "power") || stateObj.entity_id.includes("power");
        return isAvailable;
    });
  
    function checkStrings(entiyId, testStrings) {
        const firstId = getFirstEntityName(entiyId);
        const friendlyName = states[firstId]?.attributes?.friendly_name;
        return testStrings.some((str) => firstId.includes(str) || friendlyName?.includes(str));
    }
  
    const gridPowerTestString = ["grid", "utility", "net", "meter"];
    const solarTests = ["solar", "pv", "photovoltaic", "inverter"];
    const batteryTests = ["battery"];
    const batteryPercentTests = ["battery_percent", "battery_level", "state_of_charge", "soc", "percentage"];
    const firstGridPowerEntity = vrmGrid || powerEntities.filter((entityId) => checkStrings(entityId, gridPowerTestString))[0];
    const firstSolarPowerEntity = vrmSolar || powerEntities.filter((entityId) => checkStrings(entityId, solarTests))[0];
    
    const currentEntities = Object.keys(states).filter((entityId) => {
        const stateObj = states[entityId];
        const isAvailable = stateObj && stateObj.state && stateObj.attributes && stateObj.attributes.unit_of_measurement === "A";
        return isAvailable;
    });
    const percentageEntities = Object.keys(states).filter((entityId) => {
        const stateObj = states[entityId];
        const isAvailable = stateObj && stateObj.state && stateObj.attributes && stateObj.attributes.unit_of_measurement === "%";
        return isAvailable;
    });
    const firstBatteryPercentageEntity = vrmBatterySoc || percentageEntities.filter((entityId) => checkStrings(entityId, batteryPercentTests))[0];
    
    const firstCurrentEntity = vrmBatteryCurrent || currentEntities.filter((entityId) => checkStrings(entityId, batteryTests))[0];
    
    // Custom VRM overrides for missing detections
    const gridEntity = vrmGrid || firstGridPowerEntity;
    const solarEntity = vrmSolar || firstSolarPowerEntity;
    const batterySocEntity = vrmBatterySoc || firstBatteryPercentageEntity;
    const batteryCurrentEntity = vrmBatteryCurrent || firstCurrentEntity;
    const homeEntity = vrmHome || firstGridPowerEntity; // Fallback? Or leave blank? The original used grid? No, default uses Grid.

  
    return {
        param: {
            boxCol1: 2,
            boxCol3: 2,
        },
        theme: "dark",
        styles: {
            header: 10,
            sensor: 16,
        },
        devices: {
            "1-1": {
                icon: "mdi:transmission-tower",
                name: "Grid",
                entity: gridEntity ?? "",
                anchors: "R-1",
                link: {
                    "1":{
                        start: "R-1",
                        end: "2-1_L-1",
                    },
                },
            },
            "1-2": {
                icon: "mdi:battery-charging",
                name: "Battery",
                entity: batterySocEntity ?? "",
                ...(vrmBatteryPower ? { entity2: vrmBatteryPower } : {}),
                anchors: "R-1",
                gauge: true,
                link: {
                    "1":{
                        start: "R-1",
                        end: "2-1_B-1",
                        entity: batteryCurrentEntity ?? "",
                    },
                },
            },
            "2-1": {
                icon: "mdi:cellphone-charging",
                name: "Multiplus",
                anchors: "L-1, B-2, R-1",
            },
            "3-1": {
                icon: "mdi:home-lightning-bolt",
                name: "Home",
                entity: homeEntity ?? "",
                anchors: "L-1",
                link: {
                    "1":{
                        start: "L-1",
                        end: "2-1_R-1",
                    },
                },
            },
            "3-2": {
                icon: "mdi:weather-sunny",
                name: "Solar",
                entity: solarEntity ?? "",
                anchors: "L-1",
                link: {
                    "1":{
                        start: "L-1",
                        end: "2-1_B-2",
                        entity: solarEntity ?? "",
                        inv: true,
                    },
                },
            },
        },
    }
}
