"""
Violence Against Women & Girls (VAWG) — Interactive Dash application

Run:
    pip install -r requirements.txt
    python app.py

Keep violence_data.csv in the same folder as app.py.
Open http://127.0.0.1:8050

Each visualization has its own tab. Every tab contains:
- A 400px-wide explanatory text panel on the left.
- A 400px-wide Plotly graph on the right.

The dataset's Value field represents agreement percentages for survey
statements. It is not a measure of actual violence incidence or prevalence.
All cross-group averages are unweighted because respondent weights/counts
are not included in the supplied dataset.
"""

from pathlib import Path
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, dash_table
from dash.exceptions import PreventUpdate


# ---------------------------------------------------------------------
# Load and prepare the supplied dataset
# ---------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = Path(os.getenv("VAWG_DATA_PATH", BASE_DIR / "violence_data.csv"))

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Dataset not found: {DATA_PATH}\n"
        "Place violence_data.csv beside app.py or set VAWG_DATA_PATH."
    )

df = pd.read_csv(DATA_PATH)

REQUIRED_COLUMNS = [
    "RecordID", "Country", "Gender", "Demographics Question",
    "Demographics Response", "Question", "Survey Year", "Value"
]
missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
if missing:
    raise ValueError(f"Missing required dataset columns: {missing}")

df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
# Survey Year is numeric in the supplied file; this also handles date strings.
year_as_number = pd.to_numeric(df["Survey Year"], errors="coerce")
year_as_date = pd.to_datetime(df["Survey Year"], errors="coerce").dt.year
df["Survey Year"] = year_as_number.fillna(year_as_date)
df["Survey Year"] = df["Survey Year"].astype("Int64")
df["Gender"] = df["Gender"].replace({"F": "Female", "M": "Male"})

QUESTION_LABELS = {
    "... if she burns the food": "Burns the food",
    "... if she argues with him": "Argues with him",
    "... if she goes out without telling him": "Goes out without telling him",
    "... if she neglects the children": "Neglects the children",
    "... if she refuses to have sex with him": "Refuses sex",
    "... for at least one specific reason": "At least one reason",
}
df["Question label"] = df["Question"].map(QUESTION_LABELS).fillna(df["Question"])
valid = df.dropna(subset=["Value", "Survey Year"]).copy()
valid["Survey Year"] = valid["Survey Year"].astype(int)

NAVY = "#14213D"
DARK = "#101820"
GREEN = "#16A085"
RED = "#E74C3C"
BLUE = "#3977B8"
ORANGE = "#E89B35"
PURPLE = "#8064A2"
LIGHT = "#F3F6FA"
MUTED = "#687386"
GRID = "#E5E9F0"
PALETTE = [NAVY, GREEN, RED, ORANGE, BLUE, PURPLE]
PLOTLY_TEMPLATE = "plotly_white"

GRAPH_HEIGHT = 560
GRAPH_WIDTH = 800
TEXT_WIDTH = 536


def make_options(series, all_label="All"):
    values = sorted(series.dropna().unique().tolist(), key=lambda x: str(x))
    return [{"label": all_label, "value": "__ALL__"}] + [
        {"label": str(value), "value": value} for value in values
    ]


def filter_data(country, gender, demo_type, demo_response, question, year):
    data = valid.copy()
    if country != "__ALL__":
        data = data[data["Country"] == country]
    if gender != "__ALL__":
        data = data[data["Gender"] == gender]
    if demo_type != "__ALL__":
        data = data[data["Demographics Question"] == demo_type]
    if demo_response != "__ALL__":
        data = data[data["Demographics Response"] == demo_response]
    if question != "__ALL__":
        data = data[data["Question"] == question]
    if year != "__ALL__":
        data = data[data["Survey Year"] == int(year)]
    return data


def base_figure(fig, title, height=GRAPH_HEIGHT):
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=height,
        autosize=True,
        title={"text": title, "x": 0.03, "xanchor": "left",
               "font": {"size": 14, "color": NAVY}},
        margin={"l": 48, "r": 20, "t": 65, "b": 80},
        paper_bgcolor="white",
        plot_bgcolor="white",
        font={"family": "Arial, sans-serif", "size": 10, "color": DARK},
        legend={"font": {"size": 9}},
        hoverlabel={"bgcolor": "white"},
    )
    fig.update_xaxes(showgrid=False, linecolor=GRID, automargin=True,
                     tickfont={"size": 9})
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False,
                     automargin=True, tickfont={"size": 9})
    return fig


