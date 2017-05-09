__author__ = "Scott Havens"
__maintainer__ = "Scott Havens"
__email__ = "scott.havens@ars.usda.gov"
__date__ = "2016-01-07"
__version__ = "0.2.0"


import numpy as np
import logging, os
# import subprocess as sp
# from multiprocessing import Process
from smrf.distribute import image_data
from smrf.envphys import thermal_radiation
from smrf.envphys.core import envphys_c
# from smrf.utils import utils
# from smrf import ipw

import matplotlib.pyplot as plt

class th(image_data.image_data):
    """
    The :mod:`~smrf.distribute.thermal.th` class allows for variable specific distributions that 
    go beyond the base class
    
    Thermal radiation, or long-wave radiation, is calculated based on the clear sky radiation emitted by
    the atmosphere. Multiple methods for calculating thermal radition exist and SMRF has 4 options for
    estimating clear sky thermal radiation. Selecting one of the options below will change the equations
    used. The methods were chosen based on the study by Flerchinger et al (2009) who performed a model
    comparison using 21 AmeriFlux sites from North America and China.
    
    Marks1979
        The methods follow those developed by Marks and Dozier (1979) :cite:`Marks&Dozier:1979` 
        that calculates the effective clear sky atmospheric emissivity using the distributed air temperature, 
        distributed dew point temperature, and the elevation. The clear sky radiation is further adjusted for 
        topographic affects based on the percent of the sky visible at any given point.
        
    Dilley1998
        .. math::
            L_{clear} = 59.38 + 113.7 * \frac{T_a}{273.16}^6 + 96.96 \sqrt{w/25}
            
    Prata1996
        .. math::
            \epsilon_{clear} = 1 - (1 + w) exp(-1.2 + 3w)^(1/2)
            
    Angstrom1918
        .. math::
            \epsilon_{clear} = 0.83 - 0.18 * 10^{-0.067 e_a}
    
    The topographic correct clear sky thermal radiation is further adjusted for canopy and cloud affects.
    Cloud correction is based on the relationship in Garen and Marks (2005) :cite:`Garen&Marks:2005` 
    between the cloud factor and measured long wave radiation using measurement stations in the Boise 
    River Basin.  When no clouds are  present, or a cloud factor close to 1, there is little radiation 
    added.  When clouds are present, or a cloud factor close to 0, then the multipler would add long 
    wave radiation to account for the cloud cover.
    
    .. math::
        L_{cloud} = L_{clear} * (1.485 - 0.488 * cloud\_factor)
    
    The thermal radiation is further adjusted for canopy cover after the work of Link and Marks (1999)
    :cite:`Link&Marks:1999`. The correction is based on the vegetation's transmissivity, with the canopy
    temperature assumed to be the air temperature for vegetation greater than 2 meters.  The thermal
    radiation is adjusted by:
    
    .. math::
        L_{canopy} = \\tau_d * L_{cloud} + (1 - \\tau_d) \epsilon \sigma T_a^4
    
    where :math:`\\tau_d` is the optical transmissivity, :math:`L_{cloud}` is the cloud corrected thermal
    radiation, :math:`\epsilon` is the emissivity of the canopy (0.96), :math:`\sigma` is the Stephan-Boltzmann
    constant, and :math:`T_a` is the distributed air temperature. 
    
    Args:
        thermalConfig: The [thermal] section of the configuration file
    
    Attributes:
        config: configuration from [precip] section
        thermal: numpy array of the precipitation
        min: minimum value of thermal is -600 W/m^2
        max: maximum value of thermal is 600 W/m^2
        stations: stations to be used in alphabetical order
        output_variables: Dictionary of the variables held within class :mod:`!smrf.distribute.thermal.ta`
            that specifies the ``units`` and ``long_name`` for creating the NetCDF output file.
        variable: 'thermal'
        dem: numpy array for the DEM, from :py:attr:`smrf.data.loadTopo.topo.dem`
        veg_type: numpy array for the veg type, from :py:attr:`smrf.data.loadTopo.topo.veg_type`
        veg_height: numpy array for the veg height, from :py:attr:`smrf.data.loadTopo.topo.veg_height`
        veg_k: numpy array for the veg K, from :py:attr:`smrf.data.loadTopo.topo.veg_k`
        veg_tau: numpy array for the veg transmissivity, from :py:attr:`smrf.data.loadTopo.topo.veg_tau`
        sky_view: numpy array for the sky view factor, from :py:attr:`smrf.data.loadTopo.topo.sky_view`
    
    """
    
    variable = 'thermal'
    min = -600
    max = 600
    
    # these are variables that can be output
    output_variables = {'thermal':{
                                  'units': 'W/m^2',
                                  'long_name': 'thermal_radiation'
                                  }
                        }
    
    def __init__(self, thermalConfig):
        
        # extend the base class
        image_data.image_data.__init__(self, self.variable)
        self._logger = logging.getLogger(__name__)
        
