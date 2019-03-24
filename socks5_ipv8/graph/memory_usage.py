# bar chart
import numpy as np
import matplotlib.pyplot as plt

from matplotlib import rc

## for Palatino and other serif fonts use:
rc('font', **{'family': 'serif', 'serif': ['Palatino']})
rc('text', usetex=True)

client_means, client_std = (27.49, 29.69), (0.0, 0.62222)
forwarder_means, forwarder_std = (27.49, 27.49), (0.0, 0.73104)
server_means, server_std = (27.49, 29.55), (0.0, 3)

ind = np.arange(len(client_means))  # the x locations for the groups

dis = 0.2  # the width of the bars
pre_set = 0.18

fig, ax = plt.subplots()
rects1 = ax.bar(ind - dis, client_means, pre_set, yerr=client_std, ecolor="#504803",
                color='#859900', label='Client')
rects2 = ax.bar(ind, forwarder_means, pre_set, yerr=forwarder_std, ecolor="#504803",
                color='#CFA60D', label='Forwarder')
rects3 = ax.bar(ind + dis, server_means, pre_set, yerr=server_std, ecolor="#504803",
                color='#dc322f', label='Server')

# Add some text for labels, title and custom x-axis tick labels, etc.
yvars_axis = ['Memory usage (MB)']
yvars = ['Memory usage']
for x, y in zip(yvars_axis, yvars):
    ax.set_ylabel(x)
    ax.set_title('{} of each components in MultiProxy'.format(y))
    ax.set_xticks(ind)
    ax.set_xticklabels(('Before circumvention', 'After circumvention'))
    ax.legend(loc="upper right", bbox_to_anchor=(1, 1))
    ax.set_axisbelow(True)
    plt.grid(linestyle=':', linewidth=0.5)

    plt.xlim([-0.6, 2])


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
            ax.text(rect.get_x() + rect.get_width() * offset[xpos], 1.00 * height,
                    '{}'.format(height), ha=ha[xpos], va='bottom')


    autolabel(rects1, "left")
    autolabel(rects2, "center")
    autolabel(rects3, "right")

    save_dir = './fig'
    plt.show()
    # fig.savefig('{}/{}.pdf'.format(save_dir, y))
