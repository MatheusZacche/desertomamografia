# -*- coding: utf-8 -*-
"""Dissolve a malha municipal em malha por UF (27 estados) -> data/estados.geojson.
Feature.id = sigla da UF. Executar uma vez."""
import json
from collections import defaultdict
from pathlib import Path

from shapely.geometry import shape, mapping
from shapely.ops import unary_union

DATA = Path(__file__).parent / "data"
COD_SIGLA = {"11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP",
             "17": "TO", "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB",
             "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES",
             "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS", "50": "MS",
             "51": "MT", "52": "GO", "53": "DF"}

mun = json.loads((DATA / "municipios.geojson").read_text(encoding="utf-8"))
grupos = defaultdict(list)
for f in mun["features"]:
    cod = str(f["properties"]["id"])[:2]
    if cod in COD_SIGLA:
        grupos[cod].append(shape(f["geometry"]).buffer(0))

feats = []
centros = {}
for cod, geoms in grupos.items():
    sigla = COD_SIGLA[cod]
    u = unary_union(geoms).simplify(0.02, preserve_topology=True)
    minx, miny, maxx, maxy = u.bounds
    c = u.representative_point()
    span = max(maxx - minx, maxy - miny)
    centros[sigla] = {"lat": round(c.y, 3), "lon": round(c.x, 3),
                      "span": round(span, 3)}
    feats.append({"type": "Feature", "id": sigla,
                  "properties": {"id": sigla, "sigla": sigla}, "geometry": mapping(u)})

est = {"type": "FeatureCollection", "features": feats}
json.dump(est, open(DATA / "estados.geojson", "w", encoding="utf-8"), separators=(",", ":"))
json.dump(centros, open(DATA / "estados_centros.json", "w", encoding="utf-8"))
print(f"estados: {len(feats)} | tamanho: {(DATA/'estados.geojson').stat().st_size/1024:.0f} KB")
