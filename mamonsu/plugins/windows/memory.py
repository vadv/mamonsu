from mamonsu.lib.plugin import Plugin
from ._helpers import PerfData


class Memory(Plugin):

    Items = [
        # perf_item, zbx_key, desc, delta, unit, (color, site)
        (r'\Memory\Cache Bytes', '[cache]',
            'Memory cached', 'b', ('0000CC', 0)),

        (r'\Memory\Available Bytes', '[available]',
            'Memory available', 'b', ('00CC00', 0)),

        (r'\Memory\Free & Zero Page List Bytes', '[free]',
            'Memory free', 'b', ('CC0000', 0))
    ]

    def run(self, zbx):
        perf_services = []
        for item in self.Items:
            perf_services.insert(0, item[0])
        data = PerfData.get(perf_services, delay=1000)
        for idx, item in enumerate(self.Items):
            zbx.send('system.memory{0}'.format(item[1]), data[idx])

    def items(self, template):
        result = ''
        for item in self.Items:
            result += template.item({
                'name': '{0}'.format(item[2]),
                'key': 'system.memory{0}'.format(item[1]),
                'units': item[3]
            })
        return result

    def graphs(self, template):
        items = []
        for item in self.Items:
            if item[4] is not None:
                items.append({
                    'key': 'system.memory{0}'.format(item[1]),
                    'color': item[4][0],
                    'yaxisside': item[4][1]
                })
        graph = {
            'name': 'Memory overview', 'items': items, 'type': 1}
        return template.graph(graph)
