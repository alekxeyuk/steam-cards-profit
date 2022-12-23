from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster, Session
from cassandra.cqlengine import connection
from conf import ASTRA_ID, ASTRA_SECRET


def connect() -> Session:
    """Initializes connection to Cassandra.

    Returns:
        Session: Cassandra cluster session.
    """
    cloud_config = {
        "secure_connect_bundle": "db/secure-connect-base.zip",
        "init-query-timeout": 10,
        "connect_timeout": 10,
        "set-keyspace-timeout": 10,
    }
    auth_provider = PlainTextAuthProvider(ASTRA_ID, ASTRA_SECRET)
    cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
    session = cluster.connect("main")
    connection.set_session(session)
    return session
