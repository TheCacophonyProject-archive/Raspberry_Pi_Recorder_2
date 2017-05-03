import time

def datetimestamp(t = None):
    if t == None:
        return(time.strftime(format('%Y-%m-%d %H:%M:%S%z')))
    else:
        return(time.strftime(format('%Y-%m-%d %H:%M:%S%z'), t))

def timestamp():
    return(time.strftime(format('%H:%M:%S')))
