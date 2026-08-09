import time
import sys
from pyftdi.serialext import serial_for_url
from pyftdi.ftdi import Ftdi
import threading  # Neu für den parallelen Alive-Takt
import serial

# Definition der Steuerzeichen laut Protokoll-Spezifikation (S. 3)
SOH = b'\x01'
HOME = b'\x08'
STX = b'\x02'
# LF = b'\x10'
LF = b'\x0A'
EOT = b'\x04'
SPACE = b'\x20'
DC2 = b'\x12'
DC4 = b'\x14'

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

# Globale Variable für die Thread-Steuerung
keep_alive_active = False

def decode_lanes(byte1, byte2):
    lanes = []
    # Bitmaske 0x20 entfernen, falls vorhanden, um reine Datenbits zu isolieren
    b1 = byte1 & ~0x20
    b2 = byte2 & ~0x20
    
    # Bahnen 1 bis 5 aus byte1 extrahieren
    for i in range(5):
        if b1 & (1 << i):
            lanes.append(i + 1)
            
    # Bahnen 6 bis 10 aus byte2 extrahieren
    for i in range(5):
        if b2 & (1 << i):
            lanes.append(i + 6)
            
    return lanes

def decode_and_log(p1_bytes: bytes, p2_bytes: bytes, index: int):
    """Analysiert die Rohbytes und gibt ein gut lesbares Protokoll-Log aus."""
    try:
        a = chr(p1_bytes[3])
        b = chr(p1_bytes[4])
        c = chr(p1_bytes[5])
        dd_hex = p1_bytes[6:8].decode('ascii', errors='ignore') 
        dd = decode_lanes(p1_bytes[6], p1_bytes[7])
        
        # Sicheres Strippen vor dem Int-Cast, falls Leerzeichen enthalten sind
        ee = p1_bytes[8:10].decode('ascii').strip()
        fff = p1_bytes[10:13].decode('ascii').strip()
        gg = p1_bytes[13:15].decode('ascii').strip()
        hh = p1_bytes[17:19].decode('ascii').strip()

        j = chr(p2_bytes[4])
        kk = p2_bytes[5:7].decode('ascii').strip()
        
        stx_index = p2_bytes.find(STX, 4)
        time_str = p2_bytes[stx_index+1:-1].decode('ascii').strip()

        msg_name = MSG_TYPES.get(a, f"Unbekannt ({a})")
        kind_name = KIND_OF_TIMES.get(b, f"Unbekannt ({b})")
        rank_str = f"Platz: {hh}" if hh else "Platz: -"

        # Fallback für leere String-Werte bei der Protokoll-Anzeige
        ee_val = int(ee) if ee else 0
        fff_val = int(fff) if fff else 0
        gg_val = int(gg) if gg else 0
        kk_val = int(kk) if kk else 0

        print(f"\n================ [ NACHRICHTEN-PAAR #{index} ] ================")
        print(f" Typ:        {msg_name}")
        print(f" Zeit-Art:   {kind_name}")
        print(f" Wettkampf:  Event {fff_val} | Lauf {gg_val} | Runde {ee_val}")
        print(f" Details:    Bahn {j} | Akt.Runde {kk_val} | {rank_str}")
        print(f" Zeit:       >>> {time_str} <<<")
        print(f" Raw-Hex:    {p1_bytes.hex().upper()};{p2_bytes.hex().upper()}")
        print(f" Lanes:      {dd}")
        print(f" 1: {a} {b} :{c}: :{dd_hex}: {ee} {fff} {gg} {SPACE.decode()} {SPACE.decode()} {hh}")
        print(f" 2: {j} {kk} STX {time_str}")
        print("==========================================================")
    except Exception as e:
        print(f"\n[!] Fehler beim Dekodieren für das Log: {e}")

def calculate_used_lanes(lanes: list) -> bytes:
    """Berechnet die 2 Bytes für die genutzten Bahnen (Protokoll-Standard: Basis 0x20)"""
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
    c = str(time_type).encode('ascii') if time_type and time_type != " " else SPACE
    dd = calculate_used_lanes(lanes)
    
    ee = f"{lap:2d}".encode('ascii')
    fff = f"{event:3d}".encode('ascii')
    gg = f"{heat:2d}".encode('ascii')
    hh = f"{rank:2d}".encode('ascii') if rank > 0 else b'  '

    part1 = SOH + STX + HOME + a + b + c + dd + ee + fff + gg + SPACE + SPACE + hh + EOT

    j = str(active_lane).encode('ascii')
    kk = f"{current_lap:2d}".encode('ascii')
    formatted_time = f"{time_str:>11} ".encode('ascii')

    part2 = SOH + STX + HOME + LF + j + kk + STX + formatted_time + EOT

    return part1, part2