def empty_figure(message="No data for the selected filters."):
    fig = go.Figure()
    fig.add_annotation(
        text=message, x=0.5, y=0.5, xref="paper", yref="paper",
        showarrow=False, font={"size": 11, "color": MUTED}
    )
    return base_figure(fig, "No data available")


def safe_mean_by(data, column):
    return data.groupby(column, dropna=True)["Value"].mean().reset_index()


# ---------------------------------------------------------------------
# Graph builders — each uses only fields present in the supplied dataset
# ---------------------------------------------------------------------
def build_figures(data):
    if data.empty:
        blank = empty_figure()
        return {key: blank for key in GRAPH_IDS}

    figures = {}

    # 1. Pie: relative distribution of average agreement values by survey statement.
    question_avg = (
        data.groupby("Question label", as_index=False)["Value"].mean()
        .sort_values("Value", ascending=False)
    )
    pie = px.pie(
        question_avg, names="Question label", values="Value",
        color_discrete_sequence=PALETTE, hole=0.28
    )
    pie.update_traces(
        textposition="inside", textinfo="percent",
        hovertemplate="%{label}<br>Average agreement: %{value:.1f}%<extra></extra>"
    )
    pie.update_layout(
        showlegend=True,
        legend={"orientation": "h", "y": -0.13, "x": 0.5,
                "xanchor": "center", "font": {"size": 8}},
        margin={"l": 12, "r": 12, "t": 65, "b": 105},
    )
    figures["pie"] = base_figure(pie, "Average agreement by statement")

    # 2. Vertical bar: mean agreement for each statement.
    bar = px.bar(
        question_avg, x="Question label", y="Value",
        color="Question label", color_discrete_sequence=PALETTE,
        text="Value"
    )
    bar.update_traces(
        texttemplate="%{text:.1f}%", textposition="outside",
        cliponaxis=False, showlegend=False
    )
    bar.update_xaxes(tickangle=-35, title=None, tickfont={"size": 8})
    bar.update_yaxes(title="Average agreement (%)", ticksuffix="%")
    figures["bar"] = base_figure(bar, "Average agreement — vertical bar")

    # 3. Horizontal bar: leading countries by average value.
    country_avg = safe_mean_by(data, "Country").sort_values(
        "Value", ascending=True
    ).tail(12)
    barh = px.bar(
        country_avg, x="Value", y="Country", orientation="h",
        color="Value", color_continuous_scale=["#BDE8DD", GREEN],
        text="Value"
    )
    barh.update_traces(
        texttemplate="%{text:.1f}%", textposition="outside",
        cliponaxis=False
    )
    barh.update_xaxes(title="Average agreement (%)", ticksuffix="%")
    barh.update_yaxes(title=None, tickfont={"size": 8})
    figures["barh"] = base_figure(barh, "Countries by average agreement")

    # 4. Scatter: individual records, survey year against agreement value.
    scatter_data = data
    if len(scatter_data) > 2500:
        scatter_data = scatter_data.sample(2500, random_state=42)
    scatter = px.scatter(
        scatter_data, x="Survey Year", y="Value", color="Gender",
        hover_data=["Country", "Question label", "Demographics Response"],
        color_discrete_sequence=[GREEN, RED, BLUE],
        opacity=0.58
    )
    scatter.update_xaxes(title="Survey year")
    scatter.update_yaxes(title="Agreement (%)", ticksuffix="%")
    figures["scatter"] = base_figure(scatter, "Survey records: year vs agreement")

    # 5. Line: yearly average by survey statement.
    yearly_question = (
        data.groupby(["Survey Year", "Question label"], as_index=False)["Value"]
        .mean()
        .sort_values("Survey Year")
    )
    line = px.line(
        yearly_question, x="Survey Year", y="Value",
        color="Question label", markers=True,
        color_discrete_sequence=PALETTE
    )
    line.update_xaxes(title="Survey year")
    line.update_yaxes(title="Average agreement (%)", ticksuffix="%")
    figures["line"] = base_figure(line, "Agreement trends over survey years")

    # 6. Heatmap: country by question, limited to 15 countries for readability.
    heat_data = (
        data.groupby(["Country", "Question label"])["Value"].mean().reset_index()
    )
    country_order = (
        heat_data.groupby("Country")["Value"].mean()
        .sort_values(ascending=False).head(15).index.tolist()
    )
    heat_data = heat_data[heat_data["Country"].isin(country_order)]
    pivot = heat_data.pivot(
        index="Country", columns="Question label", values="Value"
    )
    heat = go.Figure(data=go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=[[0, "#F2F6FA"], [0.5, "#8FD7C2"], [1, GREEN]],
        colorbar={"title": "%", "thickness": 10},
        hovertemplate="Country: %{y}<br>Statement: %{x}<br>Average: %{z:.1f}%<extra></extra>"
    ))
    heat.update_xaxes(tickangle=-45, tickfont={"size": 8}, title=None)
    heat.update_yaxes(tickfont={"size": 8}, title=None)
    figures["heatmap"] = base_figure(heat, "Country and statement heatmap", height=520)

    # 7. Histogram: distribution of all filtered agreement percentages.
    hist = px.histogram(
        data, x="Value", nbins=18,
        color_discrete_sequence=[GREEN], opacity=0.88
    )
    hist.update_xaxes(title="Agreement (%)", ticksuffix="%")
    hist.update_yaxes(title="Number of survey records")
    figures["hist"] = base_figure(hist, "Distribution of agreement values")

    # 8. Boxplot: spread of values for each statement.
    box = px.box(
        data, x="Question label", y="Value",
        color="Question label", color_discrete_sequence=PALETTE,
        points="outliers"
    )
    box.update_layout(showlegend=False)
    box.update_xaxes(tickangle=-35, title=None, tickfont={"size": 8})
    box.update_yaxes(title="Agreement (%)", ticksuffix="%")
    figures["boxplot"] = base_figure(box, "Agreement spread by statement")

    # 9. Area: yearly mean agreement by statement.
    area_data = yearly_question.sort_values("Survey Year")
    area = px.area(
        area_data, x="Survey Year", y="Value",
        color="Question label", markers=False,
        color_discrete_sequence=PALETTE
    )
    area.update_xaxes(title="Survey year")
    area.update_yaxes(title="Average agreement (%)", ticksuffix="%")
    figures["area"] = base_figure(area, "Area chart — yearly average agreement")

    return figures


