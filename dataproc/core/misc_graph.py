#
#
# Copyright (C) 2014 Patricio Rojo
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 2 of the GNU General
# Public License as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.
#
#


__all__ = ['plot_accross', 'prep_data_plot',
           'imshowz', 'figaxes_xdate', 'figaxes', 'set_plot_props',
           'fill_between',
           ]

import warnings

import astropy.time as apt
import datetime
import dataproc as dp
import matplotlib.pyplot as plt
import astropy.io.fits as pf
import numpy as np
from typing import Optional, Tuple, List, Union
from collections.abc import Sequence
from dataproc.core.interactive_graphics import _imshowz_binding

TwoValues = Tuple[float, float]


def fill_between(ax,
                 bottom=None, top=None,
                 ylabel=None, facecolor=None,
                 **kwargs):
    if bottom is None and top is None:
        return
    if bottom is None:
        bottom = top*0
    if top is None:
        top *= max(bottom)
    if isinstance(top, float):
        top = np.array([top] * len(bottom))
    if isinstance(bottom, float):
        bottom = np.array([bottom] * len(top))
    ax2 = ax.twinx()
    ax2.fill_between(ax.get_lines()[0].get_xdata(),
                     bottom, top, **kwargs)
    ax2.set_ylabel(ylabel, color=facecolor)
    ax2.tick_params('y', colors=facecolor)
    margin = 0.05*(top.max() - bottom.min())
    ax2.set_ylim([bottom.min() - margin,
                  top.max() + margin])


def set_plot_props(ax, xlim=None, ylim=None,
                   legend: Union[dict, bool] = None,
                   save=None, show=None, close=False,
                   title=None, fill_between=None,
                   xlabel=None, ylabel=None,
                   ax_method=None,
                   vspan: Optional[TwoValues] = None,
                   ):
    """Set some standard properties for plot"""
    if ax_method is None:
        ax_method = {}
    if vspan is not None and 'vspan' not in ax_method.keys():
        ax_method['axvspan'] = {'xmin': vspan[0], 'xmax': vspan[1]}
    for method, method_kwargs in ax_method.items():
        if not isinstance(method_kwargs, list):
            method_kwargs = [method_kwargs]
        for kw in method_kwargs:
            getattr(ax, method)(**kw)
    if fill_between is not None:
        dp.fill_between(ax, **fill_between)

    if show is None:
        show = save is None

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if legend is not None:
        if 'loc' not in legend.keys():
            legend['loc'] = 1
        ax.legend(**legend)

    if xlim is not None:
        if isinstance(xlim, (int, float)):
            ax.set_xlim([0, xlim])
        else:
            ax.set_xlim(xlim)
    if ylim is not None:
        if isinstance(ylim, (int, float)):
            ax.set_ylim([0, ylim])
        else:
            ax.set_ylim(ylim)

    plt.tight_layout()
    if save is not None:
        ax.figure.savefig(save)
    if show:
        ax.figure.show()
    if close:
        plt.close(ax.figure)


def plot_accross(data,
                 axes=None, title=None,
                 ytitle=None, xtitle=None,
                 xlim=None, ylim=None,
                 ticks=True, colorbar=False,
                 hdu=0,
                 rotate=0,
                 pos=0,
                 forcenew=False,
                 **kwargs):
    """
    Plots along a cut across a particular axis of an n-dimensional data array

    Parameters
    ----------
    data : array_like
    axes: int, plt.Figure, plt.Axes, optional
    title: str, optional
    xlim : tuple, optional
        Section of the x-axis to plot
    ylim : tuple, optional
        Section of the y-axis to plot
    ticks : bool, optional
        Whether to display the ticks
    colorbar: bool, optional
        Wheteher to use a colorbar
    hdu : int, optional
        HDU to plot
    rotate : int, optional
    pos : int, optional
    forcenew : bool, optional
        Whether to create a new plot if no axis has been specified

    Returns
    -------
    accross : array_like
        Data used for the plot
    data : array_like
        A copy of the prepared data

    See Also
    --------
    prep_data_plot
    """
    print(ylim)

    data = prep_data_plot(data, hdu=hdu)

    # dt = data
    if not isinstance(pos, (list, tuple)):
        pos = [None] + [0]*(len(data.shape)-2) + [pos]
    if len(pos) != len(data.shape):
        raise TypeError(
            "pos (size: {0:d}) must have the same size as data array "
            "dimension ({1:d})".format(len(pos), len(data.shape)))
    pos = tuple([p is None and slice(None, None) or p for p in pos])

    accross = data[pos]

    fig, ax = dp.figaxes(axes)

    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)

    ax.plot(accross, label="ll")
    dp.set_plot_props(title=title, xlabel=xtitle, ylabel=ytitle)

    return accross, data


