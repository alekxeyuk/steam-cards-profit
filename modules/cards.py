import re
import urllib.parse
from argparse import Namespace
from math import ceil
from statistics import mean, median
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup
from cassandra.cqlengine.query import BatchQuery
from requests import Session
from termcolor import colored

from conf import STEAM_LOGIN_SECURE
from db import SteamApp, TradingCard, connect

CARDS_INFO_URL = "https://www.steamcardexchange.net/index.php?gamepage-appid-"
STEAM_MULTIBUY_URL = "https://steamcommunity.com/market/multibuy?appid=753&"
regex_price = re.compile(r"(\d+),(\d+)")

session = Session()


class Card:
    def __init__(self, name: str, price: int) -> None:
        self.name = name
        self.price = price

    def __repr__(self) -> str:
        return f"{urllib.parse.unquote(self.name).split('-')[1]} -> {self.price}"


def get_cards() -> None:
    with BatchQuery() as batch:
        for app in SteamApp.objects.filter(owned=False):
            print(colored(app, "cyan"))
            if (cards := parse_gameid_cards_info(app.appid)) is not None:
                print(cards)
                for card in update_cards(cards):
                    TradingCard.batch(batch).create(
                        name=card[0],
                        price=card[1],
                        appid=app.appid,
                    )
                app.batch(batch).cards = cards
                app.batch(batch).save()


def parse_gameid_cards_info(gameid: int) -> Optional[List[str]]:
    resp = session.get(f"{CARDS_INFO_URL}{gameid}")
    print(resp.url)
    if resp.status_code != 200:
        return None
    soup = BeautifulSoup(resp.content, "lxml")
    if (mkr := soup.find("span", id="series-1-cards")) is not None:
        if (prnt := mkr.parent) is not None:
            return [card.get("href").split("/")[-1] for card in prnt.find_all("a", {"class": "button-blue"})]
    return None


def update_cards(cards: List[str]) -> List[Tuple[str, int]]:
    resp = session.get(
        STEAM_MULTIBUY_URL + "&".join([f"items[]={card}&qty[]=1" for card in cards]),
        cookies={"steamLoginSecure": STEAM_LOGIN_SECURE},
    )
    if resp.status_code != 200:
        return []
    soup = BeautifulSoup(resp.content, "lxml")
    prices: List[Tuple[str, str]] = [
        regex_price.findall(price.get("value"))[0]
        for price in soup.find_all("input", {"class": "market_dialog_input market_multi_price"})
    ]
    print(prices)
    return [(card, int(price[0]) * 100 + int(price[1])) for price, card in zip(prices, cards)]


def calc_profit():
    print(colored("-" * 20, "yellow"))
    for app in SteamApp.objects.filter(owned=False):
        print(colored(app, "cyan"))
        will_get_cards = ceil(len(app.cards) / 2)
        cards_prices = [card.price for card in TradingCard.objects.filter(appid=app.appid)]
        cards_prices_with_fee = [ceil(price * (0.86364)) for price in cards_prices]
        print(cards_prices)
        data = {
            "Mean": mean(cards_prices),
            "Median": median(cards_prices),
            "Mean_with_fee": mean(cards_prices_with_fee),
            "Median_with_fee": median(cards_prices_with_fee),
        }

        for k, v in data.items():
            if (profit := will_get_cards * v) >= app.price:
                print(colored(f"{k} profit: {ceil(profit-app.price)}", "green"))
            else:
                print(colored(f"{k} loss: {ceil(app.price-profit)}", "red"))
        print(colored("-" * 20, "yellow"))


def Cards(args: Namespace) -> None:
    print(colored("Cards is running...", "green"))
    connect()
    match args.op:
        case "get":
            get_cards()
        case "profit":
            calc_profit()
    print(colored("Cards is done.", "green"))
