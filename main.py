import os
from pathlib import Path

import pandas as pd
from selenium import webdriver

from alert import create_alert, send_mail
from config import read_config
from df_html import df_to_html
from new_codes import select_new_codes
from scraper import VoucherScraper


def main():
    # importe les paramètres de configuration depuis un fichier JSON
    config = read_config("./config.json")

    driver = webdriver.Firefox()

    # récupère les codes promo sous forme de dataframe
    scraper = VoucherScraper(driver, config.url)
    website_name, current_codes = scraper.scrape()

    scraper.close_driver()

    save_location = (
        Path(config.data_dir)
        / website_name.lower().replace(" ", "_")
        / "promo_code_df.pkl"
    )

    # sélectionne les nouveaux codes dont le rabais dépasse le seuil fixé dans
    # le fichier de configuration
    try:
        previous_codes = pd.read_pickle(save_location)
        new_codes = select_new_codes(
            current_codes, previous_codes, threshold=config.min_discount
        )
    except FileNotFoundError:
        new_codes = current_codes

    # sauvegarde le dataframe contenant les codes actifs à la place de l'ancien
    os.makedirs(save_location.parent, exist_ok=True)
    current_codes.to_pickle(save_location)

    # envoie une alerte email ou non selon les paramètres de configuration
    if not config.new_discount_alert:
        return
    if new_codes.empty:
        print("No new codes found.")
    else:
        user = os.environ.get(config.env_var_user)
        password = os.environ.get(config.env_var_pass)

        if user is None or password is None:
            raise Exception("Email user or password not found.")

        df_html = df_to_html(current_codes, new_codes.index)
        alert = create_alert(
            sender=user, receiver=user, website=website_name, table=df_html
        )
        send_mail(sender=user, password=password, receiver=user, message=alert)
        print(f"Alert sent to '{user}'.")


if __name__ == "__main__":
    main()
