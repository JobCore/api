import os
from django.db.models import Q
from api.models import Employee, ShiftInvite, Shift, Profile
from api.utils.email import send_email_message, send_fcm_notification
import api.utils.jwt
from rest_framework_jwt.settings import api_settings
API_URL = os.environ.get('API_URL')
EMPLOYER_URL = os.environ.get('EMPLOYER_URL')
EMPLOYEE_URL = os.environ.get('EMPLOYEE_URL')

jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


def get_talents_to_notify(shift):

    talents_to_notify = []
    if shift.status == 'OPEN' and shift.application_restriction != 'SPECIFIC_PEOPLE':
        rating = shift.minimum_allowed_rating
        favorite_lists = shift.allowed_from_list.all()
        talents_to_notify = Employee.objects.filter(
            Q(rating__gte=rating) | Q(rating__isnull=True),
            # the employee gets to pick the minimum hourly rate
            Q(minimum_hourly_rate__lte=shift.minimum_hourly_rate),
            # is accepting invites
            Q(stop_receiving_invites=False)
        )
        if len(favorite_lists) > 0:
            talents_to_notify = talents_to_notify.filter(
                # the employer gets to pick employers only from his favlists
                Q(favoritelist__in=favorite_lists)
            )

    elif shift.status == 'CANCELLED' or shift.status == 'DRAFT':
        talents_to_notify = shift.candidates.all() | shift.employees.all()

    return talents_to_notify


def notify_password_reset_code(user):
    # password reset
    token = api.utils.jwt.internal_payload_encode({
        "user_id": user.id
    })
    send_email_message("password_reset_link", user.email, {
        "link": API_URL + '/api/user/password/reset?token=' + token
    })


def notify_email_validation(user):
    # user registration
    token = api.utils.jwt.internal_payload_encode({
        "user_id": user.id
    })
    send_email_message("registration", user.email, {
        "SUBJECT": "Please validate your email in JobCore",
        "LINK": API_URL + '/api/user/email/validate?token=' + token,
        "FIRST_NAME": user.first_name
    })


def notify_shift_update(user, shift, status='being_updated', old_data=None, pending_invites=[]):
    # automatic notification
    shift = Shift.objects.get(id=shift.id)  # IMPORTANT: override the shift

    talents_to_notify = []
    if shift.application_restriction == 'SPECIFIC_PEOPLE':
        talents_to_notify = Employee.objects.filter(id__in=pending_invites)
    else:
        talents_to_notify = get_talents_to_notify(shift)

    if status == 'being_updated':
        print("Talents to notify: " + str(len(talents_to_notify)))

        for talent in talents_to_notify:

            ShiftInvite.objects.create(
                sender=user.profile,
                shift=shift,
                employee=talent
            )

            send_email_message('new_shift', talent.user.email, {
                "COMPANY": shift.employer.title,
                "POSITION": shift.position.title,
                "DATE": shift.starting_at,
                "DATA": {"type": "shift", "id": shift.id}
            })

            send_fcm_notification("new_shift", talent.user.id, {
                "EMAIL": talent.user.first_name + ' ' + talent.user.last_name,
                "COMPANY": user.profile.employer.title,
                "POSITION": shift.position.title,
                "LINK": EMPLOYER_URL,
                "DATE": shift.starting_at.strftime('%m/%d/%Y'),
                "DATA": {"type": "shift", "id": shift.id}
            })

    if status == 'being_cancelled':
        for talent in talents_to_notify:

            send_email_message('cancelled_shift', talent.user.email, {
                "COMPANY": shift.employer.title,
                "POSITION": shift.position.title,
                "DATE": shift.starting_at,
                "DATA": {"type": "shift", "id": shift.id}
            })

            send_fcm_notification("cancelled_shift", talent.user.id, {
                "EMAIL": talent.user.first_name + ' ' + talent.user.last_name,
                "COMPANY": user.profile.employer.title,
                "POSITION": shift.position.title,
                "LINK": EMPLOYER_URL,
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
            "COMPANY": shift.employer.title,
            "POSITION": shift.position.title,
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
            "COMPANY": shift.employer.title,
            "POSITION": shift.position.title,
            "DATE": shift.starting_at,
            "DATA": {"type": "shift", "id": shift.id}
        })


def notify_jobcore_invite(invite):
    # manual invite

    token = api.utils.jwt.internal_payload_encode({
        "sender_id": invite.sender.id,
        "invite_id": invite.id,
        "user_email": invite.email
    })

    send_email_message("invite_to_jobcore", invite.email, {
        "SENDER": '{} {}'.format(invite.sender.user.first_name, invite.sender.user.last_name),
        "EMAIL": invite.email,
        "COMPANY": invite.sender.user.profile.employer.title,
        "LINK": EMPLOYER_URL + "/invite?token=" + token,
        "DATA": {"type": "invite", "id": invite.id}
    })


def notify_invite_accepted(invite):

    return send_email_message("invite_accepted", invite.sender.user.email, {
        "TALENT": invite.first_name + ' ' + invite.last_name,
        "LINK": EMPLOYER_URL,
        "DATA": {"type": "registration"}
    })


def notify_single_shift_invite(invite):

    # invite.employee.user.email
    send_email_message("invite_to_shift", invite.sender.user.email, {
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
    if rating.employee is not None:
        send_email_message("new_rating", rating.employee.user.email, {
            "SENDER": rating.sender.employer.title,
            "VENUE": rating.shift.venue.title,
            "DATE": rating.shift.starting_at.strftime('%m/%d/%Y'),
            "LINK": EMPLOYEE_URL + '/rating/' + str(rating.id),
            "DATA": {"type": "rating", "id": rating.id}
        })
        # WATCH OUT HERE.
        #
        # send_fcm_notification("new_rating", to.profile.user.id, {
        #     "SENDER": rating.sender.employer.title,
        #     "VENUE": rating.shift.venue.title,
        #     "DATE": rating.shift.starting_at.strftime('%m/%d/%Y'),
        #     "LINK": EMPLOYEE_URL+'/rating/'+str(rating.id),
        #     "DATA": {"type": "rating", "id": rating.id}
        # })

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
