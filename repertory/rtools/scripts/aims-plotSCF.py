#!/usr/bin/python2
from sys import argv
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

with open(argv[1], 'r') as f:
    aims_output = f.readlines()

its = []
rho = []
eev = []
eto = []
mom = []
sc_init_iter = 0
spin = 1

for line in aims_output:
    if 'Present geometry is not yet converged.' in line:
        # Simply reboot since this is a geometry optimization
        its = []
        rho = []
        eev = []
        eto = []
        mom = []
        sc_init_iter = 0

    if '| Number of spin channels           :' in line:
        spin = float(line.split()[6])

    if '  sc_init_iter' in line:
        sc_init_iter = int(line.split()[1])

    if 'iterations before' in line:
        sc_init_iter = int(line.split()[1])

    if 'Begin self-consistency iteration #' in line:
        its.append(int(line.split()[4]))

        # just in case we used sc_init_iter
        if sc_init_iter and len(its) >= 2:
            if its[-1] < its[-2]:
                its[-1] += sc_init_iter

    if '| <rho_up-rho_dn> = N_up-N_dn' in line:
        mom.append((float(line.split()[5][:-1]), float(line.split()[8])))

    if spin == 2:
        if '| Change of charge/spin density :' in line:
            rho.append((float(line.split()[6]), float(line.split()[7])))
    else:
        if 'Change of charge density' in line:
            rho.append(float(line.split()[6]))

    if '| Change of sum of eigenvalues  :' in line:
        eev.append(float(line.split()[7]))

    if '| Change of total energy        :' in line:
        eto.append(float(line.split()[6]))

# if wished so, do not show sc_init_iter
try:
    sc_init_iter = int(argv[2])
except:
    pass

# resize all arrays in case of non-finished calculations
if spin == 2:
    len_of_all = (len(its), len(rho), len(mom), len(eev), len(eto))
else:
    len_of_all = (len(its), len(rho), len(eev), len(eto))
its = its[0:min(len_of_all)]
rho = rho[0:min(len_of_all)]
mom = mom[0:min(len_of_all)]
eev = eev[0:min(len_of_all)]
eto = eto[0:min(len_of_all)]

fig = plt.figure(figsize=(16, 9))
ax1 = plt.subplot(2, 2, 1)
if spin == 2:
    plt.plot(its, [i for i in zip(*rho)[0]], label='charge dens')
    plt.plot(its, [i for i in zip(*rho)[1]], label='spin dens')
else:
    plt.plot(its, [i for i in rho], label='charge dens')
try:
    # spin collinear
    flat_rho = [item for sublist in rho for item in sublist]
except:
    # spin none
    flat_rho = rho
minrho = min(flat_rho) * 0.05
minrho = min(flat_rho[-10:]) * 0.01
#maxrho = (((sum(flat_rho)) / len(flat_rho))) * 10
maxrho = minrho * 1e4
plt.ylim(minrho, maxrho)
plt.legend(frameon=False, prop={'size': 11})
plt.axhline(y=0, linewidth=.2, color='r', linestyle=':')
if sc_init_iter > 0:
    plt.axvline(x=sc_init_iter, ymin=-0.2, ymax=1.0, linewidth=2, color='r')
    plt.text(sc_init_iter + 2, ax1.get_ylim()[0] * 0.99, ' sc_init_iter',
             va='bottom', rotation=90, color='r', fontsize=9,
             bbox=dict(facecolor='w', edgecolor='none', pad=0.1))
ax1.set_yscale('symlog')
ax1.yaxis.set_major_locator(ticker.AutoLocator())
#ax1.yaxis.set_minor_locator(ticker.LogLocator(numdecs=2))
ax2 = plt.subplot(2, 2, 2)
try:
    # spin collinear
    flat_eev = [item for sublist in eev for item in sublist]
except:
    # spin none
    flat_eev = eev
maxeev = max(eev[-10:]) * 1e3
mineev = -maxeev
plt.ylim(mineev, maxeev)
plt.plot(its, [i for i in eev], label='eev')
plt.legend(frameon=False, prop={'size': 11})
#plt.ylim(-100.0, 100.0)
plt.axhline(y=0, linewidth=.2, color='r', linestyle=':')
if sc_init_iter > 0:
    plt.axvline(x=sc_init_iter, ymin=-0.2, ymax=1.0, linewidth=2, color='r')
    plt.text(sc_init_iter + 2, ax2.get_ylim()[0] * 0.99, ' sc_init_iter',
             va='bottom', rotation=90, color='r', fontsize=9,
             bbox=dict(facecolor='w', edgecolor='none', pad=0.1))

ax2.set_yscale('symlog')
ax2.yaxis.set_major_locator(ticker.AutoLocator())
#ax2.yaxis.set_minor_locator(ticker.LogLocator(numdecs=0))

ax3 = plt.subplot(2, 2, 3)
try:
    # spin collinear
    flat_eto = [item for sublist in eto for item in sublist]
except:
    # spin none
    flat_eto = eto
maxeto = max(eto[-10:]) * 1e3
#maxrho = (((sum(flat_rho)) / len(flat_rho))) * 10
mineto = -maxeto
plt.ylim(mineto, maxeto)
plt.plot(its, [i for i in eto], label='eto')
plt.legend(frameon=False, prop={'size': 11})
#plt.ylim(-5.0, 5.0)
plt.axhline(y=0, linewidth=.2, color='r', linestyle=':')
if sc_init_iter > 0:
    plt.axvline(x=sc_init_iter, ymin=-0.2, ymax=1.0, linewidth=2, color='r')
    plt.text(sc_init_iter + 2, ax3.get_ylim()[0] * 0.99, ' sc_init_iter',
             va='bottom', rotation=90, color='r', fontsize=9,
             bbox=dict(facecolor='w', edgecolor='none', pad=0.1))

ax3.set_yscale('symlog')
ax3.yaxis.set_major_locator(ticker.AutoLocator())
#ax2.yaxis.set_minor_locator(ticker.LogLocator(numdecs=0))
if spin == 2:
    ax4 = plt.subplot(2, 2, 4)
    plt.plot(its, zip(*mom)[0], label='mom_tot')
    plt.plot(its, zip(*mom)[1], label='mom_abs')

plt.legend(frameon=False, prop={'size': 11})
plt.axhline(y=0, linewidth=.2, color='r', linestyle=':')
if sc_init_iter > 0:
    plt.axvline(x=sc_init_iter, ymin=-0.2, ymax=1.0, linewidth=2, color='r')
    plt.text(sc_init_iter + 2, ax3.get_ylim()[0] * 0.99, ' sc_init_iter',
             va='bottom', rotation=90, color='r', fontsize=9,
             bbox=dict(facecolor='w', edgecolor='none', pad=0.1))

plt.suptitle('development of convergence criteria in aims-run', fontsize=16)
plt.tight_layout()
fig.subplots_adjust(top=0.92)
plt.show(block=True)
