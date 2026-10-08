#!/usr/bin/env python
# coding: utf-8

# ## 1. Import Required Libraries

# In[1]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from pathlib import Path
import pyarrow.parquet as pq

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)

print("Libraries loaded successfully")


# ## 2. Dataset Paths and Sampling Settings

# In[2]:


DATASETS = {
    "FHV": Path("../data/raw/fhv"),
    "FHVHV": Path("../data/raw/fhvhv"),
    "Green": Path("../data/raw/green"),
    "Yellow": Path("../data/raw/yellow"),
}

SAMPLE_ROWS_PER_DATASET = 250_000
RANDOM_STATE = 42

for name, path in DATASETS.items():
    files = sorted(path.glob("*.parquet"))
    print(f"{name:8} | {len(files):4} files | {path}")


# ## 3. Representative Sampling

# In[3]:


SAMPLE_CONFIG = {
    "FHV": 13_800_000,
    "FHVHV": 4_400_000,
    "Green": 6_000_000,
    "Yellow": 6_350_000,
}

RANDOM_STATE = 42

def sample_parquet_folder(folder, n_rows, random_state=42):
    rng = np.random.default_rng(random_state)
    files = sorted(Path(folder).glob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"No parquet files found in {folder}")

    row_groups = []
    for file in files:
        pf = pq.ParquetFile(file)
        for rg in range(pf.num_row_groups):
            rows = pf.metadata.row_group(rg).num_rows
            row_groups.append((file, rg, rows))

    if not row_groups:
        return pd.DataFrame()

    total_available_rows = sum(rg[2] for rg in row_groups)
    target_rows = min(n_rows, total_available_rows)

    order = rng.permutation(len(row_groups))
    pieces = []
    total = 0

    for idx in order:
        file, rg, rows = row_groups[idx]
        pf = pq.ParquetFile(file)
        piece = pf.read_row_group(rg).to_pandas()

        remaining = target_rows - total
        if len(piece) > remaining:
            piece = piece.sample(n=remaining, random_state=random_state)

        pieces.append(piece)
        total += len(piece)
        if total >= target_rows:
            break

    if not pieces:
        return pd.DataFrame()

    return pd.concat(pieces, ignore_index=True).sample(frac=1, random_state=random_state).reset_index(drop=True)

samples = {}
for name, path in DATASETS.items():
    n_rows = SAMPLE_CONFIG[name]
    print(f"Sampling {name} ({n_rows:,} rows)...")
    samples[name] = sample_parquet_folder(path, n_rows=n_rows, random_state=RANDOM_STATE)

    # Calculate actual memory usage
    mem_mb = samples[name].memory_usage(deep=True).sum() / (1024 ** 2)
    print(f"  Shape: {samples[name].shape} | Memory: {mem_mb:.2f} MB")


# ## 4. First Look at the Data

# In[4]:


for name, df in samples.items():
    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)
    print("Shape:", df.shape)
    display(df.head())


# In[5]:


for name, df in samples.items():
    print("\n" + "=" * 80)
    print(name, "— INFO")
    print("=" * 80)
    df.info()


# In[6]:


for name, df in samples.items():
    print("\n" + "=" * 80)
    print(name, "— COLUMNS")
    print("=" * 80)
    print(df.columns.tolist())


# In[7]:


for name, df in samples.items():
    print("\n" + "=" * 80)
    print(name, "— NUMERICAL SUMMARY")
    print("=" * 80)
    display(df.describe(include=[np.number]).T)


# ## 5. Data Types and Missing Values

# In[8]:


for name, df in samples.items():
    print(f"\n{name} data types:")
    display(df.dtypes.to_frame("dtype"))

    missing = df.isnull().sum().sort_values(ascending=False)
    missing = missing[missing > 0]
    print(f"{name} missing values:")
    display(missing.to_frame("missing_count"))


# In[9]:


# Missing-value percentages
missing_summary = {}

for name, df in samples.items():
    result = pd.DataFrame({
        "missing_count": df.isna().sum(),
        "missing_percent": df.isna().mean() * 100
    }).sort_values("missing_percent", ascending=False)
    missing_summary[name] = result
    print(f"\n{name}")
    display(result[result["missing_count"] > 0].head(20))


