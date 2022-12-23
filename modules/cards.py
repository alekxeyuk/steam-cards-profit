import re
import urllib.parse
from argparse import Namespace
from math import ceil
from statistics import mean, median
from typing import List, Optional, Tuple, Generator

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
    with BatchQuery() as batch:
        for app in SteamApp.objects.filter(owned=False):
            print(colored(app, "cyan"))
            will_get_cards = ceil(len(app.cards) / 2)
            cards_prices = [ceil(card.price * (0.86364)) for card in TradingCard.objects.filter(appid=app.appid)]
            print(cards_prices)
            data: dict[str, float] = {
                "mean_with_fee": will_get_cards * mean(cards_prices),
                "median_with_fee": will_get_cards * median(cards_prices),
            }

            for k, profit in data.items():
                if profit >= app.price:
                    print(colored(f"{k} profit: {ceil(profit-app.price)}", "green"))
                    data[k] = ceil(profit - app.price)
                else:
                    print(colored(f"{k} loss: {ceil(app.price-profit)}", "red"))
                    data[k] = -ceil(app.price - profit)

            app.batch(batch).update(**data)
            print(colored("-" * 20, "yellow"))


def chunkify(lst: List[TradingCard], chunk_size: int) -> Generator[List[TradingCard], None, None]:
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def update_prices():
    with BatchQuery() as batch:
        for card_chunk in chunkify(TradingCard.objects.all(), 50):
            resp = session.get(
                STEAM_MULTIBUY_URL + "&".join([f"items[]={card.name}&qty[]=1" for card in card_chunk]),
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
            for price, card in zip(prices, card_chunk):
                card.batch(batch).update(price=int(price[0]) * 100 + int(price[1]))


def Cards(args: Namespace) -> None:
    print(colored("Cards is running...", "green"))
    connect()
    match args.op:
        case "get":
            get_cards()
        case "profit":
            calc_profit()
        case "update":
            update_prices()
    print(colored("Cards is done.", "green"))
