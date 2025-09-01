# Cloud – Flask UI for CS Job Density - Sampreethi66

Local run:

	  python -m venv env

	  env\Scripts\activate

	  pip install -r requirements.txt

	  python wsgi.py

Endpoints:

	  / -> simple table + filters UI

	  /api/density -> JSON (supports ?state_fips= & ?county_fips= & ?top=)



Flask UI for CS job density

	Endpoints: /, /health, /api/county_density, /download/county_density.csv

	Filters: state_fips, county_fips, county, limit