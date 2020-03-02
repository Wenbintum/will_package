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

from time import strftime

from rtools.cube import read_cube
from rtools.cube import write_cube

def work_on_cubes(cubefile1, cubefile2, operation, **kwargs):
    # read the cube file:
    cube1 = read_cube(cubefile1, 
                      verbose = False, 
                      full_output = True, 
                      convert = False,
                      **kwargs)
    
    cube2 = read_cube(cubefile2, 
                      verbose = False, 
                      full_output = True, 
                      convert = False,
                      **kwargs)

    operation = operation.lower()
    
    data1 = cube1['cube_data']
    data2 = cube2['cube_data']

    if operation == 'add':
        data = data1 + data2
        connection = 'PLUS'
    if operation == 'subtract':
        data = data1 - data2
        connection = 'MINUS'
    if operation == 'multiply':    
        data = data1 * data2
        connection = 'TIMES'
    
    # outname
    name1 = cubefile1.split('/')[-1].replace('.cube','').replace('.gz','')
    name2 = cubefile2.split('/')[-1].replace('.cube','').replace('.gz','')

    outname = name1 + '_' + connection + '_' + name2 + '.cube'   
    
    # comment
    comment = outname + ' (from rtools), written on %s'%strftime('%c')
    
    # verbosity
    print('Writing {}'.format(outname))
    
    # write cube
    write_cube(fileobj = outname, 
               atoms = cube1['atoms'], 
               data = data, 
               comment = comment,
               origin = cube1['origin'])
