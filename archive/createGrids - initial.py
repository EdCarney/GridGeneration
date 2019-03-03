
from navpy import lla2ned, ned2lla
import xml.etree.ElementTree as ET
import math, numpy, json

tolerance = 0.000001

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

class LineSegment(object):
    """
    Object class for line segment. Arguments on initialization are a start Point object and end Point object.
    Attributes include the start and end Point objects and the slope and y-intercept of the line segment.
    """
    def __init__(self, startPoint, endPoint):
        self.startPoint = startPoint
        self.endPoint = endPoint
        if math.fabs(startPoint.east - endPoint.east) < tolerance:
            self.slope = False
            self.yIntercept = False
        else:
            self.slope = (startPoint.north - endPoint.north)/(startPoint.east - endPoint.east)
            self.yIntercept = startPoint.north - self.slope*startPoint.east

class Polygon(object):
    """
    Object class for polygon. Arguments on initialization is a list of Point objects.
    Has attributes for a list of Point objects (points) and LineSegment objects (lineSegments).
    Has a method for printing the polygon points as either LLA (Type = 1) or NED (Type = 2); default does not print altitude/down coordinate, can specify printAll = 1 to print all coordinates.
    """
    def __init__(self, Points):
        self.points = Points
        self.numPoints = len(Points)
        self.lineSegments = [LineSegment(Points[i],Points[(i+1)%self.numPoints]) for i in range(self.numPoints)]
        self.minNorth = min([point.north for point in Points])
        self.maxNorth = max([point.north for point in Points])
        self.minEast = min([point.east for point in Points])
        self.maxEast = max([point.east for point in Points])
        area = 0.0
        for i in range(self.numPoints):
            area += self.points[i].east*self.points[(i+1)%self.numPoints].north - self.points[i].north*self.points[(i+1)%self.numPoints].east
        self.area = math.fabs(area/2.0)

    def printPoints(self,type,printAll=0):
        printStr = ''
        if type == 1:
            if printAll:
                for point in self.points:
                    printStr += str(point.lat) + ',' + str(point.long) + ',' + str(point.alt) + ' '
            else:
                for point in self.points:
                    printStr += str(point.lat) + ',' + str(point.long) + ' '
        elif type == 2:
            if printAll:
                for point in self.points:
                    printStr += str(point.north) + ',' + str(point.east) + ',' + str(point.down) + ' '
            else:
                for point in self.points:
                    printStr += str(point.north) + ',' + str(point.east) + ' '

        return printStr[:-1]

def pointsEqual(point1,point2):
    """
    Simple function to determine if two points are equal.
    Takes two Point objects as arguments.
    Returns True if the points are the sae and Flase otherwise.
    """
    if point1.east == point2.east and point1.north == point2.north:
        return True
    else:
        return False

def lineIntersect(segment1,segment2,referencePoint):
    """
    Function to determine if two line segments intersect.
    Takes two LineSegment objects as objects.
    Returns False if no intersection. Returns the intersection as a Point object if the segments intersect.
    """

    if type(segment1.slope) == float and type(segment2.slope) == float:

        # checks for parallel lines
        if math.fabs(segment1.slope - segment2.slope) < tolerance:
            return False

        # checks if any of the points are the same
        elif pointsEqual(segment1.startPoint,segment2.startPoint) or pointsEqual(segment1.startPoint,segment2.endPoint) or pointsEqual(segment1.endPoint,segment2.startPoint) or pointsEqual(segment1.endPoint,segment2.endPoint):
            return False

        # calculate north and east intersect point
        else:
            eastIntersect = (segment2.yIntercept - segment1.yIntercept)/(segment1.slope - segment2.slope)
            if (eastIntersect < (max([min([segment1.startPoint.east,segment1.endPoint.east]),min([segment2.startPoint.east,segment2.endPoint.east])]))) or eastIntersect > (min([max([segment1.startPoint.east,segment1.endPoint.east]),max([segment2.startPoint.east,segment2.endPoint.east])])):
                return False
            else:
                northIntersect = segment1.slope*eastIntersect + segment1.yIntercept
                return Point(northIntersect,eastIntersect,0.0,2,referencePoint)

    else:
        # checks if both lines are vertical
        if type(segment1.slope) == bool and type(segment2.slope) == bool:
            return False

        elif type(segment1.slope) == bool : # Segment 1 is a vertical line
            noSlopeSegment = segment1
            slopeSegment = segment2
        else:                      # Segment 2 is a vertical line
            noSlopeSegment = segment2
            slopeSegment = segment1

        eastIntersect = (noSlopeSegment.startPoint.east + noSlopeSegment.endPoint.east)/2.0
        northIntersect = slopeSegment.yIntercept + slopeSegment.slope*eastIntersect
        if eastIntersect < min([slopeSegment.startPoint.east,slopeSegment.endPoint.east]) or eastIntersect > max([slopeSegment.startPoint.east,slopeSegment.endPoint.east]):
            return False
        elif northIntersect < min([noSlopeSegment.startPoint.north,noSlopeSegment.endPoint.north]) or northIntersect > max([noSlopeSegment.startPoint.north,noSlopeSegment.endPoint.north]):
            return False
        else:
            return Point(northIntersect,eastIntersect,0.0,2,referencePoint)

