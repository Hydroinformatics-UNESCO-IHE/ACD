# -*- coding: utf-8 -*-
"""
Created on Tue Nov 07 13:46:24 2017

Automatic catchment delineation



@author: chaco3
"""

from pygeoprocessing import routing as rt
import numpy as np
import gdal
import ogr
import subprocess

## set here the DEM path
#dem_path = r'data\dem.tif'  # path to DEM (has to be filled and projected!!!)
fill_dem = r'data\filled.tif'
snap_dist = 10  # [integer] Pixels to search around
flow_threshold = 10  # [integer] Threshold for flow

#temporary file locations
WATERSHED_TEMP = r'temp\watershed.shp'
OUTLET_TEMP = r'temp\outlet.shp'
STREAM_TEMP = r'temp\stream.tif'
STREAM_TRIM_TEMP = r'temp\stream_trim.tif'

#outlet_path = r'data\outlet'
def opt_fun(outlet_path):
    '''
    Function to calculate the area and stream length from
    
    Parameters
    ----------
    outlet_path : string
        String to the shapefile with the outlet of the catchment. Only 1 point
        
    Returns
    -------
    stream_length : float
        Total length of streams [m] within the catchment
        
    area : float
        Catchment area [m2]
    '''
    # Delineate the catchment
    rt.delineate_watershed(fill_dem, 
                           outlet_path, 
                           snap_dist, 
                           flow_threshold, 
                           WATERSHED_TEMP,
                           OUTLET_TEMP,
                           STREAM_TEMP)
    # Get area [m2]
    dataSource = ogr.Open(WATERSHED_TEMP)
    layer = dataSource.GetLayer()
    new_field = ogr.FieldDefn("Area", ogr.OFTReal)
    new_field.SetWidth(32)
    layer.CreateField(new_field)
    for feature in layer:
        geom = feature.GetGeometryRef()
        area = geom.GetArea() 
    
    # Clip the stream tif with the polygon of the catchment
    subprocess.call('gdalwarp -cutline {0} -crop_to_cutline {1} {2}'.format(WATERSHED_TEMP, STREAM_TEMP, STREAM_TRIM_TEMP))
    
    # Load the file and count the number of pixels
    ff = gdal.Open(STREAM_TRIM_TEMP)
    x_init, xx_span, xy_span, y_init, yx_span, yy_span = ff.GetGeoTransform()
    
    # Get info from trimmed raster
    no_val = ff.GetRasterBand(1).GetNoDataValue()
    gg = ff.ReadAsArray()[0]
    gg[gg==no_val] = 0
    
    stream_len = np.sum(gg)*np.average(np.abs([xx_span, yy_span]))
    
    return stream_len, area

def test():
    outlet_path = r'data\outlet_mitad'
    stream_len, area = opt_fun(outlet_path)
    
if __name__ == '__main__':
    test()