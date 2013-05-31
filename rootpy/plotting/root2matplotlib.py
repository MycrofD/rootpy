# Copyright 2012 the rootpy developers
# distributed under the terms of the GNU General Public License
# trigger ROOT's finalSetup (GUI thread) before matplotlib's
import ROOT
ROOT.kTRUE
from .hist import _HistBase
from .graph import Graph
from math import sqrt
import matplotlib.pyplot as plt
import numpy as np
import math


__all__ = [
    'hist',
    'bar',
    'errorbar',
    'fill_between',
]


def _set_defaults(h, kwargs, types=['common']):

    defaults = {}
    for key in types:
        if key == 'common':
            defaults['label'] = h.GetTitle()
            defaults['visible'] = h.visible
        elif key == 'fill':
            defaults['linestyle'] = h.GetLineStyle('mpl')
            defaults['linewidth'] = h.GetLineWidth() * 0.5
            defaults['edgecolor'] = h.GetLineColor('mpl')
            defaults['facecolor'] = h.GetFillColor('mpl')
            root_fillstyle = h.GetFillStyle('root')
            if root_fillstyle == 0:
                defaults['fill'] = False
            elif root_fillstyle == 1001:
                defaults['fill'] = True
            else:
                defaults['hatch'] = h.GetFillStyle('mpl')
        elif key == 'errors':
            defaults['ecolor'] = h.GetLineColor('mpl')
        elif key == 'errorbar':
            defaults['fmt'] = h.GetMarkerStyle('mpl')
        elif key == 'marker':
            defaults['marker'] = h.GetMarkerStyle('mpl')
            defaults['markersize'] = h.GetMarkerSize() * 5
            defaults['markeredgecolor'] = h.GetMarkerColor('mpl')
            defaults['markerfacecolor'] = h.GetMarkerColor('mpl')
    for key, value in defaults.items():
        if key not in kwargs:
            kwargs[key] = value


def _set_bounds(h,
                axes=None,
                prev_ylim=None,
                xpadding=0,
                ypadding=.1,
                xerror_in_padding=True,
                yerror_in_padding=True,
                snap_zero=True,
                bottom=None,
                log=None):

    if axes is None:
        axes = plt.gca()

    if prev_ylim is None:
        prev_ylim = plt.ylim()
        was_empty = False
    else:
        was_empty = prev_ylim == (0., 1.)

    if log is None:
        log = axes.get_yscale() == 'log'

    if isinstance(h, _HistBase):
        xmin = h.xedgesl(0)
        xmax = h.xedgesh(-1)
        if yerror_in_padding:
            h_array = np.array(h)
            ymin = (h_array - np.array(list(h.yerrl()))).min()
            ymax = (h_array + np.array(list(h.yerrh()))).max()
        else:
            ymin = min(h)
            ymax = max(h)
    elif isinstance(h, Graph):
        if xerror_in_padding:
            x_array = np.array(list(h.x()))
            xmin = (x_array - np.array(list(h.xerrl()))).min()
            xmax = (x_array + np.array(list(h.xerrh()))).max()
        else:
            x_array = np.array(list(h.x()))
            xmin = x_array.min()
            xmax = x_array.max()
        if yerror_in_padding:
            y_array = np.array(list(h.y()))
            ymin = (y_array - np.array(list(h.yerrl()))).min()
            ymax = (y_array + np.array(list(h.yerrh()))).max()
        else:
            y_array = np.array(list(h.y()))
            ymin = y_array.min()
            ymax = y_array.max()
    else:
        raise TypeError('unable to determine plot axes ranges from object of'
                ' type %s' % type(h))

    xwidth = xmax - xmin
    if isinstance(xpadding, (tuple, list)):
        if len(xpadding) != 2:
            raise ValueError("xpadding must be of length 2")
        xmin -= xpadding[0] * xwidth
        xmax += xpadding[1] * xwidth
    else:
        xmin -= xpadding * xwidth
        xmax += xpadding * xwidth

    if isinstance(ypadding, (list, tuple)):
        if len(ypadding) != 2:
            raise ValueError("ypadding must be of length 2")
        ypadding_top = ypadding[0]
        ypadding_bottom = ypadding[1]
    else:
        ypadding_top = ypadding_bottom = ypadding

    if bottom is not None:
        ymin = bottom

    if snap_zero and not (ymin < 0 < ymax) and not log:
        if ymin >= 0:
            ywidth = ymax
            ymin = 0
            ymax += ypadding_top * ywidth
        elif ymax <= 0:
            ywidth = ymax - ymin
            ymax = 0
            ymin -= ypadding_bottom * ywidth
    elif log:
        ywidth = math.log(ymax) - math.log(ymin)
        if bottom is not None:
            ymin *= 10 ** (- ypadding_bottom * ywidth)
        ymax *= 10 ** (ypadding_top * ywidth)
    else:
        ywidth = ymax - ymin
        ymin -= ypadding_bottom * ywidth
        ymax += ypadding_top * ywidth

    if was_empty:
        axes.set_xlim([xmin, xmax])
        axes.set_ylim([ymin, ymax])
    else:
        curr_xmin, curr_xmax = axes.get_xlim()
        axes.set_xlim([min(curr_xmin, xmin), max(curr_xmax, xmax)])
        curr_ymin, curr_ymax = prev_ylim
        if bottom is not None:
            curr_ymin = bottom
        if log:
            axes.set_ylim([bottom, max(curr_ymax, ymax)])
        else:
            axes.set_ylim([min(curr_ymin, ymin), max(curr_ymax, ymax)])