def prep_data_plot(indata, **kwargs):
    """
    Extracts the data used on a plot, accepts multiple formats.

    Parameters
    ----------
    indata : str, HDUList, dataproc.AstroFile or scipy array
    hdu : int, optional
        If indata is a HDUList, it will prepare the data for this specific hdu

    Returns
    -------
    array_like
        Extracted data
    """

    error_msg = None

    if isinstance(indata, pf.hdu.base._BaseHDU):
        data = indata.data
    elif isinstance(indata, pf.HDUList):
        hdu = kwargs.pop('hdu', 0)
        data = indata[hdu].data
        error_msg = "for HDU {}.\n".format(hdu)

    elif isinstance(indata, np.ndarray):
        data = indata
    else:
        af = dp.AstroFile(indata)
        if af:
            data = af.reader(**kwargs)
        else:
            raise TypeError(
                "Unrecognized type for input data: {0:s}"
                .format(indata.__class__.__name__,))

    if data is None:
        if error_msg is None:
            error_msg = indata
        raise ValueError("Nothing to plot {0:s}".format(error_msg,))

    return data


def imshowz(data,
            axes=None,
            minmax=None, xlim=None, ylim=None,
            cxy=None, plot_rad=None,
            ticks=True, colorbar=False,
            rotate=0, invertx=False, inverty=False,
            origin='lower', force_new=False,
            trim_data=False,
            extent=None, interactive=False,
            save=None, show=None, close=None,
            **kwargs):
    """
    Plots data using the zscale algorithm to fix the min and max contrast
    values.

    Parameters
    ----------
    data : string, HDU, HDUList, scipy array
        Data to  be plotted
    axes : int, plt.Figure, plt.Axes, optional
        Where to plot
    extent : optional
        Use this for limits to the drawing... no subarraying
    minmax : 2 element list or tuple
        Force this values of contrast
    xlim : tuple, optional
        Section of the x-axis to plot
    ylim : tuple, optional
        Section of the y-axis to plot
    cxy : tuple, optional
        Center at this coordinate and use plot_rad as radius.
        If both xlim and cxy are specified, then only cxy is considered.
    plot_rad : int, optional
        Radius of plotting area. Only relevant if cxy is not None.
        If None then it is the minimum distance to an image border.
    ticks : bool, optional
        Whether to display the ticks
    colorbar : bool, optional
        Whether to use a colorbar
    rotate : int, optional
        Rotates data, must be a multiple of 90
    invertx : bool, optional
        Invert data along the x axis
    inverty : bool, optional
        Invert data along the y axis
    origin : string, optional
        Option of the same name given to imshow
    force_new : bool, optional
        Whether to create a new plot if no axis has been specified
    trim_data : bool, optional
        If true, it will plot the area delimited by xlim and ylim
    show : bool, optional
        If true, it will call plt.show at  the end
    hdu : int, optional
        Which hdu to plot (Only if data is string or HDUList)

    kwargs: passed to matplotlib.pyplot.imshow()

    Returns
    -------
    int, int :
        Min and max contrast values
    """
    if show is None:
        show = save is None

    data = prep_data_plot(data, **kwargs)

    if interactive:
        show = False
        save = None

    if extent is not None and xlim is not None and ylim is not None:
        raise ValueError(
            "If extents is specified for imshowz, then xlim and ylim "
            "should not")

    if xlim is None:
        xlim = [0, data.shape[1]]
    if ylim is None:
        ylim = [0, data.shape[0]]

    if rotate:
        times = rotate/90
        if times % 1 != 0:
            raise ValueError("rotate must be a multiple of 90")
        data = np.rot90(data, int(times))
        # TODO: update x0, x1, y0, y1

    if cxy is not None:
        border_distance = [data.shape[1]-cxy[0], cxy[0],
                           data.shape[0]-cxy[1], cxy[1]]
        if plot_rad is None:
            plot_rad = min(border_distance)
        xlim = [cxy[0]-plot_rad, cxy[0]+plot_rad]
        ylim = [cxy[1]-plot_rad, cxy[1]+plot_rad]
        xlim[0] *= xlim[0] > 0
        xlim[1] = (xlim[1] > data.shape[1]) and data.shape[1] or xlim[1]
        ylim[0] *= ylim[0] > 0
        ylim[1] = (ylim[1] > data.shape[0]) and data.shape[0] or ylim[1]

    if trim_data:
        y0, y1, x0, x1 = ylim[0], ylim[1], xlim[0], xlim[1]
        data = data[y0: y1, x0: x1]
        xlim = [0, data.shape[1]-1]
        ylim = [0, data.shape[0]-1]

    # Find the contrast
    if minmax is None:
        mn, mx = dp.zscale(data)
    else:
        mn, mx = minmax

    fig, ax = dp.figaxes(axes, force_new=force_new)

    # Draw in the canvas
    if extent is None:
        extent = [xlim[0], xlim[1], ylim[0], ylim[1]]
    imag = ax.imshow(data, vmin=mn, vmax=mx, origin=origin,
                     extent=extent, **kwargs)
    if invertx:
        xlim = xlim[::-1]
    if inverty:
        ylim = ylim[::-1]

    if not ticks:
        ax.xaxis.set_ticklabels([' '] * 20)
        ax.yaxis.set_ticklabels([' '] * 20)

    if colorbar:
        fig.colorbar(imag)

    kwargs |= {'xlim': xlim,
               'ylim': ylim,
               'save': save,
               'show': show,
               'close': close,
               }
    set_plot_props(ax, **kwargs)

    outs = {'lims': [mn, mx]}
    if interactive:
        handler = _imshowz_binding(data, ax)
        outs['marks_xy'] = handler.outs['marks_xy']
        outs['handler'] = handler

    return outs


