# 🌲 Tree Canopy Forecasting

This project forecasts **forest canopy change** at the U.S. county level using a combination of **exploratory data analysis (EDA)** and **machine learning models**.

---

## 📂 Dataset

- Source: [DataCommons API](https://datacommons.org/)  
- Variable: `LandCoverFraction_Forest` (forest land cover as % of county area)  
- Years used: **2015–2019**  
- Processed into a **binary target**:
  - `1` = High Growth (≥5% increase in canopy cover)  
  - `0` = Stable/Declining  

👉 Final target CSV:  
[`forest_canopy_data_target.csv`](https://github.com/ModelEarth/tree-canopy/blob/main/input/targets/forest_canopy_data_target.csv)

---

## 🔎 Workflow Overview

1. **Target Formation**
   - Extract U.S. county metadata via FIPS codes.
   - Retrieve Copernicus-derived forest cover data.
   - Calculate relative growth:
     ```python
     relative_growth = ((recent - start) / start) * 100
     ```
   - Label counties as High Growth (1) or Stable/Declining (0).

2. **Mathematical Analysis**
   - Rank counties by canopy change.
   - Identify **top 10 counties per state** with largest decreases.

3. **Preprocessing for EDA**
   - Clean FIPS codes, merge metadata.
   - Drop unrelated features, handle missing values.
   - Reshape data into **long format** for time-series models.

4. **Predictive Modeling**
   - **Linear Regression** (`sklearn`) for trend fitting.  
   - **ARIMA** (`statsmodels`) for 5-year canopy forecasts.  
   - Rolling-window validation used for robustness.

5. **Statewise Pipelines**
   - Group counties by state for **localized forecasting**.
   - Outputs structured for visualization.

6. **Interactive Dashboard (TODO)**
   - Planned UI with dropdown menus for **state + county selection**.
   - Direct access to forecasts from pipelines.

---

## ⚙️ Configuration

Target YAML: [`forest_canopy_config.yaml`](https://github.com/ModelEarth/tree-canopy/blob/main/parameters/forest_canopy_config.yaml)

```yaml
folder: naics6-forestcanopy-counties-simple
features:
  data: industries
  common: Fips
  path: https://raw.githubusercontent.com/ModelEarth/community-timelines/main/training/naics2/US/counties/2020/US-ME-training-naics2-counties-2020.csv
targets:
  data: forest_canopy
  path: https://raw.githubusercontent.com/ModelEarth/tree-canopy/main/input/targets/forest_canopy_data_target.csv
models: rbf
