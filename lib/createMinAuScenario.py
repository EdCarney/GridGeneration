import sys, comtypes, os, re, json, math
from os import listdir
from os.path import isfile, join
from comtypes import COMError
from datetime import datetime
from datetime import timedelta
from point import Point
import xml.etree.ElementTree as et

import comtypes
def _check_version(actual):
	from comtypes.tools.codegenerator import version as required
	if actual != required:
		raise ImportError("Wrong version")
comtypes._check_version = _check_version

from comtypes.client import CreateObject
from comtypes.gen import STKUtil, STKObjects

def createMinAuScenario():

    ######################################################################## START COMMANDS ###############################################################################################

    # Get root directory and create sub directories
    path = os.path.abspath(__file__)
    dir_path = os.path.dirname(path)[:-4]
    serviceRegionPath = dir_path + '\\bin'
    configPath = dir_path + '\\bin'

    # Get values from config file
    parsed_doc = open(configPath + '\\' + 'config.xml', 'r')
    docTree = et.parse(parsed_doc)
    docRoot = docTree.getroot()
    configDict = {
    'startTime':docRoot.find('startTime').text,
    'stopTime':docRoot.find('stopTime').text,
    }
    parsed_doc.close()

    # Get values from grid assignment file
    parsed_doc = open(configPath + '\\' + 'GridAssignments.json', 'r')
    gridAsssignments = json.loads(parsed_doc.readline().strip(''))
    parsed_doc.close()

    # Get values from rendezvous assignment file
    parsed_doc = open(configPath + '\\' + 'CUOutput.json', 'r')
    rendAsssignments = json.loads(parsed_doc.readline().strip(''))
    parsed_doc.close()

    # Open STK Application
    uiApplication = CreateObject("STK11.Application")
    uiApplication.Visible = True
    uiApplication.UserControl = True
    root = uiApplication.Personality2

    # Create a new scenario in STK
    root.NewScenario("MinAu_Scenario")
    scenario = root.CurrentScenario

    # Set STK Scenario Period
    scenario2 = scenario.QueryInterface(STKObjects.IAgScenario)
    scenario2.SetTimePeriod(configDict['startTime'],configDict['stopTime'])

    # Reset scenario time, turn batch graphics on, and disable animation
    root.Rewind()
    root.ExecuteCommand('BatchGraphics * On')
    root.ExecuteCommand('AllowAnimationUpdate * Off')

    ################################################################### AREA TARGET COMMANDS ##########################################################################################

    # Get service region data from config file
    parsed_doc = open(serviceRegionPath + '\\' + 'serviceRegionConfig.xml', "r")
    docTree = et.parse(parsed_doc)
    docRoot = docTree.getroot()
    serviceRegions = docRoot.findall('serviceRegion')
    serviceRegionData = [{'name':serviceRegion.find('name').text,'coords':serviceRegion.find('coordinates').text.split(' ')} for serviceRegion in serviceRegions]
    parsed_doc.close()

    # Create and define service regions
    for serviceRegion in serviceRegionData:
        scenario.Children.New(STKObjects.eAreaTarget,serviceRegion['name'])
        boundaryCommand = 'SetBoundary */AreaTarget/{0} Pattern LatLon {1}'.format(serviceRegion['name'],len(serviceRegion['coords']))
        for coordPair in serviceRegion['coords']:
            boundaryCommand += ' {0} {1}'.format(coordPair.split(',')[0],coordPair.split(',')[1])
        root.ExecuteCommand(boundaryCommand)

    # Set grids to cyan, set taregt area to yellow, turn off all grid labels, and hide centroids
    colorCommand = 'Graphics */AreaTarget/*Grid* SetColor cyan'
    root.ExecuteCommand(colorCommand)
    colorCommand = 'Graphics */AreaTarget/*TargetRegion* SetColor yellow'
    root.ExecuteCommand(colorCommand)
    labelCommand = 'Graphics */AreaTarget/*Grid* Label Show Off'
    root.ExecuteCommand(labelCommand)
    centroidCmd = 'Graphics */AreaTarget/* Centroid Off'
    root.ExecuteCommand(centroidCmd)

    ###################################################################### VEHICLE COMMANDS #############################################################################################

    # Get all unique auvIds and create nested list of auv-specific assignments
    auvIds = set(dict['id'] for dict in gridAsssignments['Problem']['vehicles'])
    auvAssignments = [filter(lambda x: x['vehicleID'] == auvId,gridAsssignments['Assignments']) for auvId in auvIds]
    gridMetaData = gridAsssignments['Problem']['gridDescription']

    # Create reference point for grid assignments and rendezvous
    referencePoint = [float(gridMetaData['swCornerLat']),float(gridMetaData['swCornerLon']),0.0]

    # Make scenario start a datetime object
    scenarioStart = datetime.strptime(configDict['startTime'], '%d %b %Y %H:%M:%S')

    # Create vehicles and set starting waypoint
    for auvId in auvIds:
        addVehicleCmd = 'New / */Ship AUV_{0}'.format(auvId)
        root.ExecuteCommand(addVehicleCmd)
        #addWaypointCmd = 'AddWaypoint */Ship/AUV_{0} DetVelFromTime {1} {2} 0.0 "{3}"'.format(auvId,gridMetaData['swCornerLat'],gridMetaData['swCornerLon'],scenarioStart.strftime('%d %b %Y %H:%M:%S'))
        #root.ExecuteCommand(addWaypointCmd)

    for assignmentList in auvAssignments:
        for assignment in assignmentList:

            gridPoint = Point(
                (int(assignment['gridN']) + 0.5)*float(gridMetaData['squareLength']),
                (int(assignment['gridE']) + 0.5)*float(gridMetaData['squareLength']),
                0.0,
                2,
                referencePoint
                )

            assignmentStart = scenarioStart + timedelta(milliseconds=math.trunc(float(assignment['startTime'])*1000.0))
            assignmentEnd = scenarioStart + timedelta(milliseconds=math.trunc(float(assignment['endTime'])*1000.0))

            addWaypointCmd = 'AddWaypoint */Ship/AUV_{0} DetVelFromTime {1} {2} 0.0 "{3}"'.format(assignment['vehicleID'],gridPoint.lat,gridPoint.long,assignmentStart.strftime('%d %b %Y %H:%M:%S.%f'))
            root.ExecuteCommand(addWaypointCmd)
            addWaypointCmd = 'AddWaypoint */Ship/AUV_{0} DetVelFromTime {1} {2} 0.0 "{3}"'.format(assignment['vehicleID'],gridPoint.lat,gridPoint.long,assignmentEnd.strftime('%d %b %Y %H:%M:%S.%f'))
            root.ExecuteCommand(addWaypointCmd)

    ##################################################################### RENDEZVOUS COMMANDS ###########################################################################################

    # Create dictionaries for rendezvous and data ferry info
    renedzvousPoints = []
    dataFerryPath = []

    for i,rend in enumerate(rendAsssignments['auvSurfacing']['auvId']):
        renedzvousPoints.append({
            'auvId':rend,
            'positionE':rendAsssignments['auvSurfacing']['positionE'][i],
            'positionN':rendAsssignments['auvSurfacing']['positionN'][i],
            'startTime':rendAsssignments['auvSurfacing']['startTime'][i],
            'endTime':rendAsssignments['auvSurfacing']['endTime'][i]
            })

    for i,ferryPath in enumerate(rendAsssignments['ferryPath']['pathD']):
        dataFerryPath.append({
            'waypoint':Point(float(rendAsssignments['ferryPath']['pathN'][i]),float(rendAsssignments['ferryPath']['pathE'][i]),0.3048 * float(rendAsssignments['ferryPath']['pathD'][i]),2,referencePoint),
            'departTime':rendAsssignments['ferryPath']['departTime'][i]
            })

    # Plot rendezvous points as targets
    rendCount = 0
    for rend in renedzvousPoints:
        rendPoint = Point(float(rend['positionN']),float(rend['positionE']),0.0,2,referencePoint)

        rendStart = scenarioStart + timedelta(seconds=int(rend['startTime']))
        rendEnd = scenarioStart + timedelta(seconds=int(rend['endTime']))

        addTargetCmd = 'New / */Target Rendezvous_{0}'.format(rendCount)
        root.ExecuteCommand(addTargetCmd)
        setPosCmd = 'SetPosition */Target/Rendezvous_{0} Geodetic {1} {2} 0.0'.format(rendCount,rendPoint.lat,rendPoint.long)
        root.ExecuteCommand(setPosCmd)
        displayCmd = 'DisplayTimes */Target/Rendezvous_{0} Intervals Add 1 "{1}" "{2}"'.format(rendCount,rendStart.strftime('%d %b %Y %H:%M:%S'),rendEnd.strftime('%d %b %Y %H:%M:%S'))
        root.ExecuteCommand(displayCmd)

        rendCount += 1

    # Create data ferry vehicle and set starting waypoint
    addVehicleCmd = 'New / */Aircraft DataFerry'.format(auvId)
    root.ExecuteCommand(addVehicleCmd)

    # Print out all data ferry lat/long/alt pairs (sketchy but will work for now)
    for point in dataFerryPath:
        departTime = scenarioStart + timedelta(milliseconds=math.trunc(float(point['departTime'])*1000.0))

        addWaypointCmd = 'AddWaypoint */Aircraft/DataFerry DetVelFromTime {0} {1} {2} "{3}"'.format(point['waypoint'].lat, point['waypoint'].long, point['waypoint'].alt * 0.001, departTime.strftime('%d %b %Y %H:%M:%S.%f'))
        root.ExecuteCommand(addWaypointCmd)

        #print '\nLat: {0}\nLon: {1}\nAlt: {2}\nDepart Time: {3}'.format(point['waypoint'].lat,point['waypoint'].long,point['waypoint'].alt,departTime)

    colorCommand = 'Graphics */Target/* SetColor white'
    root.ExecuteCommand(colorCommand)
    colorCommand = 'Graphics */Aircraft/* SetColor white'
    root.ExecuteCommand(colorCommand)

    ######################################################################## END COMMANDS ###############################################################################################

    # Zoom 2D window
    zoomCommand = 'Zoom * Object */AreaTarget/TargetRegion 0.05'
    root.ExecuteCommand(zoomCommand)

    # Turn batch graphics off, and enable animation
    root.ExecuteCommand('BatchGraphics * Off')
    root.ExecuteCommand('AllowAnimationUpdate * On')
    root.Rewind()