# ## 6. Duplicate Rows
# 
# A full duplicate scan over every taxi row is deliberately **not** performed here because it is one of the most expensive operations on these datasets. We use the representative samples for the standard `duplicated()` check.

# In[10]:


for name, df in samples.items():
    duplicate_count = df.duplicated().sum()
    duplicate_percent = duplicate_count / len(df) * 100 if len(df) else 0
    print(f"{name}: {duplicate_count:,} duplicate rows in sample ({duplicate_percent:.2f}%)")


# ## 7. Univariate Analysis — Categorical Variables

# In[11]:


def categorical_columns(df, max_unique=50):
    cols = []
    for col in df.columns:
        nunique = df[col].nunique(dropna=True)
        if df[col].dtype == "object" or str(df[col].dtype).startswith("category") or nunique <= max_unique:
            cols.append(col)
    return cols

for name, df in samples.items():
    cats = categorical_columns(df)
    print(f"{name}: {cats[:20]}")


# In[12]:


for name, df in samples.items():
    cats = categorical_columns(df)
    # Limit plots so the notebook stays responsive.
    for col in cats[:8]:
        counts = df[col].value_counts(dropna=False).head(10)
        if len(counts) == 0:
            continue
        plt.figure(figsize=(10, 5))
        sns.barplot(x=counts.index.astype(str), y=counts.values)
        plt.title(f"{name}: Top Categories — {col}")
        plt.xlabel(col)
        plt.ylabel("Count")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.show()


# ## 8. Univariate Analysis — Numerical Variables

# In[13]:


def numeric_columns(df):
    return df.select_dtypes(include=np.number).columns.tolist()

for name, df in samples.items():
    nums = numeric_columns(df)
    print(f"{name}: {len(nums)} numeric columns")
    print(nums[:30])


# In[14]:


for name, df in samples.items():
    nums = numeric_columns(df)[:12]
    for col in nums:
        series = df[col].dropna()
        if series.empty:
            continue
        plt.figure(figsize=(10, 5))
        sns.histplot(series, bins=40, kde=True)
        plt.title(f"{name}: Distribution of {col}")
        plt.xlabel(col)
        plt.ylabel("Frequency")
        plt.tight_layout()
        plt.show()


# In[15]:


for name, df in samples.items():
    nums = numeric_columns(df)[:12]
    for col in nums:
        series = df[col].dropna()
        if series.empty:
            continue
        plt.figure(figsize=(10, 4))
        sns.boxplot(x=series)
        plt.title(f"{name}: Box Plot of {col}")
        plt.tight_layout()
        plt.show()


# ## 9. Outlier Analysis — IQR Method

# In[16]:


outlier_summary = []

for name, df in samples.items():
    for col in numeric_columns(df):
        s = df[col].dropna()
        if s.empty:
            continue
        q1, q3 = s.quantile([0.25, 0.75])
        iqr = q3 - q1
        if iqr == 0:
            count = 0
        else:
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            count = ((s < lower) | (s > upper)).sum()
        outlier_summary.append({
            "dataset": name,
            "column": col,
            "outlier_count": int(count),
            "outlier_percent": float(count / len(s) * 100)
        })

outlier_summary = pd.DataFrame(outlier_summary).sort_values("outlier_percent", ascending=False)
display(outlier_summary.head(30))


# ## 10. Bivariate Analysis

# In[17]:


def find_col(df, candidates):
    lower = {c.lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in lower:
            return lower[candidate.lower()]
    return None

for name, df in samples.items():
    distance = find_col(df, ["trip_distance", "trip_miles"])
    fare = find_col(df, ["fare_amount", "base_passenger_fare"])
    duration = find_col(df, ["trip_duration", "trip_time", "duration"])

    print(f"{name}: distance={distance}, fare={fare}, duration={duration}")


# In[18]:


for name, df in samples.items():
    distance = find_col(df, ["trip_distance", "trip_miles"])
    fare = find_col(df, ["fare_amount", "base_passenger_fare"])

    if distance and fare:
        plot_df = df[[distance, fare]].dropna()
        # Prevent a handful of extreme observations from compressing the plot.
        if len(plot_df) > 10_000:
            plot_df = plot_df.sample(10_000, random_state=RANDOM_STATE)
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=plot_df, x=distance, y=fare, alpha=0.4)
        plt.title(f"{name}: {distance} vs {fare}")
        plt.tight_layout()
        plt.show()


