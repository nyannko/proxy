import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerLine2D
from matplotlib.ticker import MaxNLocator
from matplotlib import rc

rc('font', **{'family': 'serif', 'serif': ['Palatino']})
rc('text', usetex=True)
fig, ax = plt.subplots()
# ax = plt.figure().gca()
ax.xaxis.set_major_locator(MaxNLocator(integer=True))

data = [10, 15, 5, 20]
das1 = [10, 15, 29]
das2 = [13, 30, 49]
globals = [40, 60, 90]
keys = [1, 2, 3]

plt.xlabel('Hops')
plt.ylabel('Latency (ms)')
plt.title('Latency with different hop length')

# plt.axis([0, 3, 0, 80])
plt.grid(True, linestyle=":")
l1, = plt.plot(keys, das1, linestyle=":", marker='o', label='DAS5 same cluster', color='#859900')
l2, = plt.plot(keys, das2, linestyle="--", marker='s', label='DAS5 differnet clusters', color='#CFA60D')
l3, = plt.plot(keys, globals, linestyle="-.", marker='x', label='Global cloud instances', color='#dc322f')
plt.legend(handler_map={l1: HandlerLine2D(numpoints=4)})


plt.show()
fig.savefig('fig/{}.pdf'.format('line'))
