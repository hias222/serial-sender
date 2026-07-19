import time
import serial

# Definition der Steuerzeichen laut Protokoll-Spezifikation (S. 3)
SOH = b'\x01'
HOME = b'\x08'
STX = b'\x02'
LF = b'\x10'
EOT = b'\x04'
SPACE = b'\x20'

# Mappings für das Log (S. 2)
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
        # Part 1 parsen (SOH, STX, HOME ignorieren, danach kommen die Felder ab Index 3)
        # Struktur: A B C DD EE FFF GG (Leerräume) HH [EOT]
        a = chr(p1_bytes[3])
        b = chr(p1_bytes[4])
        # Runden, Event, Heat, Rank extrahieren
        ee = p1_bytes[8:10].decode('ascii')
        fff = p1_bytes[10:13].decode('ascii')
        gg = p1_bytes[13:15].decode('ascii')
        hh = p1_bytes[17:19].decode('ascii').strip()

        # Part 2 parsen (SOH, STX, HOME, LF ignorieren, Daten ab Index 4)
        # Struktur: J KK [STX] Zeit [EOT]
        j = chr(p2_bytes[4])
        kk = p2_bytes[5:7].decode('ascii')
        
        # Zeit auslesen (liegt hinter dem zweiten STX-Zeichen in Part 2)
        stx_index = p2_bytes.find(STX, 4)
        time_str = p2_bytes[stx_index+1:-1].decode('ascii').strip()

        # Log-Ausgabe zusammenbauen
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
    """Generiert Testdaten und speichert ein Paar (Part1/Part2) pro Zeile als Hex ab."""
    active_lanes = [1, 2, 3, 4]
    
    with open(filename, 'w', encoding='utf-8') as f:
        # 1. Beispiel: Zwischenzeit (Split) von Bahn 2
        p1_split, p2_split = generate_osm6_pair(
            msg_type="2", kind_of_time="I", time_type=" ", 
            lanes=active_lanes, lap=4, event=3, heat=2, 
            rank=3, active_lane=2, current_lap=1, time_str="21.89"
        )
        f.write(f"{p1_split.hex()};{p2_split.hex()}\n")
        
        # 2. Beispiel: Zielzeit (Final) von Bahn 4
        p1_final, p2_final = generate_osm6_pair(
            msg_type="2", kind_of_time="A", time_type=" ", 
            lanes=active_lanes, lap=4, event=3, heat=2, 
            rank=2, active_lane=4, current_lap=4, time_str="1:22.07"
        )
        f.write(f"{p1_final.hex()};{p2_final.hex()}\n")

    print(f"[*] Daten erfolgreich in '{filename}' exportiert.")

def send_from_file(filename: str, port_name: str):
    """Liest die Textdatei zeilenweise aus, loggt den Inhalt im Klartext und sendet per Serial."""
    try:
        ser = serial.Serial(
            port=port_name, baudrate=9600, bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1
        )
        print(f"[*] COM-Port {port_name} geöffnet. Starte Live-Übertragung...")
    except Exception as e:
        print(f"[!] Serieller Port Fehler: {e}")
        print("[!] Sende-Vorgang übersprungen. Logge nur den Dateiinhalt auf dem Bildschirm:")
        ser = None

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for index, line in enumerate(f, 1):
                line = line.strip()
                if not line or ";" not in line:
                    continue
                
                # Hex-Strings zurück in echte Bytes konvertieren
                part1_hex, part2_hex = line.split(";")
                p1_bytes = bytes.fromhex(part1_hex)
                p2_bytes = bytes.fromhex(part2_hex)
                
                # Live-Log im Terminal ausgeben
                decode_and_log(p1_bytes, p2_bytes, index)
                
                # Über die Hardware senden, falls der Port offen ist
                if ser and ser.is_open:
                    ser.write(p1_bytes)
                    time.sleep(0.1)  # Protokoll-Pause zwischen Kopf- und Zeitdaten
                    ser.write(p2_bytes)
                
                time.sleep(1.5)  # Pause zwischen den simulierten Anschlägen
                
    except FileNotFoundError:
        print(f"[!] Datei '{filename}' nicht gefunden.")
    finally:
        if ser:
            ser.close()
            print("\n[*] Serieller Port geschlossen.")

if __name__ == "__main__":
    LOG_FILE = "osm6_simulation_data.txt"
    TARGET_PORT = "COM3"  # Anpassen an Ihren echten COM-Port
    
    # 1. Datei erzeugen
    save_packets_to_file(LOG_FILE)
    
    # 2. Datei einlesen, parsen, loggen und abschicken
    send_from_file(LOG_FILE, TARGET_PORT)
