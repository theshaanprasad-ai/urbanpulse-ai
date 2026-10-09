# Data Source & Licensing Register

> **MonsoonWatch India Ingestion Catalog**  
> Comprehensive inventory of meteorological, geospatial, civic, and climate data providers.

---

## 1. Upstream Data Providers

| Provider Identifier | Source Name | Category | License / Terms of Use | Spatial Resolution | Update Cadence | Operational Limitations |
| :--- | :--- | :---: | :--- | :---: | :---: | :--- |
| `src-imd-aws` | **IMD Automatic Weather Station Network** | WEATHER | Open Government Data (OGD) License India | Point Stations (~5-10km spacing) | 15 minutes | Sparse gauge density in rapidly urbanizing peripheral suburbs. |
| `src-imd-nwp` | **IMD NCMRWF 4km Unified Model NWP Forecast** | WEATHER | IMD Open Meteorological Services | 4 km Grid | 6-hourly runs | Convective cloudburst cells (<2km extent) occasionally underpredicted in 24h totals. |
| `src-gcc-civic` | **Greater Chennai Corporation 1913 Grievance Stream** | COMPLAINTS | Municipal Open Public Grievance Records | Point / Ward Centroid | Near Real-Time | Citizen reporting exhibits socioeconomic and smartphone penetration bias. |
| `src-bhuvan` | **ISRO NRSC Bhuvan Flood Inundation & DEM** | GEOSPATIAL | ISRO Open Bhuvan Web Services (CC-BY 4.0) | 30m CartoDEM / Cartosat-1 | Seasonal / Historical | Micro-topographical curbs and flyover ramps are not fully resolved at 30m resolution. |
| `src-osm` | **OpenStreetMap Urban Features & Waterways** | GEOSPATIAL | Open Database License (ODbL) | Vector Polygons & Lines | Daily Sync | Subsurface storm drain pipe network incomplete; canals and rivers complete. |
| `src-indra` | **INDRA-CMIP6 High-Resolution Downscaled Climate Ensemble** | CLIMATE | CC-BY 4.0 Academic Research | 10 km Downscaled Grid | Climatological 30-Year Runs | Represents climatological distributions, not daily 24-hour weather predictions. |

---

## 2. Terms of Use & Attribution Policy

- **India Meteorological Department (IMD):** Official warnings, observational AWS telemetry, and radar summaries are utilized under Open Government Data (OGD) guidelines for public safety and disaster early warning.
- **ISRO / NRSC Bhuvan:** Inundation footprints and historical satellite-derived water spread maps are cited in accordance with ISRO National Remote Sensing Centre guidelines.
- **OpenStreetMap Data:** Map vector assets (railways, subways, culverts, river lines) are copyrighted by OpenStreetMap contributors under ODbL.
