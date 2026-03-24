# Toyota Corolla 2017 — CAN Dashboard

## Faýl düzümi
```
toyota_can_project/
├── main.py              ← Başlatmak
├── config.py            ← Sazlamalar (CAN ID, çäkler)
├── can_interface.py     ← IXXAT birikmesi
├── toyota_parser.py     ← CAN habarlaryny okamak
├── toyota_commands.py   ← Ruly / gaz buýrugy
├── gui.py               ← Tkinter GUI
└── requirements.txt
```

## Gurmak
```bash
pip install python-can cantools
```

## Işletmek

### 1. IXXAT bilen (real maşyn)
```bash
python main.py
# Soň GUI-de "ixxat (IXXAT)" saýla → Birikdir
```

### 2. Demo mod (hardware ýok, synag üçin)
```bash
python main.py --demo
# ýa-da GUI-de "demo (Ýasama)" saýla
```

## Birikdirmek tertibi
1. IXXAT USB-to-CAN → kompýutere birikdir
2. OBD-II kabel → maşynyň OBD portuna birikdir
3. Maşyny ýak (ACC işlemesi üçin)
4. python main.py → Birikdir düwme

## Näme görünýär
- Tizlık (hızometer bilen)
- Ruletka burçy (-500° ~ +500°)
- Gaz pedaly %
- Tormoz ýagdaýy
- 4 tigiriň aýratyn tizligi
- Kruiz ýagdaýy

## Ruly gözegçiligi
- ◀◀ Çepe / Saga ▶▶ → güýçli öwürmek
- ◀ Ýuwaş Çepe / Sag ▶ → ýuwaş öwürmek
- Slider → öz torque gymmatyny saýla (-1500 ~ +1500)

## Gaz gözegçiligi
- ▲ Tizlendir → +1.5 m/s²
- ▼ Haýalla → -2.0 m/s²
- Slider → -3.5 ~ +2.0 m/s² aralygynda

## Duýduryş
⚠️  Real maşynda synag diňe durka ýa-da boş meýdanda
⚠️  LKAS düwmesi bar bolsa (TSS) gözegçilik kabul edilýär
