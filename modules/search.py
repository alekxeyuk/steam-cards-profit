from argparse import Namespace

from bs4 import BeautifulSoup
from cassandra.cqlengine.query import BatchQuery
from requests_toolbelt import sessions
from termcolor import colored

from conf import STEAM_LOGIN_SECURE
from db import SteamApp, connect

from . import user


class Searcher(object):
    BASE_URL = "https://store.steampowered.com/search/results/?"
    session = sessions.BaseUrlSession(base_url=BASE_URL)

    def __init__(self) -> None:
        self.start = 0
        self.count = 50
        self.sort_by = "Price_ASC"
        self.maxprice = 10
        self.category1 = 998
        self.category2 = 29
        self.hidef2p = 1
        self.infinite = 1

    def get_html(self) -> str | None:
        res = self.session.get("query&", params=vars(self), cookies={"steamLoginSecure": STEAM_LOGIN_SECURE})
        if res.status_code != 200:
            print(colored(f"get_html failed with {res.status_code=} ...", "red"))
            return None
        res = res.json()
        if res["success"] != 1:
            print(colored(f"get_html failed with {res['success']=} ...", "red"))
            return None
        return res["results_html"]

    def parse_html(self, html: str):
        soup = BeautifulSoup(html, "lxml")
        with BatchQuery() as batch:
            for row in soup.select("a.search_result_row"):
                appid = row.get("data-ds-appid")
                if not isinstance(appid, str):
                    appid = 0
                else:
                    appid = int(appid)
                href = row.get("href")

                name = row.select_one("span.title")
                if name is None:
                    name = "Noname"
                else:
                    name = name.getText()

                price = row.select_one("div.search_price_discount_combined")
                if price is None:
                    price = 0
                else:
                    price = price.get("data-price-final")

                print(colored(f"Adding {name} {price=}", "cyan"))
                SteamApp.batch(batch).create(
                    appid=appid, name=name, url=href, price=price, owned=user.game_owned(appid)
                )

    def next_page(self) -> None:
        html = self.get_html()
        if html is None:
            print(colored("next_page failed with bad html...", "red"))
            return
        self.parse_html(html)
        self.start += self.count


def steam_search() -> None:
    s = Searcher()
    for _ in range(5):
        s.next_page()


def Search(args: Namespace) -> None:
    print(colored("Search is running...", "green"))
    connect()
    match args.op:
        case "get":
            steam_search()
        case "user":
            user.update_owned()
    print(colored("Search is done.", "green"))
