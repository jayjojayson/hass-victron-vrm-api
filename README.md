[![HACS validation](https://img.shields.io/github/actions/workflow/status/jayjojayson/hass-victron-vrm-api/validate.yml?label=HACS%20Validation)](https://github.com/jayjojayson/hass-victron-vrm-api/actions?query=workflow%3Avalidate)
[![hacs_badge](https://img.shields.io/badge/HACS-Default%20✔-brightgreen.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/jayjojayson/hass-victron-vrm-api?include_prereleases=&sort=semver&color=blue)](https://github.com/jayjojayson/hass-victron-vrm-api/releases/)
[![GH-code-size](https://img.shields.io/github/languages/code-size/jayjojayson/hass-victron-vrm-api?color=blue)](https://github.com/jayjojayson/hass-victron-vrm-api)
[![README Deutsch](https://img.shields.io/badge/README-DE-orange)](https://github.com/jayjojayson/hass-victron-vrm-api/blob/main/docs/README_deutsch.md)
[![Support](https://img.shields.io/badge/%20-Support%20Me-steelblue?style=flat&logo=paypal&logoColor=white)](https://www.paypal.me/quadFlyerFW)
![stars](https://img.shields.io/github/stars/jayjojayson/hass-victron-vrm-api)

# ⚡ Victron VRM API for Home Assistant

**Bring your Victron system into Home Assistant via the Victron VRM Portal, with no local access to the GX device needed.**

The integration reads your data from the VRM cloud API. All you need for the setup is your VRM access token, your Site ID and the instance IDs of your devices. It is perfect for **motorhomes, caravans and boats** without a local connection to the Victron system, but works just as well at home.

It also includes a **dashboard card in the style of the Venus OS GUI v2**, with animated energy flows, history graphs and a visual editor.

<p align="center">
  <img src="https://raw.githubusercontent.com/jayjojayson/hass-victron-vrm-api/main/docs/victron-vrm-api-card.png" alt="Victron VRM API Card" width="760">
</p>

If you like the integration, I would appreciate a star ⭐. 🤗

---

## ✨ Features

- 🔋 **Battery, MultiPlus, PV inverter, solar charger (MPPT), tank and grid meter**: live values, alarms and daily energy
- 🧭 **System values** calculated by Venus OS: total grid power, house consumption (AC loads before and behind the MultiPlus), total PV and battery power
- 🌡️ **Other devices via custom instance IDs**: temperature sensors / RuuviTag, GPS, Orion XS, EV charger and more. One sensor is created for every value VRM provides
- 📊 **Overall stats** for today, week, month and year, plus the **VRM solar and consumption forecast**
- 🖥️ **Dashboard card** with energy flow animation, history graphs, gauges and a full visual editor (registered automatically)
- 🌍 Translated into English and German, card editor also in French
- ✅ Compatible with **Home Assistant 2026.10** (entity IDs and history are kept on update)

---

## ✔️ Prerequisites

| What | Where to find it |
| :--- | :--- |
| **VRM access token** (keep it secret!) | VRM Portal → *Preferences → Integrations → Access tokens*, or [this link](https://vrm.victronenergy.com/access-tokens) |
| **Site ID** (VRM installation ID) | The number in the address bar when you open your installation in the VRM Portal: `vrm.victronenergy.com/installation/<Site ID>/…` |
| **Instance IDs** of your devices | VRM Portal → your installation → *Device list* (column *Instance*) |

<details>
<summary><b>📷 How to find Site ID, instance IDs and token</b></summary>
<br>
<img src="https://raw.githubusercontent.com/jayjojayson/hass-victron-vrm-api/main/docs/vrm-api-description.png" alt="Where to find Site ID, instance IDs and token" width="100%">
</details>

---

## 📥 Installation

### ➡️ HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jayjojayson&repository=hass-victron-vrm-api&category=integration)

1. Open the link above, or search for **Victron VRM API** in HACS, and install the integration
2. Restart Home Assistant
3. Go to *Settings → Devices & Services → Add Integration* and search for **Victron VRM API** (or just `vrm`)

### ➡️ Manual

1. Download the [latest release](https://github.com/jayjojayson/hass-victron-vrm-api/releases/latest)
2. Copy the folder `custom_components/victron_vrm_api` into the `custom_components` folder of your Home Assistant
3. Restart Home Assistant and add the integration as described above

---

## ⚙️ Configuration

All fields except Site ID and token are optional. **Leave a field empty** if you don't have that device. Several devices of the same type can be entered **separated by commas**, e.g. `274, 275`. You can change the configuration later at any time via *⋮ → Reconfigure*.

| Field | Example | Description |
| :--- | :--- | :--- |
| **Site ID** | `123456` | Your VRM installation ID |
| **API token** | `abc…` | VRM access token |
| **Battery** | `274` | Battery monitor / BMS (e.g. SmartShunt, BMV, Lynx) |
| **MultiPlus** | `275` | MultiPlus / Quattro / inverter-charger |
| **PV Inverter** | `20` | AC-coupled PV inverter (1 or 3 phases) |
| **Tank** | `21, 22` | Tank sensors (e.g. Mopeka, GX Tank) |
| **Solar Charger** | `278` | MPPT solar charger |
| **Grid Meter** | `30` | Energy meter on the grid connection |
| **Other devices** | `24, 25` | Any other device from the VRM device list, see below |

### 🌡️ Other devices (custom instance IDs)

Devices without their own VRM widget can be added via the field **"Other devices – instance_id"**: temperature sensors and RuuviTags, GPS, Orion XS, EV charging stations and more. Enter the instance ID from the VRM device list.

The integration creates **one device per instance and device type**, with **one sensor for every value** VRM provides for it. Name and unit are taken directly from VRM. If two different device types share the same instance ID, e.g. a tank sensor and a temperature sensor, each one gets its own device.

---

## 🖥️ Dashboard card

The integration includes the **Victron VRM API Card**. It is registered automatically as a dashboard resource, so you don't need to install anything else. Just add the card via *Edit dashboard → Add card → Victron VRM API Card*. The card automatically picks suitable VRM sensors for grid, house, solar and battery as a starting point.

<p align="center">
  <img src="https://raw.githubusercontent.com/jayjojayson/hass-victron-vrm-api/main/docs/victron-vrm-api-card-editor.png" alt="Victron VRM API Card editor" width="760">
</p>

**What the card can do**

- **Up to 10 boxes in 3 columns** (4 / 2 / 4), each with icon, name, main value, optional second value, header value and **up to 3 footer values**
- **Animated energy flows** between boxes. The direction follows the sign of a sensor (e.g. charging or discharging current), and it can be reversed per link
- **History graph** of the last 24 hours per box, with a **freely selectable color**
- **Gauge**: percentage values such as the state of charge fill the box from the bottom
- **Themes**: light, dark, auto (follows Home Assistant) or transparent
- **Colors** for frame, anchors, lines, graph, animation ball and text, plus an adjustable ball size
- **Font sizes** for header, values and footer: *Auto* or a fixed size in px
- **Footer layout per box**: side by side or stacked, aligned left, center or right
- Values are formatted like in Home Assistant (precision, language). A click on a box opens the entity details

**Visual editor**

Everything can be set in the visual editor, no YAML needed:

- **General** (*Conf.*): theme, number of boxes per column, font sizes, colors and ball size
- **Col. 1–3** (German: *Spalte 1–3*): per box, icon, name, sensors, graph, gauge, footer layout, anchors and links

<details>
<summary><b>📝 YAML example</b></summary>

```yaml
type: custom:victron-vrm-api-card
theme: auto
param:
  boxCol1: 2
  boxCol2: 1
  boxCol3: 2
  ballSize: 4
styles:
  header: 10
  sensor: 16
  footer: auto
colors:
  history: "#4caf50"
devices:
  "1-1":
    name: Grid
    icon: mdi:transmission-tower
    entity: sensor.vrm_system_grid_power
    graph: true
    anchors: R-1
    link:
      "1":
        start: R-1
        end: 2-1_L-1
  "1-2":
    name: Battery
    icon: mdi:battery-charging
    entity: sensor.vrm_state_of_charge
    entity2: sensor.vrm_batteries_power_total
    gauge: true
    anchors: R-1
    link:
      "1":
        start: R-1
        end: 2-1_B-1
        entity: sensor.vrm_current
  "2-1":
    name: Multiplus
    icon: mdi:cellphone-charging
    anchors: L-1, B-2, R-1
  "3-1":
    name: Home
    icon: mdi:home-lightning-bolt
    entity: sensor.vrm_system_ac_consumption
    footerEntity1: sensor.vrm_ac_output_power_l1
    footerLayout: vertical
    footerAlign: right
    anchors: L-1
    link:
      "1":
        start: L-1
        end: 2-1_R-1
  "3-2":
    name: Solar
    icon: mdi:weather-sunny
    entity: sensor.vrm_system_pv_power
    graph: true
    anchors: L-1
    link:
      "1":
        start: L-1
        end: 2-1_B-2
        entity: sensor.vrm_system_pv_power
        inv: true
```

| Option | Values | Description |
| :--- | :--- | :--- |
| `theme` | `light`, `dark`, `auto`, `transparent` | Card theme |
| `param.boxCol1` / `boxCol2` / `boxCol3` | 1–4 / 1–2 / 1–4 | Number of boxes per column |
| `param.ballSize` | 2–15 | Size of the animation ball |
| `styles.header` / `sensor` / `footer` | number (px) or `auto` | Font sizes |
| `colors.*` | `boxShadow`, `anchor`, `graph`, `history`, `ball`, `textMain`, `textSub` | Colors (hex) |
| `devices."c-b".anchors` | e.g. `L-1, B-2, R-1` | Anchors per side: **L**eft, **T**op, **B**ottom, **R**ight |
| `devices."c-b".link.N` | `start`, `end`, `entity`, `inv` | Line from an anchor of this box to an anchor of another box. `entity` sets the flow direction, `inv` reverses it |
| `devices."c-b".footerLayout` | `horizontal` (default), `vertical` | Footer side by side or stacked |
| `devices."c-b".footerAlign` | `left`, `center` (default), `right` | Footer alignment |

</details>

> 💡 **YAML dashboards:** if your dashboards are in YAML mode, add the resource manually: `url: /victron_vrm_api/victron-vrm-api.js`, `type: module`.

---

## 📋 Supported devices and sensors

<details>
<summary><b>🔋 Battery</b> (34 sensors)</summary>

| Sensor | VRM ID / Key | Unit | Description |
| :--- | :--- | :---: | :--- |
| State of charge | `51` | % | State of Charge (SOC) |
| Voltage | `47` | V | Battery Voltage |
| Current | `49` | A | Battery Current |
| Consumed Amphours | `50` | Ah | Consumed Amphours |
| Time to go | `52` | h | Time to go until empty |
| Battery Temperature | `115` | °C | Battery Temperature |
| Minimum Cell Voltage | `173` | V | Minimum Cell Voltage (BMS) |
| Maximum Cell Voltage | `174` | V | Maximum Cell Voltage (BMS) |
| Cell Voltage Difference | *(Calculated)* | V | Cell Voltage Difference |
| Battery Power | *(Calculated)* | W | Current Power (V*A) |
| Battery Charge Cycles | `58` | - | Full Charge Cycles |
| Battery to Consumers (Today) | `Bc` | kWh | Energy to Load (Today) |
| Battery to Grid (Today) | `Bg` | kWh | Energy to Grid (Today) |
| Low voltage alarm | `119` | - | Low voltage alarm |
| High voltage alarm | `120` | - | High voltage alarm |
| Low starter-voltage alarm | `121` | - | Low starter-voltage alarm |
| High starter-voltage alarm | `122` | - | High starter-voltage alarm |
| Low state-of-charge alarm | `123` | - | Low state of charge |
| Low battery temperature alarm | `124` | - | Battery temperature too low |
| High battery temperature alarm | `125` | - | Battery temperature too high |
| Mid-voltage alarm | `126` | - | Mid-voltage anomaly |
| Low fused-voltage alarm | `155` | - | Low fused voltage |
| High fused-voltage alarm | `156` | - | High fused voltage |
| Fuse blown alarm | `157` | - | Fuse blown |
| High internal-temperature alarm | `158` | - | Internal temperature alarm |
| Cell imbalance alarm | `286` | - | Cell imbalance detected |
| High charge current alarm | `287` | - | Charge current too high |
| High discharge current alarm | `288` | - | Discharge current too high |
| Internal failure | `289` | - | Internal failure detected |
| High charge temperature alarm | `459` | - | Charge temperature too high |
| Low charge temperature alarm | `460` | - | Charge temperature too low |
| Low cell voltage | `522` | - | Low cell voltage |
| Charge blocked | `739` | - | Charging blocked (BMS) |
| Discharge blocked | `740` | - | Discharging blocked (BMS) |

</details>

<details>
<summary><b>⚡ MultiPlus</b> (12 sensors)</summary>

| Sensor | VRM ID / Key | Unit | Description |
| :--- | :--- | :---: | :--- |
| AC Input Voltage L1 | `8` | V | AC Input Voltage Phase 1 |
| AC Input Power L1 | `17` | W | AC Input Power Phase 1 |
| AC Output Voltage L1 | `20` | V | AC Output Voltage Phase 1 |
| AC Output Power L1 | `29` | W | AC Output Power Phase 1 |
| DC Bus Voltage | `32` | V | DC Bus Voltage |
| DC Bus Current | `33` | A | DC Bus Current |
| VE.Bus State | `40` | - | Operating State (e.g., Inverting) |
| MultiPlus Temperature | `521` | °C | Device Temperature |
| DC Bus Power | *(Calculated)* | W | Current DC Power (V*A) |
| System State of Charge | `144` | % | System-calculated state of charge (replaces internal MultiPlus SOC) |
| Grid to Consumers (Today) | `Gc` | kWh | Energy from Grid to Load (Today) |
| Grid to Battery (Today) | `Gb` | kWh | Energy from Grid to Battery (Today) |

</details>

<details>
<summary><b>🏭 Grid Meter</b> (10 sensors)</summary>

| Sensor | VRM ID / Key | Unit | Description |
| :--- | :--- | :---: | :--- |
| Grid L1 Voltage | `834` | V | Voltage on grid meter phase L1 |
| Grid L1 Current | `835` | A | Current on grid meter phase L1 |
| Grid L1 Power | `379` | W | Power on grid meter phase L1. |
| Grid L2 Voltage | `837` | V | Voltage on grid meter phase L2 |
| Grid L2 Current | `838` | A | Current on grid meter phase L2 |
| Grid L2 Power | `380` | W | Power on grid meter phase L2 |
| Grid L3 Voltage | `840` | V | Voltage on grid meter phase L3 |
| Grid L3 Current | `841` | A | Current on grid meter phase L3 |
| Grid L3 Power | `381` | W | Power on grid meter phase L3. |
| Grid Total Power | *(Calculated)* | W | Sum of power across all three phases (L1+L2+L3) |

</details>

<details>
<summary><b>☀️ PV Inverter</b> (17 sensors)</summary>

| Sensor | VRM ID / Key | Unit | Description |
| :--- | :--- | :---: | :--- |
| L1 Voltage | `203` | V | Voltage Phase 1 |
| L1 Current | `204` | A | Current Phase 1 |
| L1 Power | `205` | W | Power Phase 1 |
| L1 Energy | `206` | kWh | Energy Yield Phase 1 (Total) |
| L2 Voltage | `207` | V | Voltage Phase 2 |
| L2 Current | `208` | A | Current Phase 2 |
| L2 Power | `209` | W | Power Phase 2 |
| L2 Energy | `210` | kWh | Energy Yield Phase 2 (Total) |
| L3 Voltage | `211` | V | Voltage Phase 3 |
| L3 Current | `212` | A | Current Phase 3 |
| L3 Power | `213` | W | Power Phase 3 |
| L3 Energy | `214` | kWh | Energy Yield Phase 3 (Total) |
| Status | `246` | - | Status Code |
| PV to Consumers (Today) | `Pc` | kWh | Energy from PV to Load (Today) |
| PV to Battery (Today) | `Pb` | kWh | Energy from PV to Battery (Today) |
| PV to Grid (Today) | `Pg` | kWh | Energy from PV to Grid (Today) |
| PV Total Today | *(Calculated)* | kWh | Total PV Yield Today (Pc+Pb+Pg) |

</details>

<details>
<summary><b>🌞 Solar Charger (MPPT)</b> (7 sensors)</summary>

| Sensor | VRM ID / Key | Unit | Description |
| :--- | :--- | :---: | :--- |
| Battery Watts | `107` | W | Charging Power to Battery |
| Battery Voltage | `81` | V | Battery Voltage |
| Charge State | `85` | - | Charger State (e.g., Bulk, Float) |
| Battery Temperature | `83` | °C | Battery Temperature (external) |
| Yield Today | `94` | kWh | Energy Yield Today |
| Yield Yesterday | `96` | kWh | Energy Yield Yesterday |
| Relay Status | `90` | - | Relay State |

</details>

<details>
<summary><b>🛢️ Tank</b> (6 sensors)</summary>

| Sensor | VRM ID / Key | Unit | Description |
| :--- | :--- | :---: | :--- |
| Capacity | `328` | m³ | Tank Capacity |
| Type | `329` | - | Fluid Type |
| Level | `330` | % | Fluid Level in Percent |
| Remaining | `331` | m³ | Remaining Fluid Volume |
| Status | `443` | - | Tank Status (e.g., OK) |
| Custom Name | `638` | - | User Defined Name |

</details>

<details>
<summary><b>🧭 System Overview</b> (dynamic)</summary>

| Sensor | VRM ID / Key | Unit | Description |
| :--- | :--- | :---: | :--- |
| Infos for each Device | - | - | Detailed Infos for each Device |
| ESS Battery Life State | `332` | - | Current status of the BatteryLife algorithm (e.g., "Self-consumption", "BL Disabled") |
| ESS Battery Life SOC Limit | `333` | % | Dynamic SOC limit currently set by BatteryLife |
| ESS Minimum SOC | `334` | % | User-defined minimum SOC (when grid is available) |
| ESS Scheduled Charging | `469` | - | Status of scheduled charging (e.g., "Active", "Not active") |
| System Grid Power | `/Ac/Grid/L1-3/Power` | W | Total grid power of the system (all phases, as calculated by Venus OS) |
| System AC Consumption | `/Ac/Consumption/L1-3/Power` | W | Total AC consumption (loads before and behind the MultiPlus) |
| System PV Power | `/Dc/Pv/Power` + `/Ac/PvOn…/Power` | W | Total PV power (MPPT + PV inverters) |
| System Battery Power | `/Dc/Battery/Power` | W | Battery power as calculated by the system |


*Additionally for every device of your installation: Firmware, Last Connection, Product Name, Remote IP, Connection Info, Auto Update, Battery Family, Battery Manufacturer, Serial Number, Instance ID (if provided by VRM). The system sensors are only created if your installation provides the values.*

</details>

<details>
<summary><b>📊 Overall Stats</b> (25 sensors)</summary>

| Sensor | VRM ID / Key | Unit | Description |
| :--- | :--- | :---: | :--- |
| * Batteries Total Power | `vrm_batteries_power_total` | W | Total Batteries Power |
| * PV Inverter Total Power | `vrm_pv_inverters_power_total` | W | Total PV Inverter Power |
| * Solar Charger Total Power | `vrm_solar_chargers_power_total` | W | Total Solar Charger Power |
| * DC Loads | `vrm_dc_loads` | W | Calculated DC Loads (MP, PV, Battery) |
| * Total Solar Yield | `total_solar_yield` | kWh | Total PV Yield (for selected period) |
| * Total Consumption | `total_consumption` | kWh | Total Consumption (for selected period) |
| * Grid Energy In | `grid_history_from` | kWh | Energy from Grid (for selected period) |
| * Grid Energy Out | `grid_history_to` | kWh | Energy to Grid (for selected period) |
| * Solar Forecast Today / Remaining Today / Tomorrow | `solar_yield_forecast` | kWh | VRM Solar Forecast (`stats?type=forecast`) |
| * Consumption Forecast Today / Tomorrow | `vrm_consumption_fc` | kWh | VRM Consumption Forecast |


*The Overall Stats values are created for **Today, Week, Month and Year**.*

</details>

<details>
<summary><b>🌡️ Other Devices</b> (dynamic)</summary>

| Sensor | VRM ID / Key | Unit | Description |
| :--- | :--- | :---: | :--- |
| *(one sensor per VRM value)* | `idDataAttribute` | auto | Any device from the VRM diagnostics (temperature sensors / RuuviTag, GPS, Orion XS, EV charger, …) |

</details>


### ⏱️ Update intervals

| Data | Interval |
| :--- | :---: |
| Battery, MultiPlus, PV inverter, solar charger | 20 s |
| Tank, diagnostics (grid meter, ESS, system values, other devices) | 60 s |
| Overall stats, energy stats | 5 min |
| System overview (device list) | 20 min |
| Solar / consumption forecast | 60 min |

---

## 📸 Screenshots

<p align="center">
  <img src="https://raw.githubusercontent.com/jayjojayson/hass-victron-vrm-api/main/docs/victron-vrm-api.png" alt="Victron VRM API in Home Assistant" width="760">
</p>

<details>
<summary><b>Devices in Home Assistant</b></summary>
<p align="center">
  <img src="https://raw.githubusercontent.com/jayjojayson/hass-victron-vrm-api/main/docs/Config_Menu.png" alt="Configuration" width="240">
  <img src="https://raw.githubusercontent.com/jayjojayson/hass-victron-vrm-api/main/docs/Battery.png" alt="Battery" width="240">
  <img src="https://raw.githubusercontent.com/jayjojayson/hass-victron-vrm-api/main/docs/Multiplus.png" alt="MultiPlus" width="240">
  <img src="https://raw.githubusercontent.com/jayjojayson/hass-victron-vrm-api/main/docs/PV_Inverter.png" alt="PV Inverter" width="240">
  <img src="https://raw.githubusercontent.com/jayjojayson/hass-victron-vrm-api/main/docs/Overall.png" alt="Overall Stats" width="240">
</p>
</details>

---

## ❓ Q&A / Troubleshooting

<details>
<summary><b>Show answers</b></summary>

- **I don't have a device type.** Simply leave the field empty, and no device will be created. Instance ID `0` is valid and can be used.
- **Several devices of the same type?** Enter the instance IDs separated by commas, e.g. `274, 275`.
- **An entity shows "no longer provided" after an update.** Reload the integration once: *Settings → Devices & Services → Victron VRM API → ⋮ → Reload*.
- **The card still looks like the old version after an update.** Do a hard browser refresh (Ctrl+Shift+R / Cmd+Shift+R), or clear the frontend cache in the Companion app.
- **Grid and house show the same value in the card.** Use `System Grid Power` and `System AC Consumption`. The MultiPlus AC input/output only shows the pass-through power, not loads connected before the MultiPlus.
- **MultiPlus temperature:** only available with single-phase MultiPlus setups.
- **PV inverter:** single- and three-phase inverters are supported. Three-phase inverters get additional sensors.
- **Battery-only installations** (e.g. GlobalLink 520 + SmartShunt) are supported. Missing statistics endpoints no longer block the setup.

</details>

---

⭐ **If you like the integration, I'm happy about a star on GitHub!** Ideas and bugs are welcome as an [issue](https://github.com/jayjojayson/hass-victron-vrm-api/issues).