GRAPH_IDS = [
    "pie", "bar", "barh", "scatter", "line",
    "heatmap", "hist", "boxplot", "area"
]

GRAPH_GUIDES = {
    "pie": (
        "Pie chart",
        "The pie chart compares the average agreement value for each of the six survey statements. "
        "Each slice represents one statement. The slice sizes show each statement's share of the "
        "sum of the six average values; they are not percentages of all respondents.",
        "How to read it",
        "Compare slice sizes to see which statements have larger average agreement values. "
        "Hover over a slice to see the statement and its average percentage."
    ),
    "bar": (
        "Vertical bar chart",
        "The vertical bar chart compares average agreement across the survey statements. "
        "It makes differences between reasons easy to see.",
        "How to read it",
        "Compare bar heights. A higher bar indicates a larger average percentage of respondents "
        "agreeing with that statement."
    ),
    "barh": (
        "Horizontal bar chart",
        "The horizontal bar chart ranks countries by their average reported agreement value "
        "in the currently selected records. It displays up to twelve countries.",
        "How to read it",
        "Longer bars indicate higher average agreement values. This is a descriptive comparison "
        "of available survey records, not a country ranking of actual violence."
    ),
    "scatter": (
        "Scatter plot",
        "The scatter plot displays individual survey records by survey year and agreement value. "
        "Each point is one record; colours distinguish the gender categories in the filtered data.",
        "How to read it",
        "Look for clusters, spread and possible changes across years. A dense cluster means many "
        "records share similar year and agreement values. For readability, large selections are "
        "sampled to a maximum of 2,500 plotted records."
    ),
    "line": (
        "Line chart",
        "The line chart shows the average agreement value over survey years for each survey statement. "
        "Separate lines make it possible to compare how the statements vary over time.",
        "How to read it",
        "Follow each line from left to right. Rising values indicate increasing agreement in the "
        "available survey records; falling values indicate decreasing agreement."
    ),
    "heatmap": (
        "Heatmap",
        "The heatmap compares average agreement across countries and survey statements. "
        "Each cell represents the mean Value for one country and one statement. Up to fifteen "
        "countries are shown to keep the labels readable.",
        "How to read it",
        "Darker or more saturated cells represent higher average agreement values. Blank cells "
        "indicate that no matching value is available for that country and statement."
    ),
    "hist": (
        "Histogram",
        "The histogram shows how the filtered agreement percentages are distributed across records. "
        "Values are grouped into intervals (bins), and each column counts the records in an interval.",
        "How to read it",
        "Taller columns mean more records fall within that percentage range. The overall shape helps "
        "show whether values cluster at lower, middle or higher agreement levels."
    ),
    "boxplot": (
        "Boxplot",
        "The boxplot summarises the spread of agreement values for each survey statement. "
        "It shows the median, the middle half of the values and potential outliers.",
        "How to read it",
        "Compare the median lines and box heights. A taller box indicates greater variation in the "
        "middle half of the records. Points beyond the whiskers are potential outliers."
    ),
    "area": (
        "Area chart",
        "The area chart displays yearly average agreement values for the survey statements. "
        "The filled areas help show the evolution and relative patterns across the selected years.",
        "How to read it",
        "Read the horizontal axis as survey year and the vertical axis as average agreement. "
        "Compare the series over time; the filled areas are visual emphasis, not additive totals."
    ),
}


