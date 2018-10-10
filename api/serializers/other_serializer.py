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

class AvailabilityBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityBlock
        exclude = ()