def maybe_reversed(x, reverse=False):

    if reverse:
        return reversed(x)
    return x


def hist(hists, stacked=True, reverse=False, axes=None,
         xpadding=0, ypadding=.1,
         yerror_in_padding=True,
         snap_zero=True,
         bottom=None,
         **kwargs):
    """
    Make a matplotlib 'step' hist plot.

    *hists* may be a single :class:`rootpy.plotting.hist.Hist` object or a
    :class:`rootpy.plotting.hist.HistStack`.  The *histtype* will be
    set automatically to 'step' or 'stepfilled' for each object based on its
    FillStyle.  All additional keyword arguments will be passed to
    :func:`matplotlib.pyplot.hist`.

    Keyword arguments:

      *stacked*:
        If *True*, the hists will be stacked with the first hist on the bottom.
        If *False*, the hists will be overlaid with the first hist in the
        background.

      *reverse*:
        If *True*, the stacking order will be reversed.
    """
    curr_ylim = plt.ylim()
    ymin = bottom
    if axes is None:
        axes = plt.gca()
    log_scale = kwargs.pop('log', axes.get_yscale() == 'log')
    kwargs['log'] = log_scale
    returns = []
    if isinstance(hists, _HistBase) or isinstance(hists, Graph):
        # This is a single plottable object.
        returns = _hist(hists, axes=axes, bottom=bottom, **kwargs)
        _set_bounds(hists, axes=axes, prev_ylim=curr_ylim,
                    xpadding=xpadding, ypadding=ypadding,
                    yerror_in_padding=yerror_in_padding,
                    snap_zero=snap_zero,
                    bottom=ymin, log=log_scale)
    elif stacked:
        if axes is None:
            axes = plt.gca()
        for i in range(len(hists)):
            if reverse:
                hsum = sum(hists[i:])
            elif i:
                hsum = sum(reversed(hists[:-i]))
            else:
                hsum = sum(reversed(hists))
            # Plot the fill with no edge.
            returns.append(_hist(hsum, bottom=bottom, **kwargs))
            # Plot the edge with no fill.
            axes.hist(list(hsum.x()), weights=hsum, bins=list(hsum.xedges()),
                      histtype='step', edgecolor=hsum.GetLineColor(),
                      bottom=bottom, log=log_scale)
        _set_bounds(sum(hists), axes=axes, prev_ylim=curr_ylim,
                    xpadding=xpadding, ypadding=ypadding,
                    yerror_in_padding=yerror_in_padding,
                    snap_zero=snap_zero,
                    bottom=ymin, log=log_scale)
    else:
        for h in maybe_reversed(hists, reverse):
            returns.append(_hist(h, axes=axes, bottom=bottom, **kwargs))
        _set_bounds(max(hists), axes=axes, prev_ylim=curr_ylim,
                    xpadding=xpadding, ypadding=ypadding,
                    yerror_in_padding=yerror_in_padding,
                    snap_zero=snap_zero,
                    bottom=ymin, log=log_scale)
    return returns


def _hist(h, axes=None, **kwargs):

    if axes is None:
        axes = plt.gca()
    _set_defaults(h, kwargs, ['common', 'fill'])
    kwargs['histtype'] = h.GetFillStyle('root') and 'stepfilled' or 'step'
    return axes.hist(list(h.x()), weights=list(h.y()), bins=list(h.xedges()), **kwargs)


