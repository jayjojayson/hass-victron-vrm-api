export function css(user) {
    var css =`
    
        #tab-panel {
              display: flex;
              flex-direction: column;
              height: 100%;
            }
    
            .content {
                /*padding: 16px;*/
            }
    
            .editor {
                display: flex;
                flex-direction: column;
                gap: 20px;
                padding: 20px 0px;
            }
            
            .devices-editor {
                display: flex;
                flex-direction: column;
                padding: 0px 0px;
            }
            
            .subTab-content {
                display: flex;
                flex-direction: column;
                gap: 20px;
                padding: 20px 0px;
            }
              
            .col{
                position: relative;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
              
            .row{
                position: relative;
                display: flex;
                flex-direction: row;
                align-items: center;
                gap: 10px;
            }
            
            .inner {
                padding: 10px 5px;
            }
            
            .cell{
                flex: 1; 
            }
            
            .cellx1-5{
                flex: 1.5; 
            }
              
            .left{
                position: relative;
                display: flex;
                justify-content: flex-start;
                align-items: center;
                gap: 10px;
            }
              
            .right{
                position: relative;
                display: flex;
                justify-content: flex-end;
                align-items: center;
                gap: 10px;
            }
            
            .contMenu {
                position: relative;
                display: flex;
                flex-direction: column;
                box-shadow: none;
                border-width: 1px;
                border-style: solid;
                border-color: var(--outline-color);
                border-radius: var(--ha-card-border-radius, 12px);
                padding: 0px 8px;

            }
            
            .headerMenu {
                font-weight: 500;
            }
            
            .noGap {
                gap: 0;
            }
            
            /* --- Custom Fixes for Home Assistant Integration --- */
            
            /* Ensure Entity Picker is visible */
            ha-entity-picker {
                display: block;
                margin-top: 8px;
                margin-bottom: 8px;
                width: 100%;
            }
            
            /* Ensure Expansion Panel inner content doesn't collapse */
            ha-expansion-panel .inner {
                display: block; 
                overflow: visible;
            }
            
            /* --- Tabs (eigene Buttons, unabhängig von HA-internen Komponenten) --- */
            .vrm-tabs {
                display: flex;
                flex-wrap: wrap;
                border-bottom: 1px solid var(--divider-color, #444);
                margin-bottom: 4px;
            }

            .vrm-subtabs {
                margin-top: 8px;
            }

            .vrm-tab {
                appearance: none;
                background: none;
                border: none;
                border-bottom: 2px solid transparent;
                margin-bottom: -1px;
                color: var(--secondary-text-color);
                font: inherit;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.04em;
                padding: 10px 16px;
                min-height: 40px;
                cursor: pointer;
                transition: color 0.2s ease, border-color 0.2s ease, background-color 0.2s ease;
            }

            .vrm-tab:hover {
                background-color: rgba(var(--rgb-primary-text-color, 255, 255, 255), 0.05);
                color: var(--primary-text-color);
            }

            .vrm-tab[active] {
                border-bottom-color: var(--primary-color);
                color: var(--primary-color);
            }

            .vrm-tab-panel {
                padding: 0 4px;
            }

            /* --- Eingabefelder (ersetzen ha-textfield, in HA 2026.10 entfernt) --- */
            .vrm-field {
                display: flex;
                flex-direction: column;
                gap: 4px;
                min-width: 0;
            }

            .vrm-field-label {
                font-size: 0.85em;
                color: var(--secondary-text-color);
            }

            .vrm-input {
                width: 100%;
                box-sizing: border-box;
                padding: 10px 8px;
                font: inherit;
                background: var(--input-fill-color, var(--secondary-background-color, #1c2536));
                color: var(--primary-text-color);
                border: 1px solid var(--divider-color, #404040);
                border-radius: 4px;
                outline: none;
            }

            .vrm-input:focus {
                border-color: var(--primary-color);
            }

            .vrm-input:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }

            /* --- Radio-Buttons (ersetzen ha-radio/ha-formfield) --- */
            .radio-group {
                flex-wrap: wrap;
                gap: 6px 16px;
            }

            .vrm-radio {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                cursor: pointer;
                color: var(--primary-text-color);
            }

            .vrm-radio input[type="radio"] {
                accent-color: var(--primary-color);
                width: 18px;
                height: 18px;
                margin: 0;
                cursor: pointer;
            }

            input[type="range"] {
                accent-color: var(--primary-color);
            }
            
  `
    return css;

}
