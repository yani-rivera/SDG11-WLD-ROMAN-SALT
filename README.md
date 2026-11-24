# The Long, Short Road of Salt — interactive (v1.1.0)

An interactive map of Roman salt sites and the Via Salaria. For every place it shows what it was in Roman times and what it is today:

- **Salt sites**: still making salt, salt heritage (museum, park, spa or show mine), archaeological site, closed recently, or not checked yet.
- **Via Salaria stations**: living town, archaeological site, surviving monument, inside Rome, approximate place, or lost.

The page has three views. *Via Salaria* shows the traced road from Rome to the Adriatic, plus the stretch from the salt works to Rome. The road is solid where DARMC marks its course as certain and dashed where it is uncertain; the stretch from the salt works is dotted because it is a stand-in path. *Across the empire* shows the salt sites. *As far as Tibet* adds the Yanjing salt terraces as a far-away comparison.

## Run

```
python src/run.py --config config/config.yaml
```

Requires Python 3.10+, geopandas, pyogrio, shapely, networkx, scipy, pandas, pyyaml.

The DARMC roads are licensed CC BY-NC 3.0 and are **not redistributed** in this package. Put `roman_roads_v2008.gpkg` in `external/darmc/`. The Pleiades and GeoNames inputs are cloned from GitHub (see Data); set their paths in `config/config.yaml`.

## Layout

| Path | What it is |
|---|---|
| `config/config.yaml` | inputs, catalogs, routing and web settings, script version |
| `data/` | your inputs: `saltcities.csv`, `viasalaria.gpkg`, `roman.gpkg` (Natural Earth countries, used as the base map) |
| `catalogs/site_status.csv` | present-day status of each salt site, with sources and the coordinate method |
| `catalogs/station_status.csv` | then/now status of each Via Salaria station, with sources |
| `catalogs/route_waypoints.csv` | waypoints, in order, for the traced roads |
| `catalogs/extra_sites.csv` | sites added on top of `saltcities.csv` (TB001, Yanjing) |
| `src/` | `common.py` (config, outputs, provenance), `sites.py`, `stations.py`, `route.py`, `web.py`, `run.py` |
| `web/template.html` | page template; the data is inlined at build time |
| `out/` | outputs (CSV in utf-8-sig) and `provenance.json` |

## Outputs

- `salt_sites_status.csv` / `.geojson`: all 44 sites with grade, present-day status, note, sources, and the coordinate used plus where it came from. 42 are mapped.
- `via_salaria_stations_status.csv` / `.geojson`: 26 stations with then/now, km along the traced line, and distance to it.
- `routes.geojson`: `salaria` (195.6 km, Porta Salaria to Castrum Truentinum; 15.9% of the traced line marked certain in DARMC) and `salt_to_rome` (27.2 km, Le Vignole to Porta Salaria).
- `route_pieces.geojson` / `.csv` (new in v1.1.0): each traced line cut into stretches of equal DARMC certainty, with `leg`, `piece` (order from the start of the leg), `certain`, `length_km` and the DARMC `OBJECTID`s. The Via Salaria has two pieces: the first 31.1 km out of Rome are marked certain, the remaining 164.5 km to the Adriatic are not.
- `route_legs.csv`: length and waypoint snap distances for each leg. Legs with a snap over 2.5 km are flagged. Phalacrinae is 3.6 km off the network, so its two legs are flagged.
- `index.html`: the interactive page.
- `provenance.json`: script version, run time, Pleiades snapshot commit, SHA-256 of every input and catalog, and counts.

## Methods

**Status checks.** Each site's present-day status was checked against web sources (23 Nov 2026), listed row by row in `catalogs/site_status.csv`. `checked` is `yes` when a source states the present status directly. It is `partly` when the source only describes the place, or only one side of it (for example, an ancient city with salt making today not checked). It is `no` when nothing was checked yet; those 13 sites are marked *not checked* on the map.

**Coordinates.** `saltcities.csv` has no coordinates, so each site's point comes from one of these (column `coord_method`):

- `pleiades`: the site's own Pleiades place.
- `pleiades_proxy`: the Pleiades point of the ancient town the site belongs to, not the salt works itself.
- `geonames`: the modern town point.
- `published_point`: a point from a cited page (BirdLife IBA centre, showcaves.com, Wikipedia).

