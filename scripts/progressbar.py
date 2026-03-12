import sys
import datetime

class ProgressBar(object):

    def __init__(self, min_value = 0, max_value = 100, width = 50):
        self.max_value = max_value
        self.min_value = min_value
        self.value = min_value

        self.width = width

    def start(self):
        self.start_time = datetime.datetime.now()
        sys.stderr.write( "\n" )
        self.update(0)

    def estimate_time(self, percent):
        if percent == 0:
            return "Est..."

        n = datetime.datetime.now()
        delta = n - self.start_time
        ts = delta.total_seconds()
        tt = ts / percent
        tr = tt - ts

        H = int(tr / 3600)
        tr -= H * 3600
        M = int(tr / 60)
        tr -= M * 60
        S = int(tr)

        time_remaining = "%d:%02d:%02d" % ( H, M, S )
        return time_remaining

    def update(self, value):
        self.value = value

        percent = float(self.value - self.min_value) / float(self.max_value - self.min_value)
        bar_cnt = int( self.width * percent )

        bar_str = "=" * bar_cnt
        bar_str += " " * (self.width - bar_cnt)

        percent_str = "%0.2f" % (100.0 * percent)
        time_remaining = self.estimate_time(percent)

        sys.stderr.write( "\r|%s| %6s%% | %s           " % (bar_str, percent_str, time_remaining) )

    def finish(self):
        self.update(self.max_value)
        bar_str = "=" * self.width
        sys.stderr.write( "\r|%s| 100.00%% | Done.            \n" % (bar_str) )