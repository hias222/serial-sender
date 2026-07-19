import datetime

# Definition der Steuerzeichen laut Protokoll-Spezifikation (S. 3)
SOH = b'\x01'
HOME = b'\x08'
STX = b'\x02'
LF = b'\x10'   # Im Protokoll explizit als 10 Hex definiert
EOT = b'\x04'
SPACE = b'\x20'

def calculate_used_lanes(lanes: list) -> bytes:
    """Berechnet die 2 Bytes für die genutzten Bahnen (Note 1)"""
    # Bits 7, 6, 5 sind fest auf 0, 0, 1 gesetzt (Wert 32 bzw. 0x20)
    byte1 = 0x20  # Bahnen 1-5
    byte2 = 0x20  # Bahnen 6-10
    
    for lane in lanes:
        if 1 <= lane <= 5:
            byte1 |= (1 << (lane - 1))
        elif 6 <= lane <= 10:
            byte2 |= (1 << (lane - 6))
            
    return bytes([byte1, byte2])

def generate_osm6_pair(msg_type: str, kind_of_time: str, time_type: str, 
                       lanes: list, lap: int, event: int, heat: int, 
                       rank: int, active_lane: int, current_lap: int, time_str: str) -> tuple:
    """
    Generiert Part 1 und Part 2 des OSM6-Protokolls als Byte-Strings.
    """
    # 1. Daten für Part 1 formatieren und validieren
    a = str(msg_type)[0].encode('ascii')
    b = str(kind_of_time)[0].encode('ascii')
    c = str(time_type)[0].encode('ascii') if time_type else SPACE
    dd = calculate_used_lanes(lanes)
    ee = f"{lap:02d}".encode('ascii')
    fff = f"{event:03d}".encode('ascii')
    gg = f"{heat:02d}".encode('ascii')
    hh = f"{rank:02d}".encode('ascii') if rank > 0 else b'  '

    # Part 1 zusammensetzen: [SOH][STX][HOME]ABCDDEEFFFGG¬¬HH[EOT]
    part1 = SOH + STX + HOME + a + b + c + dd + ee + fff + gg + SPACE + SPACE + hh + EOT

    # 2. Daten für Part 2 formatieren
    j = str(active_lane)[0].encode('ascii')
    kk = f"{current_lap:02d}".encode('ascii')
    
    # Zeit rechtsbündig auf 11 Bytes formatieren + 1 abschließendes Leerzeichen (S. 2/3)
    formatted_time = f"{time_str:>11} ".encode('ascii')

    # Part 2 zusammensetzen: [SOH][STX][HOME][LF]JKK[STX]Hh:Mm:Ss.dc¬[EOT]
    part2 = SOH + STX + HOME + LF + j + kk + STX + formatted_time + EOT

    return part1, part2

def print_packet(name, packet):
    """Hilfsfunktion zur lesbaren Darstellung im Terminal"""
    readable = packet.replace(SOH, b'[SOH]').replace(STX, b'[STX]')\
                     .replace(HOME, b'[HOME]').replace(LF, b'[LF]')\
                     .replace(EOT, b'[EOT]').replace(SPACE, b'¬')
    print(f"{name} (Text):  {readable.decode('ascii', errors='replace')}")
    print(f"{name} (Hex):   {packet.hex(' ').upper()}\n")

# --- ANWENDUNGSBEISPIELE (vgl. Protokoll S. 3) ---

print("--- BEISPIEL: SPLIT TIME (Bahn 2, Lauf 1, Rank 3) ---")
# Generiert exakt das Beispiel von Seite 3 des PDFs
p1, p2 = generate_osm6_pair(
    msg_type="2",       # On Line Time
    kind_of_time="I",   # Split time
    time_type=" ",      # Normal time
    lanes=[1,2,3,4],    # Platzhalter für aktive Bahnen
    lap=4,              # Gesamte Runden (400m)
    event=3, heat=2,
    rank=3,
    active_lane=2,
    current_lap=1,
    time_str="21.89"
)
print_packet("Part 1", p1)
print_packet("Part 2", p2)


print("--- BEISPIEL: ALIVE / PRESENCE MESSAGE (S. 3) ---")
# Optionales zyklisches Lebenszeichen der Konsole
alive_msg = SOH + b'\x12' + b'9' + b'\x14' + b'TP' + EOT
print_packet("Alive", alive_msg)
```

### Details zur Implementierung
* **Used Lanes (DD)**: Das Protokoll kodiert die Bahnen über ein spezielles Bitmuster in 2 Bytes (Note 1). Die Funktion `calculate_used_lanes` setzt die geforderten Bits `7, 6, 5` fest auf `0,0,1` und fügt die Bahnen 1–5 in Byte 1 sowie 6–10 in Byte 2 hinzu.
* **Zeitformatierung**: Die End- oder Zwischenzeit wird im Protokoll immer rechtsbündig in einem 11-Byte-Block übertragen, gefolgt von einem Leerzeichen. Das Skript übernimmt diese exakte Auffüllung automatisch.
* **Schnittstellen-Ausgabe**: Wenn Sie die Daten an ein echtes System (wie Quantum oder den Hy-Tek Meet Manager) senden wollen, können Sie die generierten Bytes (`p1` und `p2`) direkt über eine serielle Python-Bibliothek wie `pyserial` mittels `serial.write(p1)` abschicken.

Möchten Sie das Skript um eine **echte serielle COM-Port-Ausgabe (PySerial)** erweitern, oder benötigen Sie Unterstützung bei der Berechnung von **Relay Take-Over-Zeiten (Wechselzeiten)**?
