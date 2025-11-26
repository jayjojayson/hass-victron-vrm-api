[![HACS validation](https://img.shields.io/github/actions/workflow/status/jayjojayson/hass-victron-vrm-api/validate.yml?label=HACS%20Validation)](https://github.com/jayjojayson/hass-victron-vrm-api/actions?query=workflow%3Avalidate)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/jayjojayson/hass-victron-vrm-api?include_prereleases=&sort=semver&color=blue)](https://github.com/jayjojayson/hass-victron-vrm-api/releases/)
[![GH-code-size](https://img.shields.io/github/languages/code-size/jayjojayson/hass-victron-vrm-api?color=blue)](https://github.com/jayjojayson/hass-victron-vrm-api)
[![README Deutsch](https://img.shields.io/badge/README-Deutsch-orange)](https://github.com/jayjojayson/hass-victron-vrm-api/blob/main/docs/README_deutsch.md)

# Victron VRM API 
Victron VRM API Integration for Home Assistant

This integration use the Victron VRM Portal to get Data from the API. All you need for Setup are some Numbers from your VRM Portal.
At this Time you can read the Data from Battery, MultiPlus and PV Inverter. Also you get the Overall Stats for the Day, Week, Month and Year. I'm working on it, to get some more Data from the victron API.

If you like the Integration, I would appreciate a Star rating ⭐ from you. 🤗 

## ✔️ Prerequisites 
- VRM access token (keep this secret!). Create one in the VRM Portal under Preferences > Integrations > Access tokens or use [this link.](https://vrm.victronenergy.com/access-tokens)
- your SiteID (VRM-Installations-ID)
- Instance Number from Battery, Multiplus and PV Inverter

  <details>
   <summary> <b>"How to" - Site_ID, Instance Number, Token</b></summary>  
   <img width="3161" height="1111" alt="vrm-api-Erklärung" src="https://github.com/jayjojayson/hass-victron-vrm-api/blob/main/docs/vrm-api-description.png" />
  </details>

## 📥 Installing the Integration

### ➡️ HACS

- Simply follow the Link to integrate this repository to HACS
  
 [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jayjojayson&repository=hass-victron-vrm-api&category=integration)
- go to `Settings -> Devices and Services -> Integration`
- click on `Add Integration`
- search for `victron vrm api` or short `vrm`
- fill in your Side_ID, Token and Instance_ID for Battery, Multiplus and PV Inverter

#
### ➡️ Manual

- dowonload the latetest Release
- copy the folder "victron-vrm-api" inside your custom_components of Home Assistant
- restart home assistant
- go to `Settings -> Devices and Services -> Integration`
- click on `Add Integration`
- search for `victron vrm api` or short `vrm`
- fill in your Side_ID, Token and Instance_ID for Battery, Multiplus and PV Inverter

## ✅ How it looks in HA

<img width="1084" height="513" alt="baaf71fc1a0bd487e77f43b7fb7b184def05f512" src="https://github.com/jayjojayson/hass-victron-vrm-api/blob/main/docs/victron-vrm-api.png" />

  <details>
   <summary> <b>Pictures of Devices inside the Ingration</b></summary>  
   <img width="320" height="500" alt="vrm-api-Erklärung" src="https://github.com/jayjojayson/hass-victron-vrm-api/blob/main/docs/Config_Menu.png" />
   <img width="320" height="500" alt="vrm-api-Erklärung" src="https://github.com/jayjojayson/hass-victron-vrm-api/blob/main/docs/Battery.png" />
   <img width="320" height="500" alt="vrm-api-Erklärung" src="https://github.com/jayjojayson/hass-victron-vrm-api/blob/main/docs/Multiplus.png" />
   <img width="320" height="500" alt="vrm-api-Erklärung" src="https://github.com/jayjojayson/hass-victron-vrm-api/blob/main/docs/PV_Inverter.png" />
   <img width="320" height="500" alt="vrm-api-Erklärung" src="https://github.com/jayjojayson/hass-victron-vrm-api/blob/main/docs/Overall.png" />
  </details>

  <details>
   <summary> <b>Q&A</b></summary> 
    
  - Configuration Menu, if the instance number for Battery, Multiplus or PV Inverter is set to 0, then no device will be added!
    (Example, if you have no Battery, then you don`t need the empty Device in HA.)  
  - You get the Temperature value with a 1PH Multiplus Setup. With 3Ph Multiplus Setup you dont get this Sensor.
  - You get Data from your 1Ph or 3Ph PV-Inverter. With 3Ph you get some more Sensors.
  </details>
