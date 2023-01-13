from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os

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


def getData():
    URL = input("Everyplate URL: ")
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

    return title, description, photo, combined, steps


def buildDict(title, description, photo, combined, steps):
    Dict["name"] = title.text.strip()
    Dict["description"] = description.text.strip()
    Dict["image"] = {"@type": "ImageObject", "url": photo["src"]}
    Dict["recipeIngredient"] = combined
    Dict["recipeInstructions"] = steps
    return Dict


def buildRecipeJSON(Dict):
    strHTML = (
        '<html><body><div id="s11qqD"><script type="application/ld+json">'
    )
    strHTML = strHTML + json.dumps(Dict) + "</script></div></body></html>"

    hs = open(Dict["name"].replace("’", "") + ".html", "w")
    hs.write(strHTML)


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


getData()
title, description, photo, combined, steps = parseData()
Dict = buildDict(title, description, photo, combined, steps)
buildRecipeJSON(Dict)
buildIndexHTML()
