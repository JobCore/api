import os
from django.db.models import Q
from api.models import Employee, ShiftInvite, Shift, Profile
from api.utils.email import send_email_message, send_fcm_notification, send_sms, send_sms_valdation
import api.utils.jwt
from rest_framework_jwt.settings import api_settings
from django.utils import timezone
from datetime import timedelta
API_URL = os.environ.get('API_URL')
EMPLOYER_URL = os.environ.get('EMPLOYER_URL')
EMPLOYEE_URL = os.environ.get('EMPLOYEE_URL')
EMPLOYEE_REGISTER_URL = "https://jobcore.co/job-seekers-signup/"
BROADCAST_NOTIFICATIONS_BY_EMAIL = os.environ.get('BROADCAST_NOTIFICATIONS_BY_EMAIL')

jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


def get_talents_to_notify(shift):

    talents_to_notify = []
    if shift.status == 'OPEN' and shift.application_restriction != 'SPECIFIC_PEOPLE':

        non_expired_shifts = Shift.objects.filter(
            Q(status__in=["OPEN", "FILLED"]),
            Q(starting_at__range=[shift.starting_at, shift.ending_at]) | Q(ending_at__range=[shift.starting_at, shift.ending_at]) | 
            Q(starting_at__lte=shift.starting_at, ending_at__gte=shift.ending_at)
        )
        print(non_expired_shifts)

        
        rating = shift.minimum_allowed_rating
        favorite_lists = shift.allowed_from_list.all()
       
        talents_to_notify = Employee.objects.filter(
            Q(rating__gte=rating) | Q(rating__isnull=True),
            # the employee gets to pick the minimum hourly rate
            Q(minimum_hourly_rate__lte=shift.minimum_hourly_rate),
            # is accepting invites
            Q(stop_receiving_invites=False),
            # positions not in shift
            Q(positions__id=shift.position.id),
        ).exclude(shift_accepted_employees__in=[s.id for s in non_expired_shifts])
        # exclude the talent if it has other shifts during the same time
       
        
        # print(talents_to_notify)
        if len(favorite_lists) > 0:
            talents_to_notify = talents_to_notify.filter(
                # the employer gets to pick employers only from his favlists
                Q(favoritelist__in=favorite_lists)
            )

    return talents_to_notify


def notify_password_reset_code(user):
    # password reset
    token = api.utils.jwt.internal_payload_encode({
        "user_id": user.id
    })
    send_email_message("password_reset_link", user.email, {
        "link": API_URL + '/api/user/password/reset?token=' + token
    })

    return token


def notify_email_validation(user):
    # user registration
    token = api.utils.jwt.internal_payload_encode({
        "user_id": user.id
    })
    print('notify_email_validation')
    send_email_message("registration", user.email, {
        "SUBJECT": "Please validate your email in JobCore",
        "LINK": API_URL + '/api/user/email/validate?token=' + token,
        "FIRST_NAME": user.first_name
    })
    
def notify_sms_validation(user):
    # user registration
    token = api.utils.jwt.internal_payload_encode({
        "user_id": user.id
    })
    send_sms_valdation(user.profile.phone_number)




def notify_employee_email_validation(user):
    # user registration
    token = api.utils.jwt.internal_payload_encode({
        "user_id": user.id
    })


    send_email_message("registration_employee", user.email, {
        "SUBJECT": "Please validate your email in JobCore",
        "LINK": API_URL + '/api/user/email/validate?token=' + token,
        "FIRST_NAME": user.first_name
    })

    # send_sms_valdation(user.profile.phone_number)

def notify_company_invite_confirmation(user,employer,employer_role):
    # user company invitaiton

    token = api.utils.jwt.internal_payload_encode({
        "user_id": user.id,
        "employer_id": employer.id,
        "employer_role": employer_role
    })
    send_email_message("invite_to_jobcore_employer", user.email, {
        "SENDER": '{} {}'.format(user.first_name, user.last_name),
        "EMAIL": user.email,
        "COMPANY": employer.title,
        "COMPANY_ID": employer.id,
        "COMPANY_ROLE": employer_role,
        "LINK": API_URL + '/api/user/email/company/validate?token=' + token,
        "DATA": {"type": "invite", "id": user.id}
    })


