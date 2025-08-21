from flask import Blueprint, render_template, request, jsonify
import pandas as pd
from pathlib import Path

bp = Blueprint("main", __name__)
DATA = Path(__file__).resolve().parent / "data" / "county_density.csv"

# Load once at startup (simple v0 approach)
DF = pd.read_csv(DATA, dtype={"county_fips": str})
if "state_fips" not in DF.columns:
    DF["state_fips"] = DF["county_fips"].str[:2]

@bp.route("/")
def index():
    # simple preview table on the homepage
    table = DF.head(100).to_html(classes="table table-striped table-sm", index=False)
    states = sorted(DF["state_fips"].dropna().unique())
    return render_template("index.html", table=table, states=states)

@bp.route("/api/density")
def api_density():
    q = DF.copy()
    state = request.args.get("state_fips")
    county = request.args.get("county_fips")
    top = int(request.args.get("top", 100))

    if state:
        q = q[q["state_fips"] == state]
    if county:
        q = q[q["county_fips"] == county]

    sort_col = "density_per_1k" if "density_per_1k" in q.columns else (
        "employment_5415" if "employment_5415" in q.columns else "population"
    )
    q = q.sort_values(sort_col, ascending=False).head(top)

    cols = [c for c in ["state_fips","county_fips","county_name","population","employment_5415","density_per_1k"] if c in q.columns]
    return jsonify(q[cols].to_dict(orient="records"))
