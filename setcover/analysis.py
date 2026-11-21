"""Analyse reproductible des résultats CSV et génération de graphiques SVG.

Aucune bibliothèque graphique externe n'est nécessaire : les graphiques sont
produits au format SVG afin d'être lisibles dans un navigateur et un rapport.
"""

import csv
import html
import math
import os


def _mean(values):
    return sum(values) / len(values) if values else None


def _std(values):
    if len(values) < 2:
        return 0.0
    avg = _mean(values)
    return math.sqrt(sum((value - avg) ** 2 for value in values) / (len(values) - 1))


def _group(rows, group_fields):
    groups = {}
    for row in rows:
        key = tuple(row.get(field, "") for field in group_fields)
        groups.setdefault(key, []).append(row)
    return groups


def family_of(instance):
    name = instance.upper()
    if name.startswith("RAND"):
        return "Random"
    for family in ("CYC", "CLR", "STS"):
        if name.startswith(family):
            return family
    if name.startswith("E.") or name.startswith("E-"):
        return "E"
    return "Other"


def aggregate(rows, group_fields=("family", "algorithm"), value_field="gap_pct"):
    """Calcule moyenne, écart-type et nombre de répétitions."""
    result = []
    usable = []
    for row in rows:
        copy = dict(row)
        copy["family"] = family_of(row.get("instance", ""))
        value = row.get(value_field)
        if value not in (None, ""):
            try:
                copy["_value"] = float(value)
                usable.append(copy)
            except ValueError:
                pass

    for key, group in _group(usable, ("family", "algorithm") if group_fields == ("family", "algorithm") else group_fields).items():
        values = [row["_value"] for row in group]
        item = dict(zip(group_fields, key))
        item.update({"mean": _mean(values), "std": _std(values), "count": len(values),
                     "min": min(values), "max": max(values), "value_field": value_field})
        result.append(item)
    return sorted(result, key=lambda item: tuple(str(item.get(field, "")) for field in group_fields))


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def write_summary(rows, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    gap = aggregate(rows, value_field="gap_pct")
    time = aggregate(rows, value_field="time_s")
    fields = ["family", "algorithm", "value_field", "mean", "std", "count", "min", "max"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in gap + time:
            writer.writerow({field: item.get(field, "") for field in fields})


def svg_bar_chart(items, title, y_label, path):
    """Barres avec barres d'erreur = écart-type de l'échantillon."""
    width, height = 900, 520
    left, right, top, bottom = 90, 25, 60, 100
    chart_width = width - left - right
    chart_height = height - top - bottom

    values = [item["mean"] for item in items]
    stds = [item["std"] for item in items]
    if not values:
        values = [0]
        stds = [0]

    low = min(0.0, *(value - std for value, std in zip(values, stds)))
    high = max(0.0, *(value + std for value, std in zip(values, stds)))
    if high == low:
        high = low + 1.0

    def x_position(index):
        step = chart_width / len(items) if items else chart_width
        return left + step * (index + 0.5)

    def y_position(value):
        return top + (high - value) / (high - low) * chart_height

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="{width/2}" y="28" text-anchor="middle" font-family="sans-serif" font-size="18">{html.escape(title)}</text>',
             f'<text x="18" y="{height/2}" text-anchor="middle" font-family="sans-serif" font-size="13" transform="rotate(-90 18 {height/2})">{html.escape(y_label)}</text>']

    zero = y_position(0)
    parts.append(f'<line x1="{left}" y1="{zero:.1f}" x2="{width-right}" y2="{zero:.1f}" stroke="#666"/>')

    step = chart_width / len(items) if items else chart_width
    bar_width = min(60, step * 0.55)
    palette = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2"]

    for index, item in enumerate(items):
        x = x_position(index)
        y = y_position(item["mean"])
        top_y = y_position(item["mean"] + item["std"])
        bottom_y = y_position(item["mean"] - item["std"])
        color = palette[index % len(palette)]
        parts.append(f'<rect x="{x-bar_width/2:.1f}" y="{min(y, zero):.1f}" width="{bar_width:.1f}" height="{abs(zero-y):.1f}" fill="{color}"/>')
        parts.append(f'<line x1="{x:.1f}" y1="{top_y:.1f}" x2="{x:.1f}" y2="{bottom_y:.1f}" stroke="#222" stroke-width="2"/>')
        parts.append(f'<line x1="{x-bar_width*0.25:.1f}" y1="{top_y:.1f}" x2="{x+bar_width*0.25:.1f}" y2="{top_y:.1f}" stroke="#222" stroke-width="2"/>')
        parts.append(f'<line x1="{x-bar_width*0.25:.1f}" y1="{bottom_y:.1f}" x2="{x+bar_width*0.25:.1f}" y2="{bottom_y:.1f}" stroke="#222" stroke-width="2"/>')
        label = f'{item["family"]} / {item["algorithm"]}'
        parts.append(f'<text x="{x:.1f}" y="{height-bottom+25:.1f}" text-anchor="end" font-family="sans-serif" font-size="11" transform="rotate(-35 {x:.1f} {height-bottom+25:.1f})">{html.escape(label)}</text>')
        parts.append(f'<text x="{x:.1f}" y="{min(y, top_y)-7:.1f}" text-anchor="middle" font-family="sans-serif" font-size="11">{item["mean"]:.2f}</text>')

    for tick in range(5):
        value = low + (high - low) * tick / 4
        y = y_position(value)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" stroke="#ddd"/>')
        parts.append(f'<text x="{left-8}" y="{y+4:.1f}" text-anchor="end" font-family="sans-serif" font-size="11">{value:.2f}</text>')

    parts.append('</svg>')
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(parts))


def analyze(csv_paths, output_dir):
    """Analyse plusieurs CSV et écrit un résumé plus quatre graphiques."""
    rows = []
    for path in csv_paths:
        rows.extend(read_csv(path))

    os.makedirs(output_dir, exist_ok=True)
    ok_rows = [row for row in rows if row.get("status") == "ok"]
    gap = aggregate(ok_rows, value_field="gap_pct")
    time = aggregate(ok_rows, value_field="time_s")

    write_summary(rows, os.path.join(output_dir, "summary.csv"))
    svg_bar_chart(gap, "Écart moyen à la référence par famille", "Écart (%)", os.path.join(output_dir, "gap_by_family.svg"))
    svg_bar_chart(time, "Temps moyen par famille", "Temps (secondes)", os.path.join(output_dir, "time_by_family.svg"))

    families = sorted({item["family"] for item in gap + time})
    for family in families:
        family_gap = [item for item in gap if item["family"] == family]
        family_time = [item for item in time if item["family"] == family]
        svg_bar_chart(family_gap, f"Écart moyen — {family}", "Écart (%)", os.path.join(output_dir, f"gap_{family.lower()}.svg"))
        svg_bar_chart(family_time, f"Temps moyen — {family}", "Temps (secondes)", os.path.join(output_dir, f"time_{family.lower()}.svg"))

    return {"rows": len(rows), "feasible_runs": len(ok_rows), "summary": os.path.join(output_dir, "summary.csv")}
