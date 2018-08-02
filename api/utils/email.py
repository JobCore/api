from django.core.mail import EmailMultiAlternatives
import os
from django.template.loader import get_template
from django.template import Context
import requests

NOTIFICATIONS_ENABLED = (os.environ.get('ENABLE_NOTIFICATIONS') == 'true')

def send_email_message(slug, to, data={}):
    template = get_template_content(slug, data)
    if NOTIFICATIONS_ENABLED:
        return requests.post(
            "https://api.mailgun.net/v3/mailgun.jobcore.co/messages",
            auth=("api", os.environ.get('MAILGUN_API_KEY')),
            data={
                "from": "Excited User <mailgun@mailgun.jobcore.co>",
                "to": to,
                "subject": template['subject'],
                "text": template['text'],
                "html": template['html']
            })
        
def get_template_content(slug, data={}):
    plaintext = get_template(slug+'.txt')
    htmly     = get_template(slug+'.html')
    #d = Context({ 'username': username })
    con = {
        'APP_URL': os.environ.get('APP_URL'),
        'COMPANY_NAME': 'JobCore',
        'COMPANY_LEGAL_NAME': 'JobCore LLC',
        'COMPANY_ADDRESS': '270 Catalonia, Coral Gables, 33134',
        'LINK': os.environ.get('APP_URL')
    }
    z = con.copy()   # start with x's keys and values
    z.update(data)
    return {
        "text": plaintext.render(z),
        "html": htmly.render(z),
        "subject": get_template_subject(slug)
    }
    
def get_template_subject(slug):
    subjects = {
        "invite_to_jobcore": "You are invited to JobCore",
        "invite_to_shift": "You have been specifically invited to a Job",
        "new_shift": "New Job Waiting at JobCore",
        "updated_shift": "Job updated at JobCore",
        "password_reset": "JobCore Password Reset"
    }
    if slug in subjects:
        return subjects[slug]
    else:
        raise ValueError('Invalid template slug: No subject found')