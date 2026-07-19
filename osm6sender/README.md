# Quantum / OSM6 Timekeeping Simulator

Dieses Projekt simuliert eine **Swiss Timing Quantum** oder **ARES21** Zeitmesskonsole. Es generiert regelkonforme Datenpakete nach dem **Omega OSM6 Data Handling Protokoll (OSM6 DH)**, lagert diese in eine externe Textdatei aus und sendet sie nativ über einen angeschlossenen **FTDI USB-Konverter** (z. B. RS485 oder RS232) an Ihre Wettkampfsoftware (wie Swimify, WinGrodan oder HY-Tek Meet Manager).

## 🚀 Features
* **Nativer FTDI-Zugriff**: Arbeitet direkt mit dem FTDI D2XX/Libusb-Treiber über `pyftdi` (kein virtueller COM-Port im Betriebssystem nötig).
* **Daten-Auslagerung**: Generiert und speichert Nachrichten-Paare (Part 1 & Part 2) als Hex-Strings zeilenweise in einer externen Textdatei.
* **Live-Klartext-Log**: Dekodiert gesendete Daten live im Terminal (Wettkampf, Bahn, Runde, Platzierung, Zeit).
* **Protokoll-Konform**: Berechnet automatisch die korrekte Bit-Maske für genutzte Bahnen (Used Lanes Indicator laut Spezifikation).

---

## 🛠️ Voraussetzungen & Installation

### 1. Virtuelle Umgebung einrichten (venv)
Es wird dringend empfohlen, das Projekt in einer isolierten virtuellen Umgebung zu installieren, um Konflikte mit globalen Python-Paketen zu vermeiden.

**Unter Windows:**
```bash
# 1. Virtuelle Umgebung erstellen
python -m venv venv

# 2. Umgebung aktivieren
.\venv\Scripts\activate
```

**Unter Linux / macOS:**
```bash
# 1. Virtuelle Umgebung erstellen
python3 -m venv venv

# 2. Umgebung aktivieren
source venv/bin/activate
```

### 2. Python-Bibliotheken installieren
Installieren Sie nach der Aktivierung der virtuellen Umgebung die benötigte FTDI-Erweiterung:
```bash
pip install pyftdi
```

### 3. Spezielle Treiber-Vorbereitung (Wichtig für Windows)
Da `pyftdi` auf der systemunabhängigen Bibliothek `libusb` aufbaut, akzeptiert es unter Windows **nicht** den Standard-VCP-Treiber (Virtual COM Port) von FTDI. Der USB-Schnittstellentreiber muss einmalig für den direkten Zugriff freigeschaltet werden:

