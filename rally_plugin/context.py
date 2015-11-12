import multiprocessing
import itertools
from oslo_config import cfg

import time
from rally.task import context
from rally.task.engine import BenchmarkEngine

from rally.common import log as logging
from oslo_messaging import rpc
import oslo_messaging as messaging

import petname

import client


fake_func = lambda *x, **y: None
BenchmarkEngine.validate = fake_func

LOG = logging.getLogger(__name__)
logger = logging.oslogging.logging.getLogger("oslo.messaging")
logger.setLevel("DEBUG")


class RpcEndpoint(object):
    def info(self, ctxt, message):
        return "OK: %s" % message


@context.configure(name="oslomsg", order=1000)
class OsloMsgContext(context.Context):
    """
    Oslo messaging default context
    Cerate tranport and target;
    Set up servers
    """
    def __init__(self, *args, **kwargs):
        super(OsloMsgContext, self).__init__(*args, **kwargs)
        self.server_processes = []

    def set_config_opts(self):
        config_opts = self.config.get('config_opts', {})
        for section, values in config_opts.items():
            if not section == "DEFAULT":
                cfg.CONF.register_group(cfg.OptGroup(section))
                obj = getattr(cfg.CONF, section)
            else:
                obj = cfg.CONF
            for opt, value in values.items():
                setattr(obj, opt, value)

    def setup(self):
        url = self.context['admin']['endpoint'].auth_url
        self.set_config_opts()
        transport = messaging.get_transport(cfg.CONF, url=url)
        self.context['servers'] = []
        num_servers = self.config.get('num_servers')
        num_topics = self.config.get('num_topics')
        self._start_servers(transport, num_servers, num_topics)
        client.setup_clients(url, self.config['num_clients'])
        client.init_random_generator(self.config['msg_length_file'])

    def _start_servers(self, transport, num_servers, num_topics):
        topics = [petname.Generate(3, "_") for _i in range(num_topics)]
        topics_iter = itertools.cycle(topics)
        for i in range(num_servers):
            topic = topics_iter.next()
            server_name = 'profiler_server'
            LOG.info("Starting server %s topic %s" % (server_name, topic))
            target = messaging.Target(topic=topic,
                                      server=server_name)

            server = rpc.get_rpc_server(transport, target, [RpcEndpoint()],
                                        executor='threading')
            pr = multiprocessing.Process(target=self._start_server,
                                         args=(server,))
            pr.start()
            self.server_processes.append(pr)
            self.context['servers'].append((topic, server_name))

    def _start_server(self, server):
        server.start()
        while 1:
            time.sleep(3)

    def cleanup(self):
        for p in self.server_processes:
            p.terminate()
