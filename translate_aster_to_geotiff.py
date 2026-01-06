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

    for sub_dataset, _ in dataset.GetSubDatasets():
        print(sub_dataset)
        file_name = os.path.join(outputs, '{}_{}_{}.tif'.format(id, sub_dataset.split(':')[4], sub_dataset.split(':')[5]))
        gdal.Translate(file_name, sub_dataset)

for f in hdf_files:
    print(f)
    id = f.split('.')[0]
    translate_hdf(inputs, f, id)

