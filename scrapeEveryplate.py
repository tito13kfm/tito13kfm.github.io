from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time
import json

Dict = {"@context": "http://schema.org", "@type": "Recipe"}
URL = input("Everyplate URL:")
options = Options()
browser = webdriver.Chrome(
    executable_path=r"C:\cmder\bin\chromedriver.exe", options=options
)


browser.get(URL)
time.sleep(2)

soup = BeautifulSoup(browser.page_source, "html.parser")

title = soup.find("h1")
description = soup.find("p", {"class": "web-1u68b9m"})
photo = soup.find("img", {"class": "web-1y6p807"})
measurements = []
ingredients = []
combined = []
steps = []
pictures = []

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


Dict["name"] = title.text.strip()
Dict["description"] = description.text.strip()
Dict["image"] = {"@type": "ImageObject", "url": photo["src"]}
Dict["recipeIngredient"] = combined
Dict["recipeInstructions"] = steps


for img in soup.find_all("div", {"class": "web-1bauk15"}):
    for picture in img:
        pictures.append(picture["src"])


# print(title.text.strip())
# print(description.text)
# for ingredient in ingredients:
# print(ingredient)
# for measurement in measurements:
# print(measurement)
# for step in steps:
# print(step)
# print("\n")
# for picture in pictures:
# print(picture)
# print(photo["src"])

# print(Dict)

# with open("sample.json", "w") as outfile:
# json.dump(Dict, outfile)

strHTML = '<html><body><div id="s11qqD"><script type="application/ld+json">'
strHTML = strHTML + json.dumps(Dict) + "</script></div></body></html>"

hs = open(Dict["name"] + ".html", "w")
hs.write(strHTML)

# print(steps)
