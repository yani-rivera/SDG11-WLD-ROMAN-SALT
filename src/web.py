"""Pack the outputs into one self-contained HTML page (data inlined, d3 from cdnjs)."""
import json
import math

import geopandas as gpd
from shapely.geometry import box, mapping

from common import p

ROUND = 4


def _round_coords(obj):
    if isinstance(obj, (list, tuple)):
        if obj and isinstance(obj[0], (int, float)):
            return [round(v, ROUND) for v in obj[:2]]
        return [_round_coords(o) for o in obj]
    return obj


def _feature(geom, props):
    g = mapping(geom)
    return {"type": "Feature", "properties": props,
            "geometry": {"type": g["type"], "coordinates": _round_coords(g["coordinates"])}}


def _clean(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    return v


def land_layer(cfg):
    c = gpd.read_file(p(cfg["inputs"]["countries_gpkg"]), layer=cfg["inputs"]["countries_layer"])
    c = c.to_crs("EPSG:4326")[["ADMIN", "geometry"]]
    c["geometry"] = c.geometry.simplify(cfg["web"]["land_simplify_deg"], preserve_topology=True)
    clip = box(-25, 15, 110, 62)
    c = c[c.intersects(clip)].copy()
    c["geometry"] = c.geometry.intersection(clip)
    return [_feature(g, {"n": a}) for a, g in zip(c.ADMIN, c.geometry) if not g.is_empty]


def road_layer(cfg, roads_m):
    r = roads_m.copy()
    r["geometry"] = r.geometry.simplify(cfg["web"]["road_simplify_m"])
    r = r.to_crs("EPSG:4326")
    major = r.CLASS.astype(str).str.lower().str.startswith("maj")
    return [_feature(g, {"m": int(m)}) for g, m in zip(r.geometry, major) if not g.is_empty]


def build_page(cfg, sites_df, stations, routes, legs, roads_m):
    site_cols = ["site_id", "location", "modern_country", "roman_production_grade",
                 "roman_production_grade_label", "date_v2", "map_layer", "location_uncertainty_m",
                 "now_status", "now_label", "now_note", "checked", "status_sources",
                 "coord_method", "coord_source", "coord_note", "reference_dois_v2", "pleiades_uris"]
    sites = []
    for r in sites_df.itertuples():
        props = {c: _clean(getattr(r, c)) for c in site_cols}
        lat, lon = r.lat_used, r.lon_used
        props["lat"] = None if lat is None or (isinstance(lat, float) and math.isnan(lat)) else round(lat, ROUND)
        props["lon"] = None if props["lat"] is None else round(lon, ROUND)
        sites.append(props)

    st_cols = ["pleiades_id", "pleiades_title", "pleiades_uri", "then", "now_status", "now_label",
               "now_place", "now_note", "on_main_route", "status_sources", "route_km",
               "distance_to_route_m"]
    stations_out = [_feature(g, {c: _clean(getattr(r, c)) for c in st_cols})
                    for r, g in zip(stations.itertuples(), stations.geometry)]
    routes_out = [_feature(g, {"leg": l, "km": k, "pct": pc})
                  for l, k, pc, g in zip(routes.leg, routes.length_km, routes.pct_length_certain,
                                         routes.geometry)]
    data = {
        "meta": {"title": cfg["title"], "subtitle": cfg["subtitle"], "version": cfg["version"]},
        "land": land_layer(cfg),
        "roads": road_layer(cfg, roads_m),
        "routes": routes_out,
        "stations": stations_out,
        "sites": sites,
    }
    tpl = p("web/template.html").read_text(encoding="utf-8")
    html = tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    out = p(cfg["outputs"]["dir"]) / "index.html"
    out.write_text(html, encoding="utf-8")
    return out
