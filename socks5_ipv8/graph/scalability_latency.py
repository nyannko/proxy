import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerLine2D
from matplotlib.ticker import MaxNLocator
from matplotlib import rc

rc('font', **{'family': 'serif', 'serif': ['Palatino']})
rc('text', usetex=True)
fig, ax = plt.subplots()
ax.xaxis.set_major_locator(MaxNLocator(integer=True))

# first experiment
# multiproxy_time = [3.2004516129, 13.7819793039, 27.4041453901, 49.0140308031, 51.0447281399, 64.3305959184, 73.3000539143]
# mti_error = [0.613876007867, 9.44968077345, 18.8539221922, 27.2258935881, 38.2502476349, 48.986322341, 59.674617854]
# mth_error=[]
# multiproxy_throughput = [3326.99651613, 1159.56064064, 695.785425532, 532.185510451, 527.359228935, 471.813552653,455.4366839]
# keys = [1, 50, 100, 150, 200, 250, 300]

# second experiment
multiproxy_time = [3.4386744186046503, 3.912325284090909, 4.573214626391096, 10.133956782713085, 15.737391549295774,
                   20.6926212338594, 26.274491477272726, 29.363628133704733, 32.15415575916231, 35.323378343949045,
                   38.97251472471191, 43.61649682337993, 47.33813517060367, 47.401065375302665, 51.40561722488039,
                   54.85340324449594, 56.877130733944945, 59.54175672645739, 63.381828349944634, 66.5037003257329,
                   69.49925191675794, 73.50210432852387, 74.47266101694916, 78.15385563751316, 80.56858598726114,
                   81.49086068111455, 85.07991182572614, 89.36982328907048, 94.71875729166666, 97.09712959183673,
                   97.01868186323092]
keys = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230,
        240, 250, 260, 270, 280, 290, 300]

plt.xlabel('The number of Nodes')
plt.ylabel('Latency (s)')
plt.title('Latency with different nodes number')

# plt.axis([0, 3, 0, 80])
plt.grid(True, linestyle=":")
# l1, = plt.plot(keys, Tor, linestyle=":", marker='o', label='Tor', color='#859900')
# l3, = plt.plot(keys, multiproxy_throughput, linestyle="-.", marker='x', label='Multiproxy 1 hop', color='#dc322f')
l3, = plt.plot(keys, multiproxy_time, linestyle="-.", marker='.', label='Multiproxy 1 hop', color='#859900')
# plt.errorbar(keys, multiproxy_time, yerr=mti_error, capsize=2, linestyle=":",color='#859900')
# plt.legend(handler_map={l3: HandlerLine2D(numpoints=4)})

plt.show()

fig.savefig('fig/{}.pdf'.format('latency_scalability'))