The stated `location_uncertainty_m` from your table is kept. Two sites, Pata (DA006) and Domnești (DA008), match several Romanian villages, so they are listed but not mapped until a coordinate is supplied. The Yanjing marker sits at the Markam county seat (Gartog); the salt terraces are about 100 km south along the river.

**Road tracing.** DARMC roads carry no names. The road is traced by routing: every vertex becomes a graph node (vertices within 50 m are joined), each waypoint is snapped to its nearest node, and consecutive waypoints are joined by the shortest path. This is the same method as `roman_salt_enrich` v1.2.0, and it gives the same 195.6 km. The usual figure for the ancient road is 242 km; DARMC straightens bends. The `salt_to_rome` leg is the shortest DARMC path from the salt works to Rome. It stands in for the Via Campana / Portuensis and is not a traced named road.

**Road certainty.** DARMC digitised the roads of the Barrington Atlas and classes each segment as certain or uncertain (field `CERTAINTY`). Each edge of the traced path keeps the segment it came from, and consecutive edges with the same value are joined into one piece. The page draws certain pieces solid and uncertain ones dashed. Read "uncertain" as "the drawn course is not confirmed", not as "the road is invented". The `salt_to_rome` leg is always drawn dotted, whatever its segments say, because the whole path is a stand-in. This is about where the road ran; the A–E grades are about the evidence for Roman salt making at each site, and the two are kept apart in the legend.

Since v1.1.0 the share marked certain is measured along the traced line itself (31.1 of 195.6 km, 15.9%). v1.0.x measured it over the full length of every DARMC segment the line touched, which gave 15.3%. The road and its length are unchanged.

## Data

McCormick, M., Huang, G., Zambotti, G., & Lavash, J. (2013). Roman Road Network (version 2008). DARMC Scholarly Data Series, Data Contribution Series #2013-5. Center for Geographic Analysis, Harvard University. CC BY-NC 3.0.

Pleiades: A Gazetteer of Past Places. https://pleiades.stoa.org. Bulk data from github.com/isawnyu/pleiades.datasets: the original map used snapshot commit 36be7e8 (20 Nov 2026), accessed 21 Nov 2026; this interactive uses snapshot commit 9662ecb (23 Nov 2026), accessed 23 Nov 2026. CC BY 3.0.

Talbert, R. J. A. (Ed.). (2000). Barrington Atlas of the Greek and Roman World. Princeton University Press. (Cited through Pleiades and DARMC.)

Natural Earth. 1:50m Admin 0 Countries. Public domain. (Base map, from `roman.gpkg`.)

GeoNames, via lutangar/cities.json (github.com/lutangar/cities.json), accessed 23 Nov 2026. CC BY 4.0. (Town points for sites without a Pleiades point.)

Roads: CC BY-NC 3.0. The traced lines and the page that shows them are therefore non-commercial.

## Literature

Marzano, A. (2024). Marine salt production in the Roman world: The salinae and their ownership. Quaternary Science Reviews, 336, 108776. https://doi.org/10.1016/j.quascirev.2024.108776

Attema, P., Alessandri, L., Bulian, F., Sevink, J., & Sotgia, A. (2025). Production and demand of salt in ancient Italy from the Bronze Age to the Roman period. In P. N. Eubanks et al. (Eds.), Meridians of Salt. Springer. https://doi.org/10.1007/978-3-031-96692-7_11

Grossi, M. C., Sivilli, S., Arnoldus-Huyzendveld, A., Facciolo, A., Rinaldi, M. L., Ruggeri, D., & Morelli, C. (2015). A complex relationship between human and natural landscape: A multidisciplinary approach to the study of the Roman saltworks in "Le Vignole-Interporto" (Maccarese, Fiumicino-Roma). In R. Brigand & O. Weller (Eds.), Archaeology of Salt: Approaching an Invisible Past (pp. 83–101). Sidestone Press.

Alessandri, L., Attema, P. A. J., Bulian, F., Sevink, J., De Neef, W., Baiocchi, V., et al. (2024). Salt in Late Iron Age Italy. A multidisciplinary approach to the exploration of Italy's coastal exploitation sites: Piscina Torta (Ostia, Rome) case study. Journal of Archaeological Science: Reports. https://doi.org/10.1016/j.jasrep.2023.104361

