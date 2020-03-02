"""
Module to allow for quick fitting
"""

from __future__ import print_function

import time
import numpy as np
import warnings

from scipy.optimize import curve_fit
from scipy.optimize import minimize


def fit_generic(x, y, fitfunc, p0,
                 method='Nelder-Mead',
                 measure = 'absolute',
                 show = False,
                 _verbose=False,
                 **kwargs):
    """
    Fit a generic function by minimizing the measure

        M_absolute(param) = sum((y - fitfunc(x, param))**2),

    or

        M_relative(param) = sum((y - fitfunc(x, param)/y)**2).

    This is hence a least (relative) square optimization yet without using the
    unflexible Levenberg Marquardt algorithm. Can be as well used to do
    non-linear regression.


    Parameters
    ----------
    x : (N,) array-like
        Input x data.

    y : (N,) array-like
        Input x data.

    fitfunc : function
        Target function that is callable via fitfunc(x, *param).

    p0 : (Nparam,) array-like
        Initial parameter guess.

    method : string, optional (default = "Nelder-Mead")
        Any of scipy's minimizing routines. Have a look at
        scipy.optimize.minimize. Shortened excerpt:

        "Nelder-Mead" uses the Simplex algorithm.

        "Powell" is a modification of Powell's method which is a conjugate
            direction method.

        "CG" uses a nonlinear conjugate gradient algorithm.

        "BFGS" uses the quasi-Newton method of Broyden, Fletcher, Goldfarb, and
            Shanno (BFGS).

        "Newton-CG" uses a Newton-CG algorithm (also known as the truncated
            Newton method).

        "Anneal" uses simulated annealing, which is a probabilistic
            metaheuristic algorithm for global optimization.

    measure : string, optional ({*"absolute"*, "relative"})
        Defines the measure to be optimized. Either absolute or relative
        errors.

    show: boolean, optional (default = False)
        Visualize fit result.

    _verbose : boolean, optional (default = True)
        Print some information to stdout.

    **kwargs : Further arguments that will be directly passed to
        scipty.optimize.minimize()

    Returns
    -------
    opt_param : (Nparam,) array
        The optimized parameters.

    opt_fitfunc : function
        The readily-parametrized fit function

    res : OptimizeResult object
        The result as provided by scipy.optimize.minimize()
        We add the R^2 value on top ;)
    """

    # this is our measure. We may want to add a second measure if the data is
    # heteroscedastic.
    if measure == 'absolute':
        def _errfunc(param, x, y):
            return np.sum((y - fitfunc(x, *param))**2)

    elif measure == 'relative':
        def _errfunc(param, x, y):
            return np.sum((y - fitfunc(x, *param)/y)**2)
    else:
        msg = 'Undefined measure "{}"'.format(measure)
        raise ValueError(msg)

    options = {'disp' : _verbose}

    if not 'options' in kwargs.keys():
        kwargs['options'] = options
    else:
        kwargs['options'].update(options)

    res = minimize(fun = _errfunc,
                   x0 = p0,
                   method = method,
                   args = (x, y),
                   **kwargs)

    if res['success']:
        opt_param = res['x']
    else:
        opt_param = np.ones_like(p0) * np.nan

    opt_fitfunc = lambda x : fitfunc(x, *opt_param)

    res['R^2'] = calc_Rsquare(times=x,
                      signal=y,
                      fitfunc=opt_fitfunc)


    if show:
        import matplotlib.pyplot as plt
        ax = plt.figure().add_subplot(111)

        ax.plot(x,y, color = 'black', ls = '', marker = 'o', label = 'data points')
        ax.plot(x, opt_fitfunc(x), color = 'red', lw = 2, label = 'fit function')

        ax.set_xlabel('x')
        ax.set_ylabel('y')

        plt.show()

    return opt_param, opt_fitfunc, res


