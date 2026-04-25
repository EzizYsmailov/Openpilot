<div align="center">
  <img src="assets/logo (2).jpg" alt="ADU OpenPilot Logo" width="300"/>

  # 🛡️ RedPilot 
  **Revolutionary Cyber-Platform for Automotive Reverse Engineering & CAN Exploitation**

  <p align="center">
    <a href="README.md">Türkmençe</a> •
    <a href="README_en.md">English</a>
  </p>

  [![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
  [![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg?style=for-the-badge&logo=windows)](https://github.com/EzizYsmailov/Openpilot)
  [![Security](https://img.shields.io/badge/Security-Red%20Team%20%7C%20Pentesting-red.svg?style=for-the-badge&logo=hackthebox)](https://github.com/EzizYsmailov/Openpilot)
  [![License](https://img.shields.io/badge/License-Research%20Only-yellow.svg?style=for-the-badge)](https://github.com/EzizYsmailov/Openpilot)
</div>

---

## 🌍 Overview

**RedPilot** is not merely a collection of code comprised of programming languages and algorithms; it is a revolutionary, immensely powerful cyber-platform that completely subjugates a physical object—a multi-ton vehicle—to the sheer will of an engineer using nothing but their fingertips and a keyboard, achieving a level of control that can be considered "total domination."

The core mission of RedPilot is to empower offensive and defensive (Red Team, Blue Team) engineers to perform penetration testing, discover vulnerabilities and flaws before malicious actors do, and guarantee the fortification of defense systems and software enhancements.

**Continuous and Universal Hardware Agnostic Architecture**
This project operates not only with high-end, industry-standard specialized cybersecurity tools like the `IXXAT USB-to-CAN` interface, but it also seamlessly integrates with extremely small and affordable `ESP32 & MCP2515` microcontroller bridges designed for long-term scientific surveillance (implants) within vehicles. Consequently, this system remains universally accessible across any scenario—from the most extensive laboratory operations to covert operational research on testing grounds.

---

## ⚡ Core Features & Attack Vectors

* 🎯 **Active Payload Injection:** Bypass the vehicle's primary Electronic Control Units (ECUs) to directly inject and command steering angles, unique torque speeds, and throttle/brake states into the network.
* 📡 **CAN Traffic Sniffing & Monitoring:** Intercept and decipher proprietary manufacturer packets in real-time "on the fly" using a robust internal `.dbc` engine.
* 🛡️ **Safety Layer Analysis (Bypass):** An internal module built to study, emulate, and discover bypass techniques for modern ADAS (Advanced Driver Assistance Systems) limitations.
* 🎮 **Real-Time Vehicle Domination:** Monitor 4-wheel metrics online and maintain direct control over physical limitations straight from the C2 (Command & Control) interface.

---

## 🏗️ Hacker Toolkit Architecture

```text
RedPilot/
 ├── main.py              ➔ Core Engine / C2 Launcher
 ├── gui.py               ➔ C2 (Command & Control) Dashboard
 ├── can_interface.py     ➔ Hardware Bridge Connector (IXXAT / Serial)
 ├── can_parser.py        ➔ Universal CAN Traffic Sniffer & Decoder
 ├── toyota_parser.py     ➔ Code Decryptor for Toyota Vehicles
 ├── toyota_commands.py   ➔ Exploitation Payloads (Steering, Throttle)
 ├── safety_layer.py      ➔ Parameter Constraints & Emulator Limits
 ├── firmware/            ➔ Internal Micro-Controller Covert Firmware (ESP32 Implant)
 └── dbc_files/           ➔ 30+ Decrypted Auto-Protocol Databases
```

---

## 🚀 Installation and Execution

### Installation
```bash
pip install python-can cantools
```

### Execution

#### 1. With IXXAT (Real Vehicle)
```bash
python main.py
# Then in GUI select "ixxat (IXXAT)" → Connect
```

#### 2. Demo Mode (No hardware, for testing)
```bash
python main.py --demo
# Or select "demo (Fake)" in the GUI
```

## 🔌 Connection Procedure
1. Plug IXXAT USB-to-CAN → into the computer
2. OBD-II cable → plug into the vehicle's OBD port
3. Turn on the vehicle (to activate ACC)
4. `python main.py` → Click the Connect button

## 📊 Dashboard Metrics
- Speed (via speedometer)
- Steering Angle (-500° ~ +500°)
- Throttle Pedal %
- Brake Status
- Individual 4-Wheel Speeds
- Cruise Control Status

## 🕹️ Steering Control
- ◀◀ Left / Right ▶▶ → sharp turn
- ◀ Slow Left / Right ▶ → slow turn
- Slider → select custom torque value (-1500 ~ +1500)

## 🏎️ Throttle Control
- ▲ Accelerate → +1.5 m/s²
- ▼ Decelerate → -2.0 m/s²
- Slider → custom range from -3.5 to +2.0 m/s²

## ⚠️ Additional Warnings
> ⚠️ **Testing on a real vehicle must only be performed while stationary or in an empty testing ground!**  
> ⚠️ **If an LKAS button is present (TSS), control is only accepted through it.**

---

## ⚠️ Legal and Safety Warning (Must Read!)

> [!CAUTION]
> **FOR SCIENTIFIC RESEARCH AND AUTHORIZED PENETRATION TESTING ONLY.**
> This software is provided exclusively for cybersecurity professionals, red-team members, and researchers operating on **authorized vehicles** and legal technical platforms.
> 
> **WARNING:** Directly interfacing with a moving vehicle's CAN network and injecting packets is **extremely dangerous**, and can pose a severe threat to your life, the vehicle, and bystanders, as well as potentially brick the hardware. **NEVER USE** this tool on public roads, streets, or on real vehicles that you do not own or have explicit authorization to test.
> 
> The creator of this project, contributors, and the repository owner bear **absolutely no legal responsibility** for any crime, damage, loss of life, accidents during testing, unethical usage, or property damage. Use this tool entirely at your own discretion, at your own risk, and strictly within closed, controlled environments.

---
<div align="center">
  <b>© 2026 RedPilot Development. All Rights Reserved.</b>
</div>
