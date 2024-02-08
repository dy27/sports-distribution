import numpy as np
from scipy import special
import scipy.stats as stats
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt


def invert_odds(odds):
    prob = 1 / odds
    inverse_prob = 1 - prob
    inverse_odds = 1 / inverse_prob
    return inverse_odds


def opposing_lines_margin(home_line1, away_line1, home_line2, away_line2):
    """Calculate the margin bet odds formed by two opposing line bets"""
    line1_prob_sum = 1/home_line1 + 1/away_line1
    line2_prob_sum = 1/home_line2 + 1/away_line2

    prob_lowerbound = (1 - 1/away_line1) + (1 - 1/away_line2) - 1
    prob_theo = 1/home_line1/line1_prob_sum + 1/home_line2/line2_prob_sum - 1
    prob_upperbound = 1/home_line1 + 1/home_line2 - 1

    odds_upperbound = 1/prob_lowerbound
    odds_theo = 1/prob_theo
    odds_lowerbound = 1/prob_upperbound

    return odds_lowerbound, odds_theo, odds_upperbound




def line_transfrom(line):
    if line < 0:
        line += 0.5
    elif line > 0:
        line -= 0.5
    return line


def line_inverse_transform(line):
    if line < 0:
        line -= 0.5
    elif line > 0:
        line += 0.5
    return line


def plot_lines(ax, lines_dict, plot_midpoint=True, color=None, label=None):
    for line_value, lines in lines_dict.items():
        upperbound_prob = 1 / lines[0]['price']
        lowerbound_prob = 1 / invert_odds(lines[1]['price'])
        ax.vlines(x=line_transfrom(line_value), ymin=lowerbound_prob, ymax=upperbound_prob,
        color=color, linewidth=2, linestyle='--', label=label)
        ax.scatter(x=[line_transfrom(line_value),line_transfrom(line_value)], y=[upperbound_prob, lowerbound_prob],
                    color=color, marker='_', s=120, linewidth=2)
        if plot_midpoint:
            midpoint_prob = (upperbound_prob + lowerbound_prob) / 2
            ax.scatter(x=line_transfrom(line_value), y=midpoint_prob, color=color, marker='_', s=300, linewidth=2)


def midpoint_odds(odds, opposing_odds, tail_penalty=0):
    """Calculates a midpoint theo price based on a bookmaker quote.
    tail_penalty parameter can be adjusted to account for bookmaker leans for tail events."""
    upperbound_prob = 1 / odds
    lowerbound_prob = 1 / invert_odds(opposing_odds)
    theo_prob = (upperbound_prob + lowerbound_prob) / 2
    width = upperbound_prob - lowerbound_prob
    lean = (theo_prob - 0.5) * tail_penalty * width / 2
    adj_theo_prob = theo_prob + lean
    return 1 / adj_theo_prob


def fit_normal_cdf(lines_dict):
    line_values = sorted(lines_dict.keys())
    transformed_line_values = [line_transfrom(line) for line in line_values]
    lowerbound_probs = [1/invert_odds(lines_dict[line][1]['price']) for line in line_values]
    upperbound_probs = [1/lines_dict[line][0]['price'] for line in line_values]
    theo_probs = [1/midpoint_odds(lines_dict[line][0]['price'], lines_dict[line][1]['price']) for line in line_values]
    
    sigma_uncertainty = [abs(1/lines_dict[line][0]['price'] - 1/invert_odds(lines_dict[line][1]['price'])) for line in line_values]
    popt, pcov = curve_fit(stats.norm.cdf, transformed_line_values + transformed_line_values, lowerbound_probs + upperbound_probs, p0=[0,1], sigma=sigma_uncertainty+sigma_uncertainty)
    mu_fit, sigma_fit = popt
    return {
        'mu': mu_fit,
        'sigma': sigma_fit,
        'popt': popt,
        'pcov': pcov,
    }
    

def plot_normal_cdf(ax, model, xrange=None, plot_cov=False, cov_std_devs=2, num_points=300, color=None, label=None):
    mu = model['mu']
    sigma = model['sigma']
    if xrange is None:
        # xrange = [mu - 1.2*sigma, mu + 1.2*sigma]
        xrange = ax.get_xlim()
        xrange = [-100, 100]
    x_data = np.linspace(xrange[0], xrange[1], num_points)
    y_data = stats.norm.cdf(x_data, mu, sigma)
    ax.plot(x_data, y_data, color=color, label=label)
    if plot_cov:
        popt = model['popt']
        pcov = model['pcov']
        perr = np.sqrt(np.diag(pcov))
        ax.fill_between(x_data, stats.norm.cdf(x_data, *(popt - cov_std_devs*perr)), stats.norm.cdf(x_data, *(popt + cov_std_devs*perr)), color='gray', alpha=0.2)


class Ruler:
    def __init__(self, ax):
        self.ax = ax
        self.line_v = None
        self.line_h = None
        self.text_v = None
        self.text_h = None
        self.points = []
        self.cid_press = ax.figure.canvas.mpl_connect('button_press_event', self.on_press)

    def on_press(self, event):
        if event.inaxes == self.ax:
            rounded_x = round(event.xdata*2)/2
            self.points.append((rounded_x, event.ydata))
            if len(self.points) == 2:
                self.draw_ruler()
                self.points = []

    def draw_ruler(self):
        x1, y1 = self.points[0]
        x2, y2 = self.points[1]

        if self.line_v:
            self.line_v.remove()
        if self.line_h:
            self.line_h.remove()
        if self.text_v:
            self.text_v.remove()
        if self.text_h:
            self.text_h.remove()

        self.line_v, = self.ax.plot([x1, x1], [y1, y2], color='black', linestyle='--', linewidth=2)
        self.line_h, = self.ax.plot([x1, x2], [y2, y2], color='black', linestyle='--', linewidth=2)

        distance_v = abs(x2 - x1)
        distance_h = abs(y2 - y1)

        # Calculate text position for vertical distance
        text_v_x = (x1 + x2) / 2
        text_v_y = y2 + 0.03 * (self.ax.get_ylim()[1] - self.ax.get_ylim()[0])
        self.text_v = self.ax.text(text_v_x, text_v_y, f'dx: {distance_v:.1f}', color='black', ha='center', va='center')

        # Calculate text position for horizontal distance
        text_h_x = x1 - 0.05 * (self.ax.get_xlim()[1] - self.ax.get_xlim()[0])
        text_h_y = (y1 + y2) / 2
        self.text_h = self.ax.text(text_h_x, text_h_y, f'prob: {distance_h:.3f}\nodds: {1/distance_h:.2f}', color='black', ha='center', va='center')

        plt.draw()