Bulian, F., Alessandri, L., Attema, P., & Sevink, J. (2024). Bronze Age to Roman period salt production in the coastal areas of peninsular Italy: Palaeoenvironments, production methods and archaeological evidence. Quaternary Science Reviews, 344, 108930. https://doi.org/10.1016/j.quascirev.2024.108930

Currás Refojos et al. (2024), QSR 339, 108832, https://doi.org/10.1016/j.quascirev.2024.108832. Source for O Areal, Angeiras, Bijeca, Elaia, Añana, Prado del Rey and Bas-Lauvert.

Mihailescu-Bîrliba (2018), https://doi.org/10.14795/j.v5i4.347. Source for Ocna Mureș, Domnești, Ocna Dejului and the other Romanian sites.

Seghedi, Rădan & Briceag (2021), Geo-Eco-Marina 27, 153–182, https://doi.org/10.5281/zenodo.5795093. Source for Turda, Praid and the Romanian checks.

Ergün, N., & Arslan, N. (2026). Antik Çağ'ın tuz üretim merkezi: Troas Tragasai/Tragasae tuzlası. MANAS Sosyal Araştırmalar Dergisi, 15(1), 329–350. https://doi.org/10.33206/mjss.1775301 (Tragasai / Tuzla.)

## Sources for present-day status (checked 23 Nov 2026)

### Salt sites

