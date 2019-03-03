from shapely.geometry import Polygon, box
from navpy import lla2ned, ned2lla
from point import Point
import xml.etree.ElementTree as ET
import math, numpy, json, sys, os

path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)

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

def printToFile(gridSquares,points,eastGridLines,useTargetPolys):
    root = ET.Element('serviceRegions')
    for grid in gridSquares:
        doc = ET.SubElement(root, 'serviceRegion')

        if useTargetPolys:
            ET.SubElement(doc, 'name').text = 'Grid_Target' + str(grid['gridE'] + grid['gridN']*(len(eastGridLines)-1))
            outStr = ''
            for point in grid['targetPoints']:
                outStr += str(point.lat) + ',' + str(point.long) + ' '
            ET.SubElement(doc, 'coordinates').text = outStr[:-1]

        elif not(useTargetPolys):
            ET.SubElement(doc, 'name').text = 'Grid' + str(grid['gridE'] + grid['gridN']*(len(eastGridLines)-1))
            outStr = ''
            for point in grid['gridPoints']:
                outStr += str(point.lat) + ',' + str(point.long) + ' '
            ET.SubElement(doc, 'coordinates').text = outStr[:-1]

    doc = ET.SubElement(root, 'serviceRegion')
    ET.SubElement(doc, 'name').text = 'TargetRegion'
    outStr = ''
    for point in points:
        outStr += str(point.lat) + ',' + str(point.long) + ' '
    ET.SubElement(doc, 'coordinates').text = outStr[:-1]

    indent(root)
    tree = ET.ElementTree(root)
    dir = 'bin'
    file = 'serviceRegionConfig.xml'
    tree.write(dir + '\\' + file)

def createGrids(pointListStr,gridWidth,gridHeight,useTargetPolys):
    if not(type(pointListStr) == str):
        print "WARNING: Point list must be of type string formated as \"LAT1,LONG1 LAT2,LONG2, ...\""
        return 1

    gridHeight = float(gridHeight)
    gridWidth = float(gridWidth)

    referencePoint = [float(pointListStr.split(' ')[0].split(',')[0]),float(pointListStr.split(' ')[0].split(',')[1]),0.0]
    points = [Point(float(point.split(',')[0]),float(point.split(',')[1]),0.0,1,referencePoint) for point in pointListStr.split(' ')]
    targetPoly = Polygon([[point.east,point.north] for point in points])

    minEast = float(min([point.east for point in points]))
    maxEast = float(max([point.east for point in points]))
    minNorth = float(min([point.north for point in points]))
    maxNorth = float(max([point.north for point in points]))

    northDivs = int(math.ceil(math.fabs(maxNorth-minNorth)/gridHeight))
    eastDivs = int(math.ceil(math.fabs(maxEast-minEast)/gridWidth))

    northGridLines = [minNorth+gridHeight*div for div in range(northDivs+1)]
    eastGridLines = [minEast+gridWidth*div for div in range(eastDivs+1)]

    gridSquares = []

    for i in range(len(northGridLines)-1):
        for j in range(len(eastGridLines)-1):

            newPoly = box(eastGridLines[j],northGridLines[i],eastGridLines[j+1],northGridLines[i+1])

            if newPoly.intersects(targetPoly):
                gridSquares.append({
                'gridE': j,
                'gridN': i,
                'poly': newPoly,
                'coverage': targetPoly.intersection(newPoly).area/newPoly.area,
                'gridPoints': [
                    Point(northGridLines[i+1],eastGridLines[j+1],0.0,2,referencePoint),
                    Point(northGridLines[i+1],eastGridLines[j],0.0,2,referencePoint),
                    Point(northGridLines[i],eastGridLines[j],0.0,2,referencePoint),
                    Point(northGridLines[i],eastGridLines[j+1],0.0,2,referencePoint)
                    ],
                'targetPoints': [
                    Point(coord[1],coord[0],0.0,2,referencePoint) for coord in list(targetPoly.intersection(newPoly).exterior.coords)[:-1]
                    ]
                })


    printToFile(gridSquares,points,eastGridLines,useTargetPolys)

    swGridPoint = Point(northGridLines[0],eastGridLines[0],0.0,2,referencePoint)
    gridVisOutput = {
        'gridDescription':{
            'swCornerLat':swGridPoint.lat,
            'swCornerLon':swGridPoint.long,
            'squareLength':gridWidth,
            'gridSquareE':len(eastGridLines)-1,
            'gridSquareN':len(northGridLines)-1
            },
        'gridData':[{'gridE':grid['gridE'],'gridN':grid['gridN'],'coverage':grid['coverage']} for grid in gridSquares]
        }

    orderCreationOutput = [
        {
            'orderId':grid['gridE']+(len(eastGridLines)-1)*grid['gridN'],
            #'gridCoords':[
            #    [grid['gridPoints'][0].lat,grid['gridPoints'][0].long],
            #    [grid['gridPoints'][1].lat,grid['gridPoints'][1].long],
            #    [grid['gridPoints'][2].lat,grid['gridPoints'][2].long],
            #    [grid['gridPoints'][3].lat,grid['gridPoints'][3].long]
            #    ],
            'gridCoords':[
                [gridPoint.lat, gridPoint.long] for gridPoint in grid['gridPoints']
                ],
            'targetCoords':[
                [targetPoint.lat, targetPoint.long] for targetPoint in grid['targetPoints']
                ],
            'squareLength':gridVisOutput['gridDescription']['squareLength'],
            'coverage':grid['coverage'],
            'centerLat':(float(grid['gridPoints'][0].lat) + float(grid['gridPoints'][1].lat) + float(grid['gridPoints'][2].lat) + float(grid['gridPoints'][3].lat))/4.0,
            'centerLon':(float(grid['gridPoints'][0].long) + float(grid['gridPoints'][1].long) + float(grid['gridPoints'][2].long) + float(grid['gridPoints'][3].long))/4.0
            } for grid in gridSquares]

    return json.dumps(gridVisOutput),json.dumps(orderCreationOutput)