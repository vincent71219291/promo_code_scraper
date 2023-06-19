from datetime import datetime
from typing import Optional

import pandas as pd

COL_NAMES = {
    "discount": "Réduction",
    "description": "Description",
    "expiration_date": "Date d'expiration",
    "code": "Code",
    "days_before_exp": "Jours avant expiration",
}


def select_new_codes(
    current_codes: pd.DataFrame,
    previous_codes: pd.DataFrame,
    discount_col: str = "discount",
    threshold: int = 0,
) -> pd.DataFrame:
    df = pd.merge(
        left=current_codes, right=previous_codes, how="left", indicator=True
    )
    df = df.loc[
        (df["_merge"] == "left_only")
        & (
            df[discount_col].map(
                lambda x: int(x.replace("%", "")) >= threshold
            )
        )
    ].drop(columns="_merge")

    return df


def days_from_now(date):
    return (date - datetime.now().date()).days


def add_days_before_exp(
    data: pd.DataFrame, exp_date_col: str = "expiration_date", inplace=True
) -> Optional[pd.DataFrame]:
    if not inplace:
        data = data.copy()
        data["days_before_exp"] = data[exp_date_col].map(days_from_now)
        return data
    data["days_before_exp"] = data[exp_date_col].map(days_from_now)


def rename_cols(data: pd.DataFrame, inplace=True) -> Optional[pd.DataFrame]:
    return data.rename(columns=COL_NAMES, inplace=inplace)
