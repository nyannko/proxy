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
multiproxy_throughput = [3138.0111627906977, 2808.0810454545453, 2472.758860890302, 1467.6220396158462,
                         977.756638028169, 741.9789497847919, 632.218234375, 628.6898356545961, 569.4095353403142,
                         553.9512165605095, 504.6980960307298, 447.0715870393901, 441.7447086614173, 473.1722384987894,
                         429.69961842105266, 428.4890162224797, 405.75031307339447, 397.47953026905833,
                         380.54090697674417, 375.30434961997827, 388.9144939759036, 362.1769112097669,
                         382.32485063559324, 378.0098029504742, 362.4630552016985, 353.17570588235293,
                         365.18977178423233, 347.0949254341165, 318.2684697916667, 340.81188877551017,
                         331.5013795837463]

keys = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230,
        240, 250, 260, 270, 280, 290, 300]

plt.xlabel('The number of Nodes')
plt.ylabel('Throughput (KB/s)')
plt.title('Throughput with different nodes number')

plt.grid(True, linestyle=":")
# l1, = plt.plot(keys, Tor, linestyle=":", marker='o', label='Tor', color='#859900')
# l3, = plt.plot(keys, multiproxy_throughput, linestyle="-.", marker='x', label='Multiproxy 1 hop', color='#dc322f')
l3, = plt.plot(keys, multiproxy_throughput, linestyle="-.", marker='x', label='Multiproxy 1 hop', color='#dc322f')
# plt.errorbar(keys, multiproxy_time, yerr=mti_error, capsize=2, linestyle=":",color='#859900')
# plt.legend(handler_map={l3: HandlerLine2D(numpoints=4)})

plt.show()

fig.savefig('fig/{}.pdf'.format('throughput_scalability'))
