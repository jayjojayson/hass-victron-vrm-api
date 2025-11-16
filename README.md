[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

# Victron-VRM-API
Victron VRM API Integration for Home Assistant

This integration use the Victron VRM Portal to get Data from the API. At this Time you can read the Data from your Battery and Multiplus. Also you get the Overall Stats for the Day, Week, Month and Year.

If you like the Integration, I would appreciate a star rating ⭐ from you. 🤗

## ✔️ Prerequisites 
- VRM access token (keep this secret!). Create one in the VRM Portal under Preferences > Integrations > Access tokens or use [this link.](https://vrm.victronenergy.com/access-tokens)
- your Side_ID
- Instance Number from Battery and Multiplus


## 📥 Installing the Integration

### ➡️ HACS

- Simply follow the Link to integrate this repository to HACS
  
 [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jayjojayson&repository=hass-victron-vrm-api&category=integration)
- go to `Settings -> Devices and Services -> Integration`
- click on `Add Integration`
- search for `victron vrm api` or short `vrm`
- fill in your Side_ID, Token and Instance_ID for Battery and Multiplus

#
### ➡️ Manual

- dowonload the latetest Release
- copy the folder "victron-vrm-api" inside your custom_components of Home Assistant
- restart home assistant
- go to `Settings -> Devices and Services -> Integration`
- click on `Add Integration`
- search for `victron vrm api` or short `vrm`
- fill in your Side_ID, Token and Instance_ID for Battery and Multiplus

[![Downloads](https://img.shields.io/github/downloads/jayjojayson/hass-victron-vrm-api/total?label=downloads&logo=github)](https://github.com/jayjojayson/hass-victron-vrm-api/releases)
[![Latest release downloads](https://img.shields.io/github/downloads/jayjojayson/hass-victron-vrm-api/latest/total?label=latest%20downloads&logo=github)](https://github.com/jayjojayson/hass-victron-vrm-api/releases/latest)