def bar(hists, stacked=True, reverse=False,
        xerr=False, yerr=True,
        rwidth=0.8, axes=None,
        xpadding=0, ypadding=.1,
        yerror_in_padding=True,
        snap_zero=True,
        bottom=None,
        **kwargs):
    """
    Make a matplotlib bar plot.

    *hists* may be a single :class:`rootpy.plotting.hist.Hist`, a single
    :class:`rootpy.plotting.graph.Graph`, a list of either type, or a
    :class:`rootpy.plotting.hist.HistStack`.  All additional keyword
    arguments will be passed to :func:`matplotlib.pyplot.bar`.

    Keyword arguments:

      *stacked*:
        If *True*, the hists will be stacked with the first hist on the bottom.
        If *False*, the hists will be overlaid with the first hist in the
        background.  If 'cluster', then the bars will be arranged side-by-side.

      *reverse*:
        If *True*, the stacking order is reversed.

      *xerr*:
        If *True*, x error bars will be displayed.

      *yerr*:
        If *False*, no y errors are displayed.  If *True*, an individual y error
        will be displayed for each hist in the stack.  If 'linear' or
        'quadratic', a single error bar will be displayed with either the linear
        or quadratic sum of the individual errors.

      *rwidth*:
        The relative width of the bars as a fraction of the bin width.
    """
    curr_ylim = plt.ylim()
    ymin = bottom
    if axes is None:
        axes = plt.gca()
    log_scale = kwargs.pop('log', axes.get_yscale() == 'log')
    kwargs['log'] = log_scale
    returns = []
    if isinstance(hists, _HistBase):
        # This is a single histogram.
        returns = _bar(hists, xerr=xerr, yerr=yerr,
                       axes=axes, bottom=bottom, **kwargs)
        _set_bounds(hists, axes=axes, prev_ylim=curr_ylim,
                    xpadding=xpadding, ypadding=ypadding,
                    yerror_in_padding=yerror_in_padding,
                    snap_zero=snap_zero,
                    bottom=ymin, log=log_scale)
    elif stacked == 'cluster':
        nhists = len(hists)
        hlist = maybe_reversed(hists, reverse)
        for i, h in enumerate(hlist):
            width = rwidth / nhists
            offset = (1 - rwidth) / 2 + i * width
            returns.append(_bar(h, offset, width,
                xerr=xerr, yerr=yerr, axes=axes, bottom=bottom, **kwargs))
        _set_bounds(sum(hists), axes=axes, prev_ylim=curr_ylim,
                    xpadding=xpadding, ypadding=ypadding,
                    yerror_in_padding=yerror_in_padding,
                    snap_zero=snap_zero,
                    bottom=ymin, log=log_scale)
    elif stacked is True:
        nhists = len(hists)
        hlist = maybe_reversed(hists, reverse)
        toterr = None
        if bottom is None and log_scale:
            bottom = 10 ** np.floor(np.log10(min(1, min(hlist[0]))))
        if yerr == 'linear':
            toterr = [sum([h.GetBinError(i + 1) for h in hists])
                      for i in range(len(hists[0]))]
        elif yerr == 'quadratic':
            toterr = [sqrt(sum([h.GetBinError(i + 1) ** 2 for h in hists]))
                      for i in range(len(hists[0]))]
        for i, h in enumerate(hlist):
            err = None
            if yerr is True:
                err = True
            elif yerr and i == (nhists - 1):
                err = toterr
            returns.append(_bar(h,
                xerr=xerr, yerr=err,
                bottom=bottom,
                axes=axes, **kwargs))
            if isinstance(bottom, _HistBase):
                bottom += h
            else:
                bottom = h.Clone()
        _set_bounds(bottom, axes=axes, prev_ylim=curr_ylim,
                    xpadding=xpadding, ypadding=ypadding,
                    yerror_in_padding=yerror_in_padding,
                    snap_zero=snap_zero,
                    bottom=ymin, log=log_scale)
    else:
        for h in hlist:
            returns.append(_bar(h, xerr=xerr, yerr=yerr,
                                bottom=bottom, axes=axes, **kwargs))
        _set_bounds(max(hists), axes=axes, prev_ylim=curr_ylim,
                    xpadding=xpadding, ypadding=ypadding,
                    yerror_in_padding=yerror_in_padding,
                    snap_zero=snap_zero,
                    bottom=ymin, log=log_scale)
    return returns


