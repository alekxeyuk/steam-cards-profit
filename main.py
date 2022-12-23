import argparse

from colorama import init

from modules.search import Search
from modules.cards import Cards

init()


def main() -> None:
    parser = argparse.ArgumentParser(description="Control Steam-Cards-Profit")
    subparsers = parser.add_subparsers(help="targets choices", dest="command", required=True)

    honey_group = subparsers.add_parser("Search", help="Search options", aliases=["sr"])
    honey_group.add_argument("op", type=str, choices=["get", ])

    tail_group = subparsers.add_parser("Cards", help="Cards options", aliases=["cr"])
    tail_group.add_argument("op", type=str, choices=["get", "profit", ])

    args = parser.parse_args()

    if args.command in ("Search", "sr"):
        Search(args)
    elif args.command in ("Cards", "cr"):
        Cards(args)


if __name__ == "__main__":
    main()
