"""
Created on Tuesday Jan 06, 2026
Modified on Thursday Jan 08, 2026

@author: Nathan Roberts (lpdaac@usgs.gov)

This script will allow users to convert Version 4 ASTER HDF products to GeoTIFFs. 

################################
Environment Setup: mamba create -n hdf_translate -c conda-forge --yes python=3.12 gdal libgdal-hdf4
 Usage: python translate_aster_to_geotiff.py -f <Directory Containing Downloaded HDF L1B Products> -o <Directory where GeoTIFFs will write to>\
################################
"""

import argparse
from osgeo import gdal
import os

import warnings
warnings.filterwarnings('ignore')

gdal.SetConfigOption("GDAL_PAM_ENABLED", "NO")

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

def translate_hdf(input, hdf_file, id):
    dataset = gdal.Open(os.path.join(input, hdf_file))

    sub_datasets = [sd[0] for sd in dataset.GetSubDatasets()]
    
    for sd_uri in sub_datasets:
        parts = sd_uri.split(':')
        if len(parts) < 5:
            print(f"Skipping unexpected subdataset: {sd_uri}")
            continue
        swath, field = parts[-2], parts[-1]
        out_tif = os.path.join(outputs, f"{id}_{swath}_{field}.tif")
        print('Translating ', sd_uri)
       # translate
        gdal.Translate(
            out_tif,
            sd_uri,
            format="GTiff",
            creationOptions=["COMPRESS=LZW", "TILED=YES"])

for f in hdf_files:
    try:
        id = f.split('.')[0]
        translate_hdf(inputs, f, id)
    except Exception as e:
        print(f, 'Is not an HDF File, not converted')

