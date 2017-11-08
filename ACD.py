# -*- coding: utf-8 -*-
"""
Created on Tue Nov 07 13:46:24 2017

Automatic catchment delineation

"""
from __future__ import print_function, division
import numpy as np
import subprocess
import os
from os.path import join

from pygeoprocessing import routing as rt
import gdal
import ogr

__author__ = "Juan Carlos Chacon-Hurtado"
__license__ = "MIT"
__version__ = "0.0.1"
__maintainer__ = "Juan Carlos Chacon-Hurtado"
__email__ = "j.chaconhurtado@un-ihe.org"
__status__ = "Development"


# get current path of file
cwd = os.getcwd()


#temporary file locations
WATERSHED_TEMP = join(cwd, 'temp', 'watershed.shp')
OUTLET_TEMP = join(cwd, 'temp', 'outlet.shp')
STREAM_TEMP = join(cwd, 'temp', 'stream.tif')
STREAM_TRIM_TEMP = join(cwd, 'temp', 'stream_trim.tif')

#outlet_path = r'data\outlet'
def opt_fun(outlet_path, dem, snap_distance=10, flow_threshold=10,
            watershed=WATERSHED_TEMP, outlet_snap=OUTLET_TEMP, 
            stream=STREAM_TEMP, stream_trim=STREAM_TRIM_TEMP):
    '''
    Function to calculate the area and stream length from
    
    Parameters
    ----------
    outlet_path : string
        String to the shapefile with the outlet of the catchment. Only 1 point.
    
    dem : string
        String to the shapefile with the DEM of the catchment. DEM has to be 
        filled and projected
        
    snap_distance : int
        Number of cells that it is allowed for the point to move to match the 
        river stream
    
    flow_threshold : int
        Number of cells required to drain to generate streamflow
    
    watershed : string (optional)
        String to the shapefile with the catchment polygon. By default, stores 
        the file into the temp folder
        
    outlet_snap : string (optional)
        String to the shapefile with the outlet fixed to a cell with river 
        stream. By default, stores the file into the temp folder
    
    stream : string (optional)
        String to the shapefile with the streams for the whole DEM extent. By 
        default, stores the file into the temp folder
    
    stream_trim : string (optional)
        String to the shapefile with the streams within the delineated catchment. 
        By default, stores the file into the temp folder
        
    Returns
    -------
    stream_length : float
        Total length of streams [m] within the catchment
        
    area : float
        Catchment area [m2]
        
    '''
    # Delineate the catchment
    rt.delineate_watershed(dem, 
                           outlet_path, 
                           snap_distance, 
                           flow_threshold, 
                           watershed,
                           outlet_snap,
                           stream)
    
    # Get area [m2]
    dataSource = ogr.Open(watershed)
    layer = dataSource.GetLayer()
    new_field = ogr.FieldDefn("Area", ogr.OFTReal)
    new_field.SetWidth(32)
    layer.CreateField(new_field)
    for feature in layer:
        geom = feature.GetGeometryRef()
        area = geom.GetArea() 
    
    # Clip the stream tif with the polygon of the catchment
    trim_fun = subprocess.call('gdalwarp -cutline {0} -crop_to_cutline -overwrite {1} {2}'.format(watershed, stream, stream_trim))
    
    if trim_fun == 1:
        print('Trimming not succsesfull')
        return np.nan, np.nan
    
    # Load the file and count the number of pixels
    ff = gdal.Open(stream_trim)
    x_init, xx_span, xy_span, y_init, yx_span, yy_span = ff.GetGeoTransform()
    
    # Get info from trimmed raster
    no_val = ff.GetRasterBand(1).GetNoDataValue()
    gg = ff.ReadAsArray()
    gg[gg==no_val] = 0
    
    # Calculate stream length [m]
    stream_len = np.sum(gg)*np.average(np.abs([xx_span, yy_span]))
    
    return stream_len, area

def test():
    '''testing function'''
    outlet_path = join(cwd, 'data','outlet')
    fill_dem = join(cwd, 'data','filled.tif')
    snap_dist = 10  # [integer] Pixels to search around
    flow_threshold = 10  # [integer] Threshold for flow
    stream_len, area = opt_fun(outlet_path, fill_dem, snap_dist, flow_threshold)
    print('Stream length for the testing set is: {0} m'.format(stream_len))
    print('Area for the testing set is: {0} m2'.format(area))
    
if __name__ == '__main__':
    test()