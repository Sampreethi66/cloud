\# cloud – Flask UI for CS Job Density



Local run:

&nbsp; python -m venv env

&nbsp; env\\Scripts\\activate

&nbsp; pip install -r requirements.txt

&nbsp; python wsgi.py



Endpoints:

&nbsp; /            -> simple table + filters UI

&nbsp; /api/density -> JSON (supports ?state\_fips= \& ?county\_fips= \& ?top=)



