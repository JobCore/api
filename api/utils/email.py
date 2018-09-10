from django.core.mail import EmailMultiAlternatives
import os
from django.template.loader import get_template
from django.template import Context
import requests

NOTIFICATIONS_ENABLED = (os.environ.get('ENABLE_NOTIFICATIONS') == 'TRUE')

def send_email_message(slug, to, data={}):
    template = get_template_content(slug, data)
    print('EMAL_SENT: '+slug+' to '+to)
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
        "invite_to_jobcore":{ "type": "employee", "subject": "A job is waiting for you"},
        "invite_to_shift":  { "type": "employee", "subject": "You have been invited to work on a shift"},
        "cancelled_shift":  { "type": "employee", "subject": "One of your upcoming shifts have been cancelled"},
        "new_shift":        { "type": "employee", "subject": "There is a new shift waiting for you to apply"},
        "applicant_accepted":   { "type": "employee", "subject": "Job application accepted, time to work :)"},
        "applicant_rejected":   { "type": "employee", "subject": "Job application rejected, we are sorry :("},
        "password_reset_link":   { "type": "registration", "subject": "About your password reset"},
        "password_reset":   { "type": "registration", "subject": "You password has been reset"},
        "registration":   { "type": "registration", "subject": "Welcome to JobCore"},
        "reset_password_form":   { "type": "views", "subject": "Reset your password"},
        "email_validated":   { "type": "views", "subject": "Your email has been validated"},
    }
    if slug in subjects:
        return subjects[slug]
    else:
        raise ValueError('Invalid template slug: No subject found')