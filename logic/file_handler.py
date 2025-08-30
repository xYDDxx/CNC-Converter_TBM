import os
import re
from typing import Dict, List, Tuple

def load_cnc_file(file_path: str) -> List[str]:
    """Lädt CNC-Datei und gibt Zeilen als Liste zurück."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.readlines()

def _extract_target_func_names(rules: Dict[str, str]) -> List[str]:
    """Extrahiert Funktionsnamen aus Zielbefehlen wie WAITM(1,1,2)."""
    names = set()
    for z in rules.values():
        if z and "(" in z and ")" in z:
            name = z.split("(", 1)[0].strip()
            # Nur gültige Funktionsnamen (Buchstaben, Zahlen, Unterstrich)
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                names.add(name)
    return sorted(names, key=len, reverse=True)  # Längste zuerst (für korrekte Ersetzung)

def apply_rules_to_cnc(lines: List[str], rules: Dict[str, str]) -> List[str]:
    """
    Konvertiert CNC-Zeilen anhand Excel-Regeln.
    - Befehle mit Leerzeichen (z. B. 'M90 (1)') werden als Ganzes ersetzt
    - Einfache Befehle werden tokenweise ersetzt/gelöscht
    - Klammern werden zu ';' nur für Kommentare oder alleinstehende '('
      (ohne zusätzliches Leerzeichen nach ';')
    - Schon konvertierte Funktionsaufrufe (aus Spalte B) werden geschützt
    """
    # Regeln nach Länge sortieren (längste zuerst für korrekte Ersetzung)
    sorted_rules: List[Tuple[str, str]] = sorted(rules.items(), key=lambda x: len(x[0]), reverse=True)
    target_func_names = _extract_target_func_names(rules)

    # Regeln in komplexe (mit Leerzeichen) und einfache (tokenweise) aufteilen
    complex_rules: List[Tuple[re.Pattern, str]] = []
    simple_rules: Dict[str, str] = {}
    for q_cmd, z_cmd in sorted_rules:
        if " " in q_cmd:
            # Ganze Sequenz mit Whitespace-Grenzen matchen
            pat = re.compile(rf"(?<!\S){re.escape(q_cmd)}(?!\S)")
            complex_rules.append((pat, z_cmd))
        else:
            simple_rules[q_cmd] = z_cmd  # auch "" möglich = löschen

    new_lines: List[str] = []
    for raw_line in lines:
        line = raw_line.rstrip("\n")

        # 1) Ziel-Funktionsaufrufe schützen (Leerzeichen vor "(" entfernen)
        for fname in target_func_names:
            line = re.sub(rf"\b{re.escape(fname)}\s*\(", f"{fname}(", line)

        # 2) Komplexe Regeln (z. B. "M90 (1)") - ganze Sequenzen ersetzen
        for pat, z_cmd in complex_rules:
            line = pat.sub(z_cmd, line)

        # 3) Einfache Regeln tokenweise anwenden (einzelne Befehle)
        tokens = line.split()
        out_tokens: List[str] = []
        for tok in tokens:
            if tok in simple_rules:
                replacement = simple_rules[tok]  # kann "" sein (löschen)
                if replacement != "":
                    out_tokens.append(replacement)
            else:
                out_tokens.append(tok)
        line = " ".join(out_tokens)

        # 4) Kommentare behandeln (Klammern zu Semikolon)
        #    - ( ... ) -> ;...
        #    - alleinstehendes "(" am Zeilenende -> ";"
        def comment_sub(m: re.Match) -> str:
            # Kein zusätzliches Leerzeichen nach ';'
            content = m.group(1).strip()
            return f";{content}"

        # Normale Kommentar-Klammern: ( ... ) -> ;...
        line = re.sub(r"(?<![A-Za-z0-9_])\((.*?)\)", comment_sub, line)

        # Alleinstehendes "(" am Zeilenende → zu ";"
        line = re.sub(r"(?<![A-Za-z0-9_])\(\s*$", ";", line)

        new_lines.append(line + "\n")

    return new_lines

def process_filename(original_filename: str, 
                    source_prefix_count: int = 0,
                    source_prefix_specific: bool = False,
                    source_prefix_string: str = "",
                    target_prefix_count: int = 0,
                    target_prefix_specific: bool = False,
                    target_prefix_string: str = "",
                    file_endings: List[Dict[str, str]] = None) -> str:
    """
    Verarbeitet Dateinamen gemäß Präfix- und Endungsregeln.
    
    Args:
        original_filename: Ursprünglicher Dateiname mit Endung
        source_prefix_count: Anzahl Zeichen vom Anfang zu entfernen
        source_prefix_specific: Nur entfernen wenn spezifischer String gefunden
        source_prefix_string: Spezifischer String der entfernt werden soll
        target_prefix_count: Anzahl Zeichen für neuen Präfix
        target_prefix_specific: Nur hinzufügen wenn alter spezifischer Präfix erkannt wurde
        target_prefix_string: Neuer Präfix-String
        file_endings: Liste mit Endungs-Mappings [{"source": ".dnc", "target": ".znc"}, ...]
    
    Returns:
        Neuer Dateiname
    """
    if file_endings is None:
        file_endings = []
    
    # Dateiname und Endung trennen
    name, ext = os.path.splitext(original_filename)
    original_name = name
    
    # 1. Quell-Präfix entfernen (falls konfiguriert)
    cut_prefix = ""
    if source_prefix_count > 0:
        if source_prefix_specific and source_prefix_string:
            # Nur entfernen wenn spezifischer String am Anfang steht
            if name.startswith(source_prefix_string) and len(source_prefix_string) == source_prefix_count:
                cut_prefix = source_prefix_string
                name = name[len(source_prefix_string):]
        else:
            # Generell erste N Zeichen entfernen
            if len(name) >= source_prefix_count:
                cut_prefix = name[:source_prefix_count]
                name = name[source_prefix_count:]
    
    # 2. Ziel-Präfix hinzufügen (falls konfiguriert)
    if target_prefix_count > 0 and target_prefix_string:
        if target_prefix_specific:
            # Nur hinzufügen wenn spezifischer Quell-Präfix erkannt wurde
            if cut_prefix and len(target_prefix_string) == target_prefix_count:
                name = target_prefix_string + name
        else:
            # Immer hinzufügen (bei korrekter Länge)
            if len(target_prefix_string) == target_prefix_count:
                name = target_prefix_string + name
    
    # 3. Dateiendung anpassen (gemäß Mapping-Regeln)
    new_ext = ext
    for mapping in file_endings:
        source_end = mapping.get("source", "").strip()
        target_end = mapping.get("target", "").strip()
        
        if not source_end and not target_end:
            continue
            
        if not source_end and target_end:
            # Endung anhängen
            new_ext = ext + target_end
            break
        elif source_end and not target_end:
            # Endung entfernen
            if ext.lower() == source_end.lower():
                new_ext = ""
            break
        elif source_end and target_end:
            # Endung ersetzen
            if ext.lower() == source_end.lower():
                new_ext = target_end
            break
    
    return name + new_ext

def validate_filename_settings(source_prefix_count: int, source_prefix_string: str,
                              target_prefix_count: int, target_prefix_string: str,
                              file_endings: List[Dict[str, str]]) -> List[str]:
    """
    Validiert die Dateinamen-Einstellungen und gibt Fehlermeldungen zurück.
    
    Returns:
        Liste von Fehlermeldungen (leer wenn alles OK)
    """
    errors = []
    
    # Quell-Präfix validieren
    if source_prefix_count > 0 and source_prefix_string:
        if len(source_prefix_string) != source_prefix_count:
            errors.append(f"Quell-Präfix '{source_prefix_string}' hat {len(source_prefix_string)} Zeichen, "
                         f"aber {source_prefix_count} erwartet.")
    
    # Ziel-Präfix validieren
    if target_prefix_count > 0 and target_prefix_string:
        if len(target_prefix_string) != target_prefix_count:
            errors.append(f"Ziel-Präfix '{target_prefix_string}' hat {len(target_prefix_string)} Zeichen, "
                         f"aber {target_prefix_count} erwartet.")
    
    # Dateiendungen validieren
    for i, mapping in enumerate(file_endings):
        source_end = mapping.get("source", "").strip()
        target_end = mapping.get("target", "").strip()
        
        if source_end and not source_end.startswith("."):
            errors.append(f"Quell-Endung {i+1} '{source_end}' sollte mit '.' beginnen.")
        if target_end and not target_end.startswith("."):
            errors.append(f"Ziel-Endung {i+1} '{target_end}' sollte mit '.' beginnen.")
    
    return errors

def save_cnc_file(lines: List[str], target_path: str):
    """Speichert konvertierte CNC-Datei."""
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

def check_conversion(lines: List[str], rules: Dict[str, str]):
    """
    Prüft nach der Konvertierung, ob noch alte Quellbefehle vorhanden sind.
    """
    issues = []
    # Quellbefehle in komplexe (mit Leerzeichen) und einfache aufteilen
    complex_q = [q for q in rules.keys() if " " in q]
    simple_q = [q for q in rules.keys() if " " not in q]
    complex_pats = [(q, re.compile(rf"(?<!\S){re.escape(q)}(?!\S)")) for q in complex_q]

    # Jede Zeile auf verbleibende Quellbefehle prüfen
    for i, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")
        # Komplexe Befehle prüfen (mit Regex)
        for q, pat in complex_pats:
            if pat.search(line):
                issues.append((i, q, line))
        # Einfache Befehle prüfen (tokenweise)
        tokens = line.split()
        for q in simple_q:
            if q in tokens:
                issues.append((i, q, line))

    if issues:
        print("⚠ WARNUNG: Nicht alle Quellbefehle wurden ersetzt/entfernt:")
        for ln, q, content in issues:
            print(f"   Zeile {ln}: '{q}' noch vorhanden -> {content}")
    else:
        print("✅ Check: Keine Quellbefehle mehr vorhanden.")