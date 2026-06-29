import requests
import json

from flask import (
    Flask,
    render_template,
    request
)

app = Flask(__name__)

# =========================================
# LOAD JSON DATASET
# =========================================

with open("crop_rules.json", "r") as f:

    crop_data = json.load(f)

# =========================================
# HOME PAGE
# =========================================

@app.route("/")

def home():

    categories = list(crop_data.keys())

    return render_template(

        "index.html",

        categories=categories
    )

# =========================================
# CATEGORY PAGE
# =========================================

@app.route("/category/<path:category_name>")

def category_page(category_name):

    if category_name not in crop_data:

        return "Category not found ❌"

    crops = list(

        crop_data[category_name]["crops"].keys()
    )

    return render_template(

        "category.html",

        category_name=category_name,

        crops=crops
    )

# =========================================
# CROP PAGE
# =========================================

@app.route("/crop/<path:crop_name>")

def crop_page(crop_name):

    activities = []

    for category in crop_data:

        if crop_name in crop_data[category]["crops"]:

            activities = list(

                crop_data[category][
                    "default_rules"
                ].keys()
            )

            break

    return render_template(

        "crop.html",

        crop_name=crop_name,

        activities=activities
    )

# =========================================
# LOCATION PAGE
# =========================================

@app.route("/location/<path:crop_name>/<path:activity>")

def location_page(

    crop_name,
    activity
):

    return render_template(

        "location.html",

        crop_name=crop_name,

        activity=activity
    )

# =========================================
# FORECAST PAGE
# =========================================

@app.route("/forecast", methods=["POST"])

def forecast():

    crop_name = request.form["crop_name"]

    activity = request.form["activity"]

    latitude = request.form["latitude"]

    longitude = request.form["longitude"]

    # =====================================
    # OPENWEATHER API
    # =====================================

    API_KEY = "bf200bc11fc5d187295e4028cb8b5b0e"

    url = (

        f"https://api.openweathermap.org/data/2.5/forecast?"
        f"lat={latitude}&lon={longitude}"
        f"&appid={API_KEY}&units=metric"

    )

    response = requests.get(url)

    weather_data = response.json()

    # =====================================
    # API ERROR CHECK
    # =====================================

    if weather_data["cod"] != "200":

        return "Weather API Error ❌"

    forecasts = weather_data["list"]

    forecast_results = []

    # =====================================
    # GET ONLY ONE FORECAST PER DAY
    # =====================================

    daily_forecasts = []

    for forecast in forecasts:

        if "12:00:00" in forecast["dt_txt"]:

            daily_forecasts.append(forecast)

    # =====================================
    # FORECAST ANALYSIS
    # =====================================

    for forecast in daily_forecasts[:5]:

        # =================================
        # WEATHER DATA
        # =================================

        date = forecast["dt_txt"].split(" ")[0]

        temp = forecast["main"]["temp"]

        humidity = forecast["main"]["humidity"]

        wind = forecast["wind"]["speed"]

        # =================================
        # RAINFALL DATA
        # =================================

        rainfall = 0

        if "rain" in forecast:

            rainfall = forecast["rain"].get("3h", 0)

        # =================================
        # DEFAULT DECISION
        # =================================

        decision = "Moderately Suitable ⚠"

        rules = {}

        # =================================
        # FIND RULES
        # =================================

        for category in crop_data:

            if crop_name in crop_data[category]["crops"]:

                crop_info = (

                    crop_data[category]["crops"][crop_name]
                )

                # =============================
                # DEFAULT RULES
                # =============================

                rules = (

                    crop_data[category][
                        "default_rules"
                    ].get(activity, {})
                )

                # =============================
                # OVERRIDE RULES
                # =============================

                override_rules = (

                    crop_info.get(
                        "override",
                        {}
                    ).get(activity, {})
                )

                # =============================
                # MERGE RULES
                # =============================

                rules.update(override_rules)

                break

        # =================================
        # APPLY RULES
        # =================================

        if rules:

            suitable = True

            # =============================
            # TEMPERATURE RULES
            # =============================

            if "temperature" in rules:

                min_temp = rules["temperature"][0]

                max_temp = rules["temperature"][1]

                if temp < min_temp or temp > max_temp:

                    suitable = False

            # =============================
            # HUMIDITY RULES
            # =============================

            if "humidity" in rules:

                min_humidity = rules["humidity"][0]

                max_humidity = rules["humidity"][1]

                if (

                    humidity < min_humidity
                    or
                    humidity > max_humidity

                ):

                    suitable = False

            # =============================
            # WIND RULES
            # =============================

            if "wind" in rules:

                min_wind = rules["wind"][0]

                max_wind = rules["wind"][1]

                if wind < min_wind or wind > max_wind:

                    suitable = False

            # =============================
            # RAIN RULES
            # =============================

            if "rain" in rules:

                rain_rule = rules["rain"]

                if rain_rule == "avoid" and rainfall > 0:

                    suitable = False

                elif (

                    rain_rule == "no_rain"
                    and
                    rainfall > 0

                ):

                    suitable = False

            # =============================
            # FINAL DECISION
            # =============================

            if suitable:

                decision = "Suitable ✅"

            else:

                decision = "Not Suitable ❌"

        # =================================
        # SAVE RESULT
        # =================================

        forecast_results.append({

            "date": date,

            "temp": temp,

            "humidity": humidity,

            "wind": wind,

            "rainfall": rainfall,

            "decision": decision

        })

    # =====================================
    # SEND RESULTS TO HTML
    # =====================================

    return render_template(

        "activity.html",

        crop_name=crop_name,

        activity=activity,

        forecast_data=forecast_results
    )

# =========================================
# RUN FLASK
# =========================================

if __name__ == "__main__":

    app.run(debug=True)
