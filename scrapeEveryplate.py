from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os
import PySimpleGUI as sg
import jinja2

Dict = {"@context": "http://schema.org", "@type": "Recipe"}
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1200")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--disable-extensions")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument(
    "--user-agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'"
)
browser = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)


def getData(URL):
    # URL = input("Everyplate URL: ")
    browser.get(URL)
    time.sleep(2)
    return browser


def parseData():
    soup = BeautifulSoup(browser.page_source, "html.parser")

    title = soup.find("h1")
    description = soup.find("p", {"class": "web-1u68b9m"})
    photo = soup.find("img", {"class": "web-1y6p807"})
    measurements = []
    ingredients = []
    combined = []
    steps = []
    totaltime = soup.find("div", {"data-test-id": "prep-time"})
    totaltime = totaltime.text[:2]
    nutrition = []
    nutritionDict = {"@type": "NutritionInformation"}

    for nutritioninfo in soup.find_all("div", {"class": "web-dxsv06"}):
        if nutritioninfo.text != "Per serving":
            nutrition.append(nutritioninfo.text)

    for item in nutrition:
        key, value = (
            item[: item.index(next(filter(str.isdigit, item)))],
            item[item.index(next(filter(str.isdigit, item))) :],
        )
        match key:
            case "Calories":
                key = "calories"
            case "Fat":
                key = "fatContent"
            case "Saturated Fat":
                key = "saturatedFatContent"
            case "Carbohydrate":
                key = "carbohydrateContent"
            case "Sugar":
                key = "sugarContent"
            case "Dietary Fiber":
                key = "fiberContent"
            case "Protein":
                key = "proteinContent"
            case "Cholesterol":
                key = "cholesterolContent"
            case "Sodium":
                key = "sodiumContent"
            case _:
                key = "invalidkey"
        nutritionDict[key] = value

    for measurement in soup.find_all("p", {"class": "web-x2qc7m"}):
        measurements.append(measurement.text)

    for ingredient in soup.find_all("p", {"class": "web-1uk1gs8"}):
        ingredients.append(ingredient.text)

    for count, measurement in enumerate(measurements):
        combine = measurement + " " + ingredients[count]
        combine = combine.replace("Measurement: ", "")
        combined.append(combine)

    for step in soup.find_all("div", {"class": "web-1hhw9qn"}):
        steptype = "HowToStep"
        steptext = step.text.strip().replace("\n", " ")
        steps.append({"@type": steptype, "text": steptext})

    print(nutritionDict["calories"])
    return title, description, photo, combined, steps, totaltime, nutritionDict


def buildDict(
    title, description, photo, combined, steps, totaltime, nutritionDict
):
    Dict["name"] = title.text.strip()
    Dict["description"] = description.text.strip()
    Dict["image"] = {"@type": "ImageObject", "url": photo["src"]}
    Dict["recipeIngredient"] = combined
    Dict["recipeInstructions"] = steps
    Dict["totalTime"] = "PT" + totaltime + "M"
    Dict["nutrition"] = nutritionDict
    Dict["recipeYield"] = "2 Servings"
    return Dict


def buildRecipeJSON(Dict):
    strHTML = (
        '<html><body><div id="s11qqD"><script type="application/ld+json">'
    )
    strHTML = strHTML + json.dumps(Dict) + "</script></div></body></html>"

    hs = open(Dict["name"].replace("’", "") + ".html", "w")
    hs.write(strHTML)


def buildRecipeHTML(Dict):
    title = Dict["name"]
    outputfile = Dict["name"].replace("’", "") + ".html"
    subs = (
        jinja2.Environment(loader=jinja2.FileSystemLoader("./"))
        .get_template("template.html")
        .render(title=title, json=json.dumps(Dict))
    )
    with open(outputfile, "w") as f:
        f.write(subs)


def buildIndexHTML():
    strIndexHTML = "<!DOCTYPE html>\n<html>\n<body>"
    files = [f for f in os.listdir(".") if f.endswith("html")]
    files.sort(key=lambda x: os.path.getmtime(x))
    for f in files:
        if f != "index.html":
            strIndexHTML = (
                strIndexHTML
                + "\n<p><a href='https://tito13kfm.github.io/"
                + f
                + "'>"
                + f.strip(".html")
                + "</a>"
            )

    strIndexHTML = strIndexHTML + "\n</body></html>"

    index = open("index.html", "w")
    index.write(strIndexHTML)


def gui():
    layout = [
        [sg.Text("Enter URL for recipe.")],
        [sg.InputText()],
        [sg.Submit(), sg.Cancel()],
    ]

    window = sg.Window("EveryPlate Scraper", layout)

    event, values = window.read()
    window.close()

    text_input = values[0]
    getData(text_input)


gui()
(
    title,
    description,
    photo,
    combined,
    steps,
    totaltime,
    nutritionDict,
) = parseData()
Dict = buildDict(
    title, description, photo, combined, steps, totaltime, nutritionDict
)
buildRecipeHTML(Dict)
buildIndexHTML()
