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
    try:
        totaltime = soup.find("div", {"data-test-id": "prep-time"})
    except:
        totaltime = ""
    if totaltime:
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
        if "unit" in measurement:
            match ingredients[count]:
                case "Sour Cream" | "Cream Cheese" | "Carrot":
                    measurement = measurement.replace("unit", "oz.")
                case "Dried Oregano" | "Beef Stock Concentrate" | "Chicken Stock Concentrate" | "Cumin" | "Ancho Chili Powder" | "Chili Powder" | "Soy Sauce":
                    measurement = measurement.replace("unit", "tsp.")
                case "White Bread":
                    measurement = measurement.replace("unit", "slice")
                case "Ground Beef" | "Ground Turkey" | "Ground Pork":
                    measurement = measurement.replace("1 unit", "10oz package")
                case "Panko Breadcrumbs":
                    measurement = measurement.replace("1 unit", "1/4 cup")
                case "Shredded Pepper Jack" | "Shredded Cheddar":
                    measurement = measurement.replace("1 unit", "1/2 cup")
                case "Reduced Fat Milk":
                    measurement = measurement.replace("1 unit", "1 cup")
                case "Jasmine Rice":
                    measurement = measurement.replace("1 unit", "3/4 cup")
                case _:
                    measurement = measurement.replace("unit", "")
        combine = (
            measurement.replace("Measurement: ", "") + " " + ingredients[count]
        )
        combine = combine
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
    if totaltime:
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
        if f != "index.html" and f != "template.html":
            strIndexHTML = (
                strIndexHTML
                + "\n<p><a href='https://tito13kfm.github.io/"
                + f
                + "'>"
                + f.removesuffix(".html")
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


# gui()
listURL = [
    # "https://www.everyplate.com/recipes/gouda-bacon-smothered-chicken-5f5233ac4ee2b7481c0b502b",
    # "https://www.everyplate.com/recipes/bacon-carbonara-flatbread-63a1d054ef8967b3ec0bb717?week=2023-W03",
    # "https://www.everyplate.com/recipes/bacony-chicken-linguine-5f9c12b9e8c00e26f0491f83",
    # "https://www.everyplate.com/recipes/buffalo-turkey-smashburgers-631f81303f4a8ab56b07d3ee",
    # "https://www.everyplate.com/recipes/cajun-chicken-sandwiches-622fd490cddafb31d31766ee",
    # "https://www.everyplate.com/recipes/charred-zucchini-tomato-melts-6116743148cf1901e428cbcb",
    # "https://www.everyplate.com/recipes/cheesy-steak-onion-sandos-63a0b10d567d6a1915028767?week=2023-W03",
    # "https://www.everyplate.com/recipes/crispy-parm-frico-burgers-5da087b8f46c5975406e2b26",
    # "https://www.everyplate.com/recipes/cumin-beef-lettuce-wraps-639762ae07ec98914d0847df?week=2023-W02",
    # "https://www.everyplate.com/recipes/firehouse-mac-n-cheese-629665673cbae92968074731",
    # "https://www.everyplate.com/recipes/garlic-rosemary-chicken-5d2891f89de58100083b19b1",
    # "https://www.everyplate.com/recipes/ginger-ponzu-turkey-bowls-5fb7d364c7e7816b27768597",
    # "https://www.everyplate.com/recipes/2019-w2-r4-gooey-stuffed-pork-burgers-5c13d0bfe3f339058c1a84e2",
    # "https://www.everyplate.com/recipes/southern-style-pork-chops-gravy-63b445e1871119060104364e?week=2023-W05",
    # "https://www.everyplate.com/recipes/herby-parmesan-crusted-chicken-5fec8f42c3bf101f0400ba2f",
    # "https://www.everyplate.com/recipes/homestyle-panko-crusted-chicken-63a0cc8c0566f8f9ee039613?week=2023-W03",
    # "https://www.everyplate.com/recipes/hotel-butter-steak-5e0f4fbba69d465d296f9038",
    # "https://www.everyplate.com/recipes/jammin-fig-pork-chops-63a094e7d4ce7f7ba80f109e?week=2023-W03",
    # "https://www.everyplate.com/recipes/pepper-jack-stuffed-pork-burgers-5e7cf8088063c85c7017a0c2",
    # "https://www.everyplate.com/recipes/linguine-italiano-5f514f12b13b96435641474c",
    # "https://www.everyplate.com/recipes/roasted-bell-pepper-and-sausage-risotto-5d4d8cb4720732000b60fe8a",
    # "https://www.everyplate.com/recipes/southern-style-pork-chops-gravy-63b445e1871119060104364e?week=2023-W05",
    # "https://www.everyplate.com/recipes/southwest-pork-black-bean-chili-62b1d999aec060a5e40aa8d9",
    "https://www.everyplate.com/recipes/honey-garlic-chicken-5e73c554f1f4f54ec32b3b6c",
    "https://www.everyplate.com/recipes/gravy-lover-s-meatballs-5ec7da11c1fac21b2d322c38",
    "https://www.everyplate.com/recipes/sriracha-apricot-pork-chops-6271338b63be6525ba09ae47",
    "https://www.everyplate.com/recipes/sweet-spicy-bacon-gouda-burgers-61fc99a637144d2b12247d10",
    "https://www.everyplate.com/recipes/sweet-spicy-ponzu-pork-meatballs-60df191939d7d825ff4b8662",
    "https://www.everyplate.com/recipes/sweet-chili-chicken-60d55f89abdcef0ddd6ec002",
    "https://www.everyplate.com/recipes/triple-cheese-mac-n-cheese-63a096f2117ea980da0f45f5?week=2023-W03",
]


for URL in listURL:
    getData(URL)

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