def fit_exponential(x, y, linearize=False, **kwargs):
    """
    Fit to

        y = p[0]*exp(-p[1] * x)

    if possible, linearize the model.

    Parameters
    ----------
    x : (N,) array-like
        Input x data.

    y : (N,) array-like
        Input x data.

    linearize : boolean, optional (default=True)
        Try to linearize the data by taking the logarithm. This results in a
        linear regression which is much more wll behaved.

    method : string, optional (default = "Nelder-Mead")
        Any of scipy's minimizing routines. Have a look at
        scipy.optimize.minimize. Shortened excerpt:

        "Nelder-Mead" uses the Simplex algorithm.

        "Powell" is a modification of Powell's method which is a conjugate
            direction method.

        "CG" uses a nonlinear conjugate gradient algorithm.

        "BFGS" uses the quasi-Newton method of Broyden, Fletcher, Goldfarb, and
            Shanno (BFGS).

        "Newton-CG" uses a Newton-CG algorithm (also known as the truncated
            Newton method).

        "Anneal" uses simulated annealing, which is a probabilistic
            metaheuristic algorithm for global optimization.

    measure : string, optional ({*"absolute"*, "relative"})
        Defines the measure to be optimized. Either absolute or relative
        errors. See doc of ``fit_generic()'' for more details

    show: boolean, optional (default = False)
        Visualize fit result.

    _verbose : boolean, optional (default = True)
        Print some information to stdout.

    **kwargs : Further arguments that will be directly passed to
        scipty.optimize.minimize()

    Returns
    -------
    opt_param : (Nparam,) array
        The optimized parameters.

    opt_fitfunc : function
        The readily-parametrized fit function

    res : OptimizeResult object
        The result as provided by scipy.optimize.minimize()
    """

    x = np.asarray(x)
    y = np.asarray(y)

    def _fitfunc(x, A, alpha):
        return A*np.exp(-alpha*x)

    if linearize:
        if np.any(y <= 0.):
            msg = 'Negative values make linearization impossible'
            raise ValueError(msg)

        # caution: These are the linear paramenters
        p, opt_fitfunc, res = fit_linear(x, np.log(y), **kwargs)

        # convert these parameters to the exponential ones:
        opt_p = [np.exp(p[0]), -p[1]]
        opt_fitfunc = lambda x: _fitfunc(x, *opt_p)

    else:
        p0 = kwargs.pop('p0', None)

        if p0 is None:
            # estimating parameters
            for i in range(len(y)):
                inv_alpha_guess = x[i]
                if y[i] < y[0]/np.e:
                    break

            p0 = [y[0], 1./inv_alpha_guess]

        opt_p, opt_fitfunc, res = fit_generic(x, y, _fitfunc, p0, **kwargs)

    res['R^2adj'] = calc_adjusted_Rsquare(times=x,
                                          signal=y,
                                          fitfunc=opt_fitfunc,
                                          Nparam=2)

    return opt_p, opt_fitfunc, res


def fit_linear(x, y, **kwargs):
    """
    Fit to

        y = p[0]*x + p[1]

    Parameters
    ----------
    x : (N,) array-like
        Input x data.

    y : (N,) array-like
        Input x data.

    method : string, optional (default = "Nelder-Mead")
        Any of scipy's minimizing routines. Have a look at
        scipy.optimize.minimize. Shortened excerpt:

        "Nelder-Mead" uses the Simplex algorithm.

        "Powell" is a modification of Powell's method which is a conjugate
            direction method.

        "CG" uses a nonlinear conjugate gradient algorithm.

        "BFGS" uses the quasi-Newton method of Broyden, Fletcher, Goldfarb, and
            Shanno (BFGS).

        "Newton-CG" uses a Newton-CG algorithm (also known as the truncated
            Newton method).

        "Anneal" uses simulated annealing, which is a probabilistic
            metaheuristic algorithm for global optimization.

    measure : string, optional ({*"absolute"*, "relative"})
        Defines the measure to be optimized. Either absolute or relative
        errors. See doc of ``fit_generic()'' for more details

    show: boolean, optional (default = False)
        Visualize fit result.

    _verbose : boolean, optional (default = True)
        Print some information to stdout.

    **kwargs : Further arguments that will be directly passed to
        scipty.optimize.minimize()

    Returns
    -------
    opt_param : (Nparam,) array
        The optimized parameters.

    opt_fitfunc : function
        The readily-parametrized fit function

    res : OptimizeResult object
        The result as provided by scipy.optimize.minimize()
    """
    x = np.asarray(x)
    y = np.asarray(y)

    def _fitfunc(x, A, alpha):
        return alpha*x + A

    # initial guess... assume we start from x=0
    p0 = [y[0], (y[-1]-y[0])/(x[-1]-x[0])]

    opt_p, opt_fitfunc, res = fit_generic(x, y, _fitfunc, p0, **kwargs)

    res['R^2adj'] = calc_adjusted_Rsquare(times=x,
                                          signal=y,
                                          fitfunc=opt_fitfunc,
                                          Nparam=2)
    return opt_p, opt_fitfunc, res


