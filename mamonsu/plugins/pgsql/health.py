# -*- coding: utf-8 -*-

from mamonsu.lib.plugin import Plugin
from ._pool import Pooler
import time


class Health(Plugin):

    def __init__(self, config):
        super(Health, self).__init__(config)
        # сообщаем что у сервиса низкий аптайм, пока аптайм меньше 10 минут
        self.TriggerUptimeLessThen = self.config.fetch(
            'health', 'uptime', int)
        # алертим, если cache hit меньше чем %
        self.TriggerCacheHitLessThen = self.config.fetch(
            'health', 'cache', int)
        # счетчик, для сообщения в лог
        self.counter = 0

    def run(self, zbx):

        start_time = time.time()
        Pooler.query('select 1')
        zbx.send('pgsql.ping[]', (time.time() - start_time)*100)

        result = Pooler.query("select \
            date_part('epoch', now() - pg_postmaster_start_time())")
        zbx.send('pgsql.uptime[]', int(result[0][0]))

        result = Pooler.query('select \
            round(sum(blks_hit)*100/sum(blks_hit+blks_read), 2) \
            from pg_stat_database')
        zbx.send('pgsql.cache[hit]', int(result[0][0]))

        self.counter += 1
        if self.counter > 9:
            self.log.info('=== Keep alive ===')
            self.counter = 0

    def items(self, template):
        result = template.item({
            'name': 'PostgreSQL: ping',
            'key': 'pgsql.ping[]',
            'value_type': 0,
            'units': 'ms'
        }) + template.item({
            'name': 'PostgreSQL: service uptime',
            'key': 'pgsql.uptime[]',
            'value_type': 3,
            'units': 'uptime'
        }) + template.item({
            'name': 'PostgreSQL: cache hit ratio',
            'key': 'pgsql.cache[hit]',
            'value_type': 3,
            'units': '%'
        })
        return result

    def graphs(self, template):
        items = [
            {'key': 'pgsql.cache[hit]'},
            {'key': 'pgsql.uptime[]', 'color': 'DF0101', 'yaxisside': 1}
        ]
        graph = {'name': 'PostgreSQL uptime', 'items': items}
        return template.graph(graph)

    def triggers(self, template):
        result = template.trigger({
            'name': 'PostgreSQL service was restarted on '
            '{HOSTNAME} (uptime={ITEM.LASTVALUE})',
            'expression': '{#TEMPLATE:pgsql.uptime[].last'
            '()}&lt;' + str(self.TriggerUptimeLessThen)
        }) + template.trigger({
            'name': 'PostgreSQL cache hit ratio too low on '
            '{HOSTNAME} ({ITEM.LASTVALUE})',
            'expression': '{#TEMPLATE:pgsql.cache[hit].last'
            '()}&lt;' + str(self.TriggerCacheHitLessThen)
        })
        return result
