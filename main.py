import re
import urllib.parse
from math import ceil
from statistics import mean, median
from typing import List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from colorama import init
from termcolor import colored

init()

regex = re.compile(r"steampowered\.com/app/(\d+)/", re.IGNORECASE)
regex_price = re.compile(r"(\d+),(\d+)")

session = requests.Session()
session.cookies.set("sessionid", " ")

CARDS_INFO_URL = "https://www.steamcardexchange.net/index.php?gamepage-appid-"
GAME_INFO_URL = "https://store.steampowered.com/api/appdetails?appids={}&cc=tr"
STEAM_MULTIBUY_URL = "https://steamcommunity.com/market/multibuy?appid=753&"


class Card:
    def __init__(self, name: str, price: int) -> None:
        self.name = name
        self.price = price

    def __repr__(self) -> str:
        return f"{urllib.parse.unquote(self.name).split('-')[1]} -> {self.price}"


class Game:
    def __init__(self, gameid: int) -> None:
        self.gameid = gameid
        self.name = "None"
        self.price = 0
        self.cards_count = 0
        self.cards: List[Card] = []

    def update_self(self) -> None:
        resp = session.get(GAME_INFO_URL.format(self.gameid))
        if resp.status_code != 200:
            return None
        json: dict = resp.json()[str(self.gameid)]["data"]
        self.name: str = json["name"]
        self.price: int = json["price_overview"]["final"]

    def add_cards(self, cards: List[Card]) -> None:
        self.cards_count = len(cards)
        self.cards = cards

    def update_cards(self) -> None:
        resp = session.get(
            STEAM_MULTIBUY_URL + "&".join([f"items[]={card.name}&qty[]=1" for card in self.cards]),
            cookies={
                "steamLoginSecure": " "
            },
        )
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.content, "lxml")
        prices: List[Tuple[str, str]] = [
            regex_price.findall(price.get("value"))[0]
            for price in soup.find_all("input", {"class": "market_dialog_input market_multi_price"})
        ]
        print(prices)
        for card, price in enumerate(prices):
            self.cards[card].price = int(price[0]) * 100 + int(price[1])

    def calculate(self):
        will_get_cards = ceil(self.cards_count / 2)
        cards_prices = [card.price for card in self.cards]
        cards_prices_with_fee = [ceil(price * (0.86364)) for price in cards_prices]

        data = {
            "Mean": mean(cards_prices),
            "Median": median(cards_prices),
            "Mean_with_fee": mean(cards_prices_with_fee),
            "Median_with_fee": median(cards_prices_with_fee),
        }

        for k, v in data.items():
            if (profit := will_get_cards * v) >= self.price:
                print(colored(f"{k} profit: {ceil(profit-self.price)}", "green"))
            else:
                print(colored(f"{k} loss: {ceil(self.price-profit)}", "red"))

    def __repr__(self) -> str:
        return f"{self.name} -> {self.price} ^ {self.cards_count}"


def parse_gameid_cards_info(gameid: int) -> Optional[List[Card]]:
    resp = session.get(f"{CARDS_INFO_URL}{gameid}")
    if resp.status_code != 200:
        return None
    soup = BeautifulSoup(resp.content, "lxml")
    if (mkr := soup.find("span", id="series-1-cards")) is not None:
        if (prnt := mkr.parent) is not None:
            return [Card(card.get("href").split("/")[-1], 0) for card in prnt.find_all("a", {"class": "button-blue"})]
    return None


def parse_gameid_from_url(url: str) -> int:
    if gameid := regex.findall(url):
        return gameid[0]
    return 0


def main():
    while (user_input := input("Steam store url to the game: ")) and user_input.lower() not in ("exit", "stop", "q"):
        if (gameid := parse_gameid_from_url(user_input)) != 0:
            game = Game(gameid)
            game.update_self()
            if (cards := parse_gameid_cards_info(gameid)) is not None:
                game.add_cards(cards)
                game.update_cards()
                game.calculate()
            else:
                print("Can't get cards info for that gameid")
        else:
            print("Wrong url, can't parse gameid from it")
            continue


if __name__ == "__main__":
    main()