def fit_exponential_plus_constant(x,y, **kwargs):
    """
    Fit to

        y = p[0]*exp(-p[1] * x) + p[2]

    Parameters
    ----------
    x : (N,) array-like
        Input x data.

    y : (N,) array-like
        Input x data.

    method : string, optional (default = "Nelder-Mead")
        Any of scipy's minimizing routines. Have a look at
        scipy.optimize.minimize. Shortened excerpt:

        "Nelder-Mead" uses the Simplex algorithm.

        "Powell" is a modification of Powell's method which is a conjugate
            direction method.

        "CG" uses a nonlinear conjugate gradient algorithm.

        "BFGS" uses the quasi-Newton method of Broyden, Fletcher, Goldfarb, and
            Shanno (BFGS).

        "Newton-CG" uses a Newton-CG algorithm (also known as the truncated
            Newton method).

        "Anneal" uses simulated annealing, which is a probabilistic
            metaheuristic algorithm for global optimization.

    measure : string, optional ({*"absolute"*, "relative"})
        Defines the measure to be optimized. Either absolute or relative
        errors. See doc of ``fit_generic()'' for more details

    show: boolean, optional (default = False)
        Visualize fit result.

    _verbose : boolean, optional (default = True)
        Print some information to stdout.

    **kwargs : Further arguments that will be directly passed to
        scipty.optimize.minimize()

    Returns
    -------
    opt_param : (Nparam,) array
        The optimized parameters.

    opt_fitfunc : function
        The readily-parametrized fit function

    res : OptimizeResult object
        The result as provided by scipy.optimize.minimize()
    """
    x = np.asarray(x)
    y = np.asarray(y)

    def _fitfunc(x, A, alpha, B):
        return A*np.exp(-alpha*x) + B

    p0 = kwargs.pop('p0', None)

    if p0 is None:
        # estimating parameters
        for i in range(len(y)):
            inv_alpha_guess = x[i]
            if y[i] < y[0]/np.e:
                break

        p0 = [y[0], 1./inv_alpha_guess, y[-1]]

    opt_p, opt_fitfunc, res = fit_generic(x, y, _fitfunc, p0, **kwargs)

    res['R^2adj'] = calc_adjusted_Rsquare(times=x,
                                          signal=y,
                                          fitfunc=opt_fitfunc,
                                          Nparam=3)
    return opt_p, opt_fitfunc, res



def fit_parabola(x,y, **kwargs):
    """
    Fit to

        y = p[0]*x**2 + p[1]*x + p[2]

    Parameters
    ----------
    x : (N,) array-like
        Input x data.

    y : (N,) array-like
        Input x data.

    method : string, optional (default = "Nelder-Mead")
        Any of scipy's minimizing routines. Have a look at
        scipy.optimize.minimize. Shortened excerpt:

        "Nelder-Mead" uses the Simplex algorithm.

        "Powell" is a modification of Powell's method which is a conjugate
            direction method.

        "CG" uses a nonlinear conjugate gradient algorithm.

        "BFGS" uses the quasi-Newton method of Broyden, Fletcher, Goldfarb, and
            Shanno (BFGS).

        "Newton-CG" uses a Newton-CG algorithm (also known as the truncated
            Newton method).

        "Anneal" uses simulated annealing, which is a probabilistic
            metaheuristic algorithm for global optimization.

    measure : string, optional ({*"absolute"*, "relative"})
        Defines the measure to be optimized. Either absolute or relative
        errors. See doc of ``fit_generic()'' for more details

    show: boolean, optional (default = False)
        Visualize fit result.

    _verbose : boolean, optional (default = True)
        Print some information to stdout.

    **kwargs : Further arguments that will be directly passed to
        scipty.optimize.minimize()

    Returns
    -------
    opt_param : (Nparam,) array
        The optimized parameters.

    opt_fitfunc : function
        The readily-parametrized fit function

    res : OptimizeResult object
        The result as provided by scipy.optimize.minimize()
    """
    x = np.asarray(x)
    y = np.asarray(y)

    def _fitfunc(x, A, B, C):
        return A*x**2 + B*x + C

    p0 = kwargs.pop('p0', np.zeros(3))

    opt_p, opt_fitfunc, res = fit_generic(x, y, _fitfunc, p0, **kwargs)

    res['R^2adj'] = calc_adjusted_Rsquare(times=x,
                                          signal=y,
                                          fitfunc=opt_fitfunc,
                                          Nparam=3)
    return opt_p, opt_fitfunc, res


