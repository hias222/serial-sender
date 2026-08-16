import time
import sys
from pyftdi.serialext import serial_for_url
from pyftdi.ftdi import Ftdi
from osm6_generate_data import save_packets_to_file
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

def send_from_file_ftdi(filename: str, port_name: str):
    """Liest die Datei zeilenweise aus und sendet sie direkt via pyftdi-Treiber."""
    global keep_alive_active
    port = None

    try:
        port = serial.Serial(
            port=port_name, baudrate=9600, bytesize=serial.SEVENBITS,
            parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE, timeout=1
        )
        print(f"[*] COM-Port {port_name} geöffnet. Starte Live-Übertragung...")
    except Exception as e:
        print(f"[!] Serieller Port Fehler: {e}")
        print("[!] Sende-Vorgang übersprungen. Logge nur den Dateiinhalt auf dem Bildschirm:")
        port = None

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
            keep_alive_active = False
            alive_thread.join()

            port.close()
            print("\n[*] Serial-Port geschlossen.")

if __name__ == "__main__":
    LOG_FILE = "osm6_simulated.txt"
    TARGET_PORT = "/dev/ttyUSB0"  # Anpassen an Ihren echten COM-Port
    # Schritt 1: Datei mit allen 5 Rennphasen erzeugen
    events = [1, 2, 3]
    
    EVENT_LAP_MAPPING = {
        1: 2,  # Event 1 hat immer 3 Laps
        2: 2,  # Event 2 hat immer 4 Laps
        3: 4   # Event 3 hat immer 5 Laps
    }
    
    heats = [1, 2]
    
    for current_event, current_lap in EVENT_LAP_MAPPING.items():
        for current_heat in heats:
            
            print(f"--- Starte Durchgang: Lap, Event {current_event}, Heat {current_heat} ---")
            print(f"Speichere in: {LOG_FILE}")
            print(f"Sende an: {TARGET_PORT}")
            
            save_packets_to_file(LOG_FILE, lap=current_lap, event=current_event, heat=current_heat)
            
            # Schritt 2: Sende-Vorgang starten (URL anpassen, z.B. 'ftdi://ftdi:232:1/1')
            send_from_file_ftdi(LOG_FILE, TARGET_PORT)
