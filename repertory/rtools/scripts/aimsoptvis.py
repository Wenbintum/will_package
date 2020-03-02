#!/usr/bin/python

from ase.io import read
from ase.visualize import view
import glob, zipfile, os
from sys import argv

os.system('create_geometry_zip.pl ' + str(argv[1]))
zip_ref = zipfile.ZipFile('geometries.zip', 'r')
zip_ref.extractall('./')
zip_ref.close()
os.chdir('./geometries')

a = [geo for geo in glob.glob('geometr*in')]
a.sort
b = [read(geo) for geo in a]
view(b)

os.chdir('../')
os.system('rm -rf ./geometries*')
