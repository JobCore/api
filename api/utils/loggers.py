import logging

_logs = {
    'jobcore:general': logging.getLogger('jobcore:general'),
    'jobcore:hooks': logging.getLogger('jobcore:hooks'),
    'jobcore:clockin': logging.getLogger('jobcore:clockin'),
    'jobcore:shifts': logging.getLogger('jobcore:shifts')
}

def log_debug(context, msg):
    context = 'jobcore:'+context
    print(msg)
    if context in _logs:
        _logs[context].debug(str(msg))
    else:
        raise Exception('Invalid logger name: '+context)
