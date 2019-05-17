from rest_framework import serializers
from api.utils import notifier
from api.models import Rate, Shift, Clockin, Venue
from django.db.models import Avg, Count
from api.serializers.position_serializers import PositionSmallSerializer

#
# NESTED
#


class VenueGetSmallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = ('title', 'id')


class ShiftGetSmallSerializer(serializers.ModelSerializer):
    position = PositionSmallSerializer(read_only=True)

    class Meta:
        model = Shift
        fields = ('id', 'position', 'venue')

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

    def validate_rating(self, rating):
        if not 0 <= float(rating) <= 5:
            raise serializers.ValidationError('Invalid rating number')

        return rating

    def validate(self, data):
        current_user = self.context['request'].user
        data["sender"] = current_user.profile

        if 'shift' not in data:
            raise serializers.ValidationError(
                'You need to speficy the shift related to this rating')

        # if it is a talent rating an employer
        if current_user.profile.employee_id is not None:
            if 'employee' in data:
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
            if 'employer' in data:
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

        new_ratings = (
            obj.__class__.objects  # hack: necesitamos acceder al manager
            .aggregate(
                new_avg=Avg('rate__rating'),
                new_total=Count('rate__id')
            )
        )

        obj.total_ratings = new_ratings['new_total']
        obj.rating = new_ratings['new_avg']
        obj.save()

        notifier.notify_new_rating(rate)

        return rate
