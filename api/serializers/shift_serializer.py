import pytz
utc=pytz.UTC
from datetime import datetime
from api.serializers import other_serializer, venue_serializer, employer_serializer, employee_serializer, favlist_serializer
from rest_framework import serializers
from api.utils import notifier
from django.db.models import Q
from api.models import Shift, ShiftInvite, ShiftApplication, Employee, ShiftEmployee

class ShiftSerializer(serializers.ModelSerializer):
    # starting_at = DatetimeFormatField(required=False)
    # ending_at = DatetimeFormatField(required=False)
    allowed_from_list = serializers.ListField(write_only=True, required=False)
    employer = employer_serializer.EmployerGetSmallSerializer(read_only=True)

    class Meta:
        model = Shift
        exclude = ()
        
    def has_sensitive_updates(self, new_data, old_data=None):
        sensitive_fields = ['starting_at','ending_at','venue', 'minimum_hourly_rate', 'status']
        for key in new_data:
            if key in sensitive_fields:
                if old_data is None:
                    return True
                elif old_data is not None and new_data[key] != old_data[key]:
                    return True
        
        return False
        
    # TODO: Validate that only draft shifts can me updated
    def update(self, shift, validated_data):
        
        if ('status' in validated_data):
            if validated_data['status'] != 'DRAFT' and validated_data['status'] != 'CANCELLED' and shift.status != 'DRAFT':
                raise serializers.ValidationError('Only draft shifts can be edited')
        else:
            if shift.status != 'DRAFT':
                raise serializers.ValidationError('Only draft shifts can be edited')
        
        
        # Sync employees
        if 'allowed_from_list' in validated_data:
            current_favlists = shift.allowed_from_list.all().values_list('id', flat=True)
            new_favlists = validated_data['allowed_from_list']
            for favlist in current_favlists:
                if favlist not in new_favlists:
                    shift.allowed_from_list.remove(favlist)
            for favlist in new_favlists:
                if favlist not in current_favlists:
                    shift.allowed_from_list.add(favlist)
            validated_data.pop('allowed_from_list')
            
        old_shift = Shift.objects.get(pk=shift.id)
        old_data = {
            "starting_at": old_shift.starting_at,
            "ending_at": old_shift.ending_at,
            "position": old_shift.position,
            "status": old_shift.status,
            "minimum_hourly_rate": old_shift.minimum_hourly_rate,
            "venue": old_shift.venue.title
        }
        
        # before updating the shift I have to let the employees know that the shift is no longer available
        if self.has_sensitive_updates(validated_data, old_data) and shift.status == 'DRAFT':
            notifier.notify_shift_update(user=self.context['request'].user, shift=shift, status='being_cancelled', old_data=old_shift)

        # now i can finally update the shift
        Shift.objects.filter(pk=shift.id).update(**validated_data)
        
        # I have to delete all previous employes and invite all the new prospects
        if self.has_sensitive_updates(validated_data, old_data):
            
            notifier.notify_shift_update(user=self.context['request'].user, shift=shift, status='being_updated', old_data=old_shift)
            # delete all accepeted employees
            if validated_data['status'] in ['DRAFT'] or shift.status in ['DRAFT']:
                ShiftInvite.objects.filter(shift=shift).delete()
                ShiftApplication.objects.filter(shift=shift).delete()
                shift.candidates.clear()
                shift.employees.clear()

        return shift

class ShiftCandidatesSerializer(serializers.ModelSerializer):
    candidates = serializers.ListField(write_only=True, required=False)
    employees = serializers.ListField(write_only=True, required=False)

    class Meta:
        model = Shift
        exclude = ()
        
    def validate(self, data):
        shift = Shift.objects.get(id=self.instance.id)
        if ('status' in data and data['status'] != 'OPEN') and shift.status != 'OPEN':
            raise serializers.ValidationError('This shift is not opened for applicants')
            
        return data

    def update(self, shift, validated_data):
        talents_to_notify = { "accepted": [], "rejected": [] }
        # Sync candidates
        if 'candidates' in validated_data:
            current_candidates = shift.candidates.all()
            new_candidates = Employee.objects.filter(id__in=validated_data['candidates'])
            for employee in current_candidates:
                if employee not in new_candidates:
                    ShiftApplication.objects.filter(employee__id=employee.id, shift__id=shift.id).delete()
            for employee in new_candidates:
                if employee not in current_candidates:
                    ShiftApplication.objects.create(employee=employee, shift=shift)
            validated_data.pop('candidates')
        
        
        # Sync employees
        if 'employees' in validated_data:
            current_employees = shift.employees.all()
            new_employees = Employee.objects.filter(id__in=validated_data['employees'])
            for employee in current_employees:
                if employee not in new_employees:
                    talents_to_notify["rejected"].append(employee)
                    ShiftEmployee.objects.filter(employee__id=employee.id, shift__id=shift.id).delete()
            for employee in new_employees:
                if employee not in current_employees:
                    talents_to_notify["accepted"].append(employee)
                    ShiftEmployee.objects.create(employee=employee, shift=shift)
            validated_data.pop('employees')
            
        notifier.notify_shift_candidate_update(user=self.context['request'].user, shift=shift, talents_to_notify=talents_to_notify)

        return shift
            
class ShiftPostSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shift
        exclude = ()

class ShiftGetSmallSerializer(serializers.ModelSerializer):
    venue = venue_serializer.VenueGetSmallSerializer(read_only=True)
    position = other_serializer.PositionSerializer(read_only=True)
    employer = employer_serializer.EmployerGetSerializer(read_only=True)

    class Meta:
        model = Shift
        exclude = ('maximum_allowed_employees','minimum_allowed_rating', 'allowed_from_list','required_badges','candidates','employees',
        'rating','application_restriction','updated_at')

class ShiftGetSerializer(serializers.ModelSerializer):
    venue = venue_serializer.VenueSerializer(read_only=True)
    position = other_serializer.PositionSerializer(read_only=True)
    candidates = employee_serializer.EmployeeGetSerializer(many=True, read_only=True)
    employees = employee_serializer.EmployeeGetSerializer(many=True, read_only=True)
    required_badges = other_serializer.BadgeSerializer(many=True, read_only=True)
    allowed_from_list = favlist_serializer.FavoriteListGetSerializer(many=True, read_only=True)

    class Meta:
        model = Shift
        exclude = ()

class ShiftInviteSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShiftInvite
        exclude = ()
        
    def create(self, validated_data):
        
        # TODO: send email message not working
        invite = ShiftInvite(sender=validated_data['sender'], shift=validated_data['shift'], employee=validated_data['employee'])
        invite.save()
        
        # TODO: send email message not working
        notifier.notify_single_shift_invite(invite)
        
        return invite

class ShiftInviteGetSerializer(serializers.ModelSerializer):
    shift = ShiftGetSmallSerializer(many=False, read_only=True)

    class Meta:
        model = ShiftInvite
        exclude = ()

class ShiftApplicationSerializer(serializers.ModelSerializer):
    invite = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ShiftApplication
        exclude = ()
        
    def validate(self, data):
        
        #validate that you have not applied before
        try:
            application = ShiftApplication.objects.get(shift=data["shift"], employee=data["employee"])
            
            invite = ShiftInvite.objects.get(id=data["invite"])
            if invite.status == 'PENDING':
                invite.delete()
            
            raise serializers.ValidationError("You have already applied to this shift")
        except ShiftApplication.DoesNotExist:
            pass
        
        #get related shift    
        shift = data["shift"]
        
        #validate that is accepting applications
        if shift.status != 'OPEN':
            raise serializers.ValidationError("This shift is not open for new applications anymore")
            
        #validate that the shift has not passed
        present = utc.localize(datetime.now())
        if(shift.starting_at < present):
            raise serializers.ValidationError("This shift has already passed: "+shift.starting_at.strftime("%Y-%m-%d %H:%M:%S")+ " < "+present.strftime("%Y-%m-%d %H:%M:%S"))
            
        return data
            
    def create(self, validated_data):
        
        if validated_data['shift'].employer.automatically_accept_from_favlists == True:
            #automatically accept
            pass
        else:
            application = ShiftApplication(shift=validated_data['shift'], employee=validated_data['employee'])
            application.save()
        
        return application
        
class ApplicantGetSerializer(serializers.ModelSerializer):
    employee = employee_serializer.EmployeeGetSerializer()
    shift = ShiftGetSerializer()

    class Meta:
        model = ShiftApplication
        exclude = ()

class ApplicantGetSmallSerializer(serializers.ModelSerializer):
    employee = employee_serializer.EmployeeGetSmallSerializer()
    shift = ShiftGetSmallSerializer()

    class Meta:
        model = ShiftApplication
        exclude = ()