def fit_x_squared(x,y, **kwargs):
    """
    Fit to

        y = p[0]*x**2

    Parameters
    ----------
    x : (N,) array-like
        Input x data.

    y : (N,) array-like
        Input x data.

    method : string, optional (default = "Nelder-Mead")
        Any of scipy's minimizing routines. Have a look at
        scipy.optimize.minimize. Shortened excerpt:

        "Nelder-Mead" uses the Simplex algorithm.

        "Powell" is a modification of Powell's method which is a conjugate
            direction method.

        "CG" uses a nonlinear conjugate gradient algorithm.

        "BFGS" uses the quasi-Newton method of Broyden, Fletcher, Goldfarb, and
            Shanno (BFGS).

        "Newton-CG" uses a Newton-CG algorithm (also known as the truncated
            Newton method).

        "Anneal" uses simulated annealing, which is a probabilistic
            metaheuristic algorithm for global optimization.

    measure : string, optional ({*"absolute"*, "relative"})
        Defines the measure to be optimized. Either absolute or relative
        errors. See doc of ``fit_generic()'' for more details

    show: boolean, optional (default = False)
        Visualize fit result.

    _verbose : boolean, optional (default = True)
        Print some information to stdout.

    **kwargs : Further arguments that will be directly passed to
        scipty.optimize.minimize()

    Returns
    -------
    opt_param : (Nparam,) array
        The optimized parameters.

    opt_fitfunc : function
        The readily-parametrized fit function

    res : OptimizeResult object
        The result as provided by scipy.optimize.minimize()
    """
    x = np.asarray(x)
    y = np.asarray(y)

    def _fitfunc(x, A):
        return A*x**2

    p0 = kwargs.pop('p0', np.zeros(1))

    opt_p, opt_fitfunc, res = fit_generic(x, y, _fitfunc, p0, **kwargs)

    res['R^2adj'] = calc_adjusted_Rsquare(times=x,
                                          signal=y,
                                          fitfunc=opt_fitfunc,
                                          Nparam=1)
    return opt_p, opt_fitfunc, res


def fit_shifted_parabola(x,y, **kwargs):
    """
    Fit to

        y = p[0]*(x-p[3])**2 + p[1]*(x-p[4]) + p[2]

    Parameters
    ----------
    x : (N,) array-like
        Input x data.

    y : (N,) array-like
        Input x data.

    method : string, optional (default = "Nelder-Mead")
        Any of scipy's minimizing routines. Have a look at
        scipy.optimize.minimize. Shortened excerpt:

        "Nelder-Mead" uses the Simplex algorithm.

        "Powell" is a modification of Powell's method which is a conjugate
            direction method.

        "CG" uses a nonlinear conjugate gradient algorithm.

        "BFGS" uses the quasi-Newton method of Broyden, Fletcher, Goldfarb, and
            Shanno (BFGS).

        "Newton-CG" uses a Newton-CG algorithm (also known as the truncated
            Newton method).

        "Anneal" uses simulated annealing, which is a probabilistic
            metaheuristic algorithm for global optimization.

    measure : string, optional ({*"absolute"*, "relative"})
        Defines the measure to be optimized. Either absolute or relative
        errors. See doc of ``fit_generic()'' for more details

    show: boolean, optional (default = False)
        Visualize fit result.

    _verbose : boolean, optional (default = True)
        Print some information to stdout.

    **kwargs : Further arguments that will be directly passed to
        scipty.optimize.minimize()

    Returns
    -------
    opt_param : (Nparam,) array
        The optimized parameters.

    opt_fitfunc : function
        The readily-parametrized fit function

    res : OptimizeResult object
        The result as provided by scipy.optimize.minimize()
    """
    x = np.asarray(x)
    y = np.asarray(y)

    def _fitfunc(x, A, B, C, D):
        return A*(x-D)**2 + B*(x-D) + C

    p0 = kwargs.pop('p0', np.zeros(4))

    opt_p, opt_fitfunc, res = fit_generic(x, y, _fitfunc, p0, **kwargs)

    res['R^2adj'] = calc_adjusted_Rsquare(times=x,
                                          signal=y,
                                          fitfunc=opt_fitfunc,
                                          Nparam=5)
    return opt_p, opt_fitfunc, res


def calc_Rsquare(times, signal, fitfunc):
    """
    Evaluate the cofficient of determination

    Parameters
    ----------
    times : (N,) array
        The x-values (input of the fit)

    signal : (N,) array
        The y values (input of the fit)

    fitfunc : callable
        The fitted function
    """
    # residual sum of squares
    SSres = np.sum((signal - fitfunc(times))**2)

    # total sum of squares
    SStot = np.sum((signal - np.mean(signal))**2)

    # coefficient of determination
    Rsquare = 1. - (SSres/SStot)

    return Rsquare


def calc_adjusted_Rsquare(times, signal, fitfunc, Nparam):
    """
    Evaluate the adjusted cofficient of determination

    Parameters
    ----------
    times : (N,) array
        The x-values (input of the fit)

    signal : (N,) array
        The y values (input of the fit)

    fitfunc : callable
        The fitted function

    Nparam : int
        The number of parameters in the model.
    """

    # residual sum of squares
    SSres = np.sum((signal - fitfunc(times))**2)

    # total sum of squares
    SStot = np.sum((signal - np.mean(signal))**2)
    Npoints = float(len(times))

    Rsquare_adjusted = 1. - ((SSres / (Npoints-Nparam)) / (SStot / (Npoints-1)))

    return Rsquare_adjusted
