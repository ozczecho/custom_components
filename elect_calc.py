from datetime import datetime, timedelta
from collections import namedtuple
import pytz

# {"time" : "2019-03-26 12:50:10", "model" : "Efergy e2 CT", "id" : 58937, "current" : 7.394, "interval" : 6, "battery" : "OK", "learn" : "NO", "mic" : "CHECKSUM"}
# class GrafanaGet():
#     """Object to get grafana rendered image"""

#     def __init__(self, config):
#         """Initialize"""


class ChargeType:
    def __init__(self, type, charge):
        self.Type = type
        self.Charge = charge


def calc(charge_time, tz_name):
    tz = pytz.timezone(tz_name)
    dt = pytz.utc.localize(datetime.strptime(
        charge_time, "%Y-%m-%d %H:%M:%S")).astimezone(tz)
    day = dt.strftime('%a').lower()
    time = dt.strftime('%H:%M:%S')

    if in_between(time, "22:00:00", "07:00:00"):
        return ChargeType("off-peak", 0.16445)
    elif day in ("mon", "tue", "wed", "thu", "fri"):
        if in_between(time, "14:00:00", "20:00:00"):
            return ChargeType("peak", 0.5929)
        elif in_between(time, "07:00:00", "14:00:00") or in_between(time, "20:00:00", "22:00:00"):
            return ChargeType("shoulder", 0.25245)
        else:
            return "unknown"
    elif day in ('sat', 'sun') and in_between(time, "07:00:00", "22:00:00"):
        return ChargeType("shoulder", 0.25245)
    else:
        return "unknown"


def in_between(now, start, end):
    if start <= end:
        return start <= now < end
    else:  # over midnight e.g., 23:30-04:15
        return start <= now or now < end

# Test code
# print ("hello {0}".format(calc("2019-03-26 2:50:10", "Australia/Sydney").Charge)) #TUE, 13:00
# print ("hello {0}".format(calc("2019-03-26 8:50:10", "Australia/Sydney"))) #TUE, 19:00
# print ("hello {0}".format(calc("2019-03-26 12:50:10", "Australia/Sydney"))) #TUE, 23:00
# print ("hello {0}".format(calc("2019-03-30 2:50:10", "Australia/Sydney"))) #SAT 13:00
# print ("hello {0}".format(calc("2019-03-30 12:50:10", "Australia/Sydney"))) #SAT 23:00
# print ("hello {0}".format(calc("2019-03-31 8:50:10", "Australia/Sydney"))) #SUN 19:00
# print ("night"  if in_between("08:20:00","23:00:00","07:00:00") else "day")
