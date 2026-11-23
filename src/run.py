"""Build the Roman salt interactive: status tables, traced roads and the HTML page.

    python src/run.py [--config config/config.yaml]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import load_config, write_csv, write_geojson, write_provenance  # noqa: E402
from route import build_routes  # noqa: E402
from sites import build_sites  # noqa: E402
from stations import build_stations  # noqa: E402
from web import build_page  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/config.yaml")
    cfg = load_config(ap.parse_args().config)

    sites_df, sites_gdf = build_sites(cfg)
    stations = build_stations(cfg)
    routes, legs, stations, roads_m = build_routes(cfg, stations, sites_gdf)

    outs = {
        "sites_csv": write_csv(sites_df, "salt_sites_status.csv", cfg),
        "sites_geojson": write_geojson(sites_gdf, "salt_sites_status.geojson", cfg),
        "stations_csv": write_csv(stations.drop(columns="geometry"), "via_salaria_stations_status.csv", cfg),
        "stations_geojson": write_geojson(stations, "via_salaria_stations_status.geojson", cfg),
        "routes_geojson": write_geojson(routes, "routes.geojson", cfg),
        "legs_csv": write_csv(legs, "route_legs.csv", cfg),
        "page": build_page(cfg, sites_df, stations, routes, legs, roads_m),
    }
    notes = {
        "sites_total": int(len(sites_df)),
        "sites_mapped": int(len(sites_gdf)),
        "sites_unmapped": sites_df.loc[sites_df.lat_used.isna(), "site_id"].tolist(),
        "status_counts": sites_df.now_status.value_counts().to_dict(),
        "routes": routes.drop(columns="geometry").to_dict("records"),
        "flagged_legs": legs[legs.flag].to_dict("records"),
        "licences": "Road lines derive from DARMC (CC BY-NC 3.0); Pleiades points CC BY 3.0; "
                    "GeoNames points CC BY 4.0; Natural Earth public domain.",
    }
    outs["provenance"] = write_provenance(cfg, outs, notes)
    for k, v in notes.items():
        if k != "routes":
            print(f"{k}: {v}")
    for r in notes["routes"]:
        print({k: v for k, v in r.items() if k != "darmc_objectids"})


if __name__ == "__main__":
    main()