def _bar(h, roffset=0., rwidth=1., xerr=None, yerr=None, axes=None, **kwargs):

    if axes is None:
        axes = plt.gca()
    if xerr:
        xerr = np.array([list(h.xerrl()), list(h.xerrh())])
    if yerr:
        yerr = np.array([list(h.yerrl()), list(h.yerrh())])
    _set_defaults(h, kwargs, ['common', 'fill', 'errors'])
    width = [x * rwidth for x in h.xwidth()]
    left = [h.xedgesl(i) + h.xwidth(i) * roffset for i in range(len(h))]
    height = list(h)
    return axes.bar(left, height, width=width, xerr=xerr, yerr=yerr, **kwargs)


def errorbar(hists, xerr=True, yerr=True, axes=None,
             xpadding=0, ypadding=.1,
             xerror_in_padding=True,
             yerror_in_padding=True,
             snap_zero=True,
             emptybins=True,
             bottom=None,
             **kwargs):
    """
    Make a matplotlib errorbar plot.

    *hists* may be a single :class:`rootpy.plotting.hist.Hist`, a single
    :class:`rootpy.plotting.graph.Graph`, a list of either type, or a
    :class:`rootpy.plotting.hist.HistStack`.  All additional keyword
    arguments will be passed to :func:`matplotlib.pyplot.errorbar`.

    Keyword arguments:

      *xerr/yerr*:
        If *True*, display the x/y errors for each point.
    """
    curr_ylim = plt.ylim()
    returns = []
    if isinstance(hists, _HistBase) or isinstance(hists, Graph):
        # This is a single plottable object.
        returns = _errorbar(hists, xerr, yerr,
                axes=axes, emptybins=emptybins, **kwargs)
        _set_bounds(hists, axes=axes, prev_ylim=curr_ylim,
                    xpadding=xpadding, ypadding=ypadding,
                    xerror_in_padding=xerror_in_padding,
                    yerror_in_padding=yerror_in_padding,
                    snap_zero=snap_zero,
                    bottom=bottom)
    else:
        for h in hists:
            returns.append(_errorbar(h, xerr, yerr,
                axes=axes, emptybins=emptybins, **kwargs))
        _set_bounds(max(hists), axes=axes, prev_ylim=curr_ylim,
                    xpadding=xpadding, ypadding=ypadding,
                    xerror_in_padding=xerror_in_padding,
                    yerror_in_padding=yerror_in_padding,
                    snap_zero=snap_zero,
                    bottom=bottom)
    return returns


def _errorbar(h, xerr, yerr, axes=None, emptybins=True, **kwargs):

    if axes is None:
        axes = plt.gca()
    _set_defaults(h, kwargs, ['common', 'errors', 'errorbar', 'marker'])
    if xerr:
        xerr = np.array([list(h.xerrl()), list(h.xerrh())])
    if yerr:
        yerr = np.array([list(h.yerrl()), list(h.yerrh())])
    x = np.array(list(h.x()))
    y = np.array(list(h.y()))
    if not emptybins:
        nonempty = y != 0
        x = x[nonempty]
        y = y[nonempty]
        if xerr is not False:
            xerr = xerr[:, nonempty]
        if yerr is not False:
            yerr = yerr[:, nonempty]
    return axes.errorbar(x, y, xerr=xerr, yerr=yerr, **kwargs)


def fill_between(high, low, axes=None, **kwargs):
    """
    Fill the region between two histograms or graphs

    *high* and *low* may be a single :class:`rootpy.plotting.hist.Hist`,
    or a single :class:`rootpy.plotting.graph.Graph`. All additional keyword
    arguments will be passed to :func:`matplotlib.pyplot.fill_between`.
    """
    if axes is None:
        axes = plt.gca()
    log_scale = axes.get_yscale() == 'log'
    high_xedges = list(high.xedges())
    low_xedges = list(low.xedges())
    if high_xedges != low_xedges:
        raise ValueError("histogram x edges are incompatible")
    x = []
    top = []
    bottom = []
    for ibin in xrange(len(high)):
        x.append(high_xedges[ibin])
        top.append(high[ibin])
        bottom.append(low[ibin])
        x.append(high_xedges[ibin + 1])
        top.append(high[ibin])
        bottom.append(low[ibin])
    x = np.array(x)
    top = np.array(top)
    bottom = np.array(bottom)
    if log_scale:
        np.clip(top, 1E-300, 1E300, out=top)
        np.clip(bottom, 1E-300, 1E300, out=bottom)
    return axes.fill_between(x, top, bottom, **kwargs)
