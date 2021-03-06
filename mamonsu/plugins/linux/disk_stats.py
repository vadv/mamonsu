import re
from mamonsu.lib.plugin import Plugin


class DiskStats(Plugin):

    # todo yaxis right 100%
    # bold line

    # Track only physical devices without logical partitions
    OnlyPhysicalDevices = True

    re_stat = re.compile('^(?:\s+\d+){2}\s+([\w\d]+) (.*)$')
    # rd_ios rd_merges rd_sectors rd_ticks
    # wr_ios wr_merges wr_sectors wr_ticks
    # ios_in_prog tot_ticks rq_ticks

    def run(self, zbx):
        with open('/proc/diskstats', 'r') as f:

            devices = []
            all_read, all_write = 0, 0

            for line in f:
                if re.search('(ram|loop)', line):
                    continue
                m = self.re_stat.match(line)
                if m is None:
                    continue
                dev, val = m.group(1), m.group(2)
                if self.OnlyPhysicalDevices and re.search('\d+$', dev):
                    continue
                val = [int(x) for x in val.split()]
                read, write, ticks = val[0], val[4], val[9]
                all_read += read
                all_write += write
                devices.append({'{#BLOCKDEVICE}': dev})

                zbx.send('system.disk.read[{0}]'.format(dev), read)
                zbx.send('system.disk.write[{0}]'.format(dev), write)
                zbx.send('system.disk.utilization[{0}]'.format(dev), ticks/10)

            zbx.send('system.disk.all_read[]', all_read)
            zbx.send('system.disk.all_write[]', all_write)
            zbx.send('system.disk.discovery[]', zbx.json({'data': devices}))

    def items(self, template):
        return template.item({
            'name': 'Block devices: read requests',
            'key': 'system.disk.all_read[]',
            'delta': 2
        }) + template.item({
            'name': 'Block devices: write requests',
            'key': 'system.disk.all_write[]',
            'delta': 2
        })

    def graphs(self, template):
        items = [
            {'key': 'system.disk.all_read[]', 'color': 'CC0000'},
            {'key': 'system.disk.all_write[]', 'color': '0000CC'}
        ]
        graph = {
            'name': 'Block devices: read/write operations',
            'items': items}
        return template.graph(graph)

    def discovery_rules(self, template):

        rule = {
            'name': 'Block device discovery',
            'key': 'system.disk.discovery[]',
            'filter': '{#BLOCKDEVICE}:.*'
        }

        items = [
            {
                'key': 'system.disk.utilization[{#BLOCKDEVICE}]',
                'name': 'Block device {#BLOCKDEVICE}: utilization',
                'delta': 1,
                'units': '%'},
            {
                'key': 'system.disk.read[{#BLOCKDEVICE}]',
                'name': 'Block device {#BLOCKDEVICE}: read operations',
                'delta': 2},
            {
                'key': 'system.disk.write[{#BLOCKDEVICE}]',
                'name': 'Block device {#BLOCKDEVICE}: write operations',
                'delta': 2}]

        graphs = [{
            'name': 'Block device overview: {#BLOCKDEVICE}',
            'items': [{
                    'color': 'CC0000',
                    'key': 'system.disk.read[{#BLOCKDEVICE}]'},
                {
                    'color': '0000CC',
                    'key': 'system.disk.write[{#BLOCKDEVICE}]'},
                {
                    'yaxisside': 1,
                    'color': '00CC00',
                    'key': 'system.disk.utilization[{#BLOCKDEVICE}]'}]
        }]

        return template.discovery_rule(rule=rule, items=items, graphs=graphs)
