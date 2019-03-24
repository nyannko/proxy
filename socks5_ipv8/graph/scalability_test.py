import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerLine2D
from matplotlib.ticker import MaxNLocator
from matplotlib import rc
# import numpy as np

rc('font', **{'family': 'serif', 'serif': ['Palatino']})
rc('text', usetex=True)
fig, ax = plt.subplots()
ax.xaxis.set_major_locator(MaxNLocator(integer=True))

# multiproxy_time = [3.2004516129, 13.7819793039, 27.4041453901, 49.0140308031, 51.0447281399, 64.3305959184, 73.3000539143]
# mti_error = [0.613876007867, 9.44968077345, 18.8539221922, 27.2258935881, 38.2502476349, 48.986322341, 59.674617854]
# mth_error=[]
# multiproxy_throughput = [3326.99651613, 1159.56064064, 695.785425532, 532.185510451, 527.359228935, 471.813552653,455.4366839]
# keys = [1, 50, 100, 150, 200, 250, 300]
multiproxy_time = [0.5222198198198198, 0.5212198158168398, 0.5185151794990189, 0.5196151694990382, 0.5271285666703674,
                   0.5281265636303494, 0.5296562767597192, 0.5456562767497213, 0.5777924911212583, 0.6373924941512092,
                   0.6807901782064906]
# multiproxy_time = [0.5101206896551724, 0.5121302896458719, 0.5148587604290822, 0.5311582604193819, 0.5404959059103767,
#                    0.5424859059733729, 0.545373827279288, 0.547353837379212, 0.5553200442967886, 0.5753109243962856,
#                    0.6807901782064906]
mti_error = [0.09414361333356111, 0.09106705656112495, 0.09503009937282915, 0.10465895088616173, 0.13769812372341925,
             0.13279776526572018]
keys = [1, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500]

plt.xticks(keys);
plt.axis([1, 500, 0, 1])
plt.xlabel('The number of Nodes')
plt.ylabel('Latency (s)')
plt.title('Latency with different node number')

# plt.axis([0, 3, 0, 80])
plt.grid(True, linestyle=":")
# l1, = plt.plot(keys, Tor, linestyle=":", marker='o', label='Tor', color='#859900')
# l3, = plt.plot(keys, multiproxy_throughput, linestyle="-.", marker='x', label='Multiproxy 1 hop', color='#dc322f')
l3, = plt.plot(keys, multiproxy_time, linestyle="-.", marker='.', label='Multiproxy 1 hop', color='#859900')
# plt.errorbar(keys, multiproxy_time, yerr=mti_error, capsize=2, linestyle=":",color='#859900')
# plt.legend(handler_map={l3: HandlerLine2D(numpoints=4)})

plt.show()

fig.savefig('fig/{}.pdf'.format('latency_scalability'))
