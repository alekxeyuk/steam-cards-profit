from argparse import Namespace

import requests
from cassandra.cqlengine.query import BatchQuery
from db import TradingCard, connect
from termcolor import colored


def Cards(args: Namespace) -> None:
    print(colored("Cards is running...", "green"))
    connect()
    match args.op:
        case "update":
            update_cards()
        case "sync":
            sync_users()
        case "reward":
            collect_rewards()
    print(colored("Cards is done.", "green"))