| Site | Status | Sources |
|---|---|---|
| MZ001 O Areal (Vigo) | Salt heritage: Salinae archaeological centre | El Español, "Salinae en la calle Rosalía de Castro" (2020), https://www.elespanol.com/treintayseis/cultura/conoce-vigo/20201028/salinae-anos-historia-vigo-pies/531698281_0.html ; Turismo de Vigo, https://turismodevigo.org/en/salinae |
| MZ003 Vignole-Interporto | Archaeological site | Grossi et al. (2015), record at https://zenon.dainst.org/Record/001436710/Description |
| MZ005 Piscina Torta | Archaeological site | Pleiades 423002; Alessandri et al. (2024) |
| MZ007 Caralis (Cagliari) | Salt heritage: Molentargius production closed 1985, park since 1999 | Sardegna Cultura, https://www.sardegnacultura.it/en/articles/cagliari-parco-naturale-regionale-molentargius-saline |
| MZ012 Tragasai / Tuzla | Not confirmed | Ergün & Arslan (2026) |
| MZ018 Tahadart | Not confirmed; point = IBA centre | BirdLife International (2024), Oued Tahadart IBA factsheet, https://datazone.birdlife.org/site/factsheet/oued-tahadart-iba-morocco |
| MZ023 San Fernando / Cádiz | Still making salt | Diario Bahía de Cádiz (Feria de las Salinas), https://www.diariobahiadecadiz.com/sin-seccion/la-primera-feria-de-las-salinas-este-fin-de-semana-en-la-isla-reivindica-estos-enclaves-como-motor-de-desarrollo-en-la-bahia ; IUCN (MedArtSal), https://iucn.org/es/node/38350 ; Diario Bahía de Cádiz (El Estanquillo), https://diariobahiadecadiz.com/san-fernando/la-salina-el-estanquillo-apuesta-por-recuperar-la-produccion-salinera-y-junto-al-ayuntamiento-isleno-explorar-otros-usos-turisticos-paralelos |
| MZ024 Kaiseraugst / Schweizerhalle | Still making salt (Schweizerhalle) | cash.ch (Schweizer Salinen, Riburg new build; Schweizerhalle production to at least 2032), https://www.cash.ch/news/schweizer-salinen-planen-neubau-der-saline-riburg-im-aargau-919900 ; Historisches Lexikon der Schweiz, "Salz", https://hls-dhs-dss.ch/de/articles/014041/2020-03-12/ ; point: showcaves.com, https://showcaves.com/english/ch/mines/Schweizerhalle.html |
| GX002 Bijeca (Medulin) | Archaeological site: underwater trail | Croatia Week (6 Jul 2026), https://www.croatiaweek.com/roman-saltworks-medulin-underwater-archaeological-trail/ |
| GX003 Cervia | Still making salt | Comune di Cervia, https://www.comunecervia.it/progetti/salt-cities-network/le-citta-della-rete/cervia.html ; Gambero Rosso, https://www.gamberorosso.it/notizie/attualita/saliturismo-viaggio-esperienziale/ |
| GX005 Prado del Rey | Still making salt (Hortales) | Fuerte Hoteles blog, https://blog.fuertehoteles.com/en/?p=29452 |
| GX006 Añana | Still making salt | Gasteiz Hoy (2024 harvest), https://www.gasteizhoy.com/la-sal-de-anana-batira-record-este-verano-con-una-cosecha-de-175-toneladas/ ; Turismo Euskadi, https://turismo.euskadi.eus/es/patrimonio-cultural/valle-salado-de-salinas-de-anana/webtur00-content/es/ ; point: Wikipedia, "Salt Valley of Añana" |
| DA001 Ocna Mureș | Still making salt (extraction plant; mine flooded 1978) | Wikipedia, "Ocna Mureș", https://en.wikipedia.org/wiki/Ocna_Mure%C8%99 |
| DA002 Turda | Salt heritage: tourist mine | Economica.net, https://www.economica.net/turismul-aduce-minelor-de-sare-venituri-de-milioane-de-euro-anual-top-si-galerie-foto_105151.html/amp |
| DA003 Ocna Sibiului | Salt heritage: salt-lake spa | Știrile ProTV, https://stirileprotv.ro/stiri/actualitate/litoralul-ardealului-locul-unde-apa-este-mereu-calda-care-sunt-preturile.html |
| DA004 Cojocna | Salt heritage (partly checked) | UBB Cluj doctoral thesis, https://teze.doctorat.ubbcluj.ro/doctorat/teza/fisier/587 |
| DA007 Ocna Dejului | Still making salt | Actual de Cluj (14 Jan 2026), https://actualdecluj.ro/record-de-livrare-a-sarii-pentru-ocna-inca-functionala-din-cluj-7650-tone-intr-o-zi/ |
| DA009 Ocnele Mari | Salt heritage: show mine | showcaves.com, https://showcaves.com/english/ro/mines/OcneleMari.html ; Romania Insider, https://www.romania-insider.com/index%2ephp/romania-travel-salt-mines |
| DA011 Sovata | Salt heritage: salt lakes and spa | CORE, salt springs of Mureș county, https://core.ac.uk/download/25786235.pdf ; Romania Tourism spa list, https://romaniatourism.com/pl/spa-romania-ocna-sibiului.html |
| DA012 Praid | Closed recently (flood, May 2025) | Praid mine (Wikipedia via Wikiwand), https://www.wikiwand.com/en/articles/Praid_mine ; Radio Romania International (6 Jun 2025), https://www.rri.ro/en/news-and-current-affairs/today-in-the-news/situation-at-praid-salt-mine-continues-to-worsen-id896225.html |
| PL001 Middlewich | Still making salt | Wikipedia, "History of salt in Middlewich", https://en.wikipedia.org/wiki/History_of_salt_in_Middlewich ; MiningDataOnline, https://miningdataonline.com/property/809/Middlewich-Mine.aspx |
| PL002 Droitwich | Still making salt (small scale) | Worcestershire County Council, Salt and brine background document (2018), https://www.worcestershire.gov.uk/sites/default/files/2023-01/salt_and_brine_background_document_sept_2018_1_.pdf ; Droitwich Standard (2016), https://droitwichstandard.co.uk/?p=40528 |
| PL003 Salpi | Still making salt (Margherita di Savoia) | Gambero Rosso, https://www.gamberorosso.it/notizie/attualita/saliturismo-viaggio-esperienziale/ |
| PL008 Tuzla | Still making salt | Baština (national monument "Proizvodnja soli u Tuzli"), https://bastina.ba/?p=3161 ; Balkan Green Energy News, https://balkangreenenergynews.com/salt-miner-in-bih-to-build-renewable-energy-plants/ |
| PL011 Fontaines Salées | Archaeological site with museum | Lonely Planet, https://www.lonelyplanet.com/points-of-interest/fontaines-salees/1192741 ; Nature Junior 12 (2021), https://bfcnature.fr/wp-content/uploads/2023/02/nj12-75-77-fontaines-salees-ld_1649845650.pdf |
| PL016 Salins-les-Thermes | Salt heritage: thermal spa | Thermes de Brides-les-Bains press kit (2018), https://www.brides-les-bains.com/wp-content/uploads/2017/12/dp-renovation-thermes-brides-2018.pdf |
| PL017 Spina | Archaeological site; nearby Comacchio salt works closed 1984 | Po Delta Tourism, https://www.podeltatourism.it/en/attraction/102/3120 |
| TB001 Yanjing (Tibet) | Still making salt, by hand | China Daily (30 May 2023), https://www.chinadaily.com.cn/a/202305/30/WS6475a95fa310b6054fad5d09.html ; People's Daily (9 Oct 2026), https://en.people.cn/n3/2026/1009/c90000-20506544.html |

