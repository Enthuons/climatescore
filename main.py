import requests
import json
import pytemperature

from shapely.geometry import shape, Point
from flask import Flask, render_template, render_template_string, request
from google.cloud import bigquery
from descriptions import *

with open('config.json') as json_file:
    config = json.load(json_file)

client = bigquery.Client.from_service_account_json('client_secrets.json')

app = Flask(__name__,static_folder="static")


@app.route('/')
def index():
    return render_template("get-location-detail.html", API_KEY=config["API_KEY"])
    #return render_template("climatescore_results2.html")


@app.route('/get-location')
def page_url():
    return render_template("climatescore-results.html", API_KEY=config["API_KEY"])


@app.route('/get-latlong', methods=['POST'])
def lat_long():
    latitude = ''
    longitude = ''
    temp_score = ''
    zipcode = ''
    address = request.form['location']  # completed location name acquired....

    api_response = requests.get(
        'https://maps.googleapis.com/maps/api/geocode/json?address={0}&key={1}'.format(address, config["API_KEY"]))

    api_response_dict = api_response.json()

    # Get lat/long and zipcode (zip needed for carbon footprint)
    if api_response_dict['status'] == 'OK':
        latitude = api_response_dict['results'][0]['geometry']['location']['lat']
        longitude = api_response_dict['results'][0]['geometry']['location']['lng']
        for component in api_response_dict['results'][0]['address_components']:
            if 'postal_code' in component["types"]:
                zipcode = component["short_name"]
    # if address doesn't include a zip then geocode the lat/long to get zip
    if zipcode == '':
        api_response = requests.get(
            f'https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&key'
            f'=AIzaSyB11Toeld9R2HrFTioF2Ixxk1j7c2nA0aQ')
        api_response_dict = api_response.json()
        if api_response_dict['status'] == 'OK':
            for component in api_response_dict['results'][0]['address_components']:
                if 'postal_code' in component["types"]:
                    zipcode = component["short_name"]
    # no zip found
    if zipcode == '' or latitude == '' or longitude == '':
        msg = "Data for the given location could not be found! Please make sure your location is within CA."
        return render_template("get-location-detail.html", msg=msg, API_KEY=config["API_KEY"])

    # TEMPSCORE
    try:
        QUERY = (
            "WITH a AS ("
            f"SELECT ST_GEOGPOINT({longitude},{latitude}) my_point"
            "), b AS ("
            "SELECT *, ST_GEOGPOINT(lon,lat) latlon_geo "
            "FROM `climatescore.tempscore`"
            ") "
            "SELECT future_yearly_max_heat_days,tempscore,_98th_perc_historic "
            "FROM ("
            "SELECT loc.*, my_point "
            "FROM ("
            "SELECT ST_ASTEXT(my_point) my_point, ANY_VALUE(my_point) geop, "
            "ARRAY_AGG(STRUCT(future_yearly_max_heat_days,tempscore,_98th_perc_historic) ORDER BY  ST_DISTANCE("
            "my_point, b.latlon_geo) LIMIT 1)[SAFE_OFFSET(0)] loc "
            "FROM a, b "
            "WHERE ST_DWITHIN(my_point, b.latlon_geo, 100000) "
            "GROUP BY my_point"
            ")"
            ")"
        )
        temp_score = ""
        perc_temp = ""
        future_yearly_max_heat_days = ""
        query_job = client.query(QUERY)
        rows = query_job.result()
        for row in rows:
            temp_score = row.tempscore
            perc_temp = row._98th_perc_historic
            perc_temp = round(pytemperature.k2f(perc_temp))
            # acquire data from bigquery and convert K to F
            future_yearly_max_heat_days = row.future_yearly_max_heat_days

    except Exception as e:
        print("tempscore query error")
        print(e)

    # CARBONFOOTPRINT
    carbonFootprintScore = ''
    TotalHouseholdCarbonFootprint =''
    try:
        QUERY = (
            "SELECT TotalHouseholdCarbonFootprint, CarbonFootprintScore FROM `climatescore.carbonfootprintscore` WHERE "
            f"ZipCode = {zipcode}"
        )
        query_job = client.query(QUERY)
        rows = query_job.result()
        for row in rows:
            carbonFootprintScore = row.CarbonFootprintScore
            TotalHouseholdCarbonFootprint = round(row.TotalHouseholdCarbonFootprint, 2)

    except Exception as e:
        print("carbonfootprint query error")
        print(e)

    # FIRESCORE
    try:
        QUERY = (
            "WITH a AS ("
            f"SELECT ST_GEOGPOINT({longitude},{latitude}) my_point"
            "), b AS ("
            "SELECT *, ST_GEOGPOINT(lon,lat) latlon_geo "
            "FROM `climatescore.firescore`"
            ") "
            "SELECT avg_historic_yearly_acres,avg_future_yearly_acres,firescore "
            "FROM ("
            "SELECT loc.*, my_point "
            "FROM ("
            "SELECT ST_ASTEXT(my_point) my_point, ANY_VALUE(my_point) geop, "
            "ARRAY_AGG(STRUCT(avg_historic_yearly_acres,avg_future_yearly_acres,firescore) ORDER BY  ST_DISTANCE(my_point, b.latlon_geo) LIMIT 1)[SAFE_OFFSET(0)] loc "
            "FROM a, b "
            "WHERE ST_DWITHIN(my_point, b.latlon_geo, 100000) "
            "GROUP BY my_point"
            ")"
            ")"
        )
        avg_historic_yearly_acres = ''
        avg_future_yearly_acres = ''
        firescore = ''
        query_job = client.query(QUERY)
        rows = query_job.result()
        for row in rows:
            avg_future_yearly_acres = round(row.avg_future_yearly_acres)
            avg_historic_yearly_acres = round(row.avg_historic_yearly_acres)
            firescore = row.firescore

    except Exception as e:
        print("firescore query error")
        print(e)

    # DROUGHTSCORE
    # load GeoJSON file containing sectors
    HUC8 = ''
    with open('huc8.json') as f:
        js = json.load(f)
    # construct point based on lon/lat returned by geocoder
    point = Point(longitude, latitude)
    # check each polygon to see if it contains the point
    for feature in js['features']:
        polygon = shape(feature['geometry'])
        if polygon.contains(point):
            HUC8 = feature['properties']['HUC8']
    # quit if can't find HUC8
    if HUC8 == '':
        msg = "Data for the given location could not be found! Please make sure your location is within CA."
        return render_template("get-location-detail.html", msg=msg, API_KEY=config["API_KEY"])

    # Query DB for Droughtscore info
    droughtscore = ''
    try:
        QUERY = (
            "SELECT droughtscore, future_historic FROM `climatescore.climatescore.droughtscore` WHERE "
            f"HUC8={HUC8}"
        )
        query_job = client.query(QUERY)
        rows = query_job.result()
        for row in rows:
            droughtscore = row.droughtscore
            drought_future_historic = row.future_historic

    except Exception as e:
        print("droughtscore query error")
        print(e)

    if temp_score != '' and zipcode != '' and carbonFootprintScore != '' and firescore != '' and droughtscore != '' and HUC8 != '':
        msg = "Temperature data retrieved successfully!"
        climateScore = round((droughtscore+firescore+temp_score)/3)
        climateScoreDescription = str(ScoreDescription(climateScore,'climate change',0))
        tempScoreDescription = str(TempScoreDescription(temp_score, perc_temp, future_yearly_max_heat_days))
        fireScoreDescription = str(FireScoreDescription(firescore,avg_future_yearly_acres))
        droughtScoreDescription = str(DroughtScoreDescription(droughtscore, drought_future_historic))
        carbonScoreDescription = str(CarbonScoreDescription(carbonFootprintScore, TotalHouseholdCarbonFootprint))
        return render_template("climatescore-results.html",
                               climatescore=climateScore,
                               droughtscore=droughtscore,
                               droughtScoreDescription=droughtScoreDescription,
                               firescore=firescore,
                               fireScoreDescription=fireScoreDescription,
                               carbonFootprintScore=carbonFootprintScore,
                               carbonScoreDescription=carbonScoreDescription,
                               temp_score=temp_score,
                               tempScoreDescription=tempScoreDescription,
                               climateScoreDescription=climateScoreDescription,
                               latitude=latitude,
                               longitude=longitude, loc=address, msg=msg,
                               API_KEY=config["API_KEY"])
    else:
        # given dataset seems to have data for locations in California
        msg = "Data for the given location could not be found! Please make sure your location is within CA."
    return render_template("climatescore-results.html", msg=msg, API_KEY=config["API_KEY"])


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
