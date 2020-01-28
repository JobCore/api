from rest_framework import serializers
from api.utils import notifier
from api.models import Rate, Shift, Clockin, Venue, Employer, Profile, User
from django.db.models import Avg, Count
from api.serializers.position_serializer import PositionSmallSerializer

#
# NESTED
#

class UserGetTinySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')

class VenueGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = ('title', 'id')


class EmployerGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employer
        fields = ('title', 'id', 'picture', 'rating', 'total_ratings')


class ShiftGetSmallSerializer(serializers.ModelSerializer):
    position = PositionSmallSerializer(read_only=True)
    employer = EmployerGetSmallSerializer(read_only=True)

    class Meta:
        model = Shift
        fields = ('id', 'position', 'venue', 'employer', 'starting_at', 'ending_at')

class ProfileGetSmallSerializer(serializers.ModelSerializer):
    user = UserGetTinySerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ('picture','user')

#
# MAIN
#


class RatingGetSerializer(serializers.ModelSerializer):
    shift = ShiftGetSmallSerializer(read_only=True)
    sender = ProfileGetSmallSerializer(read_only=True)

    class Meta:
        model = Rate
        exclude = ()


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rate
        exclude = ()

    def validate_rating(self, rating):
        if not 0 <= float(rating) <= 5:
            raise serializers.ValidationError('Rating has to be between 0 and 5')

        return rating

    def validate(self, data):
        current_user = self.context['request'].user
        data["sender"] = current_user.profile

        if 'shift' not in data:
            raise serializers.ValidationError(
                'You need to speficy the shift related to this rating')

        if 'rating' not in data:
            raise serializers.ValidationError(
                'You need to speficy a rating score')

        # if it is a talent rating an employer
        if current_user.profile.employee_id is not None:
            if 'employee' in data and data['employee'] is not None:
                raise serializers.ValidationError(
                    'Only employers can rate talents')

            try:
                Clockin.objects.get(
                    shift=data["shift"],
                    employee=current_user.profile.employee
                )
            except Clockin.DoesNotExist:
                raise serializers.ValidationError(
                    "You have not worked in this shift yet, "
                    "no clockins have been found")
            except Clockin.MultipleObjectsReturned:
                pass

            try:
                Rate.objects.get(
                    shift_id=data["shift"].id,
                    employer_id=data["employer"].id,
                    sender_id=current_user.profile.id
                )
                raise serializers.ValidationError(
                    "You have already rated this employer for this shift")
            except Rate.DoesNotExist:
                pass
            except Rate.MultipleObjectsReturned:
                raise serializers.ValidationError(
                    "You have already rated this employer for this shift")

        # if it is an employer rating a talent
        elif current_user.profile.employer_id is not None:
            if 'employer' in data and data['employer'] is not None:
                raise serializers.ValidationError(
                    'Only talents can rate employers')

            if data["shift"].employer.id != current_user.profile.employer.id:
                raise serializers.ValidationError(
                    'As an employer, you can only rate talents '
                    'that have work on your own shifts')

            try:
                # unused clockin
                Clockin.objects.get(
                    shift=data["shift"], employee=data["employee"].id)
            except Clockin.DoesNotExist:
                raise serializers.ValidationError(
                    'This talent has not worked on this shift, '
                    'no clockins have been found')
            except Clockin.MultipleObjectsReturned:
                pass

            try:
                # unused rate
                Rate.objects.get(
                    shift=data["shift"].id,
                    employee=data["employee"].id)
                raise serializers.ValidationError(
                    "You have already rated this talent for this shift")
            except Rate.DoesNotExist:
                pass
            except Rate.MultipleObjectsReturned:
                raise serializers.ValidationError(
                    "You have already rated this talent for this shift")

            if 'comments' not in data or data['comments'] == '' or len(data['comments']) < 50:
                raise serializers.ValidationError(
                    "The rating must have a comment of a least 50 characters")

        return data

    def create(self, validated_data):

        rate = Rate(**validated_data)
        rate.save()

        obj = None

        if rate.employer_id is not None:
            obj = rate.employer
        elif rate.employee_id is not None:
            obj = rate.employee
        else:
            raise AssertionError('Unbound rate!')

        notifier.notify_new_rating(rate)

        return rate
