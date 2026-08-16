import os
import csv
from datetime import datetime

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