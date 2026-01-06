"""
Created on Tuesday Jan 06, 2026

@author: Nathan Roberts (lpdaac@usgs.gov)

This script will allow users to convert ASTER L1B Version 4 HDF products to properly georeferenced, projected GeoTIFFs. 

################################
 #  Usage: python makel1b_geotiff.py -f <Directory Containing Downloaded HDF L1B Products> -o <Directory where GeoTIFFs will write to>\
################################
"""



#Import Modules
import rasterio as rio
from rasterio.transform import from_origin
from rasterio.crs import CRS
from pyproj import Transformer
from affine import Affine
import os
from shapely import Polygon
import argparse
import aster_utils

import warnings
warnings.filterwarnings('ignore')

#Setup Parser
parser = argparse.ArgumentParser()

parser.add_argument('--files', '-f', type=str, required=True, help = 'Directory Containing L1B HDF Files')
parser.add_argument('--output', '-o', type=str, required=True, help = 'Output Directory for GeoTIFFs')

args = parser.parse_args()

inputs = args.files
outputs = args.output

#Get list of HDF Files to Convert
hdf_files = os.listdir(inputs)
print('Found ', len(hdf_files), ' HDF Files to Convert')

"""
This section opens the HDF files and retrieves the HDF Level Metadata and extracts the requested attributes.
"""
#Open HDF Files
def open_hdf(inputs, file):
    hdf_file = rio.open(os.path.join(inputs, file))
    return hdf_file

#Get HDF Metadata (Attributes)
def get_metadata(hdf_file):
    metadata = hdf_file.tags()
    return metadata

#Get Granule Rotation Angle from Metadata
def get_rotation(metadata):
    angle = float(metadata['MAPORIENTATIONANGLE'])
    return angle

def get_corners(metadata):
    #Split UPPERLEFT and UPPERRIGHT into list where coords are their own index to support transformation
    ul_coord = metadata['UPPERLEFT'].split(',')
    ur_coord = metadata['UPPERRIGHT'].split(',')
    return ul_coord, ur_coord

"""
This Section is required because the HDF does not have the proper projection and datum, the granules UTM zone is calculated based upon the bounds of the data
"""

#Make bounding box of granule
def make_bbox(metadata):
    #Split up Coordinates into list containing each coordinate as its own index
    ul = metadata['UPPERLEFT'].split(',')
    ur = metadata['UPPERRIGHT'].split(',')
    lr = metadata['LOWERRIGHT'].split(',')
    ll = metadata['LOWERLEFT'].split(',')
    #Asemble coordinates as list of coordinate pairs
    coords = [[ul[1],ul[0]],[ur[1],ur[0]],[lr[1],lr[0]],[ll[1],ll[0]]]
    #Make coordinates into shapley polygon
    polygon = Polygon(coords)
    return polygon

#Check if bounding box crosses anti meridian and fix if needed
def anti_meridian_check(polygon):
    #Call fix_polygon from aster_util to check if the polygon crosses antimerdian if yes then split it
    fixed_polygon, polygon_bounds = aster_utils.fix_polygon(polygon)
    return fixed_polygon, polygon_bounds

#Get UTM zone for anti meridian checked bounding box
def get_utm_zone(polygon_bounds):
    #Call get_utm_crs_for_bounds from raster_util to get the UTM Zone of the bounding box
    crs = aster_utils.get_utm_crs_for_bounds(polygon_bounds)
    #Convert UTM Zone to EPSG Code
    epsg_code = (crs.to_authority())
    return epsg_code

"""
This section retrieves the sub datasets (layers) within the HDF
"""
#Get sub datasets
def get_sub_datasets(hdf_file):
    hdf_layers = []
    for layer in hdf_file.subdatasets:
        hdf_layers.append(layer)
    return hdf_layers

"""
This section writes out the GeoTIFFs
"""

def make_geotiff(hdf_layers, epsg_code, ul_coord, ur_coord, angle, id, outputs):
    #Open each sub dataset (layer)
    for x in hdf_layers:
        with rio.open(x) as band:
            print('Converting {}'.format(x))
            arr = band.read()
            #Create Transformation, Update, Projection from default CRS (Geographic to UTM CRS returned from get_utm_crs_for_bounds function
            transformer = Transformer.from_crs("EPSG:4326", epsg_code)
            UL = transformer.transform(ul_coord[0], ul_coord[1])
            UR = transformer.transform(ur_coord[0], ur_coord[1])

            #Create Affine rotation from map orientation angle
            rotate = Affine.rotation(angle)
            #If VNIR Band then use 15, 15 Pixel Size in transformation
            if 'VNIR' in x:
                transform = from_origin(UL[0], UL[1],15, 15)*rotate
            #If SWIR Band then use 30, 30 Pixel Size in transformation
            elif 'SWIR' in x:
                transform = from_origin(UL[0], UL[1],30, 30)*rotate
            #If TIR Band then use 90, 90 Pixel Size in transformation
            elif 'TIR' in x:
                transform = from_origin(UL[0], UL[1],90, 90)*rotate
            #Copy metadata from HDF Band
            kwargs = band.meta.copy()
            #Update metadata with new CRS, Driver (GeoTIFF), transformation
            kwargs.update({
            'crs': CRS.from_epsg(epsg_code[1]),
            'driver':'GTIFF',
            'transform': transform})
            #Write out each band to GeoTIFF
            with rio.open(os.path.join(outputs,'{}_{}_{}.tif'.format(id, x.split(':')[4], x.split(':')[5])),'w', **kwargs) as dst:
                dst.write(arr)
            #with rio.open('file.tif','w', **kwargs) as dst:
            #    dst.write(arr)    

#Iterrate over list of HDF files and create GeoTIFFs 
for f in hdf_files:
        hdf_file = open_hdf(inputs, f)
        id = f.split('.')[0]
        metadata = get_metadata(hdf_file)
        angle = get_rotation(metadata)
        polygon = make_bbox(metadata)
        fixed_polygon, polygon_bounds = anti_meridian_check(polygon)
        epsg_code = get_utm_zone(polygon_bounds)
        ul_coord, ur_coord = get_corners(metadata)
        hdf_layers = get_sub_datasets(hdf_file)
        make_geotiff(hdf_layers, epsg_code, ul_coord, ur_coord, angle, id, outputs)


    








