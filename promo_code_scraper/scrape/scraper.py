import time
from datetime import datetime, timedelta
from typing import Tuple, Union

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

TIMEOUT = 10

FR_TO_EN = {
    "janvier": "january",
    "février": "february",
    "mars": "march",
    "avril": "april",
    "mai": "may",
    "juin": "june",
    "juillet": "july",
    "août": "august",
    "septembre": "september",
    "octobre": "october",
    "novembre": "november",
    "décembre": "december",
}

CSS_SELECTORS = {
    "reject_cookies": "#cmpwelcomebtnno",
    "website_name": "h1.xcrmu53",
    "display_codes_only": 'li[data-testid="Codes"]',
    "see_code": "div._1abe9s90._1abe9s91._1abe9s92 span._1oj1i5v0",
    "code": "h4.tqzsj70.tqzsj76._106202mb",
    "close_overlay": ".sb77nm5",
}

FIELD_CSS_SELECTORS = {
    "discount": "div._1abe9s90._1abe9s91._1abe9s92 span._1yyc3er0",
    "description": "div._1abe9s90._1abe9s91._1abe9s92 h3._1eilsni9",
    "expiration_date": (
        "div._1abe9s90._1abe9s91._1abe9s92 div._6h4c610._1eilsnid"
    ),
}


def get_element(
    driver: Union[webdriver.Chrome, webdriver.Firefox],
    css_selector: str,
    timeout: int = TIMEOUT,
) -> WebElement:
    element = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
    )
    return element


def get_elements(
    driver: Union[webdriver.Chrome, webdriver.Firefox],
    css_selector: str,
    timeout: int = TIMEOUT,
) -> list[WebElement]:
    elements = WebDriverWait(driver, timeout).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector))
    )
    return elements


def get_element_texts(
    driver: Union[webdriver.Chrome, webdriver.Firefox],
    css_selector: str,
    timeout: int = TIMEOUT,
) -> list[str]:
    elements = get_elements(driver, css_selector, timeout)
    return [element.text for element in elements]


def click_element(
    driver: Union[webdriver.Chrome, webdriver.Firefox],
    css_selector: str,
    timeout: int = TIMEOUT,
) -> None:
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
    )
    element.click()


def get_name(
    string: str, substrings: Tuple[str, str] = ("promo ", " valides")
):
    start, end = [string.find(substring) for substring in substrings]
    start += len(substrings[0])
    return string[start:end]


def format_exp_date(date_str: str):
    if "demain" in date_str:
        return datetime.now().date() + timedelta(days=1)
    if "aujourd'hui" in date_str:
        return datetime.now().date()
    date_str = date_str.split("\n: ")[1]
    for month_fr, month_en in FR_TO_EN.items():
        if month_fr in date_str:
            date_str = date_str.replace(month_fr, month_en)
            break
    date = datetime.strptime(f"{date_str} {datetime.now().year}", "%d %B %Y")
    if date < datetime.now():
        date = datetime.strptime(
            f"{date_str} {datetime.now().year + 1}", "%d %B %Y"
        )
    return date.date()


def get_code_str(
    driver: Union[webdriver.Chrome, webdriver.Firefox],
    see_code_button: WebElement,
    timeout: int = TIMEOUT,
) -> str:
    wait = WebDriverWait(driver, timeout)
    original_windows = driver.window_handles
    n_windows = len(driver.window_handles)

    see_code_button.click()

    # on attend que le nouvel onglet soit ouvert
    wait.until(EC.number_of_windows_to_be(n_windows + 1))

    current_windows = driver.window_handles
    new_window = [
        window for window in current_windows if window not in original_windows
    ][0]

    # on ferme les anciens onglets
    for window_handle in original_windows:
        driver.switch_to.window(window_handle)
        driver.close()

    driver.switch_to.window(new_window)
    code_str = get_element(driver, CSS_SELECTORS["code"]).text

    click_element(driver, CSS_SELECTORS["close_overlay"])

    return code_str


class VoucherScraper:
    def __init__(
        self, driver: Union[webdriver.Chrome, webdriver.Firefox], url: str
    ):
        self.driver = driver
        self.url = url
        self.data: dict = {}

    def scrape(self) -> tuple[str, pd.DataFrame]:
        codes = []

        self.driver.get(self.url)

        click_element(self.driver, CSS_SELECTORS["reject_cookies"])

        website_name = get_name(
            get_element(self.driver, CSS_SELECTORS["website_name"]).text
        )

        click_element(self.driver, CSS_SELECTORS["display_codes_only"])

        for field, css_selector in FIELD_CSS_SELECTORS.items():
            values = get_element_texts(self.driver, css_selector)
            if field == "expiration_date":
                values = list(map(format_exp_date, values))
            self.data[field] = values

        elements = get_elements(self.driver, CSS_SELECTORS["see_code"])
        n_codes = len(elements)
        print(f"{n_codes} code(s) found for {website_name}.")

        for i in range(n_codes):
            # on patiente 1 sec pour éviter de surcharger le serveur
            time.sleep(1)
            print(f"Scraping code {i + 1}/{n_codes}...")

            if i:
                # l'onglet/le contexte change à chaque itération, il est donc
                # nécessaire de récupérer à nouveau les éléments
                click_element(self.driver, CSS_SELECTORS["display_codes_only"])
                elements = get_elements(self.driver, CSS_SELECTORS["see_code"])
            elements[i].location_once_scrolled_into_view
            code_str = get_code_str(self.driver, elements[i])
            codes.append(code_str)

        self.data["code"] = codes

        current_codes = pd.DataFrame(self.data)
        current_codes = current_codes.sort_values(
            "discount",
            ascending=False,
            key=lambda x: x.str.replace("%", "").astype(int),
        )

        return website_name, current_codes

    def close_driver(self):
        self.driver.quit()
