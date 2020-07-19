import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time, os, io
import urllib.request
from PIL import Image

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\infor\PycharmProjects\FlipkartGrid\Keys\VisionAPITokens.json"


def handle_api_errors(response):
    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))


# for feature detection from image
def detect_properties_uri(uri):
    """Detects image properties in the file located in Google Cloud Storage or
    on the Web."""
    from google.cloud import vision
    from google.cloud.vision import types
    from google.protobuf.json_format import MessageToDict

    client = vision.ImageAnnotatorClient()

    try:
        image = Image.open(urllib.request.urlopen(uri))
    except:
        raise Exception("INVALID IMAGE URL ERROR")

    buffer = io.BytesIO()
    image.save(buffer, format='JPEG')
    byte_image = buffer.getvalue()

    image = types.Image(content=byte_image)

    try:
        # Performs label detection on the image file
        response = client.label_detection(image=image, max_results=20)
        handle_api_errors(response)
        # Performs logo detection on image file
        logo = client.logo_detection(image=image)
        handle_api_errors(logo)
        # image properties call
        colour = client.image_properties(image=image, max_results=5)
        handle_api_errors(colour)
    except:
        raise Exception("API ERROR")

    labels = MessageToDict(response, preserving_proto_field_name=True)
    logos = MessageToDict(logo, preserving_proto_field_name=True)
    colors = MessageToDict(colour, preserving_proto_field_name=True)

    labels = labels['label_annotations']
    colors = colors['image_properties_annotation']['dominant_colors']['colors']

    if bool(logos):
        logos = logos['logo_annotations']
        logos = logos[0]

    final_response = {}

    for label in labels:
        final_response[label['description']] = {
            "confidence": label["score"],
            "topicality": label["topicality"]
        }

    if bool(logos):
        final_response["brand"] = {
            "logo": logos["description"],
            "confidence": logos["score"]
        }
    else:
        final_response["logo"] = {
            "brand": None
        }

    final_response["colors_array"] = colors

    return final_response


# for dynamically loaded Content
def scroll_down(browser, numberOfScrollDowns):
    try:
        body = browser.find_element_by_tag_name("body")
        while numberOfScrollDowns >= 0:
            body.send_keys(Keys.PAGE_DOWN)
            numberOfScrollDowns -= 1
            return browser
    except:
        raise Exception("SELENIUM SCROLL DOWN ERROR")


# format user input URL
def handle_url(url):
    if url.startswith("//"):
        url = "https:" + url;

    if url.find("https") == -1 and url.find("http") == -1:
        url = "https://" + url

    return url


# return urls for crawling
def fetch_category_list(url, keywords_array, banned_keywords_array):
    try:
        results = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"})

        src = results.content
        soup = BeautifulSoup(src, "lxml")
        links = soup.find_all("a")

        urlList = []

        for link in links:
            val = link.get("href")

            if val is not None:
                if val.find("http") == -1 and val.find("https") == -1 and val.find("www") == -1:
                    val = url + val

            invalid = False
            if val is not None:
                for keyword in banned_keywords_array:

                    if val.find(keyword) != -1:
                        invalid = True
                        break

                for keyword in keywords_array:

                    if invalid:
                        break

                    if val.find(keyword) != -1:
                        val = handle_url(val)
                        urlList.append(val)

        return urlList
    except:
        raise Exception("CRAWLER ERROR")


def add_url(url, keywords_array):
    keywords = ['asset', 'product', 'cache']

    if url.find("data:image") != -1:
        return False

    for keyword in keywords_array:
        if url.find(keyword) != -1:
            return True

    for keys in keywords:
        if url.find(keys) != -1:
            return True

    return False


# fetch image urls from the page
def fetch_image_urls(url, driver, keywords_array, wait_time=10, scroll_times=50):
    try:
        imageurls = []

        driver.get(url)
        driver.implicitly_wait(wait_time)
        scroll_down(driver, scroll_times)
        time.sleep(wait_time)
        html = driver.page_source

        # print(html)

        soup = BeautifulSoup(html, "lxml")

        imgs = soup.find_all("img")

        for img in imgs:
            if img.has_attr('src'):
                imgURL = img['src']
                imgURL = handle_url(imgURL)
                if add_url(imgURL, keywords_array):
                    imageurls.append(imgURL)

        return imageurls
    except:
        raise Exception("SELENIUM ERROR FOR IMAGE URLS")


# decide for gender while selecting clothing
def gender_classifier(url):
    men_keywords = ["men", "male", "gentlemen"]
    boy_keywords = ["boy"]
    girl_keywords = ["girl"]
    women_keywords = ["women", "female", "lady"]
    unisex_keywords = ["unisex"]

    for keyword in women_keywords:
        if url.find(keyword) != -1:
            return "female"

    for keyword in men_keywords:
        if url.find(keyword) != -1:
            return "male"

    for keyword in boy_keywords:
        if url.find(keyword) != -1:
            return "boy"

    for keyword in girl_keywords:
        if url.find(keyword) != -1:
            return "girl"

    for keyword in unisex_keywords:
        if url.find(keyword) != -1:
            return "unisex"

    return None


def main_function(request):
    driver = webdriver.Chrome(r"C:\Users\infor\PycharmProjects\FlipkartGrid\drivers\chromedriver.exe")

    root = request["website_name"]
    # keywords_array is of type list
    keywords_array = request["keywords_array"]
    banned_keywords_array = request["banned_keywords_array"]
    num_images = request["num_images"]
    num_product_urls = request["num_product_urls"]

    url = handle_url(root)

    try:
        urlList = fetch_category_list(url, keywords_array, banned_keywords_array)
    except:
        raise Exception("NO RESULTS FOR GIVEN PRODUCT")

    response = {}

    wait_time = 10
    scroll_times = 50

    if num_images > 15:
        wait_time = 15
        scroll_times = 120

    for i in range(0, min(num_product_urls, len(urlList))):
        response[urlList[i]] = fetch_image_urls(url, driver, keywords_array, wait_time, scroll_times)
        print(urlList[i])

    final_response = {}

    for key in response:
        source_url = key
        img_url_list = response[key]

        api_responses = {}

        for i in range(0, min(num_images, len(img_url_list))):
            try:
                img_url = img_url_list[i]
                api_response = detect_properties_uri(img_url)
                api_responses[img_url] = api_response
            except:
                raise Exception("VISION API ERROR")

        final_response[source_url] = api_responses

    return final_response