def notify_shift_cancellation(user, shift):
    # automatic notification
    shift = Shift.objects.get(id=shift.id)  # IMPORTANT: override the shift
    talents_to_notify = shift.candidates.all() | shift.employees.all()
    for talent in talents_to_notify:

        send_email_message('cancelled_shift', talent.user.email, {
            "COMPANY": shift.employer.title,
            "POSITION": shift.position.title,
            "DATE": shift.starting_at,
            "DATA": {"type": "shift", "id": shift.id}
        })
 
        send_fcm_notification("cancelled_shift", talent.user.id, {
            "SENDER": '{} {}'.format(
            talent.user.first_name , talent.user.last_name),
            "COMPANY": user.profile.employer.title,
            "POSITION": shift.position.title,
            "LINK": EMPLOYEE_URL,
            "DATE": shift.starting_at.strftime('%m/%d/%Y'),
            "DATA": {"type": "shift", "id": shift.id}
        })
        

def notify_shift_update(user, shift, pending_invites=[]):
    # automatic notification
    shift = Shift.objects.get(id=shift.id)  # IMPORTANT: override the shift

    talents_to_notify = []
    if shift.application_restriction == 'SPECIFIC_PEOPLE':
        talents_to_notify = Employee.objects.filter(id__in=pending_invites)
    else:
        talents_to_notify = get_talents_to_notify(shift)

    for talent in talents_to_notify:

        ShiftInvite.objects.create(
            sender=user.profile,
            shift=shift,
            employee=talent
        )

        if BROADCAST_NOTIFICATIONS_BY_EMAIL == 'TRUE' or shift.application_restriction == 'SPECIFIC_PEOPLE':
            send_email_message('new_shift', talent.user.email, {
                "COMPANY": shift.employer.title,
                "POSITION": shift.position.title,
                "DATE": shift.starting_at,
                "DATA": {"type": "shift", "id": shift.id}
            })

        send_fcm_notification("new_shift", talent.user.id, {
            "SENDER": '{} {}'.format(
            talent.user.first_name , talent.user.last_name),            
            "COMPANY": user.profile.employer.title,
            "POSITION": shift.position.title,
            "LINK": EMPLOYEE_URL,
            "DATE": shift.starting_at.strftime('%m/%d/%Y'),
            "DATA": {"type": "shift", "id": shift.id}
        })

def notify_shift_candidate_update(user, shift, talents_to_notify=[]):

    for talent in talents_to_notify['accepted']:

        send_email_message('applicant_accepted', talent.user.email, {
            "COMPANY": shift.employer.title,
            "POSITION": shift.position.title,
            "DATE": shift.starting_at,
            "DATA": {"type": "shift", "id": shift.id}
        })
        send_fcm_notification('applicant_accepted', talent.user.id, {
            "SENDER": '{} {}'.format(
            talent.user.first_name , talent.user.last_name), 
            "COMPANY": shift.employer.title,
            "POSITION": shift.position.title,
            "LINK": EMPLOYEE_URL,
            "DATE": shift.starting_at,
            "DATA": {"type": "shift", "id": shift.id}
        })

    for talent in talents_to_notify['rejected']:
        send_email_message('applicant_rejected', talent.user.email, {
            "COMPANY": shift.employer.title,
            "POSITION": shift.position.title,
            "DATE": shift.starting_at,
            "DATA": {"type": "shift", "id": shift.id}
        })
        send_fcm_notification('applicant_rejected', talent.user.id, {
            "SENDER": '{} {}'.format(
            talent.user.first_name , talent.user.last_name), 
            "COMPANY": shift.employer.title,
            "POSITION": shift.position.title,
            "LINK": EMPLOYEE_URL,
            "DATE": shift.starting_at,
            "DATA": {"type": "shift", "id": shift.id}
        })


