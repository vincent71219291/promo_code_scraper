import json
from dataclasses import dataclass


@dataclass
class ScrapeConfig:
    url: str
    data_dir: str
    new_discount_alert: bool
    min_discount: int
    env_var_user: str
    env_var_pass: str


def read_config(config_file: str) -> ScrapeConfig:
    with open(config_file) as file:
        data = json.load(file)
        return ScrapeConfig(**data)
