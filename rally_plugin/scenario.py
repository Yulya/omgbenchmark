import collections
import random
import string
import yaml

from rally.common import log as logging
from rally.plugins.openstack.context.keystone.users import UserGenerator
from rally.task import scenario
from rally.task import context

from scipy.stats import rv_discrete

import client as cl


LOG = logging.getLogger(__name__)

# hack below is used to avoid loading UserGenerating plugin
# as it needs keystones to be run
# should be removed or replaced with better solution
_old_get_sort_ctx_lst = context.ContextManager._get_sorted_context_lst


def _new_get_sorted_context_lst(self):
    lst = _old_get_sort_ctx_lst(self)
    for pl in lst:
        if isinstance(pl, UserGenerator):
            lst.remove(pl)
    return lst

context.ContextManager._get_sorted_context_lst = _new_get_sorted_context_lst


class RabbitScenario(scenario.Scenario):
    def _get_client(self):
        random_server = random.randint(0, len(self.context['servers']) - 1)
        topic, server_name = self.context['servers'][random_server]
        client = cl.get_client()
        client = client.prepare(timeout=30, topic=topic,
                                server=server_name)
        return client

    @scenario.configure()
    def one_message(self):
        client = self._get_client()
        msg = "test message"
        client.call({}, 'info', message=msg)

    @scenario.configure()
    def send_messages(self, num_messages):
        client = self._get_client()
        ranges = cl.RANDOM_VARIABLE.rvs(size=num_messages)
        errors = 0
        for range_start in ranges:
            length = random.randint(range_start, range_start + 500)
            msg = ''.join(
                random.choice(string.lowercase) for x in range(length))
            try:
                client.call({}, 'info', message=msg)
            except Exception as e:
                LOG.error(e.message)
                errors += 1

        if errors:
            raise Exception("scenario failed")