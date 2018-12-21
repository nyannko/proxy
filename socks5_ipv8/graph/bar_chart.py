# bar chart
import numpy as np
import matplotlib.pyplot as plt

from matplotlib import rc

## for Palatino and other serif fonts use:
rc('font', **{'family': 'serif', 'serif': ['Palatino']})
rc('text', usetex=True)
# matplotlib.verbose.level = 'debug-annoying'

das1_means, das1_std = (10, 30, 10, 20), (2, 3, 4, 1)
das2_means, das2_std = (20, 40, 20, 30), (3, 5, 2, 3)
global_means, global_std = (30, 50, 30, 40), (3, 5, 2, 3)

ind = np.arange(len(das1_means))  # the x locations for the groups
width = 0.35  # the width of the bars

fig, ax = plt.subplots()
rects1 = ax.bar(ind - width / 2, das1_means, width / 2, yerr=das1_std, ecolor="#504803",
                color='#859900', label='DAS5 same cluster')
rects2 = ax.bar(ind, das2_means, width / 2, yerr=das2_std, ecolor="#504803",
                color='#CFA60D', label='DAS5 different clusters')
rects3 = ax.bar(ind + width / 2, global_means, width / 2, yerr=global_std, ecolor="#504803",
                color='#dc322f', label='Global cloud instances')

# Add some text for labels, title and custom x-axis tick labels, etc.
yvars_axis = ['Latency(ms)', 'Throughput(bps)', 'Packet loss rate(\%)', 'Page load time(ms)', 'CPU usgage(\%)',
              'Memory usage(MB)']
yvars = ['Latency', 'Throughput', 'Packet loss rate', 'Page load time', 'CPU Usage',
         'Memory Usage']
for x, y in zip(yvars_axis, yvars):
    ax.set_ylabel(x)
    ax.set_title('{} under different methods'.format(y))
    ax.set_xticks(ind)
    ax.set_xticklabels(('Unencrypted', 'Encrypted', 'No SGX', 'SGX'))
    ax.legend()
    ax.set_axisbelow(True)
    plt.grid(linestyle=':', linewidth=0.5)


    def autolabel(rects, xpos='center'):
        """
        Attach a text label above each bar in *rects*, displaying its height.

        *xpos* indicates which side to place the text w.r.t. the center of
        the bar. It can be one of the following {'center', 'right', 'left'}.
        """

        xpos = xpos.lower()  # normalize the case of the parameter
        ha = {'center': 'center', 'right': 'left', 'left': 'right'}
        offset = {'center': 0.5, 'right': 0.57, 'left': 0.43}  # x_txt = x + w*off

        for rect in rects:
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width() * offset[xpos], 1.01 * height,
                    '{}'.format(height), ha=ha[xpos], va='bottom')


    autolabel(rects1, "left")
    autolabel(rects2, "center")
    autolabel(rects3, "right")

    save_dir = './fig'
    plt.show()
    fig.savefig('{}/{}.pdf'.format(save_dir, y))
