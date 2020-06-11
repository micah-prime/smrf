import logging
import warnings

import numpy as np
from scipy.integrate import quad, IntegrationWarning
from scipy.interpolate import Akima1DInterpolator

from smrf.envphys import sunang

SOLAR_CONSTANT = 1368.0  # solar constant in W/m**2


def solar(d, w=[0.28, 2.8]):
    """
    Solar calculates exoatmospheric direct solar irradiance.  If two arguments
    to -w are given, the integral of solar irradiance over the range will be
    calculated.  If one argument is given, the spectral irradiance will be
    calculated.

    If no wavelengths are specified on the command line, single wavelengths in
    um will be read from the standard input and the spectral irradiance
    calculated for each.

    Args:
        w - [um um2] If  two  arguments  are  given, the integral of solar
            irradiance in the range um to um2 will be calculated.  If one
            argument is given, the spectral irradiance will be calculated.
        d - date object, This is used to calculate the solar radius vector
            which divides the result

    Returns:
        s - direct solar irradiance
    """

    if len(w) != 2:
        raise ValueError('length of w must be 2')

    # Adjust date time for solar noon
    d = d.replace(hour=12, minute=0, second=0)

    # Calculate the ephemeris parameters
    declination, omega, rad_vec = sunang.ephemeris(d)

    # integral over a wavelength range
    s = solint(w[0], w[1]) / rad_vec ** 2

    return s


def solint(a, b):
    """
    integral of solar constant from wavelengths a to b in micometers

    This uses scipy functions which will produce different results
    from the IPW equvialents of 'akcoef' and 'splint'
    """

    # Solar data
    data = solar_data()

    wave = data[:, 0]
    val = data[:, 1]

    # calculate splines
    c = Akima1DInterpolator(wave, val)

    with warnings.catch_warnings(record=True) as messages:
        warnings.simplefilter('always', category=IntegrationWarning)
        # Take the integral between the two wavelengths
        intgrl, ierror = quad(c, a, b, limit=120)

        log = logging.getLogger(__name__)
        for warning in messages:
            log.warning(warning.message)

    return intgrl * SOLAR_CONSTANT


