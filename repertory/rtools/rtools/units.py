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

from math import pi, sqrt

#
# NOTE: THIS MODULE IS TAKEN FROM MDsim 3.4.4
#       parts of this module made it to ASE as well
#

# the version we actually use
__codata_version__ = '2014'

# this is the hard-coded CODATA values
# all other units are dynamically derived from these values upon import of the
# module
CODATA = {
    # the "original" CODATA version ase used ever since
    # Constants from Konrad Hinsen's PhysicalQuantities module (1986 CODATA)
    # Add the constant pi used to define the mu0 and hbar here for reference
    # as well
    '1986': {'_c': 299792458.,              # speed of light, m/s
             '_mu0': 4.e-7 * pi,            # permeability of vacuum
             '_Grav': 6.67259e-11,          # gravitational constant
             '_hplanck': 6.6260755e-34,     # Planck constant, J s
             '_e': 1.60217733e-19,          # elementary charge
             '_me': 9.1093897e-31,          # electron mass
             '_mp': 1.6726231e-27,          # proton mass
             '_Nav': 6.0221367e23,          # Avogadro number
             '_k': 1.380658e-23,            # Boltzmann constant, J/K
             '_amu': 1.6605402e-27},         # atomic mass unit, kg

    # CODATA 1998 taken from
    # http://dx.doi.org/10.1103/RevModPhys.72.351
    '1998': {'_c': 299792458.,
             '_mu0': 4.0e-7 * pi,
             '_Grav': 6.673e-11,
             '_hplanck': 6.62606876e-34,
             '_e': 1.602176462e-19,
             '_me': 9.10938188e-31,
             '_mp': 1.67262158e-27,
             '_Nav': 6.02214199e23,
             '_k': 1.3806503e-23,
             '_amu': 1.66053873e-27},

    # CODATA 2002 taken from
    # http://dx.doi.org/10.1103/RevModPhys.77.1
    '2002': {'_c': 299792458.,
             '_mu0': 4.0e-7 * pi,
             '_Grav': 6.6742e-11,
             '_hplanck': 6.6260693e-34,
             '_e': 1.60217653e-19,
             '_me': 9.1093826e-31,
             '_mp': 1.67262171e-27,
             '_Nav': 6.0221415e23,
             '_k': 1.3806505e-23,
             '_amu': 1.66053886e-27},

    # CODATA 2006 taken from
    # http://dx.doi.org/10.1103/RevModPhys.80.633
    '2006': {'_c': 299792458.,
             '_mu0': 4.0e-7 * pi,
             '_Grav': 6.67428e-11,
             '_hplanck': 6.62606896e-34,
             '_e': 1.602176487e-19,
             '_me': 9.10938215e-31,
             '_mp': 1.672621637e-27,
             '_Nav': 6.02214179e23,
             '_k': 1.3806504e-23,
             '_amu': 1.660538782e-27},

    # CODATA 2010 taken from
    # http://dx.doi.org/10.1103/RevModPhys.84.1527
    '2010': {'_c': 299792458.,
             '_mu0': 4.0e-7 * pi,
             '_Grav': 6.67384e-11,
             '_hplanck': 6.62606957e-34,
             '_e': 1.602176565e-19,
             '_me': 9.10938291e-31,
             '_mp': 1.672621777e-27,
             '_Nav': 6.02214129e23,
             '_k': 1.3806488e-23,
             '_amu': 1.660538921e-27},

    # CODATA 2014 taken from
    # http://arxiv.org/pdf/1507.07956.pdf
    '2014': {'_c': 299792458.,
             '_mu0': 4.0e-7 * pi,
             '_Grav': 6.67408e-11,
             '_hplanck': 6.626070040e-34,
             '_e': 1.6021766208e-19,
             '_me': 9.10938356e-31,
             '_mp': 1.672621898e-27,
             '_Nav': 6.022140857e23,
             '_k': 1.38064852e-23,
             '_amu': 1.660539040e-27}}

