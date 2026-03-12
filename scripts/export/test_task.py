from app import celery

@celery.task
def test(arg):
    print(arg)