def save_packets_to_file(filename: str):
    """Generiert Testdaten und speichert ein Paar pro Zeile als Hex ab."""
    active_lanes = [3,4,5]
    
    with open(filename, 'w', encoding='utf-8') as f:
        # 1. Ready
        p1, p2 = generate_osm6_pair("0", " ", " ", active_lanes, 4, 3, 2, 0, 0, 0, "")
        f.write(f"{p1.hex()};{p2.hex()};5000\n")

        # 2. Start
        p1, p2 = generate_osm6_pair("2", "S", " ", active_lanes, 4, 3, 2, 0, 0, 0, "")
        f.write(f"{p1.hex()};{p2.hex()};500\n")

        # 3. Reaktionszeit
        p1, p2 = generate_osm6_pair("2", "R", " ", active_lanes, 4, 3, 2, 1, 1, 1, ".89")
        f.write(f"{p1.hex()};{p2.hex()};1\n")
        p1, p2 = generate_osm6_pair("2", "R", " ", active_lanes, 4, 3, 2, 1, 2, 1, ".70")
        f.write(f"{p1.hex()};{p2.hex()};10\n")
        p1, p2 = generate_osm6_pair("2", "R", " ", active_lanes, 4, 3, 2, 1, 3, 1, ".86")
        f.write(f"{p1.hex()};{p2.hex()};10\n")
        p1, p2 = generate_osm6_pair("2", "R", " ", active_lanes, 4, 3, 2, 1, 4, 1, ".70")
        f.write(f"{p1.hex()};{p2.hex()};1\n")
        p1, p2 = generate_osm6_pair("2", "R", " ", active_lanes, 4, 3, 2, 1, 5, 1, ".86")
        f.write(f"{p1.hex()};{p2.hex()};10\n")
        p1, p2 = generate_osm6_pair("2", "R", " ", active_lanes, 4, 3, 2, 1, 6, 1, ".86")
        f.write(f"{p1.hex()};{p2.hex()};1\n")
        p1, p2 = generate_osm6_pair("2", "R", " ", active_lanes, 4, 3, 2, 1, 7, 1, ".86")
        f.write(f"{p1.hex()};{p2.hex()};1\n")
        p1, p2 = generate_osm6_pair("2", "R", " ", active_lanes, 4, 3, 2, 1, 8, 1, ".86")
        f.write(f"{p1.hex()};{p2.hex()};10000\n")

        # 3. Zwischenzeit
        p1, p2 = generate_osm6_pair("2", "I", " ", active_lanes, 4, 3, 2, 1, 2, 2, "1:21.89")
        f.write(f"{p1.hex()};{p2.hex()};5000\n")
        
        # 4. Endzeit
        p1, p2 = generate_osm6_pair("2", "A", " ", active_lanes, 4, 3, 2, 1, 1, 4, "2:22.07")
        f.write(f"{p1.hex()};{p2.hex()};500\n")
        p1, p2 = generate_osm6_pair("2", "A", " ", active_lanes, 4, 3, 2, 2, 2, 4, "2:02.07")
        f.write(f"{p1.hex()};{p2.hex()};50\n")
        p1, p2 = generate_osm6_pair("2", "A", " ", active_lanes, 4, 3, 2, 3, 3, 4, "2:22.07")
        f.write(f"{p1.hex()};{p2.hex()};500\n")
        p1, p2 = generate_osm6_pair("2", "A", " ", active_lanes, 4, 3, 2, 4, 4, 4, "2:02.07")
        f.write(f"{p1.hex()};{p2.hex()};500\n")
        p1, p2 = generate_osm6_pair("2", "A", " ", active_lanes, 4, 3, 2, 5, 5, 4, "2:22.07")
        f.write(f"{p1.hex()};{p2.hex()};50\n")
        p1, p2 = generate_osm6_pair("2", "A", " ", active_lanes, 4, 3, 2, 6, 6, 4, "2:02.07")
        f.write(f"{p1.hex()};{p2.hex()};5\n")
        p1, p2 = generate_osm6_pair("2", "A", " ", active_lanes, 4, 3, 2, 7, 7, 4, "2:22.07")
        f.write(f"{p1.hex()};{p2.hex()};500\n")
        p1, p2 = generate_osm6_pair("2", "A", " ", active_lanes, 4, 3, 2, 8, 8, 4, "1:55.07")
        f.write(f"{p1.hex()};{p2.hex()};5000\n")

        # 5. Offizielles Ende
        p1, p2 = generate_osm6_pair("1", " ", " ", active_lanes, 4, 3, 2, 0, 0, 0, "14:17:55.2")
        f.write(f"{p1.hex()};{p2.hex()};5000\n")
        
        # 5. Offizielles Ende
        p1, p2 = generate_osm6_pair("0", " ", " ", active_lanes, 4, 3, 3, 0, 0, 0, "14:17:55.2")
        f.write(f"{p1.hex()};{p2.hex()};500\n")

    print(f"[*] Daten erfolgreich in '{filename}' exportiert.")