#         self.config = thermalConfig
        self.getConfig(thermalConfig)
        
        nthreads = 1
        if 'nthreads' in self.config:
            nthreads = int(self.config['nthreads'])
        self.config['nthreads'] = nthreads     
                
        # determine the method
        method = 'Marks1979'
        if 'method' not in self.config:
            self.method = method
        elif self.config['method'] == 'Marks1979':
            self.method = method
        elif self.config['method'] == 'Dilley1998':
            self.method = 'Dilley1998'
        elif self.config['method'] == 'Prata1996':
            self.method = 'Prata1996'
        elif self.config['method'] == 'Angstrom1918':
            self.method = 'Angstrom1918'
        else:
            self._logger.error('Could not determine method specifies for thermal')
                
        # correct for cloud and veg
        self.config['correct_cloud'] = True
        if 'correct_cloud' in self.config:
            self.correct_cloud = self.config['correct_cloud']
            
        self.config['correct_veg'] = True
        if 'correct_veg' in self.config:
            self.correct_veg = self.config['correct_veg']
            
        self.config['correct_terrain'] = True
        if 'correct_terrain' in self.config:
            self.correct_terrain = self.config['correct_terrain']
                
                
        self._logger.debug('Created distribute.thermal')
        
        
    def initialize(self, topo, metadata):
        """
        Initialize the distribution, calls :mod:`smrf.distribute.image_data.image_data._initialize`
        for gridded distirbution. Sets the following from :mod:`smrf.data.loadTopo.topo`
        
        * :py:attr:`veg_height`
        * :py:attr:`veg_tau`
        * :py:attr:`veg_k`
        * :py:attr:`sky_view`
        * :py:attr:`dem`
        
        Args:
            topo: :mod:`smrf.data.loadTopo.topo` instance contain topographic data
                and infomation
            metadata: metadata Pandas dataframe containing the station metadata,
                from :mod:`smrf.data.loadData` or :mod:`smrf.data.loadGrid`   
            
        """

        self._logger.debug('Initializing distribute.thermal')
        if self.gridded:
            self._initialize(topo, metadata)
                
        self.veg_height = topo.veg_height
        self.veg_tau = topo.veg_tau
        self.veg_k = topo.veg_k
        self.sky_view = topo.sky_view
        if not self.correct_terrain:
            self.sky_view = None
        self.dem = topo.dem


    def distribute(self, date_time, air_temp, vapor_pressure=None, dew_point=None, cloud_factor=None):
        """
        Distribute for a single time step. 
        
        The following steps are taken when distributing thermal:
        
        1. Calculate the clear sky thermal radiation from :mod:`smrf.envphys.core.envphys_c.ctopotherm`
        2. Correct the clear sky thermal for the distributed cloud factor
        3. Correct for canopy affects
        
        Args:
            date_time: datetime object for the current step
            air_temp: distributed air temperature for the time step
            dew_point: distributed dew point for the time step
            cloud_factor: distributed cloud factor for the time step measured/modeled
        """
    
        self._logger.debug('%s Distributing thermal' % date_time)
        
        # calculate clear sky thermal
        if self.method == 'Marks1979':
            cth = np.zeros_like(air_temp, dtype=np.float64)
            envphys_c.ctopotherm(air_temp, dew_point, self.dem, self.sky_view, cth, self.config['nthreads'])
             
        elif self.method == 'Dilley1998':
            cth = thermal_radiation.Dilly1998(air_temp, vapor_pressure/1000)
            
        elif self.method == 'Prata1996':
            cth = thermal_radiation.Prata1996(air_temp, vapor_pressure/1000)
            
        elif self.method == 'Angstrom1918':
            cth = thermal_radiation.Angstrom1918(air_temp, vapor_pressure/1000)
            
        # terrain factor correction
        if (self.sky_view is not None) and (self.method != 'Marks1979'):
            # apply (emiss * skvfac) + (1.0 - skvfac) to the longwave
            cth = cth * self.sky_view + (1.0 - self.sky_view) * thermal_radiation.STEF_BOLTZ * air_temp**4
        
    
        # correct for the cloud factor based on Garen and Marks 2005
        # ratio of measured/modeled solar indicates the thermal correction
        if self.correct_cloud:
            tc = 1.485 - 0.488 * cloud_factor
            cth *= tc
        
        # correct for vegetation
        if self.correct_veg:
            cth = thermal_radiation.thermal_correct_canopy(cth, air_temp, self.veg_tau, self.veg_height)
            
        self.thermal = cth
    
    
    def distribute_thread(self, queue, date):
        """
        Distribute the data using threading and queue. All data is provided and ``distribute_thread``
        will go through each time step and call :mod:`smrf.distribute.thermal.th.distribute` then
        puts the distributed data into the queue for :py:attr:`thermal`.
        
        Args:
            queue: queue dictionary for all variables
            data: pandas dataframe for all data, indexed by date time
            
        """
        
        for t in date:
                        
            air_temp = queue['air_temp'].get(t)
            dew_point = queue['dew_point'].get(t)
            vapor_pressure = queue['vapor_pressure'].get(t)
            cloud_factor = queue['cloud_factor'].get(t)
            
            self.distribute(t, air_temp, vapor_pressure, dew_point, cloud_factor)
        
            queue['thermal'].put( [t, self.thermal] )
     
           
    def distribute_thermal(self, data, air_temp):
        """
        Distribute given a Panda's dataframe for a single time step. Calls
        :mod:`smrf.distribute.image_data.image_data._distribute`. Used when thermal is given 
        (i.e. gridded datasets from WRF). Follows these steps:
        
        1. Distribute the thermal radiation from point values
        2. Correct for vegetation
        
        Args:
            data: thermal values
            
        """
    
        self._logger.debug('%s Distributing thermal' % data.name)
        
        self._distribute(data)
        
        # correct for vegetation
        self.thermal = thermal_radiation.thermal_correct_canopy(self.thermal, air_temp, self.veg_tau, self.veg_height)
        
        
    def distribute_thermal_thread(self, queue, data):
        """
        Distribute the data using threading and queue. All data is provided and ``distribute_thread``
        will go through each time step and call :mod:`smrf.distribute.thermal.th.distribute_thermal` then
        puts the distributed data into the queue for :py:attr:`thermal`. Used when thermal is given 
        (i.e. gridded datasets from WRF).
        
        Args:
            queue: queue dictionary for all variables
            data: pandas dataframe for all data, indexed by date time
            
        """
        
        for t in data.index:
        
            air_temp = queue['air_temp'].get(t)
        
            self.distribute_thermal(data.ix[t], air_temp)
            
            queue['thermal'].put( [t, self.thermal] )
    
    
