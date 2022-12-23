import requests

from conf import STEAM_LOGIN_SECURE

res = requests.get(
    "https://store.steampowered.com/dynamicstore/userdata/", cookies={"steamLoginSecure": STEAM_LOGIN_SECURE}
)
rgOwnedApps: set[int] = set(res.json()["rgOwnedApps"])


def game_owned(appid: int) -> bool:
    return appid in rgOwnedApps
