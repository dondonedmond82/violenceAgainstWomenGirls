# Violence Against Women & Girls (VAWG) — Dash Data Explorer

An interactive Python web application built with **Dash**, **Pandas** and **Plotly**. It explores survey responses about attitudes toward reasons sometimes given to justify wife-beating. The application presents nine visualizations, each in its own tab with an explanatory guide.

## Project files

Place these files in the same directory:

```text
project/
├── app.py
├── violence_data.csv
├── requirements.txt
├── README.md
└── VAWG_dashboard_visual_report.pdf
```

- `app.py` — Dash application and dashboard layout.
- `violence_data.csv` — dataset used by the application.
- `requirements.txt` — Python dependencies.
- `VAWG_dashboard_visual_report.pdf` — static report containing the nine graphs and their explanations.

## Features

- Interactive filters for country, gender, demographic grouping, demographic response, survey statement and survey year.
- KPI overview and dynamically calculated key findings.
- Nine graph tabs, each pairing a written description and “How to read it” guide with a chart:
  1. **Pie chart** — compares the relative share of the six statement-level average agreement values. Slice percentages are shares of the sum of the averages, not respondent shares.
  2. **Vertical bar chart** — compares average agreement values across survey statements.
  3. **Horizontal bar chart** — shows up to twelve countries with the highest average agreement value in the current selection.
  4. **Scatter plot** — plots survey year against agreement value for individual records, with colour representing gender. For large selections, at most 2,500 points are plotted.
  5. **Line chart** — displays yearly average agreement by survey statement.
  6. **Heatmap** — compares average agreement by country and statement, showing up to fifteen countries.
  7. **Histogram** — displays the distribution of agreement values using 18 bins.
  8. **Boxplot** — summarizes the distribution, median, middle half and potential outliers for each statement.
  9. **Area chart** — displays yearly average agreement by statement using filled areas.
- CSV data table and export.
- Responsive layout for smaller screens.

## Dataset

The application expects `violence_data.csv` beside `app.py`. The supplied dataset has 12,600 rows and these required columns:

| Column | Use in the dashboard |
|---|---|
| `RecordID` | Record identifier |
| `Country` | Country filter and country comparison |
| `Gender` | Gender filter and scatter plot grouping |
| `Demographics Question` | Demographic grouping filter |
| `Demographics Response` | Demographic response filter |
| `Question` | Survey statement filter and chart categories |
| `Survey Year` | Year filter and time-series charts |
| `Value` | Numeric agreement percentage used in calculations |

The application converts `Value` to numeric, normalizes `Survey Year` to an integer year, and maps `F`/`M` to `Female`/`Male` for display.

## Installation

Python 3.9 or later is recommended.

### 1. Create and activate a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

If you do not have a `requirements.txt`, create one with:

```text
dash>=2.17
pandas>=2.0
plotly>=5.20
```

Then run `pip install -r requirements.txt`.

### 3. Start the dashboard

```bash
python app.py
```

Open this address in your browser:

```text
http://127.0.0.1:8050
```

Stop the server with `Ctrl+C`.

## Dataset path configuration

By default, `app.py` loads `violence_data.csv` from the same directory. To use another location, set the `VAWG_DATA_PATH` environment variable.

**Windows PowerShell:**

```powershell
$env:VAWG_DATA_PATH = "C:\data\violence_data.csv"
python app.py
```

**macOS / Linux:**

```bash
export VAWG_DATA_PATH="/data/violence_data.csv"
python app.py
```

## Interpretation and methodological limitations

- `Value` represents the percentage agreeing with a survey statement. It is an attitude measure, **not a count or rate of actual violence**.
- A higher value indicates greater agreement with the relevant statement in the available survey records. It should not be interpreted as the prevalence of violence against women or girls.
- The dashboard calculates simple, unweighted means across the records in the current selection. The supplied dataset does not provide respondent weights or denominators in the fields used by this application; therefore, country and subgroup averages may not represent weighted population estimates.
- The pie chart normalizes the six statement averages into slices. Its slice percentages show each average's share of the sum of those six averages, not the percentage of respondents.
- The horizontal bar chart shows at most twelve countries; the heatmap shows at most fifteen. These are display limits for readability.
- The scatter plot samples at most 2,500 records when the current selection is larger. The underlying dataset is not changed by this display sampling.
- Missing or non-numeric values are excluded from the visual calculations that require `Value` and `Survey Year`.

## Customization

- Change colours in the colour constants near the top of `app.py` (`NAVY`, `GREEN`, `RED`, `BLUE`, `ORANGE`, `PURPLE`).
- Modify the explanatory copy in `GRAPH_GUIDES`.
- Modify chart logic in `build_figures(data)`.
- Modify dashboard layout and panel dimensions in `app.index_string` CSS.
- Modify filters and KPI logic in the Dash layout and callback functions.

## Report

`VAWG_dashboard_visual_report.pdf` provides a printable view of the nine graph tabs. Each page places the explanatory text and “How to read it” instructions on the left, with the corresponding chart on the right. The report uses the full dataset without interactive filters applied.

## Disclaimer

This dashboard is a descriptive exploration of the supplied survey dataset. It does not establish causation, diagnose individual experiences, or measure the actual incidence of violence. Interpret comparisons in light of survey design, sampling, coverage and the absence of weighting information in the supplied fields.
