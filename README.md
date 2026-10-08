# Big Data Analysis of NYC TLC Trip Records

**MIT 805: Big Data Group Project (2026)**
Part 1: Data Collection & Analysis | Part 2: MapReduce & Visualization

### Authors


- Vincent Mabuza 
- Linda Masia  

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Linda-Masia/MIT-805---Vincent-Mabuza-Linda-Masia.git
cd MIT-805---Vincent-Mabuza-Linda-Masia

# 2. Create and activate a virtual environment (Python 3.10+ recommended)
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Java 17 (required by Spark, see below)

# 5. Download the raw data
python src/download_data.py

# 6. Open the notebooks
jupyter lab
```

Then run, in order:
1. `notebooks/EDA.ipynb` (Part 1)
2. `notebooks/MapReduce & Visualization.ipynb` (Part 2)

> **Run notebooks from inside `notebooks/`.** The Part 2 notebook finds the repo root via `Path.cwd().parent`, so the kernel's working directory must be `notebooks/` (the default in Jupyter and VS Code). Restart the kernel after moving or renaming files.

---

## Requirements

| Component | Version | Notes |
|---|---|---|
| **Java** | **17 (JDK or JRE)** | **Mandatory.** The notebook asserts that the running JVM is Java 17 and stops otherwise. |
| **Python** | 3.10+ | 3.10 or newer is needed for the walrus operator used in the notebook. |
| **Apache Spark / PySpark** | 4.x (report run on **4.2.0**) | Installed through `requirements.txt`. No separate Spark install is needed. |
| Other Python libs | see `requirements.txt` | pandas, pyarrow, numpy, requests, matplotlib, seaborn, jupyter |

### Installing Java 17

| OS | Command |
|---|---|
| Windows | `winget install Microsoft.OpenJDK.17` |
| macOS | `brew install openjdk@17` |
| Linux / Colab | `sudo apt-get install openjdk-17-jre-headless` |

After installing, **restart your terminal and the Jupyter kernel**, then verify:

```bash
java -version      # should report 17.x
```

You do not have to set `JAVA_HOME` by hand. The "JAVA CHECK" cell in the Part 2 notebook searches the usual install locations (Microsoft, Adoptium, Amazon Corretto, Zulu, Homebrew, `/usr/lib/jvm`, ...), sets `JAVA_HOME` and `PATH` for the session, and also sets `PYSPARK_PYTHON` to the active interpreter. If no Java 17 is found it raises an error with the install command for your OS.

### Hardware

| Resource | Minimum | Why |
|---|---|---|
| RAM | 8 GB (16 GB recommended) | Spark driver is set to 4 GB (`spark.driver.memory`); the processing-set builder streams row groups so it stays low-memory. |
| CPU | Multi-core | Spark runs `local[*]` (all cores). The report run used 12 cores. |
| Disk | ~20 GB free for the working + processing sets; **50 GB+** if you download every raw month | See [Dataset Breakdown](#dataset-breakdown--size). |

---

## Repository Structure

```
.
├── data/
│   ├── raw/                      # Raw TLC parquet files, one sub-folder per service
│   │   ├── yellow/
│   │   ├── green/
│   │   ├── fhv/
│   │   └── fhvhv/
│   ├── processing/               # Sampled Part 2 set: {service}_processing.parquet
│   └── taxi_zone_lookup.csv      # TLC zone → borough/zone names (auto-downloaded)
├── figures/                      # Plots saved by the Part 2 notebook (fig1–fig4)
├── notebooks/
│   ├── EDA.ipynb                 # Part 1: exploratory data analysis
│   ├── EDA_extracted.py          # EDA exported to a script (nbconvert)
│   └── MapReduce & Visualization.ipynb   # Part 2: PySpark MapReduce + figures
├── src/
│   └── download_data.py          # Downloads raw TLC files
├── MIT 805 Part 2.pdf            # Part 2 written report
├── requirements.txt
├── working_data_download.ipynb   # Working-set download / selection (Part 1)
└── README.md
```

`data/` and large files are git-ignored, so they will not exist after cloning. Run the download step to create them.

---

## Project Overview

This project performs an end-to-end Big Data analysis of the **NYC Taxi and Limousine Commission (TLC) Trip Record** datasets (sourced via NYC Open Data), covering the four TLC services:

| Service | Description |
|---|---|
| **Yellow** | Street-hail medallion taxis |
| **Green** | Boro taxis (street-hail outside the core of Manhattan) |
| **FHV** | For-Hire Vehicles (traditional dispatch bases) |
| **FHVHV** | High-Volume For-Hire Vehicles (app-based: Uber, Lyft, ...) |

- **Part 1** builds a working dataset, cleans it and runs exploratory analysis on urban transit patterns, payment behaviour and fleet operations.
- **Part 2** applies a MapReduce-style workflow in PySpark to compare the four services by **when and where they pick up passengers**.

---

## Part 1: Data Collection & Analysis

### Dataset Breakdown & Size
* **Raw set (> 50 GB):** Full monthly TLC files downloaded for candidate years (2014–2026).
* **Working set (12.15 GB):** Selected sequentially backwards from the most recent records until reaching the ~12 GB target threshold.
* **Processing set (3.6 GB / ~25.6M records):** Random-seeded monthly files sampled from the working set for cleaned processing.
* **Formats:** CSV and Apache Parquet.

### Data Quality & Pipeline Preprocessing
Candidate months were first normalised for column/casing consistency because TLC schemas change between release years. Cleaning steps:
* **Timestamp validation:** parsed pickup/drop-off timestamps and dropped invalid or missing dates.
* **Duration & distance boundaries:** filtered negative, zero or extreme-outlier trip durations and distances.
* **Fare & rate-code validation:** dropped negative fares and unreasonable upper bounds; flagged non-standard rate codes.
* **Passenger restrictions:** enforced plausible passenger-count boundaries.
* **Dead-weight removal:** dropped exact duplicates and columns that are 100% null (e.g. `SR_Flag`, `ehail_fee`).

### Key Findings
1. **Schema richness:** HVFHV provides detailed metrics (driver pay, wait times, dispatch timestamps), while Yellow/Green focus on spatial, meter and surcharge fields.
2. **Right-skewed distributions:** distance, base fare and trip duration are heavily right-skewed because of long airport routes and borough transfers.
3. **Cash-tip under-representation:** cash tips are systematically logged as `$0.00` compared with electronically recorded card payments.

---

## Part 2: MapReduce & Visualization

> Full write-up: **`MIT 805 Part 2.pdf`**. Code: **`notebooks/MapReduce & Visualization.ipynb`**.

### Analytical question
*How do the four NYC TLC services differ in **when** and **where** they pick up passengers, and which borough / zone / hour combinations concentrate the most demand (weekday vs weekend)?*

### Processing set
Built by randomly sampling **Parquet row groups** (`seed = 42`) from each service's raw files, writing incrementally until each output reaches **~1.5 GB**:

| Service | Rows in sample | Size |
|---|---|---|
| Yellow | 78,463,852 | 1.50 GB |
| Green | 1,067,809 | 0.03 GB |
| FHV | 39,239,405 | 0.48 GB |
| FHVHV | 62,122,411 | 1.51 GB |
| **Total** | | **≈ 3.52 GB** |

Expected pickup window (inferred from raw file names): **1 May 2024 ≤ pickup < 1 Feb 2026**.

> **Important:** sampling is by row group and size target, so sampling fractions differ per service. **Raw trip counts are not comparable across services.** All cross-service comparisons use *share of the service's own sampled trips*.

### How the notebook is organised

| Section | What it does |
|---|---|
| Building the processing set | Samples raw parquet → `data/processing/*_processing.parquet` (downcasts floats, aligns schemas, streams row groups to limit memory). |
| Java check | Locates Java 17 and configures `JAVA_HOME` / `PATH` (must run **before** the Spark session). |
| Spark session | `local[*]`, 4 GB driver, 16 shuffle partitions, adaptive execution on, session time zone `UTC` (TLC timestamps are NYC wall-clock times, so this prevents hour shifting). |
| MapReduce implementation | Map → Shuffle → Reduce → Enrichment (below). |
| Distributed-execution evidence | Physical plan (`explain`), shuffle-partition timing, broadcast vs sort-merge join, RDD `reduceByKey` vs `groupByKey` vs DataFrame comparison, Spark UI stage summary. |
| Results & figures | Quality table, top hotspots, weekday/weekend peaks, borough distribution, Figures 1–4. |

### MapReduce design

| Stage | Implementation |
|---|---|
| **Map** | Standardise four schemas to `(service_type, pickup_ts, PULocationID, fare)`. Drop null pickup times, out-of-range dates and zone IDs outside 1–265. Derive `pickup_hour` and `is_weekend`. Fares outside (0, 500) are excluded from fare stats only, not from trip counts. |
| **Shuffle** | `groupBy(service_type, is_weekend, pickup_hour, PULocationID)`; hash-partitioned exchange. A second range-partitioned exchange handles the global sort. |
| **Reduce** | `trip_count`, `fare_sum`, `fare_n` (keeping sum and count allows a correct weighted-average fare on merge). |
| **Enrich** | Broadcast hash join with the 265-row TLC taxi-zone lookup to add `Zone` and `Borough`. |

Fields used per service:

| Service | Pickup timestamp | Fare field |
|---|---|---|
| Yellow | `tpep_pickup_datetime` | `fare_amount` |
| Green | `lpep_pickup_datetime` | `fare_amount` |
| FHV | `pickup_datetime` | none |
| FHVHV | `pickup_datetime` | `base_passenger_fare` |

### Key results
* **Data quality:** FHV has **81.55%** of pickup-zone IDs missing (31,998,424 of 39,239,405 rows), so its spatial/borough results cover only geo-assignable records. FHV has no fare column. Out-of-range timestamps: 50 Yellow, 29 Green.
* **Top zone-hour hotspots:** Yellow, Midtown Center at 18:00 (308,647 trips); Green, East Harlem North at 08:00; FHVHV, LaGuardia Airport (14:00–23:00); FHV, Staten Island zones (treat with caution given missing zones).
* **Weekday peak hour:** FHV 09:00, FHVHV 18:00, Green 17:00, Yellow 18:00. **Weekend peak hour:** FHV 09:00, FHVHV 19:00, Green 18:00, Yellow 18:00.
* **Borough concentration:** Yellow is 86.8% Manhattan; Green is 59.4% Manhattan / 24.0% Queens; FHVHV is spread across Manhattan (37.4%), Brooklyn (26.6%) and Queens (21.6%).
* **Spark performance (single run, not a controlled benchmark):** 23.1 s with 200 shuffle partitions vs 17.2 s with 16 (≈ 25.5% faster); on Green, `reduceByKey` 29.2 s, `groupByKey` 28.4 s, DataFrame `groupBy` 1.0 s, all returning identical results for 5,253 keys.

### Figures
Saved to `figures/` by the notebook:

| File | Content |
|---|---|
| `fig1_hourly_profile.png` | Hourly demand profile per service, weekday vs weekend |
| `fig2_top_hotspots.png` | Top five zone-hour hotspots per service |
| `fig3_borough_hour_heatmap.png` | Borough × hour demand-concentration heatmaps |
| `fig4_avg_fare_by_hour.png` | Average base fare by pickup hour (FHV omitted: no fare data) |

### Spark UI
While the session is open, the Spark UI is available at the URL printed by the notebook (usually `http://localhost:4040`). Keep the session open to capture DAG / stage screenshots for the report.

---

## Running Part 2 step by step

1. Make sure Java 17 is installed and `pip install -r requirements.txt` has been run.
2. Make sure `data/raw/{yellow,green,fhv,fhvhv}/` contain the TLC `.parquet` files (`python src/download_data.py`).
3. Open `notebooks/MapReduce & Visualization.ipynb` and **restart the kernel**.
4. Run the top "setup" cell(s) so `PROJECT_ROOT` is defined.
5. Run **"Building the processing set"** (only needed once; writes `data/processing/`). This is the slowest step and is I/O-bound.
6. Run the **Java check** cell, **then** the Spark session cell (never the other way round; the JVM starts once per kernel).
7. Run the MapReduce, execution-evidence and results cells. Figures are written to `figures/`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Java 17 was not found` | Install Java 17 (table above), restart the kernel, re-run the Java check cell. |
| `AssertionError: Spark is running on Java X, expected 17` | A Spark session was created earlier with another Java. **Restart the kernel** and run the Java check cell first. |
| `No parquet files found in data/raw/...` | Raw data isn't downloaded yet, or the notebook isn't running from `notebooks/`. Check `Path.cwd()`. |
| `No such file or directory: ./requirements.txt` | The notebook is now in `notebooks/`; use `../requirements.txt` or `PROJECT_ROOT / "requirements.txt"`. |
| `'cat' / 'ls' is not recognized` (Windows) | These are Unix commands. Use Python (`Path.read_text()`, `Path.iterdir()`) instead of `!cat` / `!ls`. |
| Out-of-memory in Spark | Close other apps, or raise `spark.driver.memory` in the Spark session cell. |
| Wrong hours in results | Keep `spark.sql.session.timeZone = UTC`; TLC timestamps are already NYC local time. |
| The Colab "clone repo" cell fails or duplicates the repo | That cell is only for Google Colab. Skip it when running locally. |

**Google Colab:** the notebook also runs on Colab (the Java cell installs `openjdk-17-jre-headless` via `apt-get`). Use the clone cell at the top, then run everything from the repo root.

---

## The 7 Vs of Big Data
* **Volume:** 12.15 GB working set; ~25.6M records in the Part 1 processing sample; ~3.52 GB / ~180M rows in the Part 2 processing set.
* **Velocity:** multi-year updates capturing continuous, high-density daily trip records.
* **Variety:** structured tabular data across four services, vendors, rate structures and payment modes.
* **Veracity:** schema discrepancies, missing fields (e.g. 81.55% FHV zones), outliers and invalid rates addressed.
* **Variability:** temporal fluctuations by commuting hour, day of week and borough.
* **Visualization:** distribution profiling, hotspot bars, borough × hour heatmaps and fare curves.
* **Value:** dispatch optimisation, driver shift management, congestion-surcharge analysis and public-transit planning.

---

## Limitations
* **Sampling:** both parts use sampled subsets rather than the full multi-terabyte raw history, due to compute limits. Part 2 sampling fractions differ per service, so cross-service raw counts are not comparable.
* **FHV geography:** 81.55% missing pickup zones limits the reliability of FHV spatial and borough analysis.
* **Resolution:** taxi-zone IDs give neighbourhood-level, not GPS-level, locations.
* **Fares:** "average fare" is a descriptive base-fare measure, not driver earnings, profit or total passenger spend. FHV fare analysis is unavailable.
* **No explanatory variables:** weather, events and traffic are not modelled. Time-demand association does not establish causation or policy effects.
* **Timing results** come from a single local run and should not be generalised as Spark benchmarks.
* **Historical coverage:** older data may not reflect post-pandemic commuting or multi-modal transit shifts.

---

## License & Provenance
Data published by the **NYC Taxi and Limousine Commission (TLC)** via **NYC Open Data**. Free for public and research use under the City of New York Terms of Use. Taxi-zone lookup: `https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv`.