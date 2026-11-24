"""Trace roads on the DARMC Roman Road Network by shortest path between waypoints.

DARMC roads carry no names, so every vertex becomes a graph node (vertices within
node_snap_m are merged), each waypoint is snapped to its nearest node, and consecutive
waypoints are joined by the shortest path. Same method as roman_salt_enrich v1.2.0.

Since v1.1.0 each traced line is also split into pieces by DARMC's CERTAINTY field, so the
map can draw the stretches whose course is marked certain differently from the rest.
"""
import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point
from shapely.ops import linemerge

from common import p


def load_roads(cfg):
    roads = gpd.read_file(p(cfg["inputs"]["darmc_roads"]))
    return roads.to_crs(cfg["route"]["metric_crs"])


def build_graph(roads, snap_m):
    coords, edges = [], []
    for idx, geom in zip(roads.index, roads.geometry):
        parts = getattr(geom, "geoms", [geom])
        for part in parts:
            xy = np.asarray(part.coords)[:, :2]
            start = len(coords)
            coords.extend(map(tuple, xy))
            for i in range(len(xy) - 1):
                edges.append((start + i, start + i + 1, idx))
    coords = np.array(coords)
    # merge vertices within snap_m
    tree = cKDTree(coords)
    parent = np.arange(len(coords))
    for i, j in tree.query_pairs(snap_m):
        ri, rj = parent[i], parent[j]
        while parent[ri] != ri:
            ri = parent[ri]
        while parent[rj] != rj:
            rj = parent[rj]
        if ri != rj:
            parent[rj] = ri
    for i in range(len(parent)):
        r = i
        while parent[r] != r:
            r = parent[r]
        parent[i] = r
    G = nx.Graph()
    for a, b, idx in edges:
        na, nb = parent[a], parent[b]
        if na == nb:
            continue
        w = float(np.hypot(*(coords[a] - coords[b])))
        if not G.has_edge(na, nb) or G[na][nb]["weight"] > w:
            G.add_edge(na, nb, weight=w, seg=idx)
    node_ids = np.array(sorted(G.nodes))
    return G, coords, node_ids


def is_certain(values):
    """DARMC CERTAINTY -> bool (the field is stored as Yes/No text)."""
    return values.astype(str).str.strip().str.lower().isin(["yes", "y", "1", "true"])


def split_by_certainty(G, coords, path_nodes, certain_by_seg):
    """Cut a node path into runs of edges that share the same certainty."""
    pieces, run, run_cert, run_segs = [], [path_nodes[0]], None, set()
    for u, v in zip(path_nodes[:-1], path_nodes[1:]):
        seg = G[u][v]["seg"]
        c = bool(certain_by_seg[seg])
        if run_cert is not None and c != run_cert:
            pieces.append((run, run_cert, run_segs))
            run, run_segs = [u], set()
        run.append(v)
        run_segs.add(seg)
        run_cert = c
    pieces.append((run, run_cert, run_segs))
    return [(LineString([coords[n] for n in nodes]), c, segs) for nodes, c, segs in pieces]


def snap(G, coords, node_ids, pt):
    tree = cKDTree(coords[node_ids])
    d, i = tree.query([pt.x, pt.y])
    return int(node_ids[i]), float(d)


def trace_leg(G, coords, node_ids, roads, waypoints, flag_km):
    nodes, legs, path_nodes = [], [], []
    for wp in waypoints.itertuples():
        n, d = snap(G, coords, node_ids, wp.geometry)
        nodes.append((n, d, wp))
    segs = set()
    for (a, da, wa), (b, db, wb) in zip(nodes[:-1], nodes[1:]):
        path = nx.shortest_path(G, a, b, weight="weight")
        length = nx.path_weight(G, path, weight="weight")
        segs.update(G[u][v]["seg"] for u, v in zip(path[:-1], path[1:]))
        path_nodes.extend(path if not path_nodes else path[1:])
        legs.append({"from": wa.label, "to": wb.label, "km": round(length / 1000, 2),
                     "snap_from_km": round(da / 1000, 2), "snap_to_km": round(db / 1000, 2),
                     "flag": (da / 1000 > flag_km) or (db / 1000 > flag_km)})
    line = LineString([coords[n] for n in path_nodes])
    used = roads.loc[sorted(segs)]
    certain_by_seg = is_certain(roads.CERTAINTY)
    pieces = split_by_certainty(G, coords, path_nodes, certain_by_seg)
    # share of the traced line itself (not of the whole DARMC segments it touches)
    certain_m = sum(ln.length for ln, c, _ in pieces if c)
    pct_certain = round(100 * certain_m / line.length, 1)
    pieces = [{"certain": c, "length_km": round(ln.length / 1000, 2),
               "darmc_objectids": ",".join(str(int(roads.loc[i, "OBJECTID"])) for i in sorted(sg)),
               "geometry": ln} for ln, c, sg in pieces]
    return line, pd.DataFrame(legs), sorted(map(int, used.OBJECTID)), pct_certain, pieces


def build_routes(cfg, stations, sites_gdf):
    roads = load_roads(cfg)
    G, coords, node_ids = build_graph(roads, cfg["route"]["node_snap_m"])
    wps = pd.read_csv(p(cfg["catalogs"]["route_waypoints"]), dtype=str)
    st = stations.to_crs(cfg["route"]["metric_crs"]).set_index("pleiades_id")
    si = sites_gdf.to_crs(cfg["route"]["metric_crs"]).set_index("site_id")

    def geom_for(ref):
        if ref in st.index:
            return st.loc[ref].geometry
        return si.loc[ref].geometry

    feats, legs_all, piece_feats = [], [], []
    for leg, grp in wps.groupby("leg", sort=False):
        grp = grp.sort_values("order", key=lambda s: s.astype(int))
        wp = gpd.GeoDataFrame(grp, geometry=[geom_for(r) for r in grp.pleiades_id],
                              crs=cfg["route"]["metric_crs"])
        line, legs, segs, pct, pieces = trace_leg(G, coords, node_ids, roads, wp,
                                                  cfg["route"]["flag_snap_km"])
        for i, pc in enumerate(pieces, 1):
            piece_feats.append({"leg": leg, "piece": i, **pc})
        legs.insert(0, "leg", leg)
        legs_all.append(legs)
        feats.append({"leg": leg, "length_km": round(line.length / 1000, 1),
                      "pct_length_certain": pct, "darmc_objectids": ",".join(map(str, segs)),
                      "geometry": line})
    routes = gpd.GeoDataFrame(feats, crs=cfg["route"]["metric_crs"]).to_crs("EPSG:4326")
    route_pieces = gpd.GeoDataFrame(piece_feats, crs=cfg["route"]["metric_crs"]).to_crs("EPSG:4326")

    # distance of each station to the Salaria line and position along it
    sal = next(f["geometry"] for f in feats if f["leg"] == "salaria")
    st_m = stations.to_crs(cfg["route"]["metric_crs"])
    stations = stations.copy()
    stations["distance_to_route_m"] = st_m.geometry.distance(sal).round(0).values
    stations["route_km"] = (st_m.geometry.apply(sal.project) / 1000).round(1).values
    return routes, route_pieces, pd.concat(legs_all, ignore_index=True), stations, roads
