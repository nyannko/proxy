import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerLine2D
from matplotlib.ticker import MaxNLocator
from matplotlib import rc

rc('font', **{'family': 'serif', 'serif': ['Palatino']})
rc('text', usetex=True)
fig, ax = plt.subplots()
# ax = plt.figure().gca()
ax.xaxis.set_major_locator(MaxNLocator(integer=True))

keys = ['without proxy', '0', '1', '2', '3']
data = [10, 15, 5, 20]
das1 = [1135.82603687, 1139.61986301, 1140.44691781, 1142.19343696, 1154.59005146]
das2 = [0, 0, 0, 0, 0]
globals = [None, None, 3188.9, 3223.95454545, 4129.55]
das1_err = [109.985622917, 113.470227294, 109.843696193, 107.096040502, 107.670141573]
global_err = [106.367711266, 226.683094223, 253.225882366]

plt.xlabel('Hops')
plt.ylabel('Latency (ms)')
plt.title('Latency with different hop length')

# plt.axis([0, 3, 0, 80])
plt.grid(True, linestyle=":")
l1, = plt.plot(keys, das1, linestyle=":", marker='o', label='DAS5 same cluster', color='#859900')
# l2, = plt.plot(keys, das2, linestyle="--", marker='s', label='DAS5 differnet clusters', color='#CFA60D')
l3, = plt.plot(keys, globals,linestyle="-.", marker='x', label='Global cloud instances', color='#dc322f')
plt.legend(handler_map={l1: HandlerLine2D(numpoints=4)})


# e = [0.11, 0.16, 0.19, 0.10]
plt.errorbar(keys, das1, yerr=das1_err, capsize=2, linestyle=":",color='#859900')
plt.errorbar(keys[2:], globals[2:], yerr=global_err, capsize=2, linestyle="-.",color='#dc322f')

# label the data
for i,j in enumerate(das1):
    ax.annotate("{:.0f}".format(j), xy=(i, j))

for i,j in enumerate(globals):
    if i <= 1: continue
    ax.annotate("{:.0f}".format(j), xy=(i, j))

plt.show()
fig.savefig('fig/{}.pdf'.format('line'))
