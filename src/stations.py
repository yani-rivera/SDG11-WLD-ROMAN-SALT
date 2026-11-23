"""Via Salaria stations: the user's GeoPackage joined with the station status catalog."""
import geopandas as gpd
import pandas as pd

from common import p

STATUS_LABELS = {
    "living_town": "Living town",
    "archaeological_site": "Archaeological site",
    "monument": "Surviving monument",
    "in_rome": "Inside Rome",
    "approximate": "Approximate location",
    "lost": "Lost (location unknown)",
}


def build_stations(cfg):
    st = gpd.read_file(p(cfg["inputs"]["stations_gpkg"]), layer=cfg["inputs"]["stations_layer"])
    st["pleiades_id"] = st.pleiades_id.astype(str)
    cat = pd.read_csv(p(cfg["catalogs"]["station_status"]), dtype=str).fillna("")
    missing = set(st.pleiades_id) - set(cat.pleiades_id)
    if missing:
        raise ValueError(f"Stations without a status row: {sorted(missing)}")
    st = st.merge(cat, on="pleiades_id", how="left", validate="one_to_one")
    st["now_label"] = st.now_status.map(STATUS_LABELS)
    return st.to_crs("EPSG:4326")