def polyIntersect(poly1,poly2,referencePoint):
    for segment1 in poly1.lineSegments:
        for segment2 in poly2.lineSegments:
            if lineIntersect(segment1,segment2,referencePoint):
                return lineIntersect(segment1,segment2,referencePoint)
    return False


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
    # referencePoint = [0.0,0.0,0.0]
    points = [Point(float(point.split(',')[0]),float(point.split(',')[1]),0.0,1,referencePoint) for point in pointListStr.split(' ')]
    targetPoly = Polygon(points)

    minEast = min([point.east for point in points])
    maxEast = max([point.east for point in points])
    minNorth = min([point.north for point in points])
    maxNorth = max([point.north for point in points])

    northDivs = int(math.ceil(math.fabs(targetPoly.maxNorth-targetPoly.minNorth)/gridHeight))
    eastDivs = int(math.ceil(math.fabs(targetPoly.maxEast-targetPoly.minEast)/gridWidth))

    northGridLines = [targetPoly.minNorth+gridHeight*div for div in range(northDivs+1)]
    eastGridLines = [targetPoly.minEast+gridWidth*div for div in range(eastDivs+1)]

    gridSquares = []

    for i in range(len(northGridLines)):
        if i+1 == len(northGridLines):
            break
        for j in range(len(eastGridLines)):
            if j+1 == len(eastGridLines):
                break

            newGrid = {
                'number': i*len(eastGridLines)+j,
                'poly': Polygon([
                    Point(northGridLines[i],eastGridLines[j],0.0,2,referencePoint),
                    Point(northGridLines[i+1],eastGridLines[j],0.0,2,referencePoint),
                    Point(northGridLines[i+1],eastGridLines[j+1],0.0,2,referencePoint),
                    Point(northGridLines[i],eastGridLines[j+1],0.0,2,referencePoint)
                    ])
                }

            gridSquares.append(newGrid)

            #if polyIntersect(newGrid['poly'],targetPoly,referencePoint):
            #    gridSquares.append(newGrid)

    root = ET.Element('serviceRegions')
    for grid in gridSquares:
        doc = ET.SubElement(root, 'serviceRegion')
        ET.SubElement(doc, 'name').text = 'Grid' + str(grid['number'])
        ET.SubElement(doc, 'coordinates').text = grid['poly'].printPoints(1)

    doc = ET.SubElement(root, 'serviceRegion')
    ET.SubElement(doc, 'name').text = 'Target'
    ET.SubElement(doc, 'coordinates').text = targetPoly.printPoints(1)

    tree = ET.ElementTree(root)
    tree.write('C:\\Users\\ecarney\\Desktop\\Local_Tests\\OneWeb\\Task 4\\Misc Python Scripts\\Generate STK Scenario\\data\\ServiceRegions\\serviceRegionConfig.xml')
    root = ET.parse('C:\\Users\\ecarney\\Desktop\\Local_Tests\\OneWeb\\Task 4\\Misc Python Scripts\\Generate STK Scenario\\data\\ServiceRegions\\serviceRegionConfig.xml').getroot()
    indent(root)
    ET.dump(root)

    return gridSquares
    #return json.dumps(gridSquares)
