# Big Data Analysis of NYC Yellow Taxi Trip Records

**MIT 805: Big Data Group Project (2026) – Part 1: Data Collection & Analysis**

### Authors
* **Vincent Mabuza**
* **Linda Masia**

---

## Project Overview
This project performs an end-to-end Big Data analysis of the **NYC Taxi and Limousine Commission (TLC) Yellow Taxi Trip Record** dataset (sourced via NYC Open Data). The project processes 2026 trip records and rolls back through prior years (2014–2026) to construct a working analysis dataset to evaluate urban transit patterns, payment behaviors, and fleet operations across New York City.

---

## Dataset Breakdown & Size
* **Raw Set (> 50 GB):** Full monthly TLC files downloaded for candidate years (2014–2026).
* **Working Set (12.15 GB):** Selected sequentially backwards from the most recent records until reaching the ~12 GB target threshold.
* **Processing Set (3.6 GB / ~25.6M Records):** Random-seeded monthly files sampled from the working set for cleaned processing.
* **Formats:** CSV and Apache Parquet.

---

## Data Quality & Pipeline Preprocessing
To handle schema inconsistencies across TLC release years, candidate months were first normalized for column/casing consistency. 

Key data cleaning and filtering steps applied:
* **Timestamp Validation:** Parsed pickup/drop-off timestamps and dropped invalid or missing dates.
* **Duration & Distance Boundaries:** Filtered out negative, zero, or extreme outlier trip durations and distances.
* **Fare & Ratecode Validation:** Dropped negative fares, unreasonable upper fare bounds, and flagged non-standard rate codes.
* **Passenger Restrictions:** Enforced plausible passenger count physical boundaries.
* **Dead-Weight Removal:** Dropped exact duplicate records and completely uninformative columns with 100% missing/null values (e.g., `SR_Flag`, `ehail_fee`).

---

## Key Findings & Exploratory Analysis
1. **Schema Richness:** High-Volume For-Hire Vehicles (HVFHV) provide detailed metrics (driver pay, wait times, dispatch timestamps), while street-hail Yellow/Green taxis focus primarily on spatial, meter, and surcharge distributions.
2. **Right-Skewed Distribution:** Heavy right-skewness observed across distance, base fare, and trip duration due to long-distance airport routes and borough transfers.
3. **Cash Tipping Under-representation:** Tip amounts for cash transactions are systematically logged as `$0.00` compared to electronically tracked credit card payments.

---

## The 7 Vs of Big Data
* **Volume:** 12.15 GB working set; ~25.6 million records in the sampled processing set.
* **Velocity:** Multi-year updates capturing continuous high-density daily trip updates.
* **Variety:** Multi-sector structured tabular data across different vendors, rate structures, and payment modes.
* **Veracity:** Addressed schema discrepancies, missing fields, severe outliers, and invalid rates.
* **Variability:** Temporal fluctuations based on peak commuting hours, day-of-week trends, and borough dynamics.
* **Visualization:** Profiling distribution metrics across distance, fares, and spatial routes.
* **Value:** Practical insights for fleet dispatch optimization, driver shift management, congestion surcharge analysis, and public transit planning.

---

## Limitations
* **Sampling Constraints:** Analysis was conducted on a sampled ~25.6M row subset rather than the full multi-terabyte raw historical set due to compute resource bounds.
* **Historical Coverage:** Older historical data may not fully reflect post-pandemic commuting behavior or multi-modal transit shifts.

---

## 📜 License & Provenance
Data published by the **NYC Taxi and Limousine Commission (TLC)** via **NYC Open Data**. Free for public and research use under the City of New York Terms of Use.
