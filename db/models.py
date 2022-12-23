from datetime import datetime

from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class SteamApp(Model):
    __keyspace__ = "main"
    appid = columns.BigInt(primary_key=True, required=True)
    name = columns.Text(required=True)
    url = columns.Text(required=True)
    price = columns.BigInt(required=True)
    owned = columns.Boolean(default=False, required=True, index=True)
    cards = columns.List(columns.Text)
    created_at = columns.DateTime(default=datetime.now)

    def __str__(self):
        return f"{self.name}({self.appid}): {self.price} -> {self.owned}"


class TradingCard(Model):
    __keyspace__ = "main"
    name = columns.Text(primary_key=True, required=True)
    price = columns.BigInt(required=True)
    appid = columns.BigInt(required=True, index=True)
    created_at = columns.DateTime(default=datetime.now)

    def __str__(self):
        return f"{self.name} -> {self.price}"
