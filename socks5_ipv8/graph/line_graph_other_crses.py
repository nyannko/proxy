import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerLine2D
from matplotlib.ticker import MaxNLocator
from matplotlib import rc

rc('font', **{'family': 'serif', 'serif': ['Palatino']})
rc('text', usetex=True)
ax = plt.figure().gca()
ax.xaxis.set_major_locator(MaxNLocator(integer=True))

Tor = [10, 15, 29]
multiproxy = [40, 60, 90]
keys = [1, 2, 3]

plt.xlabel('Hops')
plt.ylabel('Latency (ms)')
plt.title('Latency with different hop length')

# plt.axis([0, 3, 0, 80])
plt.grid(True, linestyle=":")
l1, = plt.plot(keys, Tor, linestyle=":", marker='o', label='Tor', color='#859900')
l3, = plt.plot(keys, multiproxy, linestyle="-.", marker='x', label='Multiproxy', color='#dc322f')
plt.legend(handler_map={l1: HandlerLine2D(numpoints=4)})


plt.show()
