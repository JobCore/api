from rest_framework import serializers
from api.serializers import profile_serializer
from api.models import Badge, Position, JobCoreInvite, Rate, AvailabilityBlock

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        exclude = ()
        
class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        exclude = ()
        
class JobCoreInviteGetSerializer(serializers.ModelSerializer):
    sender = profile_serializer.ProfileGetSerializer()

    class Meta:
        model = JobCoreInvite
        exclude = ()

class JobCoreInvitePostSerializer(serializers.ModelSerializer):

    class Meta:
        model = JobCoreInvite
        exclude = ()
        
    def validate(self,data):
        error = True;
        try:
            user = User.objects.get(email=data["email"])
            if(user): 
                raise ValidationError("The user is already registered in jobcore")
        except User.DoesNotExist:
            error = False
        
        try:
            user = JobCoreInvite.objects.get(sender=self.context['request'].user.id, email=data["email"])
            if(user):
                raise ValidationError("User with this email has already been invited")
        
        except User.DoesNotExist:
            error = False
            
        if(error):
            raise ValidationError("Uknown error on the request") 
        
        return data
        
    def create(self, validated_data):
        # TODO: send email message not working
        invite = JobCoreInvite(**validated_data)
        invite.save()
        
        notifier.notify_jobcore_invite(invite)
        
        return invite
        
class RateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rate
        exclude = ()
        
    def validate(self, data):

        current_user = self.context['request'].user;
        data["sender"] = current_user.profile

        if 'shift' not in data:
            raise serializers.ValidationError('You need to speficy the shift related to this rating')
            
        # if it is an employee
        if(current_user.profile.employee != None):
            if 'employee' in data:
                raise serializers.ValidationError('Only employers can rate talents')
                
            try:
                rate = Rate.objects.get(shift=data["shift"].id, employer=data["employer"].id)
                raise serializers.ValidationError("You have already rated this employer for this shift")
            except Rate.DoesNotExist:
                pass
            except Rate.MultipleObjectsReturned:
                raise serializers.ValidationError("You have already rated this talent for this shift")
                
        # if it is an employer
        elif(current_user.profile.employer != None):
            if 'employer' in data:
                raise serializers.ValidationError('Only talents can rate employers')
            
            if data["shift"].employer.id != current_user.profile.employer.id:
                raise serializers.ValidationError('As an employer, you can only rate talents that have work on your own shifts')
                
            try:
                rate = Rate.objects.get(shift=data["shift"].id, employee=data["employee"].id)
                raise serializers.ValidationError("You have already rated this talent for this shift")
            except Rate.DoesNotExist:
                pass
            except Rate.MultipleObjectsReturned:
                raise serializers.ValidationError("You have already rated this talent for this shift")
                
        
        return data

class AvailabilityBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityBlock
        exclude = ()