<div align="center">
  <img src="assets/logo (2).jpg" alt="ADU OpenPilot Logo" width="500"/>

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

## 🌍 Platforma Barada (Overview)

**RedPilot** – diňe bir programmirleme dillerinden we algoritmlerden ybarat bolan kod toplumy däl-de, ol fiziki obýekte eýe bolan, birnäçe tonnalyk agyrlykdaky awtoulagy diňe bir inženeriň barmaklarynyň ujy we klawiaturasy arkaly doly öz erkine boýun egdirýän we “doly ele alyp biljek derejede” güýçli, rewolusion bir kiber-platformadyr. 

RedPilot düýp maksady hüjüm we goranyş (Red Team, Blue Team) inžinerlerine jenaýatçylardan öň pentest edip şol kemçilikleri we gowşaklyklary tapmagy, we berk gorag ulgamy, programmalary kämilleşdirmekligi kepillendirýär.

**Üznüksiz we Ähliumumy Apparat Utgaşyklygy (Hardware Agnostic Architecture)**
Bu proýekt diňe bir ýokary senagat-standartly, ýöriteleşen kiberhowpsuzlyk gurallary bolan `IXXAT USB-to-CAN` ýaly abzal bilen işlemän, eýsem awtoulaglaryň içinde uzak möhletli ylmy gözegçilik (implant) arkaly ulanmak üçin niýetlenen çakdanaşa kiçi we arzan `ESP32 & MCP2515` mikrokontroller köprüleri bilen hem işleşip bilýär. Şeýlelikde, bu ulgam iň uly laboratoriýa amallaryndan başlap, türgenleşik meýdanlarynda gizlin operasion barlaglara çenli islendik halda elýeterlidir.

---

## ⚡ Esasy Aýratynlyklar we Hujüm Wektorlary

* 🎯 **Işjeň Tarp (Payload) Inýeksiýasy:** Awtoulagyň esasy dolandyryş bloklaryny (ECU) böküp geçmek arkaly ulgama göni rulyň burçuny, özboluşly torque tizligini we gaz/tormoz welaýatlaryny siňdirmek.
* 📡 **CAN Trafik Diňlemek & Gözegçilik:** Ulag öndürijiniň hakyky wagtda ugradýan hususy paketlerini berk içki `.dbc` motory arkaly "on the fly" (dessine) açyp okamak.
* 🛡️ **Gorag Gatlagy Analizi (Safety Layer Bypass):** Häzirki zaman ADAS (Ulagy sürüjisiz dolandyrma ulgamlary) çäklendirmelerini öwrenmek, emulýasiýa etmek we olary aýlanyp geçmegiň (bypass) ýollaryny açmak üçin gurulan içki modul.
* 🎮 **Real-wagtda Ulagy Tabyn Etmek (Domination):** 4 tigiriň ölçeglerini onlaýn görmek we fiziki çäklendirmeleri C2 (Command & Control) edaralyk interfeýsden göni el astynda saklamak.

---

## 🏗️ Hakerlik Toplumynyň Gurluşy (Architecture)

```text
RedPilot/
 ├── main.py              ➔ Guralyň esasy ýadrosy / C2 başlangyjy
 ├── gui.py               ➔ C2 (Command & Control) Dolandyryş Paneli
 ├── can_interface.py     ➔ Apparat köprülerini birikdiriji (IXXAT / Serial)
 ├── can_parser.py        ➔ Umumy CAN trafik diňleýji (Sniffer & Decoder)
 ├── toyota_parser.py     ➔ Toyota awtoulaglarynyň kodlarynyň deşifratory
 ├── toyota_commands.py   ➔ Exploitation Payload'lary (Rul gysymlary, Gaz)
 ├── safety_layer.py      ➔ Parametr çäklendirmeleri we emulýator limitleri
 ├── firmware/            ➔ Içerki mikro-kontroller gizlin firmwary (ESP32 implant)
 └── dbc_files/           ➔ 30+ Deşifirlenen awto-protokol bazalary
```

---

## 🚀 Gurmak we Işletmek

### Gurmak
```bash
pip install python-can cantools
```

### Işletmek

#### 1. IXXAT bilen (real maşyn)
```bash
python main.py
# Soň GUI-de "ixxat (IXXAT)" saýla → Birikdir
```

#### 2. Demo mod (hardware ýok, synag üçin)
```bash
python main.py --demo
# ýa-da GUI-de "demo (Ýasama)" saýla
```

## 🔌 Birikdirmek tertibi
1. IXXAT USB-to-CAN → kompýutere birikdir
2. OBD-II kabel → maşynyň OBD portuna birikdir
3. Maşyny ýak (ACC işlemesi üçin)
4. `python main.py` → Birikdir düwmäni bas

## 📊 Näme görünýär
- Tizlık (hızometer bilen)
- Ruletka burçy (-500° ~ +500°)
- Gaz pedaly %
- Tormoz ýagdaýy
- 4 tigiriň aýratyn tizligi
- Kruiz ýagdaýy

## 🕹️ Ruly gözegçiligi
- ◀◀ Çepe / Saga ▶▶ → güýçli öwürmek
- ◀ Ýuwaş Çepe / Sag ▶ → ýuwaş öwürmek
- Slider → öz torque gymmatyny saýla (-1500 ~ +1500)

## 🏎️ Gaz gözegçiligi
- ▲ Tizlendir → +1.5 m/s²
- ▼ Haýalla → -2.0 m/s²
- Slider → -3.5 ~ +2.0 m/s² aralygynda

## ⚠️ Goşmaça Duýduryşlar
> ⚠️ **Real maşynda synag diňe durka ýa-da boş meýdanda geçirilmelidir!**  
> ⚠️ **LKAS düwmesi bar bolsa (TSS) gözegçilik şol arkaly kabul edilýär.**

---

## ⚠️ Kanun we Howpsuzlyk Duýduryşy (Hökman Okaň!)

> [!CAUTION]
> **DIŇE YLMY-BARLAG WE RUGSAT EDILEN SYNAGLAR ÜÇIN (PENTESTING).**
> Bu programma, **dine rugsat berlen ulaglarda** we kanuny tehniki platformalarda işleýän kiberhowpsuzlyk işgärleri, red-team topary we barlagçylar üçin berilýär.
> 
> **DUÝDURYŞ:** Hereket edýän maşynyň CAN toruna we çyzyklaryna göni aralaşyp paket siňdirmek **örän howpludyr**, janyňyza, maşyna ýa daş-töwerekdäkilere howp salyp biler hem-de hardware-y ugrukdyryp biler. Bu guraly açyk ýollarda, köçelerde ýa-da siziň eýeçilik etmeýän, rugsatnama alynmadyk hakyky ulaglaryňyzda **ASLA ULANMAŇ**. 
> 
> Bu taslamany dörediji ýa-da onuň proýektine goşant goşujylar, repository-nýn eýesi islendik jenaýat, zyýan, adam ölüm-ýitgisi, synag mahaly heläkçilik, ahlaksyz ulanmak we emlägiň ýitmegi babatda kanuny taýdan **hiç hili jogapkärçilik çekmeýär**. Guraly öz paýhasyňyz we jogapkärçiligiňiz astynda, ýapyk we dolandyrylýan meýdançalarda ulanyň.

---
<div align="center">
  <b>© 2026 RedPilot Development. Ähli hukuklar goralan.</b>
</div>
