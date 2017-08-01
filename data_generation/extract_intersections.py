import fiona
import numpy as np
import sys
import math
from shapely.geometry import Point, shape, mapping
import itertools
import cPickle

#Import shapefile specified at commandline
shp = sys.argv[1]

#Get all lines, dummy id
lines = [
         (
         line[0],
         shape(line[1]['geometry'])
         ) for line in enumerate(fiona.open(shp))
        ]

#Track progress
def track(index, step, tot):
    if index%step==0:
        print "finished {} of {}".format(index, tot)

#Function for extracting intersections, return coordinates + properties
def ex_inters(inter, prop):
    if "Point" == inter.type:
        yield inter, prop
    #If multiple intersections, return each point
    elif "MultiPoint" == inter.type:
        for i in inter:
            yield(i,prop)
    #If line with overlap, find start/end, return
    elif "MultiLineString" == inter.type:
        multiLine = [line for line in inter]
        first_coords = multiLine[0].coords[0]
        last_coords = multiLine[-1].coords[1]
        for i in [Point(first_coords[0], first_coords[1]),Point(last_coords[0], last_coords[1])]:
            yield(i,prop)
    #If collection points/lines (rare), just re-run on each part
    elif "GeometryCollection" == inter.type:
        for geom in inter:
            for i in ex_inters(geom, prop):
                yield i

if not os.path.exists('inters.pkl'):
    inters = []
    i = 0
    #Total combinations
    def nCr(n,r):
        f = math.factorial
        return f(n) / f(r) / f(n-r)
    tot = nCr(len(lines), 2)
    #Iterate, extract intersections
    for line1,line2 in itertools.combinations(lines, 2):
        track(i, 10000, tot)
        if line1[1].intersects(line2[1]):
            inter = line1[1].intersection(line2[1])
            inters.extend(ex_inters(inter, 
                                    {'id_1':line1[0], 'id_2':line2[0]}
                                   ))
        i+=1

    #Save to pickle in case script breaks    
    with open('inters.pkl', 'w') as f:
        cPickle.dump(inters, f)
else:
    with open('inters.pkl', 'w') as f:
        inters = cPickle.load(f)

# de duplicated
inters_de = []
# schema of the shapefile
schema = {'geometry': 'Point', 
          'properties': {'id_1':'int',
                        'id_2':'int'}
         }
# creation of the shapefile
with fiona.open('inters.shp','w','ESRI Shapefile', schema) as output:
    i = 0
    for pt in inters:
        if pt[0] not in inters_de:
            track(i, 10000, len(inters))
            output.write({'geometry':mapping(pt[0]), 'properties':pt[1]})
            inters_de.append(pt[0])
            i+=1
