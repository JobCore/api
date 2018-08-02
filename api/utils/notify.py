from api.models import Employee
from api.utils.email import send_email_message
from rest_framework_jwt.settings import api_settings

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

def get_talents_to_notify(shift):
    talents_to_notify = []
    if shift.status == 'OPEN':
        rating = shift.minimum_allowed_rating
        favorite_lists = shift.allowed_from_list.all()
        if len(favorite_lists) == 0:
            talents_to_notify = Employee.objects.filter(
                rating__gte=rating,
                #the employee gets to pick the minimum hourly rate
                minimum_hourly_rate__lte=shift.minimum_hourly_rate
            )
        else:
            talents_to_notify = Employee.objects.filter(
                rating__gte=rating, 
                #the employer gets to pick employers only from his favlists
                favoritelist__in=favorite_lists,
                #the employee gets to pick the minimum hourly rate
                minimum_hourly_rate__lte=shift.minimum_hourly_rate
            )
    
    return talents_to_notify

def notify_shift_creation(shift, being_created=False):
    talents_to_notify = get_talents_to_notify(shift)
    for talent in talents_to_notify:
        
        #payload = jwt_payload_handler(user)
        #token = jwt_encode_handler(payload)
        
        
        if being_created:
            send_email_message('new_shift', talent.profile.user.email, {
                "shift": shift,
                "talent": talent
            })
        else:
            send_email_message('updated_shift', talent.profile.user.email, {
                "shift": shift,
                "talent": talent
            })