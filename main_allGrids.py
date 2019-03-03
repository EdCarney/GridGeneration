import os, sys
from lib.createGrids import createGrids
from lib.createOrders import createOrders
from lib.createMinAuScenario import createMinAuScenario

path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)
if sys.argv[4]:
    isPoint = int(sys.argv[4])
if sys.argv[5]:
    useTargetPolys = int(sys.argv[5])

#gridVisOutput,orderCreationOutput = createGrids(sys.argv[1],float(sys.argv[2]),float(sys.argv[3]),useTargetPolys)
gridVisOutput = createGrids(sys.argv[1],float(sys.argv[2]),float(sys.argv[3]),useTargetPolys)
#createOrders(orderCreationOutput,isPoint,useTargetPolys)

outFile = open(dir_path + '\\out\\out.json','w')
outFile.write(gridVisOutput)
outFile.close()

if not(isPoint):
    createMinAuScenario()