1. **Laden** Sie das kostenlose Tool **[Zadig](https://akeo.ie)** herunter.
2. **Schließen** Sie Ihren FTDI-Adapter per USB an den PC an.
3. **Öffnen** Sie Zadig und wählen Sie im Menü *Options -> List All Devices*.
4. **Wählen** Sie Ihren FTDI-Chip aus der Dropdown-Liste aus (z. B. *FT232R USB UART*).
5. **Wechseln** Sie den Ziel-Treiber (rechts vom grünen Pfeil) auf **`libusb-win32`** oder **`WinUSB`**.
6. **Klicken** Sie auf **Replace Driver** (bzw. *Reinstall Driver*).

*Hinweis für Linux/macOS:* Es ist keine Treiber-Installation nötig. Unter Linux müssen lediglich Lese-/Schreibrechte für die USB-Schnittstelle vorhanden sein (z. B. über eine udev-Regel oder Ausführung als `sudo`).

---

## 📦 Konfiguration

1. **Speichern** Sie den untenstehenden Python-Code in einer Datei namens `osm6_simulator.py`.
2. **Starten** Sie das Skript bei aktiver virtueller Umgebung einmalig, um die angeschlossenen FTDI-Geräte aufzulisten:
   ```bash
   python osm6_simulator.py
   ```
3. **Suchen** Sie im Terminal-Output nach der Geräte-URL. Die Ausgabe sieht beispielsweise so aus:
   ```text
   [*] Suche nach angeschlossenen FTDI-Geräten...
   Available interfaces:
     ftdi://ftdi:232r:21A345B/1   (FT232R USB UART)
   ```
4. **Öffnen** Sie die Skriptdatei und tragen Sie Ihre ermittelte URL im `__main__`-Block ein:
   ```python
   FTDI_DEVICE_URL = 'ftdi://ftdi:232r:21A345B/1'
   ```

---

## 💻 Nutzung

Führen Sie das Skript aus, um die Simulation zu starten:
```bash
python osm6_simulator.py
```

### Ablauf des Programms:
1. **Generieren**: Das Skript erzeugt vordefinierte Rennsegmente (z. B. Zwischenzeiten und Zielanschläge).
2. **Speichern**: Die Rohdaten werden als Hex-Paare in der Datei `osm6_simulation_data.txt` hinterlegt.
3. **Senden & Loggen**: Das Programm liest die erzeugte Datei ein, schickt die Bytes im 9600-Baud-Takt über den FTDI-Chip und gibt parallel folgendes Klartext-Log aus:

```text
================ [ NACHRICHTEN-PAAR #1 ] ================
 Typ:        Laufende Zeit (On Line Time)
 Zeit-Art:   Zwischenzeit (Split time)
 Wettkampf:  Event 3 | Lauf 2 | Runde 4
 Details:    Bahn 2 | Akt.Runde 1 | Platz: 3
 Zeit:       >>> 21.89 <<<
 Raw-Hex:    0102083249202F203034303033303230322020303304;010208103230310220202020202032312E38392004
==========================================================
```

### Virtuelle Umgebung verlassen
Wenn Sie fertig sind, können Sie die Umgebung mit folgendem Befehl wieder deaktivieren:
```bash
deactivate
```

---

## 📄 Struktur der Datendatei (`osm6_simulation_data.txt`)
Jede Zeile enthält exakt **ein zusammengehöriges Nachrichten-Paar**, getrennt durch ein Semikolon `;`:
* **Teil 1 (Kopfdaten)**: Enthält Event, Lauf, Rundenanzahl und Platzierung.
* **Teil 2 (Zeitdaten)**: Enthält Bahnnummer, aktuelle Runde und die gestoppte Zeit im 11-Byte-ASCII-Format.

Dadurch bleibt die Datei plattformübergreifend editierbar, ohne dass binäre Steuerzeichen (`SOH`, `STX`, `EOT`) beim Speichern beschädigt werden.

---

## 🐍 Quellcode (`osm6_simulator.py`)

```python
import time
import sys
from pyftdi.serialext import serial_for_url
from pyftdi.ftdi import Ftdi

# Definition der Steuerzeichen laut Protokoll-Spezifikation (S. 3)
SOH = b'\x01'
HOME = b'\x08'
STX = b'\x02'
LF = b'\x10'
EOT = b'\x04'
SPACE = b'\x20'

# Mappings für das Klartext-Log (S. 2)
MSG_TYPES = {
    '0': 'Bereit am Start (Ready at start)',
    '1': 'Offizielles Ende (Official End)',
    '2': 'Laufende Zeit (On Line Time)',
    '3': 'Aktuelle Rennergebnisse (Current race results)',
    '5': 'Vorheriges Rennergebnis (Previous race result)'
}

KIND_OF_TIMES = {
    'S': 'Startzeit (Start)',
    'I': 'Zwischenzeit (Split time)',
    'A': 'Endzeit (Finish)',
    'D': 'Wechselzeit/Staffel (Take over time)',
    'R': 'Reaktionszeit (Reaction time)',
    'B': 'Manueller Handtaster (Button only)'
}

def decode_and_log(p1_bytes: bytes, p2_bytes: bytes, index: int):
    """Analysiert die Rohbytes und gibt ein gut lesbares Protokoll-Log aus."""
    try:
        a = chr(p1_bytes)
        b = chr(p1_bytes)
        ee = p1_bytes[8:10].decode('ascii')
        fff = p1_bytes[10:13].decode('ascii')
        gg = p1_bytes[13:15].decode('ascii')
        hh = p1_bytes[17:19].decode('ascii').strip()

        j = chr(p2_bytes)
        kk = p2_bytes[5:7].decode('ascii')
        
        stx_index = p2_bytes.find(STX, 4)
        time_str = p2_bytes[stx_index+1:-1].decode('ascii').strip()

        msg_name = MSG_TYPES.get(a, f"Unbekannt ({a})")
        kind_name = KIND_OF_TIMES.get(b, f"Unbekannt ({b})")
        rank_str = f"Platz: {hh}" if hh else "Platz: -"

        print(f"\n================ [ NACHRICHTEN-PAAR #{index} ] ================")
        print(f" Typ:        {msg_name}")
        print(f" Zeit-Art:   {kind_name}")
        print(f" Wettkampf:  Event {int(fff)} | Lauf {int(gg)} | Runde {int(ee)}")
        print(f" Details:    Bahn {j} | Akt.Runde {int(kk)} | {rank_str}")
        print(f" Zeit:       >>> {time_str} <<<")
        print(f" Raw-Hex:    {p1_bytes.hex().upper()};{p2_bytes.hex().upper()}")
        print("==========================================================")
    except Exception as e:
        print(f"\n[!] Fehler beim Dekodieren für das Log: {e}")

def calculate_used_lanes(lanes: list) -> bytes:
    """Berechnet die 2 Bytes für die genutzten Bahnen (Note 1)"""
    byte1 = 0x20
    byte2 = 0x20
    for lane in lanes:
        if 1 <= lane <= 5:
            byte1 |= (1 << (lane - 1))
        elif 6 <= lane <= 10:
            byte2 |= (1 << (lane - 6))
    return bytes([byte1, byte2])

def generate_osm6_pair(msg_type: str, kind_of_time: str, time_type: str, 
                       lanes: list, lap: int, event: int, heat: int, 
                       rank: int, active_lane: int, current_lap: int, time_str: str) -> tuple:
    """Generiert Part 1 und Part 2 des OSM6-Protokolls als Byte-Strings."""
    a = str(msg_type).encode('ascii')
    b = str(kind_of_time).encode('ascii')
    c = str(time_type).encode('ascii') if time_type else SPACE
    dd = calculate_used_lanes(lanes)
    ee = f"{lap:02d}".encode('ascii')
    fff = f"{event:03d}".encode('ascii')
    gg = f"{heat:02d}".encode('ascii')
    hh = f"{rank:02d}".encode('ascii') if rank > 0 else b'  '

    part1 = SOH + STX + HOME + a + b + c + dd + ee + fff + gg + SPACE + SPACE + hh + EOT

    j = str(active_lane).encode('ascii')
    kk = f"{current_lap:02d}".encode('ascii')
    formatted_time = f"{time_str:>11} ".encode('ascii')

    part2 = SOH + STX + HOME + LF + j + kk + STX + formatted_time + EOT

    return part1, part2

def save_packets_to_file(filename: str):
    """Generiert Testdaten und speichert ein Paar pro Zeile als Hex ab."""
    active_lanes =
    
    with open(filename, 'w', encoding='utf-8') as f:
        # Zwischenzeit
        p1_split, p2_split = generate_osm6_pair(
            msg_type="2", kind_of_time="I", time_type=" ", 
            lanes=active_lanes, lap=4, event=3, heat=2, 
            rank=3, active_lane=2, current_lap=1, time_str="21.89"
        )
        f.write(f"{p1_split.hex()};{p2_split.hex()}\n")
        
        # Endzeit
        p1_final, p2_final = generate_osm6_pair(
            msg_type="2", kind_of_time="A", time_type=" ", 
            lanes=active_lanes, lap=4, event=3, heat=2, 
            rank=2, active_lane=4, current_lap=4, time_str="1:22.07"
        )
        f.write(f"{p1_final.hex()};{p2_final.hex()}\n")

    print(f"[*] Daten erfolgreich in '{filename}' exportiert.")

