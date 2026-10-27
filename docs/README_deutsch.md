[![HACS validation](https://img.shields.io/github/actions/workflow/status/jayjojayson/hass-victron-vrm-api/validate.yml?label=HACS%20Validation)](https://github.com/jayjojayson/hass-victron-vrm-api/actions?query=workflow%3Avalidate)
[![hacs_badge](https://img.shields.io/badge/HACS-Default%20✔-brightgreen.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/jayjojayson/hass-victron-vrm-api?include_prereleases=&sort=semver&color=blue)](https://github.com/jayjojayson/hass-victron-vrm-api/releases/)
[![GH-code-size](https://img.shields.io/github/languages/code-size/jayjojayson/hass-victron-vrm-api?color=blue)](https://github.com/jayjojayson/hass-victron-vrm-api)
[![README English](https://img.shields.io/badge/README-English-orange)](https://github.com/jayjojayson/hass-victron-vrm-api/blob/main/README.md)
[![Support](https://img.shields.io/badge/%20-Support%20Me-steelblue?style=flat&logo=paypal&logoColor=white)](https://www.paypal.me/quadFlyerFW)
![stars](https://img.shields.io/github/stars/jayjojayson/hass-victron-vrm-api)

# ⚡ Victron VRM API für Home Assistant

**Eure Victron-Anlage in Home Assistant, über das Victron VRM-Portal und ohne lokalen Zugriff auf das GX-Gerät.**

Die Integration holt die Daten über die VRM-Cloud-API. Für die Einrichtung braucht ihr nur euren VRM-Zugriffstoken, die Site-ID und die Instanz-IDs eurer Geräte. Ideal für **Wohnmobile, Wohnwagen und Boote** ohne lokale Verbindung zur Victron-Anlage, funktioniert aber genauso gut zu Hause.

Dazu gibt es eine **Dashboard-Karte im Stil der Venus OS GUI v2**, mit animierten Energieflüssen, Verlaufsgrafiken und grafischem Editor.

<p align="center">
  <img src="https://raw.githubusercontent.com/jayjojayson/hass-victron-vrm-api/main/docs/victron-vrm-api-card.png" alt="Victron VRM API Card" width="760">
</p>

Wenn euch die Integration gefällt, freue ich mich über einen Stern ⭐. 🤗

---

## ✨ Funktionen

- 🔋 **Batterie, MultiPlus, PV-Wechselrichter, Solarladeregler (MPPT), Tank und Netzzähler**: Live-Werte, Alarme und Tagesenergie
- 🧭 **System-Werte** wie von Venus OS berechnet: Netzleistung gesamt, Hausverbrauch (AC-Verbraucher vor und hinter dem MultiPlus), PV- und Batterieleistung gesamt
- 🌡️ **Weitere Geräte über eigene Instanz-IDs**: Temperatursensoren / RuuviTag, GPS, Orion XS, EV-Charger und mehr. Für jeden Wert, den VRM liefert, wird ein Sensor angelegt
- 📊 **Gesamtstatistiken** für Tag, Woche, Monat und Jahr sowie die **VRM-Solar- und Verbrauchsprognose**
- 🖥️ **Dashboard-Karte** mit Energiefluss-Animation, Verlaufsgrafiken, Füllstandsanzeige und vollständigem grafischem Editor (wird automatisch registriert)
- 🌍 Auf Deutsch und Englisch übersetzt, Karten-Editor zusätzlich auf Französisch
- ✅ Kompatibel mit **Home Assistant 2026.10** (Entitäts-IDs und Verlauf bleiben beim Update erhalten)

---

## ✔️ Voraussetzungen

| Was | Wo zu finden |
| :--- | :--- |
| **VRM-Zugriffstoken** (geheim halten!) | VRM-Portal → *Einstellungen → Integrationen → Zugriffstoken*, oder [dieser Link](https://vrm.victronenergy.com/access-tokens) |
| **Site-ID** (VRM-Installations-ID) | Die Zahl in der Adresszeile, wenn ihr eure Installation im VRM-Portal öffnet: `vrm.victronenergy.com/installation/<Site-ID>/…` |
| **Instanz-IDs** eurer Geräte | VRM-Portal → eure Installation → *Geräteliste* (Spalte *Instance*) |

<details>
<summary><b>📷 So findet ihr Site-ID, Instanz-IDs und Token</b></summary>
<br>
<img src="https://raw.githubusercontent.com/jayjojayson/hass-victron-vrm-api/main/docs/vrm-api-description.png" alt="Site-ID, Instanz-IDs und Token finden" width="100%">
</details>

---

## 📥 Installation

### ➡️ HACS (empfohlen)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jayjojayson&repository=hass-victron-vrm-api&category=integration)

1. Link oben öffnen oder in HACS nach **Victron VRM API** suchen und die Integration installieren
2. Home Assistant neu starten
3. *Einstellungen → Geräte & Dienste → Integration hinzufügen* → nach **Victron VRM API** (oder kurz `vrm`) suchen

### ➡️ Manuell

1. Den [neuesten Release](https://github.com/jayjojayson/hass-victron-vrm-api/releases/latest) herunterladen
2. Den Ordner `custom_components/victron_vrm_api` in den Ordner `custom_components` eures Home Assistant kopieren
3. Home Assistant neu starten und die Integration wie oben beschrieben hinzufügen

---

## ⚙️ Konfiguration

Alle Felder außer Site-ID und Token sind optional. **Lasst ein Feld leer**, wenn ihr das Gerät nicht habt. Mehrere Geräte desselben Typs tragt ihr **durch Kommas getrennt** ein, z.B. `274, 275`. Die Konfiguration lässt sich jederzeit über *⋮ → Neu konfigurieren* ändern.

| Feld | Beispiel | Beschreibung |
| :--- | :--- | :--- |
| **Site-ID** | `123456` | Eure VRM-Installations-ID |
| **API-Token** | `abc…` | VRM-Zugriffstoken |
| **Batterie** | `274` | Batteriemonitor / BMS (z.B. SmartShunt, BMV, Lynx) |
| **MultiPlus** | `275` | MultiPlus / Quattro / Wechselrichter-Ladegerät |
| **PV Inverter** | `20` | AC-gekoppelter PV-Wechselrichter (1- oder 3-phasig) |
| **Tank** | `21, 22` | Tanksensoren (z.B. Mopeka, GX Tank) |
| **Solar Charger** | `278` | MPPT-Solarladeregler |
| **Grid Meter** | `30` | Energiezähler am Netzanschluss |
| **Weitere Geräte** | `24, 25` | Jedes andere Gerät aus der VRM-Geräteliste, siehe unten |

### 🌡️ Weitere Geräte (eigene Instanz-IDs)

Geräte ohne eigenes VRM-Widget fügt ihr über das Feld **„Weitere Geräte – instance_id“** hinzu: Temperatursensoren und RuuviTags, GPS, Orion XS, EV-Ladestationen und mehr. Tragt dort die Instanz-ID aus der VRM-Geräteliste ein.

Die Integration legt **pro Instanz und Gerätetyp ein Gerät** an, mit **einem Sensor für jeden Wert**, den VRM dafür liefert. Name und Einheit kommen direkt von VRM. Teilen sich zwei verschiedene Gerätetypen dieselbe Instanz-ID, z.B. ein Tanksensor und ein Temperatursensor, bekommt jeder ein eigenes Gerät.

---

## 🖥️ Dashboard-Karte

Zur Integration gehört die **Victron VRM API Card**. Sie wird automatisch als Dashboard-Ressource registriert, ihr müsst also nichts zusätzlich installieren. Einfach über *Dashboard bearbeiten → Karte hinzufügen → Victron VRM API Card* einfügen. Als Startpunkt wählt die Karte automatisch passende VRM-Sensoren für Netz, Haus, Solar und Batterie.

<p align="center">
  <img src="https://raw.githubusercontent.com/jayjojayson/hass-victron-vrm-api/main/docs/victron-vrm-api-card-editor.png" alt="Editor der Victron VRM API Card" width="760">
</p>

**Das kann die Karte**

- **Bis zu 10 Boxen in 3 Spalten** (4 / 2 / 4), jeweils mit Icon, Name, Hauptwert, optionalem zweitem Wert, Header-Wert und **bis zu 3 Footer-Werten**
- **Animierte Energieflüsse** zwischen den Boxen. Die Richtung folgt dem Vorzeichen eines Sensors (z.B. Lade- oder Entladestrom) und lässt sich pro Verbindung umkehren
- **Verlaufsgrafik** der letzten 24 Stunden pro Box, mit **frei wählbarer Farbe**
- **Füllstandsanzeige**: Prozentwerte wie der Ladezustand füllen die Box von unten
- **Themes**: hell, dunkel, auto (folgt Home Assistant) oder transparent
- **Farben** für Rahmen, Ankerpunkte, Linien, Graph, Animationspunkt und Schrift, dazu eine einstellbare Größe des Animationspunkts
- **Schriftgrößen** für Header, Werte und Footer: *Auto* oder ein fester Wert in px
- **Footer-Layout pro Box**: nebeneinander oder untereinander, links, mittig oder rechts ausgerichtet
- Werte werden wie in Home Assistant formatiert (Nachkommastellen, Sprache). Ein Klick auf eine Box öffnet die Entitätsdetails

**Grafischer Editor**

Alles lässt sich im grafischen Editor einstellen, YAML ist nicht nötig:

- **Allgemein**: Theme, Anzahl der Boxen pro Spalte, Schriftgrößen, Farben und Größe des Animationspunkts
- **Spalte 1–3**: pro Box Icon, Name, Sensoren, Graph, Füllstand, Footer-Layout, Ankerpunkte und Verbindungen

<details>
<summary><b>📝 YAML-Beispiel</b></summary>

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
    name: Netz
    icon: mdi:transmission-tower
    entity: sensor.vrm_system_grid_power
    graph: true
    anchors: R-1
    link:
      "1":
        start: R-1
        end: 2-1_L-1
  "1-2":
    name: Batterie
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
    name: Haus
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

| Option | Werte | Beschreibung |
| :--- | :--- | :--- |
| `theme` | `light`, `dark`, `auto`, `transparent` | Theme der Karte |
| `param.boxCol1` / `boxCol2` / `boxCol3` | 1–4 / 1–2 / 1–4 | Anzahl der Boxen pro Spalte |
| `param.ballSize` | 2–15 | Größe des Animationspunkts |
| `styles.header` / `sensor` / `footer` | Zahl (px) oder `auto` | Schriftgrößen |
| `colors.*` | `boxShadow`, `anchor`, `graph`, `history`, `ball`, `textMain`, `textSub` | Farben (Hex) |
| `devices."s-b".anchors` | z.B. `L-1, B-2, R-1` | Ankerpunkte pro Seite: **L**inks, **T**op (oben), **B**ottom (unten), **R**echts |
| `devices."s-b".link.N` | `start`, `end`, `entity`, `inv` | Linie von einem Anker dieser Box zu einem Anker einer anderen Box. `entity` bestimmt die Flussrichtung, `inv` kehrt sie um |
| `devices."s-b".footerLayout` | `horizontal` (Standard), `vertical` | Footer nebeneinander oder untereinander |
| `devices."s-b".footerAlign` | `left`, `center` (Standard), `right` | Ausrichtung des Footers |

</details>

> 💡 **YAML-Dashboards:** Wenn eure Dashboards im YAML-Modus laufen, die Ressource manuell eintragen: `url: /victron_vrm_api/victron-vrm-api.js`, `type: module`.

---

## 📋 Unterstützte Geräte und Sensoren

<details>
<summary><b>🔋 Batterie</b> (34 Sensoren)</summary>

| Sensor | VRM-ID / Key | Einheit | Beschreibung |
| :--- | :--- | :---: | :--- |
| State of charge | `51` | % | Ladezustand (SOC) |
| Voltage | `47` | V | Batteriespannung |
| Current | `49` | A | Batteriestrom |
| Consumed Amphours | `50` | Ah | Verbrauchte Amperestunden |
| Time to go | `52` | h | Restlaufzeit bis leer |
| Battery Temperature | `115` | °C | Batterietemperatur |
| Minimum Cell Voltage | `173` | V | Minimale Zellspannung (BMS) |
| Maximum Cell Voltage | `174` | V | Maximale Zellspannung (BMS) |
| Cell Voltage Difference | *(berechnet)* | V | Differenz der Zellspannungen |
| Battery Power | *(berechnet)* | W | Aktuelle Leistung (V*A) |
| Battery Charge Cycles | `58` | - | Vollladezyklen |
| Battery to Consumers (Today) | `Bc` | kWh | Energie an Verbraucher (heute) |
| Battery to Grid (Today) | `Bg` | kWh | Energie ins Netz (heute) |
| Low voltage alarm | `119` | - | Alarm Unterspannung |
| High voltage alarm | `120` | - | Alarm Überspannung |
| Low starter-voltage alarm | `121` | - | Alarm Starterbatterie Unterspannung |
| High starter-voltage alarm | `122` | - | Alarm Starterbatterie Überspannung |
| Low state-of-charge alarm | `123` | - | Niedriger Ladezustand |
| Low battery temperature alarm | `124` | - | Batterietemperatur zu niedrig |
| High battery temperature alarm | `125` | - | Batterietemperatur zu hoch |
| Mid-voltage alarm | `126` | - | Mittelpunktspannung auffällig |
| Low fused-voltage alarm | `155` | - | Gesicherte Spannung zu niedrig |
| High fused-voltage alarm | `156` | - | Gesicherte Spannung zu hoch |
| Fuse blown alarm | `157` | - | Sicherung ausgelöst |
| High internal-temperature alarm | `158` | - | Alarm interne Temperatur |
| Cell imbalance alarm | `286` | - | Zellungleichgewicht erkannt |
| High charge current alarm | `287` | - | Ladestrom zu hoch |
| High discharge current alarm | `288` | - | Entladestrom zu hoch |
| Internal failure | `289` | - | Interner Fehler erkannt |
| High charge temperature alarm | `459` | - | Ladetemperatur zu hoch |
| Low charge temperature alarm | `460` | - | Ladetemperatur zu niedrig |
| Low cell voltage | `522` | - | Zellspannung zu niedrig |
| Charge blocked | `739` | - | Laden gesperrt (BMS) |
| Discharge blocked | `740` | - | Entladen gesperrt (BMS) |

</details>

<details>
<summary><b>⚡ MultiPlus</b> (12 Sensoren)</summary>

| Sensor | VRM-ID / Key | Einheit | Beschreibung |
| :--- | :--- | :---: | :--- |
| AC Input Voltage L1 | `8` | V | AC-Eingangsspannung Phase 1 |
| AC Input Power L1 | `17` | W | AC-Eingangsleistung Phase 1 |
| AC Output Voltage L1 | `20` | V | AC-Ausgangsspannung Phase 1 |
| AC Output Power L1 | `29` | W | AC-Ausgangsleistung Phase 1 |
| DC Bus Voltage | `32` | V | DC-Bus-Spannung |
| DC Bus Current | `33` | A | DC-Bus-Strom |
| VE.Bus State | `40` | - | Betriebszustand (z.B. Inverting) |
| MultiPlus Temperature | `521` | °C | Gerätetemperatur |
| DC Bus Power | *(berechnet)* | W | Aktuelle DC-Leistung (V*A) |
| System State of Charge | `144` | % | Vom System berechneter Ladezustand (ersetzt den internen MultiPlus-SOC) |
| Grid to Consumers (Today) | `Gc` | kWh | Energie vom Netz an Verbraucher (heute) |
| Grid to Battery (Today) | `Gb` | kWh | Energie vom Netz in die Batterie (heute) |

</details>

<details>
<summary><b>🏭 Netzzähler (Grid Meter)</b> (10 Sensoren)</summary>

| Sensor | VRM-ID / Key | Einheit | Beschreibung |
| :--- | :--- | :---: | :--- |
| Grid L1 Voltage | `834` | V | Spannung Netzzähler Phase L1 |
| Grid L1 Current | `835` | A | Strom Netzzähler Phase L1 |
| Grid L1 Power | `379` | W | Leistung Netzzähler Phase L1 |
| Grid L2 Voltage | `837` | V | Spannung Netzzähler Phase L2 |
| Grid L2 Current | `838` | A | Strom Netzzähler Phase L2 |
| Grid L2 Power | `380` | W | Leistung Netzzähler Phase L2 |
| Grid L3 Voltage | `840` | V | Spannung Netzzähler Phase L3 |
| Grid L3 Current | `841` | A | Strom Netzzähler Phase L3 |
| Grid L3 Power | `381` | W | Leistung Netzzähler Phase L3 |
| Grid Total Power | *(berechnet)* | W | Summe der Leistung aller drei Phasen (L1+L2+L3) |

</details>

<details>
<summary><b>☀️ PV-Wechselrichter</b> (17 Sensoren)</summary>

| Sensor | VRM-ID / Key | Einheit | Beschreibung |
| :--- | :--- | :---: | :--- |
| L1 Voltage | `203` | V | Spannung Phase 1 |
| L1 Current | `204` | A | Strom Phase 1 |
| L1 Power | `205` | W | Leistung Phase 1 |
| L1 Energy | `206` | kWh | Energieertrag Phase 1 (gesamt) |
| L2 Voltage | `207` | V | Spannung Phase 2 |
| L2 Current | `208` | A | Strom Phase 2 |
| L2 Power | `209` | W | Leistung Phase 2 |
| L2 Energy | `210` | kWh | Energieertrag Phase 2 (gesamt) |
| L3 Voltage | `211` | V | Spannung Phase 3 |
| L3 Current | `212` | A | Strom Phase 3 |
| L3 Power | `213` | W | Leistung Phase 3 |
| L3 Energy | `214` | kWh | Energieertrag Phase 3 (gesamt) |
| Status | `246` | - | Statuscode |
| PV to Consumers (Today) | `Pc` | kWh | Energie von PV an Verbraucher (heute) |
| PV to Battery (Today) | `Pb` | kWh | Energie von PV in die Batterie (heute) |
| PV to Grid (Today) | `Pg` | kWh | Energie von PV ins Netz (heute) |
| PV Total Today | *(berechnet)* | kWh | PV-Ertrag heute gesamt (Pc+Pb+Pg) |

</details>

<details>
<summary><b>🌞 Solarladeregler (MPPT)</b> (7 Sensoren)</summary>

| Sensor | VRM-ID / Key | Einheit | Beschreibung |
| :--- | :--- | :---: | :--- |
| Battery Watts | `107` | W | Ladeleistung in die Batterie |
| Battery Voltage | `81` | V | Batteriespannung |
| Charge State | `85` | - | Ladezustand des Laders (z.B. Bulk, Float) |
| Battery Temperature | `83` | °C | Batterietemperatur (extern) |
| Yield Today | `94` | kWh | Energieertrag heute |
| Yield Yesterday | `96` | kWh | Energieertrag gestern |
| Relay Status | `90` | - | Relaisstatus |

</details>

<details>
<summary><b>🛢️ Tank</b> (6 Sensoren)</summary>

| Sensor | VRM-ID / Key | Einheit | Beschreibung |
| :--- | :--- | :---: | :--- |
| Capacity | `328` | m³ | Tankkapazität |
| Type | `329` | - | Flüssigkeitstyp |
| Level | `330` | % | Füllstand in Prozent |
| Remaining | `331` | m³ | Restmenge |
| Status | `443` | - | Tankstatus (z.B. OK) |
| Custom Name | `638` | - | Benutzerdefinierter Name |

</details>

<details>
<summary><b>🧭 System Overview</b> (dynamisch)</summary>

| Sensor | VRM-ID / Key | Einheit | Beschreibung |
| :--- | :--- | :---: | :--- |
| Infos zu jedem Gerät | - | - | Detail-Infos zu jedem Gerät |
| ESS Battery Life State | `332` | - | Aktueller Status des BatteryLife-Algorithmus (z.B. "Self-consumption", "BL Disabled") |
| ESS Battery Life SOC Limit | `333` | % | Aktuell von BatteryLife gesetzte dynamische SOC-Grenze |
| ESS Minimum SOC | `334` | % | Eingestellter Mindest-SOC (bei vorhandenem Netz) |
| ESS Scheduled Charging | `469` | - | Status des geplanten Ladens (z.B. "Active", "Not active") |
| System Grid Power | `/Ac/Grid/L1-3/Power` | W | Netzleistung gesamt (alle Phasen, wie von Venus OS berechnet) |
| System AC Consumption | `/Ac/Consumption/L1-3/Power` | W | AC-Verbrauch gesamt (Verbraucher vor und hinter dem MultiPlus) |
| System PV Power | `/Dc/Pv/Power` + `/Ac/PvOn…/Power` | W | PV-Leistung gesamt (MPPT + PV-Wechselrichter) |
| System Battery Power | `/Dc/Battery/Power` | W | Batterieleistung laut System |


*Pro Gerät der Anlage zusätzlich: Firmware, Last Connection, Product Name, Remote IP, Connection Info, Auto Update, Battery Family, Battery Manufacturer, Serial Number, Instance ID (sofern VRM sie liefert). Die System-Sensoren werden nur angelegt, wenn eure Anlage die Werte liefert.*

</details>

<details>
<summary><b>📊 Overall Stats</b> (25 Sensoren)</summary>

| Sensor | VRM-ID / Key | Einheit | Beschreibung |
| :--- | :--- | :---: | :--- |
| * Batteries Total Power | `vrm_batteries_power_total` | W | Leistung aller Batterien |
| * PV Inverter Total Power | `vrm_pv_inverters_power_total` | W | Leistung aller PV-Wechselrichter |
| * Solar Charger Total Power | `vrm_solar_chargers_power_total` | W | Leistung aller Solarladeregler |
| * DC Loads | `vrm_dc_loads` | W | Berechnete DC-Verbraucher (MP, PV, Batterie) |
| * Total Solar Yield | `total_solar_yield` | kWh | PV-Ertrag (für den Zeitraum) |
| * Total Consumption | `total_consumption` | kWh | Verbrauch (für den Zeitraum) |
| * Grid Energy In | `grid_history_from` | kWh | Energie vom Netz (für den Zeitraum) |
| * Grid Energy Out | `grid_history_to` | kWh | Energie ins Netz (für den Zeitraum) |
| * Solar Forecast Today / Remaining Today / Tomorrow | `solar_yield_forecast` | kWh | VRM-Solarprognose (`stats?type=forecast`) |
| * Consumption Forecast Today / Tomorrow | `vrm_consumption_fc` | kWh | VRM-Verbrauchsprognose |


*Die Overall-Stats-Werte gibt es jeweils für **Heute, Woche, Monat und Jahr**.*

</details>

<details>
<summary><b>🌡️ Weitere Geräte</b> (dynamisch)</summary>

| Sensor | VRM-ID / Key | Einheit | Beschreibung |
| :--- | :--- | :---: | :--- |
| *(ein Sensor pro VRM-Wert)* | `idDataAttribute` | auto | Jedes Gerät aus der VRM-Diagnose (Temperatursensoren / RuuviTag, GPS, Orion XS, EV-Charger, …) |

</details>


### ⏱️ Aktualisierungsintervalle

| Daten | Intervall |
| :--- | :---: |
| Batterie, MultiPlus, PV-Wechselrichter, Solarladeregler | 20 s |
| Tank, Diagnose (Netzzähler, ESS, System-Werte, weitere Geräte) | 60 s |
| Gesamtstatistiken, Energiestatistiken | 5 min |
| System Overview (Geräteliste) | 20 min |
| Solar- / Verbrauchsprognose | 60 min |

---

## 📸 Screenshots

<p align="center">
  <img src="https://raw.githubusercontent.com/jayjojayson/hass-victron-vrm-api/main/docs/victron-vrm-api.png" alt="Victron VRM API in Home Assistant" width="760">
</p>

<details>
<summary><b>Geräte in Home Assistant</b></summary>
<p align="center">
  <img src="https://raw.githubusercontent.com/jayjojayson/hass-victron-vrm-api/main/docs/Config_Menu.png" alt="Konfiguration" width="240">
  <img src="https://raw.githubusercontent.com/jayjojayson/hass-victron-vrm-api/main/docs/Battery.png" alt="Batterie" width="240">
  <img src="https://raw.githubusercontent.com/jayjojayson/hass-victron-vrm-api/main/docs/Multiplus.png" alt="MultiPlus" width="240">
  <img src="https://raw.githubusercontent.com/jayjojayson/hass-victron-vrm-api/main/docs/PV_Inverter.png" alt="PV-Wechselrichter" width="240">
  <img src="https://raw.githubusercontent.com/jayjojayson/hass-victron-vrm-api/main/docs/Overall.png" alt="Gesamtstatistiken" width="240">
</p>
</details>

---

## ❓ Fragen & Antworten / Fehlerbehebung

<details>
<summary><b>Antworten anzeigen</b></summary>

- **Ich habe einen Gerätetyp nicht.** Lasst das Feld einfach leer, dann wird kein Gerät angelegt. Die Instanz-ID `0` ist gültig und kann verwendet werden.
- **Mehrere Geräte desselben Typs?** Instanz-IDs durch Kommas getrennt eintragen, z.B. `274, 275`.
- **Eine Entität zeigt nach einem Update „wird nicht mehr bereitgestellt“.** Integration einmal neu laden: *Einstellungen → Geräte & Dienste → Victron VRM API → ⋮ → Neu laden*.
- **Die Karte sieht nach einem Update noch alt aus.** Harter Reload im Browser (Strg+Shift+R / Cmd+Shift+R), in der Companion App den Frontend-Cache leeren.
- **Netz und Haus zeigen in der Karte denselben Wert.** Nutzt `System Grid Power` und `System AC Consumption`. Der AC-Ein-/Ausgang des MultiPlus zeigt nur die durchgeschleifte Leistung, nicht die Verbraucher vor dem MultiPlus.
- **MultiPlus-Temperatur:** nur bei einphasigem MultiPlus-Setup verfügbar.
- **PV-Wechselrichter:** ein- und dreiphasige Wechselrichter werden unterstützt. Dreiphasige bekommen zusätzliche Sensoren.
- **Reine Batterie-Anlagen** (z.B. GlobalLink 520 + SmartShunt) werden unterstützt. Fehlende Statistik-Endpunkte blockieren das Setup nicht mehr.

</details>

---

⭐ **Wenn euch die Integration gefällt, freue ich mich über einen Stern auf GitHub!** Ideen und Fehler gerne als [Issue](https://github.com/jayjojayson/hass-victron-vrm-api/issues).