def figaxes_xdate(x, axes=None, clear=True):
    """
    Returns the figure and axes with a properly formatted date X-axis.

    Parameters
    ----------
    x : astropy.Time, datetime.datetime, float
        Time data used for the x axis. If its a float, then assumes JD
    axes : int, plt.Figure, plt.Axes, optional
    clear: bool, optional

    Returns
    -------
    Matplotlib figure, axes and x-axis data
    """
    import matplotlib.dates as md

    f, ax = dp.figaxes(axes, clear=clear)
    if isinstance(x, apt.Time):
        retx = x.plot_date
    elif isinstance(x, datetime.datetime):
        retx = x
    elif hasattr(x, '__iter__') and isinstance(x[0], (float, int)):
        retx = apt.Time(x, format='jd').plot_date
    else:
        raise ValueError("Time format not understood")

    ax.xaxis_date()
    tdelta = (retx[-1] - retx[0])*24*60
    if tdelta < 4:  # If range is smaller than 4 minutes
        fmt = '%H:%M:%S'
    elif tdelta < 8*60:  # If range is smaller than 8 hours
        fmt = '%H:%M'
    elif tdelta < 5*60*24:  # If range is smaller than 5 days
        fmt = '%Y-%b-%d %H:%M'
    elif tdelta < 1*60*24*365:  # If range is smaller than 1 years
        fmt = '%Y %b'
    else:
        fmt = '%Y'
    ax.xaxis.set_major_formatter(md.DateFormatter(fmt))

    return f, ax, retx


def figaxes(axes=None, force_new=True, clear=True) -> (plt.Figure, plt.Axes):
    """
    Function that accepts a variety of axes specifications  and returns the output
    ready for use with matplotlib

    Parameters
    ----------
    axes : int, plt.Figure, plt.Axes
    force_new : bool, optional
        If true starts a new axes when axes=None (and only then) instead of using last figure
    clear: bool, optional
        Delete previous axes content, if any

    Returns
    -------
    Matplotlib.pyplot figure and axes
    """
    if axes is None:
        if force_new:
            fig, ax = plt.subplots()
        else:
            plt.gcf().clf()
            fig, ax = plt.subplots(num=plt.gcf().number)
    elif isinstance(axes, int):
        fig = plt.figure(axes)
        if clear or len(fig.axes) == 0:
            fig.clf()
            ax = fig.add_subplot(111)
        else:
            ax = fig.axes[0]
    elif isinstance(axes, plt.Figure):
        fig = axes
        if clear:
            fig.clf()
        if len(fig.axes) == 0:
            ax = fig.add_subplot(111)
        ax = fig.axes[0]
    elif isinstance(axes, plt.Axes):
        ax = axes
        if clear:
            ax.cla()
        fig = axes.figure
    else:
        raise ValueError("Given value for axes ({0:s}) is not"
                         "recognized".format(axes,))

    return fig, ax


if __name__ == '__main__':
    a = dp.imshowz('/home/raw/tramos//ctio09/20190827/20190827_043.fits.gz', interactive=True)

