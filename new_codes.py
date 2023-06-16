import pandas as pd


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
