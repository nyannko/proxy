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
colors = ['#cb4b16', '#dc322f','#d33682', '#6c71c4', '#268bd2', '#2aa198', '#859900']
# Example data
crses = ('Shadowsocks', 'V2ray', 'Tor', 'OpenVPN', 'OpenConnect', 'Multiproxy')
y_pos = np.arange(len(crses))
performance = 1 + 2 * np.random.rand(len(crses))
error = np.random.rand(len(crses))
ax.barh(y_pos, performance,  xerr=error, align='center',
        ecolor='black', color=colors)
ax.set_yticks(y_pos)
ax.set_yticklabels(crses)
ax.invert_yaxis()  # labels read top-to-bottom
ax.set_xlabel('Latency (ms)')
ax.set_title('Latency Comparison')
plt.grid(True, linestyle=":")
ax.set_axisbelow(True)
plt.show()
fig.savefig('fig/{}.pdf'.format('graph'))
