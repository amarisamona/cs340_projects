from aiohttp.web import Application, run_app, RouteTableDef, Request, FileResponse, StreamResponse, Response
import asyncio
import aiohttp
import tempfile
import datetime
import csv
import shlex

routes = RouteTableDef()

@routes.get('/')
async def index(req: Request) -> StreamResponse:
    return FileResponse(path="index.html")

@routes.post('/filter')
async def filter_image(req: Request) -> StreamResponse:
    multi = await req.multipart()
    png_data = None
    location_data = None 
    lat = None
    lng = None
    tmp = None

    async for part in multi:
        if part.name == 'png':
            try:
                png_data = await part.read()
            except:
                return Response(status=415) # if png invalid
        if part.name == 'location':
            location_data = await part.read()
    
    # open the csv to find latitude and longitude
    with open("cities.csv", newline='') as f:
        reader = csv.DictReader(f)
        city = location_data.decode().split(',')[0]
        city_ascii = city.encode("ascii", errors="ignore").decode()
        
        lat = 40.1164
        lng = 88.2434
        for row in reader:
            if row['city_ascii'] == city_ascii:
                lat = row['lat']
                lng = row['lng']
                break   
    
    tmp = 70
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"https://api.weather.gov/points/{lat},{lng}") as resp1:
                metadata = await resp1.json()
                endpoint = metadata.get("properties", {}).get("forecastHourly")
            if endpoint:
                async with session.get(endpoint) as resp2:
                    forecast = await resp2.json()
                    periods = forecast.get("properties", {}).get("periods", [])
                    if periods:
                        tmp = periods[0].get("temperature", 70)
        except Exception:
            tmp = 70
            
    if (tmp >= 80):
        effect = 'hazy'
    elif (tmp >= 61 and tmp <= 79):
        effect = 'vibrance'
    else:
        effect = 'blue tint'

    #     Usage: ./filter input.png output.png effect
    # Effects: hazy, blue tint, blur, vibrance, red tint, green tint, grayscale, invert, sepia
    img_bytes = None
    with tempfile.TemporaryDirectory() as tmpdir: # creating temporary directory for this request
        input_path = tmpdir + "/input.png"
        output_path = tmpdir + "/output.png"
        with open(input_path, "wb") as f:
            f.write(png_data)
        proc = await asyncio.create_subprocess_exec("./filter", input_path, output_path, effect, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        print("STDERR:", stderr.decode())
        print("STDOUT:", stdout.decode())
        
        with open(output_path, "rb") as f:
            img_bytes = f.read()
        return Response(body=img_bytes, content_type="image/png")

def setup_app(app):
    # put any setup you want to do in this function, not in the global scope
    app.add_routes(routes)


#### DO NOT MODIFY CODE BELOW THIS LINE ####
if __name__ == '__main__':
    app = Application()
    setup_app(app)
    run_app(app, host='0.0.0.0', port=4595)
# trigger regrade
# trigger regrade
# triggerring me so badly
