import datetime, time
import re
from pyqtgraph.graphicsItems.AxisItem import AxisItem

class DateTimeAxisItem(AxisItem):
    def __init__(self, *args, **kwds):
        self.formats = {
            'msec':  ('%H:%M:%s', '%b %d -', ' %b %d, %Y'),
            'sec':   ('%H:%M:%S', '%b %d -', ' %b %d, %Y'),
            'min':   ('%H:%M',    '%b %d -', ' %b %d, %Y'),
            'day':   ('%d',       '%b - ',   '%b, %Y'),
            'month': ('%b',       '%Y -',    ' %Y'),
            'year':  ('%Y',       '',        ''),
        }
        
        sph = 3600
        spd = sph*24
        spm = spd*30
        spy = spd*365
        self.levels = [
            (1,  'year',   spy, 'year'),
            (6,  'month',  spm, 'month'), 
            (3,  'month',  spm, 'month'), 
            (1,  'month',  spm, 'month'), 
            (16, 'day',    spd, 'day'),
            (11, 'day',    spd, 'day'),
            (1,  'day',    spd, 'day'), 
            (12, 'hour',   sph, 'min'),
            (6,  'hour',   sph, 'min'),
            (1,  'hour',   sph, 'min'), 
            (20, 'minute', 60,  'min'),
            (10, 'minute', 60,  'min'),
            (2,  'minute', 60,  'min'), 
            (1,  'minute', 60,  'min'), 
            (20, 'second', 1,   'sec'),
            (10, 'second', 1,   'sec'),
            (2,  'second', 1,   'sec'),
            (1,  'second', 1,   'sec')
        ]
        AxisItem.__init__(self, *args, **kwds)
        
        
    def tickValues(self, minVal, maxVal, size):
        levels = self.levels
        
        # Decide which level to start at
        # todo: make this a bit more clever
        #   - more aesthetic determination of starting level based on size
        startLevel = len(levels)
        rng = maxVal - minVal
        for i, level in enumerate(levels):
            if rng > level[0]*level[2]:
                startLevel = i
                break
        
        tickLevelInds = [startLevel, startLevel+1, startLevel+2]
        
        # If we are at years or seconds, use the superclass method to determine tick levels
        spy = 3600*24*365
        yearLevels = []
        secLevels = []
        if startLevel == 0:
            yearLevelsScaled = AxisItem.tickValues(self, minVal/spy, maxVal/spy, size)
            yearLevels = []
            for yl in yearLevelsScaled:
                if yl[0] > 1:
                    yearLevels.append((yl[0]*spy, [x*spy for x in yl[1]]))
            tickLevelInds = range(3-min(3,len(yearLevels)))
                    
        if len(tickLevelInds) > 0 and tickLevelInds[-1] >= len(levels):
            tickLevelInds = [x for x in tickLevelInds if x < len(levels)] # only keep tick levels >= 1 second
            secLevels = AxisItem.tickValues(self, minVal, maxVal, size)
            secLevels = [x for x in secLevels if x[0] < 1] # only keep second levels smaller than 1 second
            
        
        # date/time of left boundary
        minDate = datetime.datetime.fromtimestamp(minVal)
        maxDate = datetime.datetime.fromtimestamp(maxVal)
        
        tickLevels = []
        for tickLevel in tickLevelInds:
            # Determine starting tick starting point
            minArgs = {'year': 1, 'month': 1, 'day': 1, 'hour': 0, 'minute': 0, 'second': 0}
            args = {}
            for i,level in enumerate(levels):
                k = level[1]
                if level[1] == levels[tickLevel][1] or i >= tickLevel:
                    args[k] = minArgs[k]
                else:
                    args[k] = getattr(minDate, level[1])
                
            #args.update({levels[i][1]: getattr(minDate, levels[i][1]) for i in range(startLevel)})
            tick = datetime.datetime(**args)
            dt = datetime.timedelta(seconds=(levels[tickLevel][0]+0.5)*levels[tickLevel][2])
            #print "start level:", tickLevel, levels[tickLevel][1]
            #print "start args:", args
            #print "start tick:", tick
            #print "dt:", dt

            # make list of ticks
            ticks = []
            while tick <= maxDate:
                if tick >= minDate:
                    # append timestamp for this tick
                    ticks.append(time.mktime(tick.timetuple()))
                # advance tick by one time unit (this is tricky)
                tick = tick + dt
                args.update({levels[i][1]: getattr(tick, levels[i][1]) for i in range(tickLevel+1)})
                tick = datetime.datetime(**args)

            tickLevels.append( (levels[startLevel][0]*levels[startLevel][2], ticks) )
    
        # combine with year/second levels
        return yearLevels + tickLevels + secLevels
    
        
    def tickStrings(self, values, scale, spacing):
        if len(values) == 0:
            return []
        strns = []
        string = None
        if spacing > 3600*24*365:
            string, label1, label2 = self.formats['year']
        elif spacing < 1:
            string, label1, label2 = self.formats['msec']
        for lev in self.levels:
            if spacing == lev[0] * lev[2]:
                string, label1, label2 = self.formats[lev[3]]
        if string is None:
            print("unknown spacing:"), spacing
            
        for x in values:
            try:
                if '%s' in string:
                    sec = time.strftime('%S', time.localtime(x))
                    sec += ("%0.4f" % (x-int(x))).lstrip('0')
                    string = re.sub(r'%s', sec, string)
                    print(x, sec)
                strns.append(time.strftime(string, time.localtime(x)))
                    
            except ValueError:  ## Windows can't handle dates before 1970
                strns.append('')
        try:
            label = time.strftime(label1, time.localtime(min(values)))+time.strftime(label2, time.localtime(max(values)))
        except ValueError:
            label = ''
        self.setLabel(text=label)
        return strns
