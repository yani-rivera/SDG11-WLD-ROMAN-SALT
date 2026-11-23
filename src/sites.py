"""Salt sites: join the user's table with the status catalog and resolve coordinates.

Coordinate methods (column coord_method in catalogs/site_status.csv):
  pleiades        Pleiades representative point of the site's own Pleiades place
  pleiades_proxy  Pleiades point of the ancient town the site belongs to (not the works itself)
  geonames        GeoNames point of the modern town (lutangar/cities.json mirror, CC BY 4.0)
  published_point coordinate written in the catalog, with its source in coord_ref
  none            not resolved; the site is listed but not mapped
"""
import json
import unicodedata

import geopandas as gpd
import pandas as pd

from common import p

STATUS_LABELS = {
    "making_salt": "Still making salt",
    "heritage": "Salt heritage (museum, park, spa or show mine)",
    "archaeology": "Archaeological site",
    "closed": "Closed recently",
    "not_checked": "Not checked yet",
}


def _norm(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def load_pleiades(cfg):
    pl = pd.read_csv(p(cfg["inputs"]["pleiades_places"]), dtype=str).set_index("id")
    return pl


def load_geonames(cfg):
    with open(p(cfg["inputs"]["geonames_cities"]), encoding="utf-8") as f:
        return json.load(f)


def geonames_lookup(cities, ref):
    """ref looks like 'Vigo (ES)'."""
    name, cc = ref.rsplit("(", 1)
    name, cc = _norm(name.strip()), cc.strip(" )")
    hits = [c for c in cities if c["country"] == cc and _norm(c["name"]) == name]
    if len(hits) != 1:
        raise ValueError(f"GeoNames lookup for {ref!r} returned {len(hits)} hits")
    return float(hits[0]["lat"]), float(hits[0]["lng"]), "geonames:" + ref


def resolve_coords(row, pl, cities):
    m = row["coord_method"]
    if m in ("pleiades", "pleiades_proxy"):
        rec = pl.loc[str(row["coord_ref"])]
        return (float(rec.representative_latitude), float(rec.representative_longitude),
                f"pleiades:{row['coord_ref']} ({rec.title})")
    if m == "geonames":
        return geonames_lookup(cities, row["coord_ref"])
    if m == "published_point":
        return float(row["lat"]), float(row["lon"]), "published:" + str(row["coord_ref"])
    return None, None, "unresolved"


def build_sites(cfg):
    base = pd.read_csv(p(cfg["inputs"]["sites_csv"]), dtype=str, encoding="utf-8-sig")
    extra = pd.read_csv(p(cfg["catalogs"]["extra_sites"]), dtype=str)
    base = pd.concat([base, extra], ignore_index=True)
    status = pd.read_csv(p(cfg["catalogs"]["site_status"]), dtype=str).fillna("")

    missing = set(base.site_id) - set(status.site_id)
    if missing:
        raise ValueError(f"Sites without a status row: {sorted(missing)}")

    df = base.merge(status, on="site_id", how="left", validate="one_to_one")
    pl, cities = load_pleiades(cfg), load_geonames(cfg)
    coords = df.apply(lambda r: resolve_coords(r, pl, cities), axis=1, result_type="expand")
    df[["lat_used", "lon_used", "coord_source"]] = coords
    df["now_label"] = df.now_status.map(STATUS_LABELS)
    df = df.drop(columns=["lat", "lon"])

    mapped = df.dropna(subset=["lat_used"])
    gdf = gpd.GeoDataFrame(mapped, geometry=gpd.points_from_xy(mapped.lon_used, mapped.lat_used),
                           crs="EPSG:4326")
    return df, gdf
