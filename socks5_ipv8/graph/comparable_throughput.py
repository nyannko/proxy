from random import shuffle

import matplotlib.pyplot as plt
import numpy as np

from matplotlib import rc, cm

## for Palatino and other serif fonts use:
rc('font', **{'family': 'serif', 'serif': ['Palatino']})
rc('text', usetex=True)
# Fixing random state for reproducibility
np.random.seed(19680801)
fig, ax = plt.subplots()
colors = ['#cb4b16', '#dc322f', '#d33682', '#6c71c4', '#268bd2', '#2aa198', '#859900']
# Example data
crses = ('Normal', 'Shadowsocks', 'V2ray', 'Multiproxy1', 'Multiproxy2', 'Multiproxy3', 'OpenConnect', 'OpenVPN', 'Tor')
y_pos = np.arange(len(crses))
performance = [1095.91936384, 1126.19699929, 1032.21777344, 1186.93560113, 3403.92776805, 2298.28261719, 851.295703125, 976.211669922, 17.1072265625]
error = [70.1302590218, 91.5766681151, 225.122664865, 210.913890436, 381.02297157, 65.3997210143, 191.965443524, 110.369981015, 2.5354092107]
for i, v in enumerate(performance):
    ax.text(v + 2.5, i, "{:.0f}".format(v), color='black', fontweight='bold')
# performance = 1 + 2 * np.random.rand(len(crses))
# print performance
# error = np.random.rand(len(crses))
ax.barh(y_pos, performance, xerr=error, capsize=2, align='center',
        ecolor='black', color=colors)
ax.set_yticks(y_pos)
ax.set_yticklabels(crses)
ax.invert_yaxis()  # labels read top-to-bottom
ax.set_xlabel('Throughput (KB/s)')
ax.set_title('Throughput Comparison')
plt.grid(True, linestyle=":")
ax.set_axisbelow(True)
plt.show()
# fig.savefig('fig/{}.pdf'.format('graph'))
