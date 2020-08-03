from django.core.mail import EmailMultiAlternatives
from rest_framework.exceptions import APIException
import os
from django.template.loader import get_template
from django.template import Context
from pyfcm import FCMNotification
from api.models import FCMDevice
from django.conf import settings
import requests
from twilio.rest import Client

push_service = None
FIREBASE_KEY = os.environ.get('FIREBASE_KEY')
if(FIREBASE_KEY and FIREBASE_KEY!=''):
    push_service = FCMNotification(api_key=FIREBASE_KEY)


def send_email_message(slug, to, data={}):
    if settings.EMAIL_NOTIFICATIONS_ENABLED:
        template = get_template_content(slug, data, ["email"])
        # print('Email notification '+slug+' sent')
        return requests.post(
            "https://api.mailgun.net/v3/mailgun.jobcore.co/messages",
            auth=(
                "api",
                os.environ.get('MAILGUN_API_KEY')),
            data={
                "from": os.environ.get('MAILGUN_FROM') +
                " <mailgun@mailgun.jobcore.co>",
                "to": to,
                "subject": template['subject'],
                "text": template['text'],
                "html": template['html']}).status_code == 200
    else:
        # print('Email not sent because notifications are not enabled')
        return True

def send_sms(slug, phone_number, data={}):

    template = get_template_content(slug, data, ["sms"])
    # Your Account Sid and Auth Token from twilio.com/console
    # DANGER! This is insecure. See http://twil.io/secure
    TWILLIO_SID = os.environ.get('TWILLIO_SID')
    TWILLIO_SECRET = os.environ.get('TWILLIO_SECRET')
    client = Client(TWILLIO_SID, TWILLIO_SECRET)

    try:
        message = client.messages.create(
            body=template['sms'],
            from_='+15017122661',
            to='+1'+phone_number
        )
        return True
    except Exception:
        return False


def send_fcm(slug, registration_ids, data={}):
    if(len(registration_ids) > 0 and push_service):
        template = get_template_content(slug, data, ["email", "fms"])

        if 'fms' not in template:
            raise APIException(
                "The template " +
                slug +
                " does not seem to have a valid FMS version")

        message_title = template['subject']
        message_body = template['fms']
        if 'DATA' not in data:
            raise Exception("There is no data for the notification")
        message_data = data['DATA']

        result = push_service.notify_multiple_devices(
            registration_ids=registration_ids,
            message_title=message_title,
            message_body=message_body,
            data_message=message_data)

        # if(result["failure"] or not result["success"]):
        #     raise APIException("Problem sending the notification")

        return result
    else:
        return False


def send_fcm_notification(slug, user_id, data={}):
    device_set = FCMDevice.objects.filter(user=user_id)
    registration_ids = [device.registration_id for device in device_set]
    send_fcm(slug, registration_ids, data)


def get_template_content(slug, data={}, formats=None):
    info = get_template_info(slug)

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

    templates = {
        "subject": info['subject']
    }

    if formats is None or "email" in formats:
        plaintext = get_template(info['type'] + '/' + slug + '.txt')
        html = get_template(info['type'] + '/' + slug + '.html')
        templates["text"] = plaintext.render(z)
        templates["html"] = html.render(z)

    if formats is not None and "fms" in formats:
        fms = get_template(info['type'] + '/' + slug + '.fms')
        templates["fms"] = fms.render(z)

    if formats is not None and "sms" in formats:
        sms = get_template(info['type'] + '/' + slug + '.sms')
        templates["sms"] = sms.render(z)

    return templates


def get_template_info(slug):
    subjects = {
        "general": {"type": "utils", "subject": "Important message from JobCore"},
        "invite_to_jobcore": { "type": "employee", "subject": "A job is waiting for you", },
        "invite_to_jobcore_employer": { "type": "invite", "subject": "You have been invited to jobcore", },
        "invite_to_jobcore_employer_accepted": { "type": "invite", "subject": "You have been accepted to a company", },
        "email_validated": {"type": "views", "subject": "Your email has been validated"},
        "reset_password_form": {"type": "views", "subject": "Reset your password"},
        "registration": {"type": "registration", "subject": "Welcome to JobCore"},
        "password_reset_link": {"type": "registration", "subject": "About your password reset"},
        "password_reset": {"type": "registration", "subject": "You password has been reset"},

        # more complex notifications
        "invite_to_shift": {
            "type": "invite",
            "subject": "You have been invited to work on a shift"
        },
        "invite_accepted": {
            "type": "registration",
            "subject": "Someone you invited has join JobCore"
        },
        "cancelled_shift": {
            "type": "shift",
            "subject": "One of your upcoming shifts have been cancelled"
        },
        "updated_shift": {
            "type": "shift",
            "subject": "Atention Needed: One of your upcoming shifts was updated"
        },
        "new_shift": {
            "type": "invite",
            "subject": "There is a new shift waiting for you to apply"
        },
        "new_rating": {
            "type": "rating",
            "subject": "You have received a new rating"
        },
        "applicant_accepted": {
            "type": "shift",
            "subject": "Job application accepted, time to work :)"
        },
        "applicant_rejected": {
            "type": "shift",
            "subject": "Job application rejected, we are sorry :("
        },
    }
    if slug in subjects:
        return subjects[slug]
    else:
        raise ValueError(
            'Invalid template slug: "' +
            slug +
            "' no subject found")
