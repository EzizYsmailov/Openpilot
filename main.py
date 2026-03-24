"""
Universal CAN Dashboard — opendbc
Windows | IXXAT USB-to-CAN

Başlatmak:
    pip install python-can cantools
    python main.py

    Demo mod üçin (hardware ýok):
    python main.py --demo

Islendik DBC faýly:
  1. DBC faýlyny bu klasöre goý
  2. GUI-de saýla we "Ýükle" düwmesine bas
  3. Signallar awtomatiki görünýär!
"""
import sys

if '--demo' in sys.argv:
    import config
    config.DEMO_MODE = True

from gui import App

if __name__ == '__main__':
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
