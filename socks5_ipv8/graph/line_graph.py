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
# data = [10, 15, 5, 20]
ytb = [1135.82603687, 1139.61986301, 1140.44691781, 1142.19343696, 1154.59005146]
ytb_err = [59.985622917, 63.470227294, 59.843696193, 57.096040502, 57.670141573]

twi = [501.20517831, 506.970573811, 514.471799902, 517.5, 521.004426955]
twi_err = [56.637889078, 62.260810484, 56.330432738, 54.975332544, 65.7793490211]

ins = [432.844628099, 434.587155963, 434.844628099, 443.228476821, 448]
ins_err = [50.381801553, 57.645641194, 56.1254910117, 57.436036587, 56.309415901]

goo = [396.895833333, 417.851963746, 427.232980333, 431.863636364, 446.122913505]
goo_err = [54.318771163, 57.4047019936, 52.0205538527, 57.237363753, 57.537393959]

fbo = [645.664566929, 648.754330709, 651.744038156, 664.630331754, 668.524539877]
fbo_err = [57.0572155836, 51.159659407, 59.448068079, 56.140635955, 53.5430402957]
# das2 = [0, 0, 0, 0, 0]
# globals = [None, None, 3188.9, 3223.95454545, 4129.55]

# global_err = [106.367711266, 226.683094223, 253.225882366]

plt.xlabel('Hops')
plt.ylabel('Latency (ms)')
plt.title('Latency with different hop length')

# plt.axis([0, 3, 0, 80])
plt.grid(True, linestyle=":")
l2, = plt.plot(keys, goo, linestyle="--", marker='p', label='Google', color='#859900')
l3, = plt.plot(keys, ins, linestyle="-", marker='.', label='Instagram', color='#CFA60D')
l4, = plt.plot(keys, twi, linestyle="-.", marker='x', label='Twitter', color='#dc322f')
l5, = plt.plot(keys, fbo, linestyle="", marker='*', label='Facebook', color='#268bd2')
l1, = plt.plot(keys, ytb, linestyle=":", marker='o', label='YouTube', color='#586e75')

plt.legend(handler_map={l1: HandlerLine2D(numpoints=4)}, loc="upper right", bbox_to_anchor=(1,0.8))

# e = [0.11, 0.16, 0.19, 0.10]
plt.errorbar(keys, goo, yerr=goo_err, capsize=2, linestyle=":", color='#859900')
plt.errorbar(keys, ins, yerr=ins_err, capsize=2, linestyle=":", color='#CFA60D')
plt.errorbar(keys, twi, yerr=twi_err, capsize=2, linestyle=":", color='#dc322f')
plt.errorbar(keys, fbo, yerr=fbo_err, capsize=2, linestyle=":", color='#268bd2')
plt.errorbar(keys, ytb, yerr=ytb_err, capsize=2, linestyle=":", color='#586e75')
# plt.errorbar(keys[2:], globals[2:], yerr=global_err, capsize=2, linestyle="-.",color='#dc322f')

# label the data
for i, j in enumerate(goo):
    ax.annotate("{:.0f}".format(j), xy=(i, j))
# for i, j in enumerate(ins):
#     ax.annotate("{:.0f}".format(j), xy=(i, j))
for i, j in enumerate(twi):
    ax.annotate("{:.0f}".format(j), xy=(i, j))
for i, j in enumerate(fbo):
    ax.annotate("{:.0f}".format(j), xy=(i, j))
for i, j in enumerate(ytb):
    ax.annotate("{:.0f}".format(j), xy=(i, j))
# for i,j in enumerate(globals):
#     if i <= 1: continue
#     ax.annotate("{:.0f}".format(j), xy=(i, j))

plt.show()
fig.savefig('fig/{}.pdf'.format('line'))
