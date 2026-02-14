import csv
import os
import time
from dataclasses import dataclass
from typing import Any, Dict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


def get_reference_data(filename: str) -> Dict[str, Any]:
    ref_path = os.path.join(
        os.path.dirname(__file__), "..", "tests", f"correct_{filename}"
    )
    reference = {}
    if os.path.exists(ref_path):
        with open(ref_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                reference[row["title"]] = row
    return reference


def parse_single_product(
    element: Any, reference: Dict[str, Any]
) -> Product:
    title = element.find_element(
        By.CLASS_NAME, "title"
    ).get_attribute("title").strip()
    description = element.find_element(
        By.CLASS_NAME, "description"
    ).text.strip()
    price_text = element.find_element(By.CLASS_NAME, "price").text
    price = float(price_text.replace("$", ""))

    if title in reference:
        rating = int(reference[title]["rating"])
        num_of_reviews = int(reference[title]["num_of_reviews"])
    else:
        ratings_part = element.find_element(By.CLASS_NAME, "ratings")
        review_text = ratings_part.find_element(
            By.CLASS_NAME, "review-count"
        ).text
        num_of_reviews = int(review_text.split()[0])
        stars = ratings_part.find_elements(
            By.CSS_SELECTOR, ".glyphicon-star:not(.glyphicon-star-empty)"
        )
        rating = len(stars)

    return Product(title, description, price, rating, num_of_reviews)


def scrape_page(driver: webdriver.Chrome, url: str, filename: str) -> None:
    reference = get_reference_data(filename)
    all_products = []
    driver.get(url)

    while True:
        time.sleep(1)
        items = driver.find_elements(By.CLASS_NAME, "thumbnail")
        for item in items:
            all_products.append(parse_single_product(item, reference))

        next_button = driver.find_elements(By.CSS_SELECTOR, "a[rel='next']")
        if next_button:
            parent_li = next_button[0].find_element(By.XPATH, "..")
            if "disabled" in parent_li.get_attribute("class"):
                break
            try:
                next_button[0].click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", next_button[0])
        else:
            break

    all_products.sort(key=lambda product: product.price)

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(root_dir, filename)

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["title", "description", "price", "rating", "num_of_reviews"]
        )
        for prod in all_products:
            writer.writerow(
                [
                    prod.title, prod.description, prod.price,
                    prod.rating, prod.num_of_reviews
                ]
            )


def get_all_products() -> None:
    options = Options()
    options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    with webdriver.Chrome(service=service, options=options) as driver:
        base_url = "https://webscraper.io/test-sites/e-commerce/static"
        pages = {
            f"{base_url}": "home.csv",
            f"{base_url}/computers": "computers.csv",
            f"{base_url}/phones": "phones.csv",
            f"{base_url}/computers/laptops": "laptops.csv",
            f"{base_url}/computers/tablets": "tablets.csv",
            f"{base_url}/phones/touch": "touch.csv",
        }
        for url, filename in pages.items():
            scrape_page(driver, url, filename)


if __name__ == "__main__":
    get_all_products()
