# This file is part of rtools.
#
#    rtools is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    rtools is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with rtools.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np
from scipy.interpolate import InterpolatedUnivariateSpline as spline

class Curve(object):
    """
    Class to represent a curve in 3D cartesian space.

    Initialization
    --------------
    points : (Npts, 3) array
        The points defining the curve

    t : (Npts,) array, optional
        The parametrization for the curve. Defaults to <np.linspace(0, 1,
        Npts)>, ie. a linear spacing in parameter space between the provided
        points.
    """

    def __init__(self, points, t=None):
        self.points = np.asarray(points)
        self.Ndim = 3

        assert points.shape[1] == self.Ndim

        self.Npoints = points.shape[0]

        if t is None:
            self.t = np.linspace(0, 1, self.Npoints)
        else:
            self.t = np.asarray(t)
            assert self.t.shape[-1] == self.Npoints

        self.splines = [spline(self.t, self.points[:,i]) for i in range(self.Ndim)]
        self.derivatives = [self.splines[i].derivative() for i in range(self.Ndim)]

    def __call__(self, t):
        """
        Evaluate the curve at point t in parameter space
        """
        return np.array([self.splines[i](t) for i in range(self.Ndim)])

    def tangent(self, t):
        """
        Return the tangent vector at point t in parameter space
        """
        return np.array([self.derivatives[i](t) for i in range(self.Ndim)])

    def tangent_norm(self, t):
        """
        Return the norm of the tangent vector at point t in parameter space
        """
        return float(np.linalg.norm(self.tangent(t)))

    def visualize(self, show_points=True, show_curve=True):
        """
        Visualize the parametrized curve.

        <show_points> : include underlying points
        <show_curve>  : include splined path
        """
        import matplotlib.pyplot as plt
        import matplotlib.cm as cmx
        import matplotlib.colors as colors
        from mpl_toolkits.mplot3d import Axes3D

        fig= plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        # for proper visualization
        cm = plt.get_cmap('Reds')
        cNorm  = colors.Normalize(vmin=self.t[0], vmax=self.t[1])
        scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)

        if show_points:
            ax.scatter(xs=self.points[:,0],
                       ys=self.points[:,1],
                       zs=self.points[:,2],
                       c=cm(self.t),
                       edgecolors='none')
        if show_curve:
            Npts = 200
            pts = np.empty((Npts, self.Ndim))
            ts = np.linspace(min(self.t), max(self.t), Npts)
            for i, t in enumerate(ts):
                pts[i,:] = self.__call__(t)

            ax.plot(*pts.T)
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_zlabel('z')
        plt.show()

