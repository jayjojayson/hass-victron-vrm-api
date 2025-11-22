
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/jayjojayson/hass-victron-vrm-api?include_prereleases=&sort=semver&color=blue)](https://github.com/jayjojayson/hass-victron-vrm-api/releases/)
[![GH-code-size](https://img.shields.io/github/languages/code-size/jayjojayson/hass-victron-vrm-api?color=blue)](https://github.com/jayjojayson/hass-victron-vrm-api)
[![HACS validation](https://img.shields.io/github/actions/workflow/status/jayjojayson/hass-victron-vrm-api/validate.yml?label=HACS%20Validation)](https://github.com/jayjojayson/hass-victron-vrm-api/actions?query=workflow%3Avalidate)

# Victron VRM API 
Victron VRM API Integration for Home Assistant

Diese Integration nutzt das Victron VRM-Portal, um Daten von der API abzurufen. Alles was ihr dafür braucht, sind ein paar Zahlen aus eurem VRM Portal. 
Aktuell könnt ihr Daten von Batterie, MultiPlus und PV Inverter auslesen. Außerdem erhaltet ihr die Gesamtstatistiken für Tag, Woche, Monat und Jahr von Solar, Netz, und Total. Ich arbeite daran, weitere Daten von der Victron-API abzurufen.

Wenn euch die Integration gefällt, würde ich mich über eine Sternebewertung ⭐ freuen. 🤗

## ✔️ Voraussetzungen
- VRM-Zugriffstoken (bitte geheim halten!). Erstelle eines im VRM-Portal unter Einstellungen > Integrationen > Zugriffstoken oder verwende [diesen Link](https://vrm.victronenergy.com/access-tokens).
- Deine Side_ID
- Instanz Nummer von Battery, Multiplus und PV Inverter

  <details>
   <summary> <b>"How to" Site_ID, Instanz Nummer, Token</b></summary>  
   <img width="3161" height="1111" alt="vrm-api-Erklärung" src="https://github.com/user-attachments/assets/042554e5-9585-4098-8ff6-d4c11b017495" />
  </details>

## 📥 Installation der Integration

### ➡️ HACS

- Folge einfach dem Link, um dieses Repository in HACS zu integrieren.  
 [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jayjojayson&repository=hass-victron-vrm-api&category=integration)
- Gehe zu `Einstellungen` → `Geräte und Dienste` → `Integration`.
- Klicke auf `Integration hinzufügen`.
- Suche nach `victron vrm api` oder kurz `vrm`.
- Gebe die Side_ID, dein Token und den Instance_ID für Battery, Multiplus und PV Inverter ein.

#
### ➡️ Manual

- Lade die neueste Version herunter.
- Kopiere den Ordner „victron-vrm-api“ in Ihren benutzerdefinierten Komponentenordner von Home Assistant.
- Starte Home Assistant neu.
- Gehe zu `Einstellungen` → `Geräte und Dienste` → `Integration`.
- Klicke auf `Integration hinzufügen`.
- Suche nach `victron vrm api` oder kurz `vrm`.
- Gebe die Side_ID, den Token und deine Instance_ID für Battery, Multiplus und PV Inverterv ein.

## ✅ So sollte es aussehen in HA

<img width="1084" height="513" alt="baaf71fc1a0bd487e77f43b7fb7b184def05f512" src="https://github.com/user-attachments/assets/f0219972-1b75-476b-ad58-1a8cd7bb6816" />
