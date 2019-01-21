# bar chart
import numpy as np
import matplotlib.pyplot as plt

from matplotlib import rc

## for Palatino and other serif fonts use:
rc('font', **{'family': 'serif', 'serif': ['Palatino']})
rc('text', usetex=True)
# matplotlib.verbose.level = 'debug-annoying'

# with tor
go_means, go_std = (907.8, 940.4, 1164.5, 1190.72727273, 1713.47826087, 1345.7, 1351.71428571, 11797.1666667),(4.83321838944, 74.1082991304, 87.1105619314, 365.234608929, 170.912860982, 10.9731490467, 22.0013914217, 2538.97071774)
in_means, in_std = (1220.3, 1261.2, 1436.1, 1345.35714286, 2399.29166667, 1677.7, 1703.6, 14835.1),(4.36004587132, 8.2316462509, 20.2556165051, 100.620295555, 482.237189148, 87.494056941, 101.726299451, 3369.04041086)
tw_means, tw_std = (1967.7, 2000.0, 2140.7, 2379.52, 2982.34782609, 2402.1, 2575.1, 20620.5),(39.2302179448, 27.0333127826, 20.6835683575, 2015.65358373, 919.22545887, 41.9200429389, 444.320031059, 3905.19861851)
fb_means, fb_std = (2203.1, 2223.5, 2506.9, 2885.26666667, 3379.45454545, 2770.7, 2730.2, 34119.2),(74.0060132692, 59.6192083141, 129.279890161, 964.692729434, 201.8975274, 155.006483735, 28.6803068324, 3815.97292443)
yt_means, yt_std = (2968.5, 3032.5, 3188.9, 3223.95454545, 4129.55, 3286.8, 3302.3, 22220.6),(67.970949677, 96.575618041, 106.367711266, 226.683094223, 253.225882366, 69.4705693082, 75.6479345389, 4419.3432589)

# without tor
# go_means, go_std = (907.8, 940.4, 1164.5, 1190.72727273, 1713.47826087, 1345.7, 1351.71428571),(4.83321838944, 74.1082991304, 87.1105619314, 365.234608929, 170.912860982, 10.9731490467, 22.0013914217)
# in_means, in_std = (1220.3, 1261.2, 1436.1, 1345.35714286, 2399.29166667, 1677.7, 1703.6),(4.36004587132, 8.2316462509, 20.2556165051, 100.620295555, 482.237189148, 87.494056941, 101.726299451)
# tw_means, tw_std = (1967.7, 2000.0, 2140.7, 2379.52, 2982.34782609, 2402.1, 2575.1),(39.2302179448, 27.0333127826, 20.6835683575, 2015.65358373, 919.22545887, 41.9200429389, 444.320031059)
# fb_means, fb_std = (2203.1, 2223.5, 2506.9, 2885.26666667, 3379.45454545, 2770.7, 2730.2),(74.0060132692, 59.6192083141, 129.279890161, 964.692729434, 201.8975274, 155.006483735, 28.6803068324)
# yt_means, yt_std = (2968.5, 3032.5, 3188.9, 3223.95454545, 4129.55, 3286.8, 3302.3),(67.970949677, 96.575618041, 106.367711266, 226.683094223, 253.225882366, 69.4705693082, 75.6479345389)

ind = np.arange(len(go_means))  # the x locations for the groups
width = 0.25  # the width of the bars

fig, ax = plt.subplots()
rects1 = ax.bar(ind - width, go_means, width / 2, yerr=go_std, capsize=2, ecolor="#504803",
                color='#859900', label='Google')
rects2 = ax.bar(ind - width / 2, in_means, width / 2, yerr=in_std, capsize=2, ecolor="#504803",
                color='#CFA60D', label='Instagram')
rects3 = ax.bar(ind, tw_means, width / 2, yerr=tw_std, capsize=2, ecolor="#504803",
                color='#dc322f', label='Twitter')
rects4 = ax.bar(ind + width / 2, fb_means, width / 2, yerr=fb_std, capsize=2, ecolor="#504803",
                color='#268bd2', label='Facebook')
rects5 = ax.bar(ind + width, yt_means, width / 2, yerr=yt_std, capsize=2, ecolor="#504803",
                color='#586e75', label='YouTube')

# Add some text for labels, title and custom x-axis tick labels, etc.
yvars_axis = ['Latency(ms)']
yvars = ['Latency']
for x, y in zip(yvars_axis, yvars):
    ax.set_ylabel(x)
    ax.set_title('{} under different methods'.format(y))
    ax.set_xticks(ind)
    ax.set_xticklabels(('Shadowsocks', 'V2Ray', 'MProxy1', 'MProxy2', 'MProxy3', 'OpenVPN', 'OpenConnect', 'Tor'))
    # ax.set_xticklabels(('Shadowsocks', 'V2Ray', 'MultiProxy1', 'MultiProxy2', 'MultiProxy3', 'OpenVPN', 'OpenConnect'))
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


    # autolabel(rects1, "left")
    # autolabel(rects2, "center")
    # autolabel(rects3, "right")

    save_dir = './fig'
    plt.show()
    fig.savefig('{}/{}.pdf'.format(save_dir, y))
