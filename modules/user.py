import requests
from cassandra.cqlengine.query import BatchQuery
from termcolor import colored

from conf import STEAM_LOGIN_SECURE
from db import SteamApp, TradingCard

res = requests.get(
    "https://store.steampowered.com/dynamicstore/userdata/", cookies={"steamLoginSecure": STEAM_LOGIN_SECURE}
)
rgOwnedApps: set[int] = set(res.json()["rgOwnedApps"])


def game_owned(appid: int) -> bool:
    return appid in rgOwnedApps


def update_owned():
    with BatchQuery() as batch:
        for app in SteamApp.objects.filter(owned=False):
            if game_owned(app.appid):
                print(colored(f"Game owned {app.name}", "yellow"))
                app.batch(batch).update(owned=True)
                for card in TradingCard.objects.filter(name__in=app.cards):
                    print(colored(f"Card removed {card.name}", "cyan"))
                    card.batch(batch).delete()