def create_units(codata_version):
    """
    Function that creates a dictionary containing all units previously hard
    coded in ase.units depending on a certain CODATA version. Note that you can
    use the dictionary returned to update your local or global namespace.

    Parameters:

    codata_version: str
        The CODATA version to be used. Implemented are

        * '1986'
        * '1998'
        * '2002'
        * '2006'
        * '2010'
        * '2014'

    Returns:

    units: dict
        Dictionary that contains all formerly hard coded variables from
        ase.units as key-value pairs.

    Raises:

    NotImplementedError
        If the required CODATA version is not known.
    """

    try:
        u = dict(CODATA[codata_version])
    except KeyError:
        raise NotImplementedError('CODATA version "{0}" not implemented'
                                  .format(__codata_version__))

    u['_yotta'] = 1e24
    u['_zetta'] = 1e21
    u['_exa']   = 1e18
    u['_peta']  = 1e15
    u['_tera']  = 1e12
    u['_giga']  = 1e9
    u['_mega']  = 1e6
    u['_kilo']  = 1e3
    u['_hecto'] = 1e2
    u['_deca']  = 1e1
    u['_deci']  = 1e-1
    u['_centi'] = 1e-2
    u['_milli'] = 1e-3
    u['_micro'] = 1e-6
    u['_nano'] = 1e-9
    u['_pico'] = 1e-12
    u['_femto'] = 1e-15
    u['_atto'] = 1e-18
    u['_zepto'] = 1e-21
    u['_yocto'] = 1e-24

    # derived from the CODATA values
    u['_eps0'] = (1 / u['_mu0'] / u['_c']**2)  # permittivity of vacuum
    u['_hbar'] = u['_hplanck'] / (2 * pi)  # Planck constant / 2pi, J s

    # derived units we need to convert to atomic units
    u['_a0'] = 4.*pi *u['_eps0'] * u['_hbar']**2 / (u['_me'] * u['_e']**2)
    u['_hartree'] = u['_hbar']**2 / (u['_me'] * u['_a0']**2)

    # fine structure constant
    u['_alpha'] = u['_e']**2 / (4. * pi * u['_eps0'] * u['_hbar'] * u['_c'])

    # useful values in SI units
    u['_eV'] = u['_e'] # J
    u['_angstrom'] = 1e-10 # m
    u['_fs'] = u['_femto'] # s
    u['_debye'] = 3.33564e-30 # C * m
    u['_calorie'] = 4.1868 # J
    u['_dyn'] = 1e-5 # N

    # atomic units in SI, see:
    # https://en.wikipedia.org/wiki/Atomic_units
    u['_au_length'] = u['_a0'] # m
    u['_au_energy'] = u['_hartree'] # J
    u['_au_time'] = u['_hbar'] / u['_hartree'] # s
    u['_au_velocity'] = u['_a0'] * u['_hartree'] / u['_hbar'] # m/s
    u['_au_force'] = u['_hartree'] / u['_a0'] # N
    u['_au_mass'] = u['_me'] # kg
    u['_au_temperature'] = u['_hartree'] / u['_k'] # K
    u['_au_pressure'] = u['_hartree'] / (u['_a0']**3) # Pa
    u['_au_efield'] = u['_hartree'] / (u['_e']*u['_a0']) # V/m
    u['_au_edipole'] = u['_e'] * u['_a0'] # C m
    u['_au_bfield'] = u['_hbar'] / (u['_e'] * u['_a0']**2) # T
    u['_au_bdipole'] = u['_e'] * u['_hbar'] / (2. * u['_me'])


    # here come the conversions
    # explicit naming
    c = {}
    u['BDIPOLE_AU_TO_SI'] = u['_au_bdipole']
    u['BFIELD_AU_TO_SI'] = u['_au_bfield']
    u['EDIPOLE_AU_TO_SI'] = u['_au_edipole']
    u['EFIELD_AU_TO_SI'] = u['_au_efield']
    u['ENERGY_AU_TO_SI'] = u['_au_energy']
    u['FORCE_AU_TO_SI'] = u['_au_force']
    u['LENGTH_AU_TO_SI'] = u['_au_length']
    u['MASS_AU_TO_SI'] = u['_au_mass']
    u['MOMENTUM_AU_TO_SI'] = u['_au_mass'] * u['_au_velocity']
    u['PRESSURE_AU_TO_SI'] = u['_au_pressure']
    u['TEMPERATURE_AU_TO_SI'] = u['_au_temperature']
    u['TIME_AU_TO_SI'] = u['_au_time']
    u['VELOCITY_AU_TO_SI'] = u['_au_velocity']
    u['FREQUENCY_AU_TO_SI'] = 1./u['_au_time']

    u['BDIPOLE_SI_TO_AU'] = 1./ u['_au_bdipole']
    u['BFIELD_SI_TO_AU'] = 1./ u['_au_bfield']
    u['EDIPOLE_SI_TO_AU'] = 1./ u['_au_edipole']
    u['EFIELD_SI_TO_AU'] = 1./ u['_au_efield']
    u['ENERGY_SI_TO_AU'] = 1./ u['_au_energy']
    u['FORCE_SI_TO_AU'] = 1./ u['_au_force']
    u['LENGTH_SI_TO_AU'] = 1./ u['_au_length']
    u['MASS_SI_TO_AU'] = 1./ u['_au_mass']
    u['MOMENTUM_SI_TO_AU'] = 1./ (u['_au_mass'] * u['_au_velocity'])
    u['PRESSURE_SI_TO_AU'] = 1./ u['_au_pressure']
    u['TEMPERATURE_SI_TO_AU'] = 1./ u['_au_temperature']
    u['TIME_SI_TO_AU'] = 1./ u['_au_time']
    u['VELOCITY_SI_TO_AU'] = 1./ u['_au_velocity']
    u['FREQUENCY_SI_TO_AU'] = 1./u['FREQUENCY_AU_TO_SI']

    # chemical/physical units used in MDsim
    # some are redundant, but they're here for convenience
    u['EV_TO_SI'] = u['_eV']
    u['EV_TO_SI'] = u['_eV']
    u['FS_TO_SI'] = u['_fs']
    u['ANGSTROM_TO_SI'] = u['_angstrom']
    u['AMU_TO_SI'] = u['_amu']
    u['DEBYE_TO_SI'] = u['_debye']
    # derived conversions
    u['AMU_PER_FS_TO_SI'] = u['AMU_TO_SI'] / u['FS_TO_SI']
    u['ANGSTROM_AMU_PER_FS_TO_SI'] = u['ANGSTROM_TO_SI'] * u['AMU_TO_SI'] / u['FS_TO_SI']
    u['ANGSTROM_PER_FS_TO_SI'] = u['ANGSTROM_TO_SI'] / u['FS_TO_SI']
    u['DEBYE_TO_SI'] = u['_debye']
    u['EV_FS_PER_AMU_TO_SI'] = u['EV_TO_SI'] * u['FS_TO_SI'] / u['AMU_TO_SI']
    u['EV_PER_ANGSTROM_SQUARED_TO_SI'] = u['EV_TO_SI'] / (u['ANGSTROM_TO_SI']**2)
    u['EV_PER_ANGSTROM_TO_SI'] = u['EV_TO_SI'] / u['ANGSTROM_TO_SI']
    u['EV_PER_FS_TO_SI'] = u['EV_TO_SI'] / u['FS_TO_SI']
    # normalmodes
    u['ANGSTROM_SQRT_AMU_TO_SI'] = u['ANGSTROM_TO_SI'] * sqrt(u['AMU_TO_SI'])

    u['KAYSER_TO_SI'] = u['_c'] / u['_centi']
    u['THZ_TO_SI'] = u['_tera']

    # conversion to AU
    u['AMU_TO_AU'] = u['AMU_TO_SI'] * u['MASS_SI_TO_AU']
    u['FS_TO_AU'] = u['FS_TO_SI'] * u['TIME_SI_TO_AU']
    u['EV_TO_AU'] = u['EV_TO_SI'] * u['ENERGY_SI_TO_AU']
    u['MEV_TO_AU'] = u['_milli']*u['EV_TO_AU']
    u['ANGSTROM_TO_AU'] = u['ANGSTROM_TO_SI'] * u['LENGTH_SI_TO_AU']

    u['AMU_PER_FS_TO_AU'] = u['AMU_TO_AU'] / u['FS_TO_AU']
    u['ANGSTROM_AMU_PER_FS_TO_AU'] = u['ANGSTROM_TO_AU'] * u['AMU_TO_AU'] / u['FS_TO_AU']
    u['ANGSTROM_PER_FS_TO_AU'] = u['ANGSTROM_TO_AU'] / u['FS_TO_AU']
    u['DEBYE_TO_AU'] = u['DEBYE_TO_SI'] * u['EDIPOLE_SI_TO_AU']
    u['EV_FS_PER_AMU_TO_AU'] = u['EV_TO_AU'] * u['FS_TO_AU'] / u['AMU_TO_AU']
    u['EV_PER_ANGSTROM_SQUARED_TO_AU'] = u['EV_TO_AU'] / (u['ANGSTROM_TO_AU']**2)
    u['EV_PER_ANGSTROM_TO_AU'] = u['EV_TO_AU'] / u['ANGSTROM_TO_AU']
    u['EV_PER_FS_TO_AU'] = u['EV_TO_AU'] / u['FS_TO_AU']
    u['KELVIN_TO_AU'] = u['TEMPERATURE_SI_TO_AU']

    u['KAYSER_TO_AU'] = u['KAYSER_TO_SI'] * u['_hplanck'] * u['ENERGY_SI_TO_AU']
    u['THZ_TO_AU'] = u['THZ_TO_SI']*u['FREQUENCY_SI_TO_AU']

    # normalmodes
    u['ANGSTROM_SQRT_AMU_TO_AU'] = u['ANGSTROM_TO_AU'] * sqrt(u['AMU_TO_AU'])
    u['ANGSTROM_SQRT_AMU_PER_FS_TO_AU'] = u['ANGSTROM_TO_AU'] * sqrt(u['AMU_TO_AU']) / u['FS_TO_AU']

    # conversion to MDsim basis units
    u['AU_TO_AMU'] = 1./u['AMU_TO_AU']
    u['AU_TO_AMU_PER_FS'] = 1./u['AMU_PER_FS_TO_AU']
    u['AU_TO_ANGSTROM'] = 1./u['ANGSTROM_TO_AU']
    u['AU_TO_ANGSTROM_AMU_PER_FS'] = 1./u['ANGSTROM_AMU_PER_FS_TO_AU']
    u['AU_TO_ANGSTROM_PER_FS'] = 1./u['ANGSTROM_PER_FS_TO_AU']
    u['AU_TO_DEBYE'] = 1./u['DEBYE_TO_AU']
    u['AU_TO_EV'] = 1./u['EV_TO_AU']
    u['AU_TO_MEV'] = 1./u['MEV_TO_AU']
    u['AU_TO_EV_FS_PER_AMU']= 1./u['EV_FS_PER_AMU_TO_AU']
    u['AU_TO_EV_PER_ANGSTROM'] = 1./u['EV_PER_ANGSTROM_TO_AU']
    u['AU_TO_EV_PER_ANGSTROM_SQUARED']= 1./u['EV_PER_ANGSTROM_SQUARED_TO_AU']
    u['AU_TO_EV_PER_FS']= 1./u['EV_PER_FS_TO_AU']
    u['AU_TO_FS'] = 1./u['FS_TO_AU']
    u['AU_TO_KELVIN'] = 1./u['KELVIN_TO_AU']
    u['AU_TO_THZ'] = 1./u['THZ_TO_AU']
    u['AU_TO_KAYSER'] = 1./u['KAYSER_TO_AU']
    u['AU_TO_ANGSTROM_SQRT_AMU'] = 1./ u['ANGSTROM_SQRT_AMU_TO_AU']
    u['AU_TO_ANGSTROM_SQRT_AMU_PER_FS'] = 1./ u['ANGSTROM_SQRT_AMU_PER_FS_TO_AU']

    # further conversions, feel free to extend
    u['KELVIN_TO_EV'] = u['TEMPERATURE_SI_TO_AU'] * u['AU_TO_EV']
    u['EV_TO_KELVIN'] = 1./u['KELVIN_TO_EV']

    u['KAYSER_TO_THZ'] = u['KAYSER_TO_SI'] / u['_tera']
    u['THZ_TO_KAYSER'] = 1./u['KAYSER_TO_THZ']

    u['KAYSER_TO_EV'] = u['KAYSER_TO_AU'] * u ['AU_TO_EV']
    u['EV_TO_KAYSER'] = 1./ u['KAYSER_TO_EV']

    u['EV_TO_KCAL_PER_MOLE'] = u['EV_TO_SI'] * u['_Nav'] / (u['_kilo'] * u['_calorie'])
    u['KCAL_PER_MOLE_TO_EV'] = 1./u['EV_TO_KCAL_PER_MOLE']


    # # ASE basis unit definition (Angstrom, AMU, eV are unity)
    u['_ase_second'] = 1e10 * sqrt(u['_e'] / u['_amu'])

    # conversions from the ASE unit system to SI
    u['ENERGY_ASE_TO_SI'] = u['EV_TO_SI']
    u['LENGTH_ASE_TO_SI'] = u['ANGSTROM_TO_SI']
    u['MASS_ASE_TO_SI'] = u['AMU_TO_SI']
    u['TEMPERATURE_ASE_TO_SI'] = 1.
    u['TIME_ASE_TO_SI'] = 1./u['_ase_second']
    # derived
    u['FORCE_ASE_TO_SI'] = u['ENERGY_AU_TO_SI'] / (u['LENGTH_ASE_TO_SI']**2)
    u['MOMENTUM_ASE_TO_SI'] = u['MASS_ASE_TO_SI'] * u['LENGTH_ASE_TO_SI'] / u['TIME_ASE_TO_SI']

    # inverse
    u['ENERGY_SI_TO_ASE'] = 1./u['ENERGY_ASE_TO_SI']
    u['FORCE_SI_TO_ASE'] = 1./u['FORCE_ASE_TO_SI']
    u['LENGTH_SI_TO_ASE'] = 1./u['LENGTH_ASE_TO_SI']
    u['MASS_SI_TO_ASE'] = 1./u['MASS_ASE_TO_SI']
    u['MOMENTUM_SI_TO_ASE'] = 1./u['MOMENTUM_ASE_TO_SI']
    u['TEMPERATURE_SI_TO_ASE'] = 1./u['MASS_ASE_TO_SI']
    u['TIME_SI_TO_ASE'] = 1./u['TIME_ASE_TO_SI']

    # ASE <-> AU
    u['ENERGY_AU_TO_ASE'] = u['ENERGY_AU_TO_SI'] * u['ENERGY_SI_TO_ASE']
    u['FORCE_AU_TO_ASE'] = u['FORCE_AU_TO_SI'] * u['FORCE_SI_TO_ASE']
    u['LENGTH_AU_TO_ASE'] = u['LENGTH_AU_TO_SI'] * u['LENGTH_SI_TO_ASE']
    u['MASS_AU_TO_ASE'] = u['MASS_AU_TO_SI'] * u['MASS_SI_TO_ASE']
    u['MOMENTUM_AU_TO_ASE'] = u['MOMENTUM_AU_TO_SI'] * u['MOMENTUM_SI_TO_ASE']
    u['TEMPERATURE_AU_TO_ASE'] = u['TEMPERATURE_AU_TO_SI'] * u['TEMPERATURE_SI_TO_ASE']
    u['TIME_AU_TO_ASE'] = u['TIME_AU_TO_SI'] * u['TIME_SI_TO_ASE']

    u['ENERGY_ASE_TO_AU'] = 1./u['ENERGY_AU_TO_ASE']
    u['FORCE_ASE_TO_AU'] = 1./u['FORCE_AU_TO_ASE']
    u['LENGTH_ASE_TO_AU'] = 1./u['LENGTH_AU_TO_ASE']
    u['MASS_ASE_TO_AU'] = 1./u['MASS_AU_TO_ASE']
    u['MOMENTUM_ASE_TO_AU'] = 1./u['MOMENTUM_AU_TO_ASE']
    u['TEMPERATURE_ASE_TO_AU'] = 1./u['TEMPERATURE_AU_TO_ASE']
    u['TIME_ASE_TO_AU'] = 1./u['TIME_AU_TO_ASE']

    # ASE <-> MDsim
    u['ASE_TO_FS'] = u['TIME_ASE_TO_SI'] / u['_femto']
    u['ASE_TO_EV'] = 1.
    u['ASE_TO_EV_PER_ANGSTROM'] = 1.
    u['ASE_TO_ANGSTROM'] = 1.
    u['ASE_TO_ANGSTROM_PER_FS'] = 1./u['ASE_TO_FS']
    u['ASE_TO_ANGSTROM_AMU_PER_FS'] = 1./u['ASE_TO_FS']
    u['ASE_TO_AMU'] = 1.
    u['ASE_TO_KELVIN'] = 1.

    u['FS_TO_ASE'] = 1./u['ASE_TO_FS']
    u['EV_TO_ASE'] = 1.
    u['EV_PER_ANGSTROM_TO_ASE'] = 1.
    u['ANGSTROM_TO_ASE'] = 1.
    u['ANGSTROM_PER_FS_TO_ASE'] = 1./u['FS_TO_ASE']
    u['ANGSTROM_AMU_PER_FS_TO_ASE'] = 1./ u['FS_TO_ASE']
    u['AMU_TO_ASE'] = 1.
    u['KELVIN_TO_ASE'] = 1.
    return u

globals().update(create_units(__codata_version__))
