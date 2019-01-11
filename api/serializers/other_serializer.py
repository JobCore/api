from rest_framework import serializers
from api.serializers import profile_serializer
from api.utils import notifier
from api.models import Badge, Position, JobCoreInvite, Rate, AvailabilityBlock, Employer, Shift, Employee, Clockin,User

class PositionSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ('title', 'id')
        
class EmployerGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        fields = ('title', 'id')

class ShiftGetSmallSerializer(serializers.ModelSerializer):
    position = PositionSmallSerializer(read_only=True)
    employer = EmployerGetSmallSerializer(read_only=True)

    class Meta:
        model = Shift
        fields = ('id','position', 'employer','minimum_hourly_rate','starting_at','ending_at')
        
class RatingGetSerializer(serializers.ModelSerializer):
    shift = ShiftGetSmallSerializer(read_only=True)
    class Meta:
        model = Rate
        exclude = ()


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        exclude = ()

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        exclude = ()

# reset the employee badges
class EmployeeBadgeSerializer(serializers.Serializer):
    badges = serializers.ListField(child=serializers.IntegerField())
    employee = serializers.IntegerField()
        
    def validate(self, data):

        if 'badges' not in data:
            raise serializers.ValidationError('You need to specify the badges')

        if 'employee' not in data:
            raise serializers.ValidationError('You need to specify the employee')
            
        try:
            employee = Employee.objects.get(id=data['employee'])
        except Employee.DoesNotExist:
            return Response(validators.error_object('Employee not found.'), status=status.HTTP_404_NOT_FOUND)
            
        for badge in data['badges']:
            try:
                badge = Badge.objects.get(id=badge)
            except Badge.DoesNotExist:
                raise serializers.ValidationError('Badge not found')
                
        return data
        
    def create(self, validated_data):
        
        Employee.badges.through.objects.filter(employee_id=validated_data['employee']).delete()
        
        employee = Employee.objects.get(id=validated_data['employee'])
        for badge_id in validated_data['badges']:
            badge = Badge.objects.get(id=badge_id)
            employee.badges.add(badge)
        
        return validated_data
        
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
        error = True
        try:
            user = User.objects.get(email=data["email"])
            if(user): 
                raise ValidationError("The user is already registered in jobcore")
        except User.DoesNotExist:
            error = False
        
        try:
            user = JobCoreInvite.objects.get(sender=self.context['request'].user.profile.id, email=data["email"])
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
        
class AvailabilityBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityBlock
        exclude = ()