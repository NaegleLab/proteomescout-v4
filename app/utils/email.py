from flask_mail import Message
from app import mail, celery
from flask import render_template
from app import current_app
import os 



def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)




# ...

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[Proteomescout] Reset Your Password',
               sender= "ProteomeScout <proteomescout3mail@gmail.com>", #config['MAIL_USERNAME'],
               recipients=[user.email],
               text_body=render_template('proteomescout/email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('proteomescout/email/reset_password.html',
                                         user=user, token=token))
    

# Making function to send email and registering as a celery task 

@celery.task
def send_email_with_exp_download(recipient, subject, body, attachment_path):
    #sender = current_app.config['ADMINS'][0]
    sender = "ProteomeScout <proteomescout3mail@gmail.com>"
    msg = Message(subject, recipients=[recipient], sender = sender)
    msg.body = body

    with open(attachment_path, "rb") as fp:
        msg.attach(
            filename=os.path.basename(attachment_path),
            content_type="text/csv",
            data=fp.read(),
        )

    mail.send(msg)

@celery.task
def send_email_with_exp_url(recipient, subject, body):
    #sender = current_app.config['ADMINS'][0]
    sender = "ProteomeScout <proteomescout3mail@gmail.com>"
    msg = Message(subject, recipients=[recipient], sender = sender)
    msg.body = body


    mail.send(msg)

# building in log sending function 
## This will only work when deployed in container. Local dev wont have any attachments to send because file structure 
# will provide daily or hourly server logs 
@celery.task
def send_email_with_logs(recipient, subject, body):
    sender = "ProteomeScout <proteomescout3mail@gmail.com>"
    msg = Message(subject, recipients=[recipient], sender=sender)
    msg.body = body

    log_files = ['/var/log/uwsgi.log', '/var/log/uwsgi_debug.log', 
                 '/var/log/nginx.log', '/var/log/nginx_debug.log',
                 '/var/log/celery_worker.log', '/var/log/celery_worker.log']

    #log_files = ['/logs']

    for log_file in log_files:
        try:
            with open(log_file, "rb") as fp:
                msg.attach(
                    filename=os.path.basename(log_file),
                    content_type="text/plain",
                    data=fp.read(),
                )
        except (IOError, FileNotFoundError) as e:
            print(f"Failed to open {log_file}: {e}")

    mail.send(msg)