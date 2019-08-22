import requests
import json

from flask import Flask,render_template,render_template_string,request
from google.cloud import bigquery

with open('config.json') as json_file:
    config = json.load(json_file)


client = bigquery.Client()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("get-location.html", API_KEY = config["API_KEY"])

@app.route('/get-location')
def page_url():
    return render_template("get-location.html", API_KEY = config["API_KEY"])

@app.route('/get-latlong', methods=['POST'])
def lat_long():
    temp_score = ''
    address =  request.form['location'] #completed location name acquired....
    
        
    api_response = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address={0}&key={1}'.format(address, config["API_KEY"]))
    
    api_response_dict = api_response.json()

    if api_response_dict['status'] == 'OK':
        latitude = api_response_dict['results'][0]['geometry']['location']['lat']
        longitude = api_response_dict['results'][0]['geometry']['location']['lng']
    #acquired latitude and longitude from google api...
    try:          
        QUERY = (
            "WITH a AS ("
            f"SELECT ST_GEOGPOINT({longitude},{latitude}) my_point"
            "), b AS ("
            "SELECT *, ST_GEOGPOINT(lon,lat) latlon_geo "
            "FROM `climatescore.tempscore`" 
            ") "
            "SELECT tempscore,_98th_perc_historic "
            "FROM ("
                "SELECT loc.*, my_point "
                "FROM ("
                    "SELECT ST_ASTEXT(my_point) my_point, ANY_VALUE(my_point) geop, "
                    "ARRAY_AGG(STRUCT(tempscore,_98th_perc_historic) ORDER BY  ST_DISTANCE(my_point, b.latlon_geo) LIMIT 1)[SAFE_OFFSET(0)] loc "
                    "FROM a, b "
                    "WHERE ST_DWITHIN(my_point, b.latlon_geo, 100000) "
                    "GROUP BY my_point"
                    ")"
                ")"         
            )  
        temp_score = ""
        perc_temp = ""
        query_job = client.query(QUERY)
        rows = query_job.result()
        for row in rows:
            temp_score = row.tempscore
            perc_temp  = row._98th_perc_historic
            #temp data acquired from bigquery dataset

    except Exception as e:
        print("query error......................................")
        print(e)
    
    
    if temp_score:
        msg = "Temprature data retrieved successfully!"
        return render_template("get-location.html", loc=address, temp_score=temp_score, perc_temp=perc_temp, msg=msg, API_KEY = config["API_KEY"])
    else:
        #given dataset seems to have data for locations in California
        msg = "Data for the given location could not be found! Please try some other location or check your entry.(dataset seems to have data from California only)"
    return render_template("get-location.html", msg = msg,API_KEY = config["API_KEY"])
    

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)  


