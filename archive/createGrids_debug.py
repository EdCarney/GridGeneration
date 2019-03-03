
from shapely.geometry import Polygon, box
from navpy import lla2ned, ned2lla
import xml.etree.ElementTree as ET
import math, numpy, json

class Point(object):
    """
    Object class for points. Arguments on initialization are Var1, Var2, Var3, Type. Type == 1 is LLA, Type == 2 is NED.
    Depending on type Var1, Var2, Var3 are either Lat, Long, Alt or North, East, Down.
    Conversions are done automatically using reference LLA point of 0,0,0.
    """
    def __init__(self, Var1, Var2, Var3, type, referencePoint):
        Var1 = float(Var1)
        Var2 = float(Var2)
        Var3 = float(Var3)
        if type == 1:
            self.lat = Var1
            self.long = Var2
            self.alt = Var3

            nedArray = lla2ned(Var1,Var2,Var3,referencePoint[0],referencePoint[1],referencePoint[2])
            self.north = nedArray[0]
            self.east = nedArray[1]
            self.down = nedArray[2]

        elif type == 2:
            self.north = Var1
            self.east = Var2
            self.down = Var3

            llaArray = ned2lla(numpy.array([Var1,Var2,Var3]),referencePoint[0],referencePoint[1],referencePoint[2])
            self.lat = llaArray[0]
            self.long = llaArray[1]
            self.alt = llaArray[2]


def indent(elem, level=0):
    i = "\n" + level*"  "
    j = "\n" + (level-1)*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = j
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = j
    return elem 

def createGrids(pointListStr,gridWidth,gridHeight):
    if not(type(pointListStr) == str):
        print "WARNING: Point list must be of type string formated as \"LAT1,LONG1 LAT2,LONG2, ...\""
        return 1

    referencePoint = [float(pointListStr.split(' ')[0].split(',')[0]),float(pointListStr.split(' ')[0].split(',')[1]),0.0]
    points = [Point(float(point.split(',')[0]),float(point.split(',')[1]),0.0,1,referencePoint) for point in pointListStr.split(' ')]
    targetPoly = Polygon([[point.east,point.north] for point in points])

    minEast = min([point.east for point in points])
    maxEast = max([point.east for point in points])
    minNorth = min([point.north for point in points])
    maxNorth = max([point.north for point in points])

    northDivs = int(math.ceil(math.fabs(maxNorth-minNorth)/gridHeight))
    eastDivs = int(math.ceil(math.fabs(maxEast-minEast)/gridWidth))

    northGridLines = [minNorth+gridHeight*div for div in range(northDivs+1)]
    eastGridLines = [minEast+gridWidth*div for div in range(eastDivs+1)]

    gridSquares = []

    for i in range(len(northGridLines)):
        if i+1 == len(northGridLines):
            break
        for j in range(len(eastGridLines)):
            if j+1 == len(eastGridLines):
                break

            newPoly = box(eastGridLines[j],northGridLines[i],eastGridLines[j+1],northGridLines[i+1])

            if newPoly.intersects(targetPoly):
                gridSquares.append({
                'number': i*len(eastGridLines)+j,
                'poly': newPoly,
                'coverage': targetPoly.intersection(newPoly).area/newPoly.area,
                'points': [
                    Point(northGridLines[i],eastGridLines[j],0.0,2,referencePoint),
                    Point(northGridLines[i+1],eastGridLines[j],0.0,2,referencePoint),
                    Point(northGridLines[i+1],eastGridLines[j+1],0.0,2,referencePoint),
                    Point(northGridLines[i],eastGridLines[j+1],0.0,2,referencePoint)
                    ]
                })

    root = ET.Element('serviceRegions')
    for grid in gridSquares:
        doc = ET.SubElement(root, 'serviceRegion')
        ET.SubElement(doc, 'name').text = 'Grid' + str(grid['number'])
        outStr = ''
        for point in grid['points']:
            outStr += str(point.lat) + ',' + str(point.long) + ' '
        ET.SubElement(doc, 'coordinates').text = outStr[:-1]

    doc = ET.SubElement(root, 'serviceRegion')
    ET.SubElement(doc, 'name').text = 'Target'
    outStr = ''
    for point in points:
        outStr += str(point.lat) + ',' + str(point.long) + ' '
    ET.SubElement(doc, 'coordinates').text = outStr[:-1]

    tree = ET.ElementTree(root)
    tree.write('C:\\Users\\ecarney\\Desktop\\Local_Tests\\OneWeb\\Task 4\\Misc Python Scripts\\Generate STK Scenario\\data\\ServiceRegions\\serviceRegionConfig.xml')
    root = ET.parse('C:\\Users\\ecarney\\Desktop\\Local_Tests\\OneWeb\\Task 4\\Misc Python Scripts\\Generate STK Scenario\\data\\ServiceRegions\\serviceRegionConfig.xml').getroot()
    indent(root)
    ET.dump(root)

    return json.dumps(gridSquares)
