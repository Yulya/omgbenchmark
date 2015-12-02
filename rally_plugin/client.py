import copy
import json
import yaml
import collections

from oslo_config import cfg
import oslo_messaging as messaging
from oslo_messaging import rpc

from scipy.stats import rv_discrete


CLIENTS = None
RANDOM_VARIABLE = None
MESSAGES = {}


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
    global MESSAGES
    MESSAGES = create_messages(ranges_start)


def create_messages(messages_length):
    networks_info = open('networks.json').read()
    net_info_dict = json.loads(networks_info)

    network = net_info_dict['result'][0]
    subnet = network['subnets'][0]
    subnet_len = len(json.dumps(subnet))

    messages = {}
    for message_length in messages_length:
        msg = copy.deepcopy(net_info_dict)
        msg['result'] = []

        message_length_c = message_length
        message_length_c -= len(json.dumps(msg))

        net_n = 0

        while message_length_c > 0:
            net = copy.deepcopy(net_info_dict['result'][net_n])

            net_copy = copy.deepcopy(net)
            net_copy['subnets'] = []
            net_l = len(json.dumps(net_copy))

            subnet_count = (message_length_c - net_l) / subnet_len

            subnet_count = subnet_count if subnet_count >= 0 else 0

            net['subnets'] = net['subnets'][:subnet_count]
            msg['result'].append(net)
            net_n += 1
            message_length_c -= len(json.dumps(net))

        messages[message_length] = msg
    return messages