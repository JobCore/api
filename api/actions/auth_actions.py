import pytz
from datetime import datetime, timedelta
from api.models import AvailabilityBlock

def create_shift_invites_from_jobcore_invites(jc_invites, employee):
    shift_invites = []
    for invite in jc_invites:
        if invite.shift.starting_at > timezone.now():
            invite = ShiftInvite(sender=invite.sender, shift=invite.shift, employee=employee)
            invite.save()
            shift_invites.insert(0,invite)
            #notifier.notify_invite_accepted(invite)
    jc_invites.delete()
    return shift_invites