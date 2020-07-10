from inicheck.tools import cast_all_variables

from smrf.framework.model_framework import run_smrf
from smrf.tests.smrf_test_case import SMRFTestCase


class TestLoadGrid(SMRFTestCase):
    def test_grid_wrf(self):
        """ WRF NetCDF loading """

        config = self.base_config_copy()
        del config.raw_cfg['csv']

        adj_config = {
            'gridded': {
                'data_type': 'wrf',
                'wrf_file': './gridded/WRF_test.nc',
            },
            'system': {
                'threading': 'False',
                'log_file': './output/log.txt'
            },
            'precip': {
                'station_adjust_for_undercatch': 'False'
            },
            'wind': {
                'wind_model': 'interp'
            },
            'thermal': {
                'correct_cloud': 'False',
                'correct_veg': 'True'
            },
            'time': {
                'start_date': '2015-03-03 00:00',
                'end_date': '2015-03-03 04:00'
            }
        }

        config.raw_cfg.update(adj_config)

        # set the distribution to grid, thermal defaults will be fine
        for v in self.dist_variables:
            config.raw_cfg[v]['grid_mask'] = 'False'

        # fix the time to that of the WRF_test.nc
        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        # ensure that the recipes are used
        self.assertTrue(
            'station_adjust_for_undercatch' not in config.cfg['precip'].keys()
        )
        self.assertFalse(config.cfg['thermal']['correct_cloud'])
        self.assertTrue(config.cfg['thermal']['correct_veg'])

        run_smrf(config)

    def test_grid_hrrr_local(self):
        """ HRRR grib2 loading with local elevation gradient """

        config = self.base_config_copy()
        del config.raw_cfg['csv']

        adj_config = {
            'gridded': {
                'data_type': 'hrrr_grib',
                'hrrr_directory': './gridded/hrrr_test/',
            },
            'time': {
                'start_date': '2018-07-22 16:00',
                'end_date': '2018-07-22 20:00',
                'time_zone': 'utc'
            },
            'system': {
                'threading': False,
                'log_file': './output/test.log'
            },
            'air_temp': {
                'grid_local': True,
                'grid_local_n': 25
            },
            'vapor_pressure': {
                'grid_local': True,
                'grid_local_n': 25
            },
            'precip': {
                'grid_local': True,
                'grid_local_n': 25,
                'precip_temp_method': 'dew_point'
            },
            'wind': {
                'wind_model': 'interp'
            },
            'thermal': {
                'correct_cloud': True,
                'correct_veg': True
            },
            'albedo': {
                'grain_size': 300.0,
                'max_grain': 2000.0
            }
        }
        config.raw_cfg.update(adj_config)

        # set the distribution to grid, thermal defaults will be fine
        for v in self.dist_variables:
            config.raw_cfg[v]['distribution'] = 'grid'
            config.raw_cfg[v]['grid_mask'] = 'False'

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        # ensure that the recipes are used
        self.assertTrue(
            'station_adjust_for_undercatch' not in config.cfg['precip'].keys())
        self.assertTrue(config.cfg['thermal']['correct_cloud'])
        self.assertTrue(config.cfg['thermal']['correct_veg'])

        run_smrf(config)

        self.compare_hrrr_gold(self.basin_dir.joinpath('gold_hrrr'))

    def test_grid_netcdf(self):
        """ Generic NetCDF loading """

        config = self.base_config_copy()
        del config.raw_cfg['csv']

        generic_grid = {
            'data_type': 'netcdf',
            'netcdf_file': './gridded/netcdf_test.nc',
            'air_temp': 'air_temp',
            'vapor_pressure': 'vapor_pressure',
            'precip': 'precip',
            'wind_speed': 'wind_speed',
            'wind_direction': 'wind_direction',
            'thermal': 'thermal',
            'cloud_factor': 'cloud_factor'
        }
        config.raw_cfg['gridded'] = generic_grid
        config.raw_cfg['system']['time_out'] = '25'
        config.raw_cfg['system']['queue_max_values'] = '2'
        # Doesn't work with true
        config.raw_cfg['system']['threading'] = 'False'

        # set the distribution to grid, thermal defaults will be fine
        for v in self.dist_variables:
            config.raw_cfg[v]['distribution'] = 'grid'
            config.raw_cfg[v]['grid_mask'] = 'False'

        config.raw_cfg['thermal']['correct_cloud'] = 'False'
        config.raw_cfg['thermal']['correct_veg'] = 'True'

        config.raw_cfg['wind']['wind_model'] = 'interp'

        # fix the time to that of the WRF_test.nc
        config.raw_cfg['time']['start_date'] = '2015-03-03 00:00'
        config.raw_cfg['time']['end_date'] = '2015-03-03 04:00'

        config.apply_recipes()
        config = cast_all_variables(config, config.mcfg)

        # ensure that the recipes are used
        self.assertTrue(
            'station_adjust_for_undercatch' not in config.cfg['precip'].keys())
        self.assertFalse(config.cfg['thermal']['correct_cloud'])
        self.assertTrue(config.cfg['thermal']['correct_veg'])

        run_smrf(config)
