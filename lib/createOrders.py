import os, json, math, glob
import xml.etree.ElementTree as ET 

path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)

def getMinDuration(squareLength,coverage):
    """
    Function to determine the minimum duration of the point order collection.
    This uses the same calculations as the MinAu grid assignment code.
    Requires that the vehicle speed, horizontal sensor view, and order standoff range be defined properly.
    """
    ########## USER-DEFINED ##########
    vehicleSpeed = 5.0 # m/s
    horizView = 30.0 # deg
    standoffRange = 50.0 # m
    ########## USER-DEFINED ##########

    # Calculate the swath width and the minimum number of passes
    sensorSwathWidth = 2 * standoffRange * math.tan((horizView / 180.0) * math.pi)
    passes = math.ceil(squareLength / sensorSwathWidth)

    passTime = squareLength / vehicleSpeed # s
    turnTime = (math.pi * sensorSwathWidth + 0.5) / vehicleSpeed # s
    coverageTime = passes * passTime + (passes - 1) * turnTime # s

    return str(round((coverageTime * coverage), 2))


def createOrders(orderCreationOutput,isPoint=0,useTargetPolys=0):

    ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    ET.register_namespace('xsd', 'http://www.w3.org/2001/XMLSchema')
    ET.register_namespace('q1', 'http://www.opengis.net/gml')
    ET.register_namespace('q2', 'http://www.opengis.net/gml')

    # Delete all files currently in orders directory

    orderDir = 'out\\orders'
    for orderFile in os.listdir(orderDir):
        file_path = os.path.join(orderDir, orderFile)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)

    if not(isPoint):
        tree = ET.parse('bin\\orderTemplate.xml')
        root = tree.getroot()

        orderCreationOutput = json.loads(orderCreationOutput)

        id = root.find('{http://com.orbitlogic.schemas}id')
        origGeom = root.find('{http://com.orbitlogic.schemas}originalGeometry/{http://www.opengis.net/gml}polygonMember/{http://www.opengis.net/gml}Polygon/{http://www.opengis.net/gml}outerBoundaryIs/{http://www.opengis.net/gml}LinearRing/{http://www.opengis.net/gml}coordinates')
        unfillGeom = root.find('{http://com.orbitlogic.schemas}unfulfilledGeometry/{http://www.opengis.net/gml}polygonMember/{http://www.opengis.net/gml}Polygon/{http://www.opengis.net/gml}outerBoundaryIs/{http://www.opengis.net/gml}LinearRing/{http://www.opengis.net/gml}coordinates')

        for order in orderCreationOutput:

            if useTargetPolys:
                id.text = 'Target_' + str(order['orderId'])
                coordStr = ''
                for coord in order['targetCoords']:
                    coordStr += str(coord[1]) + ',' + str(coord[0]) + ',0.0 '
                coordStr += str(order['targetCoords'][0][1]) + ',' + str(order['targetCoords'][0][0]) + ',0.0 '
                origGeom.text = coordStr[:-1]
                unfillGeom.text = coordStr[:-1]
                tree.write('out\\orders\\targetOrder_{0}.xml'.format(order['orderId']))

            elif not(useTargetPolys):
                id.text = 'Grid_' + str(order['orderId'])
                coordStr = ''
                for coord in order['gridCoords']:
                    coordStr += str(coord[1]) + ',' + str(coord[0]) + ',0.0 '
                coordStr += str(order['gridCoords'][0][1]) + ',' + str(order['gridCoords'][0][0]) + ',0.0 '
                origGeom.text = coordStr[:-1]
                unfillGeom.text = coordStr[:-1]
                tree.write('out\\orders\\gridOrder_{0}.xml'.format(order['orderId']))
                
            # Open new XML file to remove/replace namespaces and add appropriate header 
            file_path = 'out\\orders\\*Order_{0}.xml'.format(order['orderId'])
            if len(glob.glob(file_path)) > 1:
                print 'WARN: Multiple possible files matching order file name in out\\orders directory.'
            fileName = glob.glob(file_path)[0]
            file = open(fileName,'r')
            fileData = [line for line in file]
            file.close()
            fileData[0] = fileData[0].replace(':ns0','')
            fileData[0] = fileData[0].replace('ns0:','')

            file = open(fileName,'w')
            file.write('<?xml version="1.0" encoding="utf-8"?>' + '\n')

            for i,line in enumerate(fileData):
                fileData[i] = fileData[i].replace('ns0:','')
                if i < 14:
                    fileData[i] = fileData[i].replace('q2:','q1:')
                if '<XSDOrder' in fileData[i]:
                    fileData[i] = '<XSDOrder xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://com.orbitlogic.schemas">\n'
                if 'cs="," decimal="."' in fileData[i]:
                    fileData[i] = fileData[i].replace('cs="," decimal="."','decimal="." cs=","')
                if 'xsi:type="q1:XSDMultiPolygon"' in fileData[i]:
                    fileData[i] = fileData[i].replace('Geometry xsi:','Geometry xmlns:q1="http://www.opengis.net/gml" xsi:')
                elif 'xsi:type="q2:XSDMultiPolygon"' in fileData[i]:
                    fileData[i] = fileData[i].replace('Geometry xsi:','Geometry xmlns:q2="http://www.opengis.net/gml" xsi:')
                file.write(fileData[i])

            file.close()

    elif isPoint:
        tree = ET.parse('bin\\pointOrderTemplate.xml')
        root = tree.getroot()

        orderCreationOutput = json.loads(orderCreationOutput)

        id = root.find('{http://com.orbitlogic.schemas}id')
        origGeomLon = root.find('{http://com.orbitlogic.schemas}originalGeometry/{http://com.orbitlogic.schemas}longitude')
        origGeomLat = root.find('{http://com.orbitlogic.schemas}originalGeometry/{http://com.orbitlogic.schemas}latitude')
        unfillGeomLon = root.find('{http://com.orbitlogic.schemas}unfulfilledGeometry/{http://com.orbitlogic.schemas}longitude')
        unfillGeomLat = root.find('{http://com.orbitlogic.schemas}unfulfilledGeometry/{http://com.orbitlogic.schemas}latitude')
        minDuration = root.find('{http://com.orbitlogic.schemas}minDuration')

        for order in orderCreationOutput:
            id.text = 'Point_' + str(order['orderId'])
            origGeomLon.text = str(order['centerLon'])
            origGeomLat.text = str(order['centerLat'])
            unfillGeomLon.text = str(order['centerLon'])
            unfillGeomLat.text = str(order['centerLat'])
            minDuration.text = getMinDuration(float(order['squareLength']),float(order['coverage']))
            tree.write('out\\orders\\pointOrder_{0}.xml'.format(order['orderId']))

            file = open('out\\orders\\pointOrder_{0}.xml'.format(order['orderId']),'r')
            fileData = [line for line in file]
            file.close()

            file = open('out\\orders\\pointOrder_{0}.xml'.format(order['orderId']),'w')
            file.write('<?xml version="1.0" encoding="utf-8"?>' + '\n')

            for i,line in enumerate(fileData):
                fileData[i] = fileData[i].replace('ns0:','')
                if '<XSDOrder' in fileData[i]:
                    fileData[i] = '<XSDOrder xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="http://com.orbitlogic.schemas">\n'
                file.write(fileData[i])

            file.close()
