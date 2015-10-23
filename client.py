from collections import deque

from oslo_config import cfg
import oslo_messaging as messaging
from oslo_messaging import rpc


CLIENTS = None


def setup_clients(rabbit_url, num_clients):
    clients = []
    target = messaging.Target()
    for i in range(num_clients):
        transport = messaging.get_transport(cfg.CONF, url=rabbit_url)
        client = rpc.RPCClient(transport, target)
        clients.append(client)
    global CLIENTS
    CLIENTS = deque(clients)


def get_client():
    if not CLIENTS:
        raise Exception("Need to set up clients first")
    client = CLIENTS.popleft()
    CLIENTS.append(client)
    return client
