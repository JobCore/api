from rest_framework import serializers
from api.serializers import profile_serializer
from api.utils import notifier
from api.models import Position, Rate, Employer, Shift, Employee, Clockin, Venue


#
# NESTED
#

class PositionSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ('title', 'id')

class VenueGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = ('title','id')

class ShiftGetSmallSerializer(serializers.ModelSerializer):
    position = PositionSmallSerializer(read_only=True)

    class Meta:
        model = Shift
        fields = ('id','position', 'venue')
        
#
# MAIN
#
        
class RatingGetSerializer(serializers.ModelSerializer):
    shift = ShiftGetSmallSerializer(read_only=True)
    
    class Meta:
        model = Rate
        exclude = ()

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rate
        exclude = ()
        
    def validate(self, data):

        current_user = self.context['request'].user;
        data["sender"] = current_user.profile

        if 'shift' not in data:
            raise serializers.ValidationError('You need to speficy the shift related to this rating')
            
        # if it is a talent rating an employer
        if current_user.profile.employee != None:
            if 'employee' in data:
                raise serializers.ValidationError('Only employers can rate talents')
                
            try:
                clockin = Clockin.objects.get(shift=data["shift"], employee=current_user.profile.employee)
            except Clockin.DoesNotExist:
                raise serializers.ValidationError("You have not worked in this shift yet, no clockins have been found")
            except Clockin.MultipleObjectsReturned:
                pass
                
            try:
                rate = Rate.objects.get(shift__id=data["shift"].id, employer__id=data["employer"].id, sender__id = current_user.profile.id)
                raise serializers.ValidationError("You have already rated this employer for this shift")
            except Rate.DoesNotExist:
                pass
            except Rate.MultipleObjectsReturned:
                raise serializers.ValidationError("You have already rated this employer for this shift")
                
        # if it is an employer rating a talent
        elif current_user.profile.employer != None:
            if 'employer' in data:
                raise serializers.ValidationError('Only talents can rate employers')
            
            if data["shift"].employer.id != current_user.profile.employer.id:
                raise serializers.ValidationError('As an employer, you can only rate talents that have work on your own shifts')
                
            try:
                clockin = Clockin.objects.get(shift=data["shift"], employee=data["employee"].id)
            except Clockin.DoesNotExist:
                return Response(validators.error_object('This talent has not worked on this shift, no clockins have been found'), status=status.HTTP_400_BAD_REQUEST)
            except Clockin.MultipleObjectsReturned:
                pass
                
            try:
                rate = Rate.objects.get(shift=data["shift"].id, employee=data["employee"].id)
                raise serializers.ValidationError("You have already rated this talent for this shift")
            except Rate.DoesNotExist:
                pass
            except Rate.MultipleObjectsReturned:
                raise serializers.ValidationError("You have already rated this talent for this shift")
                
        
        return data
        
    def create(self, validated_data):

        rate = Rate(**validated_data)
        rate.save()
        
        if rate.employee != None:
            rate.employee.rating = ((rate.employee.total_ratings * rate.employee.total_ratings) + rate.rating) / (rate.employee.total_ratings+1)
            rate.employee.total_ratings += 1
            rate.employee.save()
            
        if rate.employer != None:
            rate.employer.rating = ((rate.employer.total_ratings * rate.employer.total_ratings) + rate.rating) / (rate.employer.total_ratings+1)
            rate.employer.total_ratings += 1
            rate.employer.save()
            
        
        notifier.notify_new_rating(rate)
        
        return rate