fig = plt.figure()
plt.rcParams['figure.figsize'] = [5, 5]
plt.rcParams.update({'font.size': 14})
plt.rcParams.update({'figure.autolayout': True})
plt.rcParams['font.family'] = 'serif'
ax = fig.add_subplot(111)
ax.plot(np.log10(surface[:, 0]), surface[:, 1], 's', color='crimson', ls='--', label='train')
ax.plot(np.log10(surface[:, 0]), surface[:, 2], 'v', color='cornflowerblue', ls=':', label='validation')
# ax.axhline(surface[s][-1]+surface[s][-1]*0.05, ls=':', color='k')
if sigma_elected is not None:
    ax.axvline(np.log10(sigma_elected), ls='-.', color='k', label=r'$\sigma$')
else:
    ax.axvline(np.log10(surface[s, 0]), ls=':', color='k')
ax.set_xlabel(r'log($\sigma$)')
ax.set_ylabel(r'RMSE {} [eV]'.format(label_name))
# ax.set_ylim((0, 0.03))
ax.legend()
plt.savefig('{}_cv_hypersurface.png'.format(save_fig))   
