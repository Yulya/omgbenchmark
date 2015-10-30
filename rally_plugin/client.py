import yaml
import collections

from oslo_config import cfg
import oslo_messaging as messaging
from oslo_messaging import rpc

from scipy.stats import rv_discrete


CLIENTS = None
RANDOM_VARIABLE = None


def setup_clients(rabbit_url, num_clients):
    clients = []
    target = messaging.Target()
    for i in range(num_clients):
        transport = messaging.get_transport(cfg.CONF, url=rabbit_url)
        client = rpc.RPCClient(transport, target)
        clients.append(client)
    global CLIENTS
    CLIENTS = collections.deque(clients)


def get_client():
    if not CLIENTS:
        raise Exception("Need to set up clients first")
    client = CLIENTS.popleft()
    CLIENTS.append(client)
    return client


def init_random_generator(msg_length_file):
    data = []
    with open(msg_length_file) as m_file:
        content = yaml.load(m_file)
        data += [int(n) for n in content[
            'test_data']['string_lengths'].split(', ')]

    ranges = collections.defaultdict(int)
    for msg_length in data:
        range_start = (msg_length / 500) * 500 + 1
        ranges[range_start] += 1

    ranges_start = sorted(ranges.keys())
    total_count = len(data)
    ranges_dist = []
    for r in ranges_start:
        r_dist = float(ranges[r]) / total_count
        ranges_dist.append(r_dist)

    random_var = rv_discrete(values=(ranges_start, ranges_dist))
    global RANDOM_VARIABLE
    RANDOM_VARIABLE = random_var

