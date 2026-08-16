import os
import csv
from datetime import datetime

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