import openpyxl

def load_rules_from_excel(excel_path: str) -> dict:
    """
    Lädt Mapping-Regeln aus Excel (Spalte A = Quelle, Spalte B = Ziel).
    - Erfasst auch Löschregeln (wenn Ziel leer ist -> Map auf "").
    - Whitespace wird getrimmt.
    """
    rules: dict[str, str] = {}
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    sheet = wb.active

    # ab Zeile 2 (Header in Zeile 1)
    for row in sheet.iter_rows(min_row=2, values_only=True):
        q = row[0]
        z = row[1] if len(row) > 1 else None
        if q is None:
            continue
        q = str(q).strip()
        z = "" if z is None else str(z).strip()  # leeres Ziel = löschen
        if q == "":
            continue
        rules[q] = z
    return rules
