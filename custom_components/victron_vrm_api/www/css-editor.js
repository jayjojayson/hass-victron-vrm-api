export function css(user) {
    var css =`
    
        #sl-tab-content {
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
            
            /* Style sl-tab to look like tabs (buttons) */
            sl-tab {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                padding: 10px 16px;
                cursor: pointer;
                font-weight: 500;
                text-transform: uppercase;
                border-bottom: 2px solid transparent;
                transition: all 0.3s ease;
                min-height: 40px;
            }
            
            sl-tab:hover {
                background-color: rgba(var(--rgb-primary-text-color), 0.05);
            }
            
            sl-tab[active] {
                border-bottom-color: var(--primary-color);
                color: var(--primary-color);
            }
            
  `
    return css;

}
