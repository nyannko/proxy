import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerLine2D
from matplotlib.ticker import MaxNLocator
from matplotlib import rc

rc('font', **{'family': 'serif', 'serif': ['Palatino']})
rc('text', usetex=True)
fig, ax = plt.subplots()
ax.xaxis.set_major_locator(MaxNLocator(integer=True))

# multiproxy_time = [3.2004516129, 13.7819793039, 27.4041453901, 49.0140308031, 51.0447281399, 64.3305959184, 73.3000539143]
# mti_error = [0.613876007867, 9.44968077345, 18.8539221922, 27.2258935881, 38.2502476349, 48.986322341, 59.674617854]
# mth_error=[]
# multiproxy_throughput = [3326.99651613, 1159.56064064, 695.785425532, 532.185510451, 527.359228935, 471.813552653,455.4366839]
# keys = [1, 50, 100, 150, 200, 250, 300]
multiproxy_throughput = [0.6468474234234234, 0.6478774434234264, 0.6507866789795682, 0.6482863791793621,
                         0.6450012935351241, 0.6409724267854086, 0.6399724267854086,
                         0.6191252179853175, 0.5967366818873668, 0.5343671249173517, 0.4990390031063517]

keys = [1, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500]

plt.xlabel('The number of Nodes')
plt.ylabel('Throughput (KB/s)')
plt.title('Throughput with different node number')
plt.xticks(keys);
plt.axis([1, 500, 0, 1])

plt.grid(True, linestyle=":")
# l1, = plt.plot(keys, Tor, linestyle=":", marker='o', label='Tor', color='#859900')
# l3, = plt.plot(keys, multiproxy_throughput, linestyle="-.", marker='x', label='Multiproxy 1 hop', color='#dc322f')
l3, = plt.plot(keys, multiproxy_throughput, linestyle="-.", marker='x', label='Multiproxy 1 hop', color='#dc322f')
# plt.errorbar(keys, multiproxy_time, yerr=mti_error, capsize=2, linestyle=":",color='#859900')
# plt.legend(handler_map={l3: HandlerLine2D(numpoints=4)})

plt.show()

fig.savefig('fig/{}.pdf'.format('throughput_scalability'))
