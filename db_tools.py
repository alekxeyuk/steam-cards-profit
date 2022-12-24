from pprint import pprint

from cassandra import InvalidRequest
from cassandra.cqlengine.management import sync_table
from cassandra.cqlengine.query import BatchQuery
from termcolor import colored

from db.connect import connect
from db.models import SteamApp, TradingCard


def main():
    print(colored("Connecting to database...", "green"))
    connect()

    while user_input := input("What do you want? {sync / create / get }: "):
        match user_input:
            case "sync":
                sync_table(SteamApp)
                sync_table(TradingCard)
                print(colored("Table synced", "green"))
            case "create":
                try:
                    inst = SteamApp.create(appid=1, name="Test", url="https://test.ru", price=100, owned=True)
                    print(colored(f"Created: {inst}", "green"))
                except InvalidRequest as e:
                    print(colored(f"Wrong request: {e}", "red"))
            case "get":
                print(SteamApp.objects.count())
                pprint(SteamApp.objects.all()[:])
                print(TradingCard.objects.count())
                pprint(TradingCard.objects.all()[:])
            case "nuke":
                print(colored("Nuking DB", "red"))
                with BatchQuery() as batch:
                    for inst in SteamApp.objects.all():
                        inst.batch(batch).delete()
                    for inst in TradingCard.objects.all():
                        inst.batch(batch).delete()
                print(colored("DB nuked", "red"))
            case "exit":
                print(colored("Bye", "green"))
                break
            case _:
                print(colored(f"Command '{user_input}' not understood", "red"))


if __name__ == "__main__":
    main()
