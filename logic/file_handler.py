import os
import re
from typing import Dict, List, Tuple

def load_cnc_file(file_path: str) -> List[str]:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.readlines()

def _extract_target_func_names(rules: Dict[str, str]) -> List[str]:
    """Extrahiert Funktionsnamen aus Zielbefehlen wie WAITM(1,1,2)."""
    names = set()
    for z in rules.values():
        if z and "(" in z and ")" in z:
            name = z.split("(", 1)[0].strip()
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                names.add(name)
    return sorted(names, key=len, reverse=True)

def apply_rules_to_cnc(lines: List[str], rules: Dict[str, str]) -> List[str]:
    """
    Konvertiert CNC-Zeilen anhand Excel-Regeln.
    - Befehle mit Leerzeichen (z. B. 'M90 (1)') werden als Ganzes ersetzt
    - Einfache Befehle werden tokenweise ersetzt/gelöscht
    - Klammern werden zu ';' nur für Kommentare oder alleinstehende '('
      (ohne zusätzliches Leerzeichen nach ';')
    - Schon konvertierte Funktionsaufrufe (aus Spalte B) werden geschützt
    """
    sorted_rules: List[Tuple[str, str]] = sorted(rules.items(), key=lambda x: len(x[0]), reverse=True)
    target_func_names = _extract_target_func_names(rules)

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

        # 2) Komplexe Regeln (z. B. "M90 (1)")
        for pat, z_cmd in complex_rules:
            line = pat.sub(z_cmd, line)

        # 3) Einfache Regeln tokenweise anwenden
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

        # 4) Kommentare behandeln
        #    - ( ... ) -> ;...
        #    - alleinstehendes "(" am Zeilenende -> ";"
        def comment_sub(m: re.Match) -> str:
            # Kein zusätzliches Leerzeichen nach ';'
            content = m.group(1).strip()
            return f";{content}"

        # Normale Kommentar-Klammern: ( ... )
        line = re.sub(r"(?<![A-Za-z0-9_])\((.*?)\)", comment_sub, line)

        # Alleinstehendes "(" → zu ";"
        line = re.sub(r"(?<![A-Za-z0-9_])\(\s*$", ";", line)

        new_lines.append(line + "\n")

    return new_lines

def save_cnc_file(lines: List[str], target_path: str):
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

def check_conversion(lines: List[str], rules: Dict[str, str]):
    """
    Prüft nach der Konvertierung, ob noch alte Quellbefehle vorhanden sind.
    """
    issues = []
    complex_q = [q for q in rules.keys() if " " in q]
    simple_q = [q for q in rules.keys() if " " not in q]
    complex_pats = [(q, re.compile(rf"(?<!\S){re.escape(q)}(?!\S)")) for q in complex_q]

    for i, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")
        for q, pat in complex_pats:
            if pat.search(line):
                issues.append((i, q, line))
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