# ## 11. Multivariate Analysis — Correlation Heatmaps

# In[19]:


for name, df in samples.items():
    nums = numeric_columns(df)
    if len(nums) < 2:
        continue
    # Select the first 12 numeric columns to keep the heatmap readable.
    selected = nums[:12]
    corr = df[selected].corr(numeric_only=True)

    plt.figure(figsize=(12, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0)
    plt.title(f"{name}: Correlation Heatmap")
    plt.tight_layout()
    plt.show()


# ## 12. Pair Plot — Selected Variables

# In[20]:


for name, df in samples.items():
    nums = numeric_columns(df)
    selected = nums[:4]
    if len(selected) >= 2:
        pair_df = df[selected].dropna()
        if len(pair_df) > 3_000:
            pair_df = pair_df.sample(3_000, random_state=RANDOM_STATE)
        sns.pairplot(pair_df)
        plt.suptitle(f"{name}: Selected Numerical Variables", y=1.02)
        plt.show()


# ## 13. Taxi-Specific Time Analysis

# In[21]:


def datetime_columns(df):
    result = []
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            result.append(col)
        elif df[col].dtype == "object" and any(k in col.lower() for k in ["datetime", "date", "time"]):
            converted = pd.to_datetime(df[col], errors="coerce")
            if converted.notna().mean() > 0.5:
                result.append(col)
    return result

for name, df in samples.items():
    print(name, "datetime-like columns:", datetime_columns(df))


# In[22]:


for name, df in samples.items():
    dt_cols = datetime_columns(df)
    if not dt_cols:
        continue

    col = dt_cols[0]
    dt = pd.to_datetime(df[col], errors="coerce")
    time_df = pd.DataFrame({"datetime": dt}).dropna()
    if time_df.empty:
        continue

    hourly = time_df["datetime"].dt.hour.value_counts().sort_index()
    plt.figure(figsize=(10, 5))
    sns.lineplot(x=hourly.index, y=hourly.values, marker="o")
    plt.title(f"{name}: Trips by Hour — {col}")
    plt.xlabel("Hour of Day")
    plt.ylabel("Trips in Sample")
    plt.xticks(range(24))
    plt.tight_layout()
    plt.show()

    weekday = time_df["datetime"].dt.dayofweek.value_counts().sort_index()
    plt.figure(figsize=(10, 5))
    sns.barplot(x=weekday.index, y=weekday.values)
    plt.title(f"{name}: Trips by Day of Week")
    plt.xlabel("Day of Week (0=Monday)")
    plt.ylabel("Trips in Sample")
    plt.tight_layout()
    plt.show()


# ## 14. Data Quality Checks

# In[23]:


quality_flags = []

for name, df in samples.items():
    checks = {
        "negative_trip_distance": find_col(df, ["trip_distance", "trip_miles"]),
        "negative_fare": find_col(df, ["fare_amount", "base_passenger_fare"]),
        "negative_total": find_col(df, ["total_amount"]),
        "negative_passenger_count": find_col(df, ["passenger_count"]),
    }

    for check, col in checks.items():
        if col is not None:
            count = (pd.to_numeric(df[col], errors="coerce") < 0).sum()
            quality_flags.append({"dataset": name, "check": check, "count": int(count)})

quality_flags = pd.DataFrame(quality_flags)
display(quality_flags)


# ## 15. Cross-Dataset Comparison

# In[24]:


comparison = pd.DataFrame([
    {
        "dataset": name,
        "sample_rows": len(df),
        "columns": df.shape[1],
        "numeric_columns": len(numeric_columns(df)),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum())
    }
    for name, df in samples.items()
])

display(comparison)


# In[25]:


plt.figure(figsize=(10, 5))
sns.barplot(data=comparison, x="dataset", y="sample_rows")
plt.title("Sample Size Used for EDA")
plt.xlabel("Dataset")
plt.ylabel("Rows")
plt.tight_layout()
plt.show()


# ## 16. Final Summary

# In[26]:


print("EDA completed.")
print(f"Sample size per dataset target: {SAMPLE_ROWS_PER_DATASET:,}")
print("Datasets analysed:", ", ".join(samples.keys()))

