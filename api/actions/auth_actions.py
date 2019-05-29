from django.utils import timezone
from api.models import ShiftInvite


def create_shift_invites_from_jobcore_invites(jc_invites, employee):
    shift_invites = []

    for invite in jc_invites:
        if invite.shift is not None:
            if invite.shift.starting_at > timezone.now():
                invite = ShiftInvite(
                    sender=invite.sender,
                    shift=invite.shift,
                    employee=employee)
                shift_invites.append(invite)
                # notifier.notify_invite_accepted(invite)
    ShiftInvite.objects.bulk_create(shift_invites)
    jc_invites.delete()
    return shift_invites
