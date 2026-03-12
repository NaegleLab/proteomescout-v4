import time

def rate_limit(rate=None):
    def wrap(fn):
        def rate_limited_task(*args, **kwargs):
            now = time.clock()
            diff = now - rate_limited_task.last_call_time

            if diff < rate_limited_task.seconds_per_task:
                time.sleep(rate_limited_task.seconds_per_task - diff)

            rval = fn(*args, **kwargs)

            rate_limited_task.last_call_time = now
            return rval

        if rate != None:
            rate_limited_task.seconds_per_task = 1.0 / float(rate)
        else:
            rate_limited_task.seconds_per_task = 0

        rate_limited_task.last_call_time = 0
        return rate_limited_task

    return wrap