def send_alive_message_ftdi(port):
    """Sendet das Keep-Alive-Signal."""
    alive_message = SOH + DC2 + b'9' + DC4 + b'TP' + EOT
    try:
        port.write(alive_message)
        print("[Alive] 3s-Heartbeat gesendet.")
    except Exception as e:
        print(f"[Alive] Fehler beim Senden: {e}")

def alive_loop(port):
    """Hintergrund-Funktion: Sendet exakt alle 3 Sekunden."""
    global keep_alive_active
    while keep_alive_active:
        send_alive_message_ftdi(port)
        # Überprüft in kleinen Schritten (0.1s), ob abgebrochen werden soll
        for _ in range(30): 
            if not keep_alive_active:
                break
            time.sleep(0.1)

def send_from_file_ftdi(filename: str, ftdi_url: str):
    """Liest die Datei zeilenweise aus und sendet sie direkt via pyftdi-Treiber."""
    global keep_alive_active
    port = None
    try:
        port = serial_for_url(ftdi_url, baudrate=9600, bytesize=serial.SEVENBITS, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE)
        print(f"[*] FTDI-Gerät ({ftdi_url}) erfolgreich initialisiert (9600 8N1).")
    except Exception as e:
        print(f"[!] FTDI-Initialisierungsfehler: {e}")
        print("[*] Tipp: Nutzen Sie 'Ftdi.show_devices()', um angeschlossene IDs zu finden.")
        return

    # Alive-Thread starten
    keep_alive_active = True
    alive_thread = threading.Thread(target=alive_loop, args=(port,), daemon=True)
    alive_thread.start()
    print("[*] Automatischer 3-Sekunden Alive-Takt gestartet.")

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for index, line in enumerate(f, 1):

                line = line.strip()
                if not line or ";" not in line:
                    continue

                parts = line.split(";")
                if len(parts) < 3:
                    print(f"[!] Zeile {index} unvollständig. Erwartet: Hex1;Hex2;ms")
                    continue
                        
                part1_hex, part2_hex, ms_str = parts[0], parts[1], parts[2]
                 
                
                # part1_hex, part2_hex = line.split(";")
                p1_bytes = bytes.fromhex(part1_hex)
                p2_bytes = bytes.fromhex(part2_hex)
                
                decode_and_log(p1_bytes, p2_bytes, index)
                
                port.write(p1_bytes)
                time.sleep(0.1)  
                port.write(p2_bytes)
                
                # Millisekunden in Sekunden umrechnen (z.B. 500ms = 0.5s)
                wait_seconds = float(ms_str) / 1000.0

                # Dynamische Wartezeit aus der Datei anwenden
                print(f"[*] Zeile {index} gesendet. Warte {ms_str} ms...")
                time.sleep(wait_seconds) 
                
    except FileNotFoundError:
        print(f"[!] Datei '{filename}' nicht gefunden.")
    finally:
        if port:
            port.close()
            print("\n[*] FTDI-Port geschlossen.")

if __name__ == "__main__":
    LOG_FILE = "osm6_simulated.txt"
    # Schritt 1: Datei mit allen 5 Rennphasen erzeugen
    save_packets_to_file(LOG_FILE)
    
    # Schritt 2: Sende-Vorgang starten (URL anpassen, z.B. 'ftdi://ftdi:232:1/1')
    send_from_file_ftdi(LOG_FILE, "ftdi://ftdi:232/1")