Sites marked archaeological or not checked without a source above rest on their Pleiades entry only: MZ002, MZ006, MZ009, MZ010, MZ017, GX001, GX004, GX007, DA005, DA006, DA008, DA010, PL009, PL010, PL012, PL015.

### Via Salaria stations

Then/now for every station comes from its Pleiades entry and the Barrington Atlas Directory note quoted there (links in `catalogs/station_status.csv`). Also used:

- Trismegistos Places, Eretum (Casacotta; Monterotondo marked obsolete), https://trismegistos.org/place/32733
- Tabula Peutingeriana online (KU Eichstätt): Interocrium, https://tp-online.ku.de/trefferanzeige_en.php?id=208 ; Forum Decii, https://tp-online.ku.de/trefferanzeige_en.php?id=206 ; Falacrinae, https://tp-online.ku.de/trefferanzeige_en.php?id=205 ; Surpicanum, https://tp-online.ku.de/trefferanzeige_es.php?id=203
- FAI, Castrum Truentinum, https://fondoambiente.it/luoghi/castrum-truentinum

## Licence

Code: MIT. Catalogs and outputs: CC BY-NC 4.0, because the road lines derive from DARMC (CC BY-NC 3.0). Pleiades (CC BY 3.0) and GeoNames (CC BY 4.0) points need attribution as listed above.

## Changes

- **1.1.0** (24 Nov 2026): the road is split by DARMC certainty (solid = certain, dashed = uncertain, dotted = stand-in path), with a legend entry and a note in the panel; new `route_pieces` outputs; the certain share is measured along the traced line (15.9%); the Via Salaria view fits the road into the part of the map the open legend doesn't cover.
- **1.0.1** (23 Nov 2026): first published version.

## Mobile and security checks (v1.1.0)

**Mobile.** The layout stacks below 820 px wide: map on top at 62% of the screen, reading panel below. The view buttons span the full width. The legend folds into "Legend and filters" and starts closed on phones. Sites have 16 px invisible tap areas on touch screens. Tapping a station in the table scrolls the map back into view. The page only re-fits the view when the width changes, so the phone address bar showing or hiding doesn't reset it. Line widths and dash patterns stay constant at any zoom. When the legend is open, the Via Salaria view fits the road into the free part of the map, so the solid stretch near Rome isn't hidden behind it. Checked at 390 × 844 (phone, legend open and closed) and 1366 × 820 (light and dark): no sideways scrolling, no script errors.

**Security.**
- The page holds no secrets, takes no input, stores nothing and sends nothing. All data is inlined at build time.
- The only third-party code is d3 7.8.5, pinned to an exact version on jsDelivr and checked with Subresource Integrity (`sha384-su5kReKy…`), so a changed file is refused.
- A Content-Security-Policy meta tag blocks every other script, connection, form, frame and base URL. `referrer` is set to `no-referrer`.
- All text from the catalogs is HTML-escaped before display. Source links are only shown if they are plain `http(s)` URLs, and they open with `rel="noopener noreferrer"`.
- If d3 fails to load, the page says so instead of showing a blank map.
- v1.1.0 adds no new third-party code or connections; the new legend and note are static text.
- The pipeline records the SHA-256 of every input and catalog in `provenance.json`.
