from navpy import lla2ned, ned2lla
import numpy

class Point(object):
    """
    Object class for points. Arguments on initialization are Var1, Var2, Var3, Type. Type == 1 is LLA, Type == 2 is NED.
    Depending on type Var1, Var2, Var3 are either Lat, Long, Alt or North, East, Down.
    Conversions are done automatically using reference LLA point of defined by referencePoint list [lat,long,alt].
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