import tools
import line_apis
from multi_query_apis import tab_multi_margin_sweep
import matplotlib.pyplot as plt
import numpy as np


SWEEPS = False

TAB_EVENT_ID_STR = 'Charlotte%20v%20Toronto'
POINTSBET_EVENT_ID_STR = '1764151'
NEDS_EVENT_ID_STR = 'dc48195f-0064-41de-b872-2a10ae8078b2'

# TAB_EVENT_ID_STR = 'Washington%20v%20Cleveland'
# POINTSBET_EVENT_ID_STR = '1764153'
# NEDS_EVENT_ID_STR = '811713c7-f570-4efa-8bd9-d957f73e7e11'

# TAB_EVENT_ID_STR = 'Boston%20v%20Atlanta'
# POINTSBET_EVENT_ID_STR = '1764154'
# NEDS_EVENT_ID_STR = '03bde8a1-f27c-4f7b-8222-1287a41408fa'

# TAB_EVENT_ID_STR = 'Miami%20v%20San%20Antonio'
# POINTSBET_EVENT_ID_STR = '1764155'
# NEDS_EVENT_ID_STR = 'aa98af98-05cb-4f0c-aeb1-3d143fe3327f'

# TAB_EVENT_ID_STR = 'Philadelphia%20v%20Golden%20State'
# POINTSBET_EVENT_ID_STR = '1764152'
# NEDS_EVENT_ID_STR = 'c463bb8f-bea3-4c0b-b69b-3a4dec1eae12'

# TAB_EVENT_ID_STR = 'LA%20Clippers%20v%20New%20Orleans'
# POINTSBET_EVENT_ID_STR = '1764240'
# NEDS_EVENT_ID_STR = '366313b5-5cfe-4603-95a2-80a5348bda29'

# TAB_EVENT_ID_STR = 'Sacramento%20v%20Detroit'
# POINTSBET_EVENT_ID_STR = '1764241'
# NEDS_EVENT_ID_STR = '35570099-47af-418b-b2f3-138f38445cf0'



def main():

    fig, ax = plt.subplots(figsize=(12,8))

    teams, tab_lines = line_apis.tab_get_lines(TAB_EVENT_ID_STR)
    _, pb_lines = line_apis.pointsbet_get_lines(POINTSBET_EVENT_ID_STR)
    _, neds_lines = line_apis.neds_get_lines(NEDS_EVENT_ID_STR)

    tab_lines_dict = line_apis.make_lines_dict(tab_lines)
    pb_lines_dict = line_apis.make_lines_dict(pb_lines)
    neds_lines_dict = line_apis.make_lines_dict(neds_lines)

    tools.plot_lines(ax, pb_lines_dict, color='red')
    tools.plot_lines(ax, neds_lines_dict, color='orange')
    tools.plot_lines(ax, tab_lines_dict, color='green')

    ax.set_autoscale_on(False)

    tab_model = tools.fit_normal_cdf(tab_lines_dict)
    pb_model = tools.fit_normal_cdf(pb_lines_dict)
    neds_model = tools.fit_normal_cdf(neds_lines_dict)

    tools.plot_normal_cdf(ax, pb_model, color='red', label='PointsBet')
    tools.plot_normal_cdf(ax, neds_model, color='orange', label='Neds')
    tools.plot_normal_cdf(ax, tab_model, color='green', label='TAB')
    # print(pb_model['mu'], pb_model['sigma'])

    if SWEEPS:
        sweeps = tab_multi_margin_sweep(tab_lines_dict)
        # print(sweeps) 

        for sweep in sweeps:
            price = sweep['price']
            line1 = sweep['home_line']['home_line']
            line2 = sweep['away_line']['home_line']
            print('lines', line1, line2)

            try:
                lb, tab_theo, ub = tools.opposing_lines_margin(tab_lines_dict[line1][0]['price'], tab_lines_dict[line1][1]['price'],
                                                            tab_lines_dict[line2][1]['price'], tab_lines_dict[line2][0]['price'])
            except:
                print("SOMETHING MESSED")
                continue
            print(tab_lines_dict[line1][0]['price'], tab_lines_dict[line1][1]['price'],tab_lines_dict[line2][1]['price'], tab_lines_dict[line2][0]['price'] )
            print(round(tab_theo, 2), price)
            print('EV bound: ',  100*round(price / ub, 3)-100, ' - ', 100*round(price / lb, 3)-100)
            print('EV:', 100*round(price / tab_theo, 3)-100)
            if price/tab_theo - 1 > 0:
                print('!!!!!!!!!!!!!!!')

            print()

    def custom_formatter(x, pos):
        if x > 0:
            return '{:.1f}'.format(x + 0.5)
        elif x < 0:
            return '{:.1f}'.format(x - 0.5)
        else:
            return '{:.1f}'.format(x)

    ax.xaxis.set_major_formatter(plt.FuncFormatter(custom_formatter))

    current_xlim = ax.get_xlim()
    min_tick = np.floor(current_xlim[0] / 1.5) * 1.5 - 0.5
    max_tick = np.ceil(current_xlim[1] / 1.5) * 1.5 + 0.5
    # print(min_tick, max_tick)
    ax.set_xticks(np.arange(min_tick, max_tick + 0.1, 1))
    # print(np.arange(min_tick, max_tick + 0.1, 1))
    ax.set_yticks(np.arange(0, 1+0.01, 0.05))
    ax.set_xlabel(f'Home Side Handicap')
    ax.set_ylabel('Probability')
    ax.set_title(f'Handicap Line CDF: {teams[0]} (Home) vs {teams[1]} (Away)')
    ax.minorticks_on()
    ax.legend(loc='upper left')
    ax.grid()

    ruler = tools.Ruler(ax)
    fig.tight_layout()
    plt.show()



if __name__ == '__main__':
    main()