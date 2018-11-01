from django.core.mail import EmailMultiAlternatives
import os
from django.template.loader import get_template
from django.template import Context
from pyfcm import FCMNotification

import requests

NOTIFICATIONS_ENABLED = (os.environ.get('ENABLE_NOTIFICATIONS') == 'TRUE')

FIREBASE_KEY = os.environ.get('FIREBASE_KEY')
push_service = FCMNotification(api_key=FIREBASE_KEY)

def send_email_message(slug, to, data={}):
    template = get_template_content(slug, data)
    print('EMAL_SENT: '+slug+' to '+to)
    if NOTIFICATIONS_ENABLED:
        return requests.post(
            "https://api.mailgun.net/v3/mailgun.jobcore.co/messages",
            auth=("api", os.environ.get('MAILGUN_API_KEY')),
            data={
                "from": os.environ.get('MAILGUN_FROM')+" <mailgun@mailgun.jobcore.co>",
                "to": to,
                "subject": template['subject'],
                "text": template['text'],
                "html": template['html']
            })
            
def send_fcm_notification(slug, registration_ids, data={}):
    if(len(registration_ids) > 0):
        template = get_template_content(slug, data)
        message_title = template['subject']
        message_body = template['text']
        #print(data)
        # if 'data' not in data:
        #     raise Exception("There is no data for the notification")
        data['data'] = {}
            
        message_data = data['data']
        result = push_service.notify_multiple_devices(registration_ids=registration_ids, message_title=message_title, message_body=message_body, data_message=message_data)
        print('FMC_SENT: '+slug+' to '+"".join(map(str, registration_ids)))
        return result
    else:
        print('FMC_SENT: no registration_ids found')
        return False
        
def get_template_content(slug, data={}):
    info = get_template_info(slug)
    
    plaintext = get_template(info['type']+'/'+slug+'.txt')
    html     = get_template(info['type']+'/'+slug+'.html')
    #d = Context({ 'username': username })
    con = {
        'EMPLOYEE_URL': os.environ.get('EMPLOYEE_URL'),
        'EMPLOYER_URL': os.environ.get('EMPLOYER_URL'),
        'API_URL': os.environ.get('API_URL'),
        'COMPANY_NAME': 'JobCore',
        'COMPANY_LEGAL_NAME': 'JobCore LLC',
        'COMPANY_ADDRESS': '270 Catalonia, Coral Gables, 33134'
    }
    z = con.copy()   # start with x's keys and values
    z.update(data)
    return {
        "text": plaintext.render(z),
        "html": html.render(z),
        "subject": info['subject']
    }
    
def get_template_info(slug):
    subjects = {
        "invite_to_jobcore":{ 
            "type": "employee", 
            "subject": "A job is waiting for you", 
        },
        "email_validated":   { "type": "views", "subject": "Your email has been validated"},
        "reset_password_form":   { "type": "views", "subject": "Reset your password"},
        "registration":   { "type": "registration", "subject": "Welcome to JobCore"},
        "password_reset_link":   { "type": "registration", "subject": "About your password reset"},
        "password_reset":   { "type": "registration", "subject": "You password has been reset"},
        
        # more complex notifications
        "invite_to_shift":  { 
            "type": "invite", 
            "subject": "You have been invited to work on a shift"
        },
        "cancelled_shift":  { 
            "type": "shift", 
            "subject": "One of your upcoming shifts have been cancelled"
        },
        "new_shift": { 
            "type": "invite", 
            "subject": "There is a new shift waiting for you to apply"
        },
        "applicant_accepted": { 
            "type": "shift", 
            "subject": "Job application accepted, time to work :)"
        },
        "applicant_rejected": { 
            "type": "application", 
            "subject": "Job application rejected, we are sorry :("
        },
    }
    if slug in subjects:
        return subjects[slug]
    else:
        raise ValueError('Invalid template slug: No subject found')