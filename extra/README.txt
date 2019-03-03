Description:
	-createGrids generates a set of grid quares of configurable length/width from a target area

Prerequisites:
	-Python 2.7
	-The following python libraries downloaded (steps for each download are included):
		-numpy:
			-run "pip install numpy"
		-navpy
			-run "pip install -e git+https://github.com/NavPy/NavPy#egg=NavPy"
		-shapely
			-run "pip install wheel" to install wheels package			
			-download Shapely-1.6.4.post1-cp27-cp27m-win32.whl from https://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely
			-run "pip install [PATH TO FILE]\Shapely-1.6.4.post1-cp27-cp27m-win32.whl" to install shapely package

Usage:
	-open a cmd prompt
	-run "python main.py '[TAGRET LAT/LONG]' '[GRID WIDTH]' '[GRID HEIGHT]' 0 1"
	-an out.json file will be created in the same directory as the createGrids.py file

	*first three arguments are entered as strings, last two arguments are entered as boolean 0 or 1
	*target lat/long is entered as decimal degrees in the format "LAT1,LONG1 LAT2,LONG2, LAT3,LONG3 ..."
	*grid width/height are in meters
	*the boolean values dictate the type of grids that will be created, setting the first to 0 and the second to 1 is the most common usage
	*the script will also generate visualization in the STK scenario for the grid collections and data ferry rendezvous based on the CUOutput.json and GridAssignments.json in the bin folder; unless these are needed, any visualization can be ignored

	-example command: "python main.py '32.67163,-117.15004 32.66265,-117.14313 32.67177,-117.13167 32.68055,-117.13993' '250' '250' 0 1"
		