def solar_data():
    """
    Solar data from Thekaekara, NASA TR-R-351, 1979
    """

    return np.array([[0.00e+0, 0.0000000000000000e+0],
                     [1.20e-1, 7.2064702602003287e-5],
                     [1.40e-1, 2.1619410780600986e-5],
                     [1.50e-1, 5.0445291821402301e-5],
                     [1.60e-1, 1.6574881598460755e-4],
                     [1.70e-1, 4.5400762639262068e-4],
                     [1.80e-1, 9.0080878252504105e-4],
                     [1.90e-1, 1.9529534405142891e-3],
                     [2.00e-1, 7.7109231784143517e-3],
                     [2.10e-1, 1.6502816895858752e-2],
                     [2.20e-1, 4.1437203996151890e-2],
                     [2.25e-1, 4.6769991988700132e-2],
                     [2.30e-1, 4.8067156635536191e-2],
                     [2.35e-1, 4.2734368642987949e-2],
                     [2.40e-1, 4.5400762639262071e-2],
                     [2.45e-1, 5.2102779981248376e-2],
                     [2.50e-1, 5.0733550631810313e-2],
                     [2.55e-1, 7.4947290706083422e-2],
                     [2.60e-1, 9.3684113382604272e-2],
                     [2.65e-1, 1.3331969981370607e-1],
                     [2.70e-1, 1.6719011003664763e-1],
                     [2.75e-1, 1.4701199330808671e-1],
                     [2.80e-1, 1.5998363977644729e-1],
                     [2.85e-1, 2.2700381319631035e-1],
                     [2.90e-1, 3.4735186654165584e-1],
                     [2.95e-1, 4.2085786319569921e-1],
                     [3.00e-1, 3.7041257137429690e-1],
                     [3.05e-1, 4.3455015669007980e-1],
                     [3.10e-1, 4.9652580092780263e-1],
                     [3.15e-1, 5.5057432787930508e-1],
                     [3.20e-1, 5.9813703159662727e-1],
                     [3.25e-1, 7.0263085036953205e-1],
                     [3.30e-1, 7.6316520055521482e-1],
                     [3.35e-1, 7.7901943512765555e-1],
                     [3.40e-1, 7.7397490594551530e-1],
                     [3.45e-1, 7.7037167081541515e-1],
                     [3.50e-1, 7.8766719943989590e-1],
                     [3.55e-1, 7.8046072917969557e-1],
                     [3.60e-1, 7.6965102378939508e-1],
                     [3.65e-1, 8.1577243345467720e-1],
                     [3.70e-1, 8.5108413772965880e-1],
                     [3.75e-1, 8.3378860910517805e-1],
                     [3.80e-1, 8.0712466914243679e-1],
                     [3.85e-1, 7.9127043456999609e-1],
                     [3.90e-1, 7.9127043456999609e-1],
                     [3.95e-1, 8.5684931393781909e-1],
                     [4.00e-1, 1.0298046001826270e+0],
                     [4.05e-1, 1.1847437107769340e+0],
                     [4.10e-1, 1.2618529425610776e+0],
                     [4.15e-1, 1.2784278241595383e+0],
                     [4.20e-1, 1.2589703544569974e+0],
                     [4.25e-1, 1.2200554150519156e+0],
                     [4.30e-1, 1.1811404756468339e+0],
                     [4.35e-1, 1.1984360042713147e+0],
                     [4.40e-1, 1.3043711170962595e+0],
                     [4.45e-1, 1.3850835840105032e+0],
                     [4.50e-1, 1.4456179341961859e+0],
                     [4.55e-1, 1.4823709325232076e+0],
                     [4.60e-1, 1.4888567557573879e+0],
                     [4.65e-1, 1.4758851092890273e+0],
                     [4.70e-1, 1.4650754038987267e+0],
                     [4.75e-1, 1.4730025211849472e+0],
                     [4.80e-1, 1.4946219319655481e+0],
                     [4.85e-1, 1.4239985234155849e+0],
                     [4.90e-1, 1.4052617007390641e+0],
                     [4.95e-1, 1.4124681709992644e+0],
                     [5.00e-1, 1.3994965245309039e+0],
                     [5.05e-1, 1.3836422899584631e+0],
                     [5.10e-1, 1.3562577029697018e+0],
                     [5.15e-1, 1.3209459986947202e+0],
                     [5.20e-1, 1.3209459986947202e+0],
                     [5.25e-1, 1.3346382921891008e+0],
                     [5.30e-1, 1.3274318219289006e+0],
                     [5.35e-1, 1.3101362933044197e+0],
                     [5.40e-1, 1.2849136473937186e+0],
                     [5.45e-1, 1.2640148836391377e+0],
                     [5.50e-1, 1.2431161198845568e+0],
                     [5.55e-1, 1.2395128847544565e+0],
                     [5.60e-1, 1.2214967091039557e+0],
                     [5.65e-1, 1.2287031793641560e+0],
                     [5.70e-1, 1.2337477085462963e+0],
                     [5.75e-1, 1.2387922377284365e+0],
                     [5.80e-1, 1.2359096496243563e+0],
                     [5.85e-1, 1.2337477085462963e+0],
                     [5.90e-1, 1.2250999442340559e+0],
                     [5.95e-1, 1.2121282977656953e+0],
                     [6.00e-1, 1.2005979453493748e+0],
                     [6.05e-1, 1.1869056518549941e+0],
                     [6.10e-1, 1.1782578875427537e+0],
                     [6.20e-1, 1.1544765356840926e+0],
                     [6.30e-1, 1.1314158308514516e+0],
                     [6.40e-1, 1.1126790081749307e+0],
                     [6.50e-1, 1.0888976563162696e+0],
                     [6.60e-1, 1.0708814806657688e+0],
                     [6.70e-1, 1.0492620698851678e+0],
                     [6.80e-1, 1.0283633061305869e+0],
                     [6.90e-1, 1.0103471304800861e+0],
                     [7.00e-1, 9.8656577862142496e-1],
                     [7.10e-1, 9.6854960297092417e-1],
                     [7.20e-1, 9.4693019219032319e-1],
                     [7.30e-1, 9.2963466356584240e-1],
                     [7.40e-1, 9.0801525278524139e-1],
                     [7.50e-1, 8.8999907713474059e-1],
                     [8.00e-1, 7.9775625780417640e-1],
                     [8.50e-1, 7.1199926170779244e-1],
                     [9.00e-1, 6.4065520613180922e-1],
                     [9.50e-1, 6.0174026672672744e-1],
                     [1.00e+0, 5.3760268141094450e-1],
                     [1.10e+0, 4.2662303940385946e-1],
                     [1.20e+0, 3.4879316059369590e-1],
                     [1.30e+0, 2.8537622230393302e-1],
                     [1.40e+0, 2.4213740074273104e-1],
                     [1.50e+0, 2.0682569646774943e-1],
                     [1.60e+0, 1.7583787434888801e-1],
                     [1.70e+0, 1.4557069925604664e-1],
                     [1.80e+0, 1.1458287713718522e-1],
                     [1.90e+0, 9.0801525278524142e-2],
                     [2.00e+0, 7.4226643680063386e-2],
                     [2.10e+0, 6.4858232341802959e-2],
                     [2.20e+0, 5.6931115055582595e-2],
                     [2.30e+0, 4.9003997769362232e-2],
                     [2.40e+0, 4.6121409665282103e-2],
                     [2.50e+0, 3.8914939405081775e-2],
                     [2.60e+0, 3.4591057248961578e-2],
                     [2.70e+0, 3.0987822118861412e-2],
                     [2.80e+0, 2.8105234014781281e-2],
                     [2.90e+0, 2.5222645910701150e-2],
                     [3.00e+0, 2.2340057806621019e-2],
                     [3.10e+0, 1.8736822676520856e-2],
                     [3.20e+0, 1.6286622788052742e-2],
                     [3.30e+0, 1.3836422899584630e-2],
                     [3.40e+0, 1.1962740631932545e-2],
                     [3.50e+0, 1.0521446579892480e-2],
                     [3.60e+0, 9.7287348512704438e-3],
                     [3.70e+0, 8.8639584200464042e-3],
                     [3.80e+0, 7.9991819888223649e-3],
                     [3.90e+0, 7.4226643680063384e-3],
                     [4.00e+0, 6.8461467471903120e-3],
                     [4.10e+0, 6.2696291263742857e-3],
                     [4.20e+0, 5.6210468029562563e-3],
                     [4.30e+0, 5.1165938847422333e-3],
                     [4.40e+0, 4.6842056691302139e-3],
                     [4.50e+0, 4.2518174535181938e-3],
                     [4.60e+0, 3.8194292379061740e-3],
                     [4.70e+0, 3.4591057248961576e-3],
                     [4.80e+0, 3.2429116170901479e-3],
                     [4.90e+0, 2.9546528066821346e-3],
                     [5.00e+0, 2.7600781096567258e-3],
                     [6.00e+0, 1.2611322955350576e-3],
                     [7.00e+0, 7.1344055575983254e-4],
                     [8.00e+0, 4.3238821561201970e-4],
                     [9.00e+0, 2.7384586988761247e-4],
                     [1.00e+1, 1.8016175650500822e-4],
                     [1.10e+1, 1.2250999442340559e-4],
                     [1.20e+1, 8.6477643122403945e-5],
                     [1.30e+1, 6.2696291263742856e-5],
                     [1.40e+1, 3.9635586431101808e-5],
                     [1.50e+1, 3.5311704274981611e-5],
                     [1.60e+1, 2.7384586988761248e-5],
                     [1.70e+1, 2.2340057806621018e-5],
                     [1.80e+1, 1.7295528624480788e-5],
                     [1.90e+1, 1.4412940520400656e-5],
                     [2.00e+1, 1.1530352416320527e-5],
                     [2.50e+1, 4.3959468587222005e-6],
                     [3.00e+1, 2.1619410780600985e-6],
                     [3.50e+1, 1.1530352416320526e-6],
                     [4.00e+1, 6.7740820445883089e-7],
                     [5.00e+1, 2.7384586988761249e-7],
                     [6.00e+1, 1.3692293494380625e-7],
                     [8.00e+1, 5.0445291821402299e-8],
                     [1.00e+2, 2.1619410780600986e-8],
                     [1.00e+3, 0.0000000000000000e+0]])