def graph_tab(graph_id):
    title, explanation, how_title, how_text = GRAPH_GUIDES[graph_id]
    return dcc.Tab(
        label=title,
        value=graph_id,
        children=html.Div(
            className="graph-tab-body",
            children=[
                html.Div(
                    className="guide-card",
                    children=[
                        html.Div("GRAPH GUIDE", className="guide-eyebrow"),
                        html.H3(title, className="guide-title"),
                        html.P(explanation, className="guide-description"),
                        html.Div(
                            className="how-to-card",
                            children=[
                                html.Strong(how_title),
                                html.P(how_text),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    className="graph-card",
                    children=dcc.Graph(
                        id=f"graph-{graph_id}",
                        figure=empty_figure(),
                        config={"displayModeBar": False, "responsive": True},
                        style={"width": "800px", "height": "560px", "minWidth": "800px"},
                    ),
                ),
            ],
        ),
    )


def kpi_card(label, component_id, subtitle):
    return html.Div(
        className="kpi-card",
        children=[
            html.Div(label, className="kpi-label"),
            html.Div(id=component_id, className="kpi-number"),
            html.Div(subtitle, className="kpi-subtitle"),
        ],
    )


# ---------------------------------------------------------------------
# Dash app and responsive page styling
# ---------------------------------------------------------------------
app = Dash(__name__, title="VAWG | Gender Equality Data Explorer")
server = app.server

app.index_string = """
<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <style>
      * { box-sizing: border-box; }
      body { margin: 0; background: #F3F6FA; color: #101820;
             font-family: Arial, Helvetica, sans-serif; }
      .topbar { background: #101820; color: white; padding: 22px 4%;
                border-bottom: 4px solid #16A085; }
      .topbar h1 { margin: 0 0 7px; font-size: 24px; letter-spacing: .3px; }
      .topbar p { margin: 0; color: #D7DEE8; font-size: 13px; }
      .page { max-width: 1500px; margin: auto; padding: 22px 3% 42px; }
      .section-title { color: #14213D; font-size: 16px; font-weight: 700;
                       margin: 22px 0 11px; }
      .filters { background: white; border: 1px solid #E5E9F0; border-radius: 10px;
                 padding: 16px 17px; display: grid;
                 grid-template-columns: repeat(3, minmax(170px, 1fr)); gap: 13px 16px; }
      .filter-label { font-size: 10px; font-weight: 700; color: #687386;
                      text-transform: uppercase; margin-bottom: 6px; display: block; }
      .kpi-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 13px; }
      .kpi-card { background: white; border: 1px solid #E5E9F0; border-radius: 9px;
                  padding: 15px 17px; min-height: 105px; }
      .kpi-label { font-size: 10px; font-weight: 700; text-transform: uppercase;
                   color: #687386; letter-spacing: .45px; }
      .kpi-number { font-size: 26px; font-weight: 700; color: #14213D; margin: 8px 0 3px; }
      .kpi-subtitle { font-size: 10px; color: #687386; }
      .insight { background: #EAF5F2; border-left: 4px solid #16A085; border-radius: 6px;
                 padding: 13px 15px; color: #183B36; font-size: 12px; line-height: 1.55; }
      .graph-tabs { margin-top: 12px; }
      .graph-tab-body {
          display: grid;
          grid-template-columns: 536px 800px;
          gap: 18px;
          align-items: stretch;
          width: max-content;
          min-width: 0;
          padding: 18px 2px 8px;
          overflow-x: auto;
      }
      .graph-card {
          grid-column: 2;
          width: 800px;
          min-width: 800px;
          max-width: 800px;
          height: 560px;
          min-height: 560px;
          background: white;
          border: 1px solid #E5E9F0;
          border-radius: 10px;
          padding: 8px;
          overflow: hidden;
      }
      .graph-card .dash-graph,
      .graph-card .dash-graph > div,
      .graph-card .js-plotly-plot,
      .graph-card .plot-container,
      .graph-card .svg-container {
          width: 800px !important;
          min-width: 800px !important;
          max-width: 800px !important;
      }
      .graph-card .dash-graph,
      .graph-card .js-plotly-plot,
      .graph-card .plot-container,
      .graph-card .svg-container {
          height: 100% !important;
      }
      .guide-card {
          grid-column: 1;
          width: 536px;
          min-width: 536px;
          max-width: 536px;
          min-height: 560px;
          background: white;
          border: 1px solid #E5E9F0;
          border-right: 5px solid #16A085;
          border-radius: 10px;
          padding: 28px 25px;
          overflow-wrap: anywhere;
      }
      .guide-eyebrow { color: #16A085; font-size: 10px; font-weight: 800;
                       letter-spacing: 1.5px; margin-bottom: 12px; }
      .guide-title { color: #14213D; font-size: 20px; line-height: 1.25; margin: 0 0 15px; }
      .guide-description { color: #46566C; font-size: 13px; line-height: 1.7; margin: 0 0 20px; }
      .how-to-card { background: #F3F6FA; border-radius: 8px; padding: 14px 13px;
                     color: #14213D; font-size: 12px; line-height: 1.6; }
      .how-to-card p { margin: 7px 0 0; }
      .data-panel { background: white; border: 1px solid #E5E9F0;
                    border-radius: 9px; padding: 12px; }
      .note { color: #687386; font-size: 11px; line-height: 1.5; margin: 12px 2px; }
      .footer { color: #687386; font-size: 10px; text-align: center; margin-top: 25px; }
      @media(max-width: 850px) {
        .filters { grid-template-columns: repeat(2, minmax(150px, 1fr)); }
        .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .graph-tab-body {
            display: flex;
            flex-direction: column;
            width: 100%;
            gap: 14px;
            overflow-x: hidden;
        }
        .graph-card, .guide-card {
            width: 100%;
            min-width: 0;
            max-width: 100%;
            grid-column: auto;
            min-height: auto;
        }
        .graph-card { height: 540px; }
        .graph-card .dash-graph,
        .graph-card .dash-graph > div,
        .graph-card .js-plotly-plot,
        .graph-card .plot-container,
        .graph-card .svg-container {
            width: 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
        }
        .guide-card { order: 1; }
        .graph-card { order: 2; }
      }
      @media(max-width: 560px) {
        .filters, .kpi-grid { grid-template-columns: 1fr; }
        .topbar h1 { font-size: 20px; }
        .page { padding-left: 12px; padding-right: 12px; }
        .graph-card { height: 480px; }
      }
    </style>
</head>
<body>
    {%app_entry%}
    <footer>
      {%config%}
      {%scripts%}
      {%renderer%}
    </footer>
</body>
</html>
"""

app.layout = html.Div([
    html.Div(className="topbar", children=[
        html.H1("VIOLENCE AGAINST WOMEN & GIRLS"),
        html.P("SDG 5 — Gender Equality | Demographic and Health Survey (DHS) attitudes data"),
    ]),
    html.Div(className="page", children=[
        html.Div("DATA EXPLORER — FILTERS", className="section-title"),
        html.Div(className="filters", children=[
            html.Div([
                html.Label("Country", className="filter-label"),
                dcc.Dropdown(id="country-filter", options=make_options(valid["Country"]),
                             value="__ALL__", clearable=False),
            ]),
            html.Div([
                html.Label("Gender", className="filter-label"),
                dcc.Dropdown(id="gender-filter", options=make_options(valid["Gender"]),
                             value="__ALL__", clearable=False),
            ]),
            html.Div([
                html.Label("Demographic grouping", className="filter-label"),
                dcc.Dropdown(id="demo-filter", options=make_options(valid["Demographics Question"]),
                             value="__ALL__", clearable=False),
            ]),
            html.Div([
                html.Label("Demographic response", className="filter-label"),
                dcc.Dropdown(id="response-filter", options=make_options(valid["Demographics Response"]),
                             value="__ALL__", clearable=False),
            ]),
            html.Div([
                html.Label("Survey statement", className="filter-label"),
                dcc.Dropdown(id="question-filter", options=make_options(valid["Question"], "All statements"),
                             value="__ALL__", clearable=False),
            ]),
            html.Div([
                html.Label("Survey year", className="filter-label"),
                dcc.Dropdown(id="year-filter", options=make_options(valid["Survey Year"]),
                             value="__ALL__", clearable=False),
            ]),
        ]),

        html.Div("OVERVIEW", className="section-title"),
        html.Div(className="kpi-grid", children=[
            kpi_card("Average agreement", "kpi-average", "Unweighted mean of filtered percentages"),
            kpi_card("Countries represented", "kpi-countries", "Distinct countries in filtered data"),
            kpi_card("Survey records", "kpi-records", "Rows with a valid percentage value"),
            kpi_card("Highest reported value", "kpi-high", "Maximum percentage in filtered data"),
        ]),

        html.Div("KEY FINDINGS", className="section-title"),
        html.Div(id="insight-text", className="insight"),

        html.Div("GRAPH EXPLORER", className="section-title"),
        dcc.Tabs(
            id="graph-tabs",
            value="bar",
            className="graph-tabs",
            children=[graph_tab(graph_id) for graph_id in GRAPH_IDS],
        ),

        html.Div("FILTERED DATA", className="section-title"),
        html.Div(className="data-panel", children=[
            html.Div(
                style={"display": "flex", "justifyContent": "space-between",
                       "alignItems": "center", "gap": "12px", "flexWrap": "wrap",
                       "padding": "5px 3px 12px"},
                children=[
                    html.Div("Explore the underlying survey percentages",
                             style={"fontWeight": "700", "color": NAVY}),
                    html.Button(
                        "Download filtered CSV", id="download-button",
                        style={"background": GREEN, "color": "white", "border": "0",
                               "padding": "10px 15px", "borderRadius": "6px",
                               "fontWeight": "700", "cursor": "pointer"},
                    ),
                    dcc.Download(id="download-data"),
                ],
            ),
            dash_table.DataTable(
                id="data-table",
                columns=[
                    {"name": "Country", "id": "Country"},
                    {"name": "Gender", "id": "Gender"},
                    {"name": "Demographic grouping", "id": "Demographics Question"},
                    {"name": "Demographic response", "id": "Demographics Response"},
                    {"name": "Survey statement", "id": "Question label"},
                    {"name": "Survey year", "id": "Survey Year"},
                    {"name": "Agreement (%)", "id": "Value", "type": "numeric",
                     "format": {"specifier": ".1f"}},
                ],
                page_size=12,
                sort_action="native",
                filter_action="native",
                style_table={"overflowX": "auto"},
                style_cell={"fontFamily": "Arial", "fontSize": 11, "padding": "9px",
                            "textAlign": "left", "minWidth": "95px",
                            "maxWidth": "260px", "whiteSpace": "normal"},
                style_header={"backgroundColor": NAVY, "color": "white",
                              "fontWeight": "bold", "border": "0"},
                style_data={"borderColor": GRID},
                style_data_conditional=[
                    {"if": {"row_index": "odd"}, "backgroundColor": "#F8FAFC"}
                ],
            ),
        ]),
        html.Div(
            "Interpretation: Value is the percentage of people surveyed in the relevant group "
            "who agree with the statement. These are attitudes/perceived justifications, not "
            "measured incidence or prevalence of violence. The dataset does not include respondent "
            "counts or weights, so averages are unweighted. Missing Value entries are excluded.",
            className="note",
        ),
        html.Div("Source: supplied VAWG dataset, data dictionary and data description.",
                 className="footer"),
    ]),
])


# ---------------------------------------------------------------------
# Shared filter callback
# ---------------------------------------------------------------------
@app.callback(
    Output("response-filter", "options"),
    Output("response-filter", "value"),
    Input("demo-filter", "value"),
    State("response-filter", "value"),
)
def update_response_options(demo_type, current_value):
    if demo_type == "__ALL__":
        subset = valid["Demographics Response"]
    else:
        subset = valid.loc[
            valid["Demographics Question"] == demo_type, "Demographics Response"
        ]
    values = sorted(subset.dropna().unique().tolist(), key=lambda x: str(x))
    opts = [{"label": "All", "value": "__ALL__"}] + [
        {"label": str(value), "value": value} for value in values
    ]
    value = current_value if current_value in values else "__ALL__"
    return opts, value


@app.callback(
    Output("kpi-average", "children"),
    Output("kpi-countries", "children"),
    Output("kpi-records", "children"),
    Output("kpi-high", "children"),
    Output("insight-text", "children"),
    Output("data-table", "data"),
    *[Output(f"graph-{graph_id}", "figure") for graph_id in GRAPH_IDS],
    Input("country-filter", "value"),
    Input("gender-filter", "value"),
    Input("demo-filter", "value"),
    Input("response-filter", "value"),
    Input("question-filter", "value"),
    Input("year-filter", "value"),
)
def update_dashboard(country, gender, demo_type, demo_response, question, year):
    data = filter_data(country, gender, demo_type, demo_response, question, year)

    if data.empty:
        no_data = "No valid percentage values match the selected filters. Change or clear one or more filters."
        figs = build_figures(data)
        return ("—", "0", "0", "—", no_data, [], *[figs[g] for g in GRAPH_IDS])

    avg = data["Value"].mean()
    highest = data["Value"].max()
    country_count = data["Country"].nunique()

    question_means = data.groupby("Question label")["Value"].mean().sort_values(ascending=False)
    highest_question = question_means.index[0]
    lowest_question = question_means.index[-1]

    insight = (
        f"Within the current selection, the average agreement is {avg:.1f}%. "
        f"The highest average agreement is for “{highest_question}” "
        f"({question_means.iloc[0]:.1f}%), while the lowest is for "
        f"“{lowest_question}” ({question_means.iloc[-1]:.1f}%). "
        "These figures describe respondents’ stated attitudes, not actual violence rates."
    )

    table = data[[
        "Country", "Gender", "Demographics Question", "Demographics Response",
        "Question label", "Survey Year", "Value"
    ]].copy()
    table["Value"] = table["Value"].round(1)
    table = table.sort_values(["Country", "Survey Year", "Gender"])

    figures = build_figures(data)
    return (
        f"{avg:.1f}%", f"{country_count:,}", f"{len(data):,}", f"{highest:.1f}%",
        insight, table.to_dict("records"),
        *[figures[g] for g in GRAPH_IDS]
    )


@app.callback(
    Output("download-data", "data"),
    Input("download-button", "n_clicks"),
    State("country-filter", "value"),
    State("gender-filter", "value"),
    State("demo-filter", "value"),
    State("response-filter", "value"),
    State("question-filter", "value"),
    State("year-filter", "value"),
    prevent_initial_call=True,
)
def download_filtered(n_clicks, country, gender, demo_type, demo_response, question, year):
    if not n_clicks:
        raise PreventUpdate
    data = filter_data(country, gender, demo_type, demo_response, question, year)
    columns = [
        "RecordID", "Country", "Gender", "Demographics Question",
        "Demographics Response", "Question", "Survey Year", "Value"
    ]
    return dcc.send_data_frame(
        data[columns].to_csv, "vawg_filtered_data.csv", index=False
    )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)