def notify_jobcore_invite(invite, include_sms=False, employer_role=""):
# def notify_jobcore_invite(invite, include_sms=False, is_jobcore_employer=False):
    # manual invite
    token = api.utils.jwt.internal_payload_encode({
        "sender_id": invite.sender.id,
        "invite_id": invite.id,
        "user_email": invite.email
    })
    if invite.employer is not None:

        send_email_message("invite_to_jobcore_employer", invite.email, {
            "SENDER": '{} {}'.format(invite.sender.user.first_name, invite.sender.user.last_name),
            "EMAIL": invite.email,
            "COMPANY": invite.sender.user.profile.employer.title,
            "COMPANY_ID": invite.employer.id,
            "COMPANY_ROLE": employer_role,
            "LINK": EMPLOYER_URL + "/invite?token_invite=" + token + "&employer="+str(invite.employer.id),
            "DATA": {"type": "invite", "id": invite.id}
        })
        
    else:
        send_email_message("invite_to_jobcore", invite.email, {
            "SENDER": '{} {}'.format(invite.sender.user.first_name, invite.sender.user.last_name),
            "EMAIL": invite.email,
            "COMPANY": invite.sender.user.profile.employer.title,
            "LINK": EMPLOYER_URL + "/invite?token_invite=" + token,
            "DATA": {"type": "invite", "id": invite.id}
        })

        if include_sms:
            send_sms("invite_to_jobcore", invite.phone_number)


def notify_invite_accepted(invite):

    return send_email_message("invite_accepted", invite.sender.user.email, {
        "TALENT": invite.first_name + ' ' + invite.last_name,
        "LINK": EMPLOYER_URL,
        "DATA": {"type": "registration"}
    })


def notify_single_shift_invite(invite, withEmail=False):

    # invite.employee.user.email
    if withEmail:
        send_email_message("invite_to_shift", invite.employee.user.email, {
            "SENDER": '{} {}'.format(
                invite.sender.user.first_name, invite.sender.user.last_name),
            "COMPANY": invite.sender.user.profile.employer.title,
            "POSITION": invite.shift.position.title,
            "DATE": invite.shift.starting_at.strftime('%m/%d/%Y'),
            "LINK": EMPLOYEE_URL + '/shift/'+str(invite.shift.id),
            "DATA": {"type": "invite", "id": invite.id}
        })

    send_fcm_notification("invite_to_shift", invite.employee.user.id, {
        "SENDER": '{} {}'.format(
            invite.sender.user.first_name, invite.sender.user.last_name),
        "COMPANY": invite.sender.user.profile.employer.title,
        "POSITION": invite.shift.position.title,
        "DATE": invite.shift.starting_at.strftime('%m/%d/%Y'),
        "LINK": EMPLOYEE_URL + '/shift/'+str(invite.shift.id),
        "DATA": {"type": "invite", "id": invite.id}
    })


def notify_new_rating(rating):
    print('the new rating', rating)
    if rating.employee is not None:
        send_email_message("new_rating", rating.employee.user.email, {
            "SENDER": rating.sender.employer.title,
            "VENUE": rating.shift.venue.title,
            "DATE": rating.shift.starting_at.strftime('%m/%d/%Y'),
            "LINK": EMPLOYEE_URL + '/rating/' + str(rating.id),
            "DATA": {"type": "rating", "id": rating.id}
        })

        send_fcm_notification("new_rating", rating.employee.user.id, {
            "SENDER": rating.sender.employer.title,
            "VENUE": rating.shift.venue.title,
            "RATING": rating.rating,
            "DATE": rating.shift.ending_at.strftime('%m/%d/%Y'),
            "LINK": EMPLOYEE_URL+'/rating/'+str(rating.id),
            "DATA": {"type": "rating", "id": rating.id}
        })

    elif rating.employer is not None:
        employer_users = Profile.objects.filter(
            employer__id=rating.employer.id)
        for profile in employer_users:
            send_email_message("new_rating", profile.user.email, {
                "SENDER": '{} {}'.format(
                    rating.sender.user.first_name,
                    rating.sender.user.last_name),
                "VENUE": rating.shift.venue.title,
                "DATE": rating.shift.starting_at.strftime('%m/%d/%Y'),
                "LINK": EMPLOYEE_URL + '/rating/' + str(rating.id),
                "DATA": {"type": "rating", "id": rating.id}
            })
