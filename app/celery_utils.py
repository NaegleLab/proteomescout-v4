from celery.schedules import crontab

def init_celery(celery, app):
    celery.conf.update(app.config)

    celery.conf.update(
        enable_utc = False,
        timezone = 'America/New_York', 
        broker_pool_limit = 10, 
    )

    #celery.conf.beat_schedule = {"run-me-on_wednesday": {
    #    "task": "scripts.export.test_task.test",
    #    "schedule": crontab(minute=29, hour=0, day_of_week='wednesday'),
    #    "args": ("hello",)
    #    }
    #}
    celery.conf.beat_schedule = {
    # other tasks here...
        'send-log-email-every-day': {
            'task': 'app.utils.email.send_email_with_logs',  # replace with the actual name of your task
            #'schedule': crontab(minute='*/10'), 
            'schedule': crontab(minute='0', hour='*/6'),  # execute every 6 hours'schedule'
            'args': ('zxa7aw@virginia.edu', 'Daily Log Email', 'Here are the logs for today.'),  # replace with your actual arguments
            # Set email to whoever is primarily responsible for app
        },
    }
    
    
    # celery.conf.beat_schedule = {"run-me-every-ten-seconds": {
    #     "task": "scripts.export.test_task.test",
    #     "schedule": 10.0,
    #     "args": ("hello",)
    #     }
    # }

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
