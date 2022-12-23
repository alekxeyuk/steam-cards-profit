from datetime import datetime

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class SteamApp(Model):
    __keyspace__ = "main"
    appid = columns.BigInt(primary_key=True, required=True)
    name = columns.Text(required=True)
    url = columns.Text(required=True)
    price = columns.BigInt(required=True)
    owned = columns.Boolean(default=False, required=True)
    cards = columns.List(columns.BigInt)
    created_at = columns.DateTime(default=datetime.now)

    def __str__(self):
        return f"{self.name}({self.appid}): {self.price} -> {self.owned}"


class TradingCard(Model):
    __keyspace__ = "main"
    id = columns.BigInt(primary_key=True, required=True)
    name = columns.Text(required=True)
    price = columns.BigInt(required=True)
    appid = columns.BigInt(required=True)
    created_at = columns.DateTime(default=datetime.now)

    def __str__(self):
        return f"{self.name} -> {self.price}"
