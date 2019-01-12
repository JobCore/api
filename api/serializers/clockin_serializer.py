import decimal
from api.serializers import shift_serializer, employee_serializer
from rest_framework import serializers
from django.db.models import Q
from api.models import Clockin
from api.utils.utils import haversine
from django.utils import timezone
import datetime
NOW = timezone.now()

class ClockinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clockin
        exclude = ()
        
    def validate(self, data):
        # @todo: you need to be part of the shift to be able to clockin or clockout
        if 'started_at' in data:
            if 'latitude_in' not in data or 'longitude_in' not in data:
                raise serializers.ValidationError("You need to specify latitude_in,longitude_in")
            else:
                distance = haversine(data['latitude_in'], data['longitude_in'], data["shift"].venue.latitude, data["shift"].venue.longitude)
                if distance > 0.1: # 0.1 miles
                    raise serializers.ValidationError("You need to be 0.1 miles near "+data["shift"].venue.title+" to clock in and right now your are at "+str(distance)+" miles")
    
            # previous clockin opened
            clockins = Clockin.objects.filter(ended_at=None, employee=data["employee"])
            if len(clockins) > 0:
                raise serializers.ValidationError("You need to clock out first from all your previous shifts before attempting to clockin again")
            
            try:
                validate_clock_in(data["shift"].started_at, data["shift"].ended_at, data["shift"].employer.maximum_clockin_delta_minutes)
            except ValueError as e:
                raise serializers.ValidationError(str(e))

            # check for first checking
            # if data["shift"].employer.maximum_clockin_delta_minutes is not None:
            #     clockins = Clockin.objects.filter(shift__id=data["shift"].id, employee__id=data["employee"].id)
            #     if(len(clockins) == 0):
            #         if NOW > data["shift"].started_at + datetime.timedelta(minutes=data["shift"].employer.maximum_clockin_delta_minutes) :
            #             raise serializers.ValidationError("You can only clockin "+data["shift"].employer.maximum_clockin_delta_minutes+" minutes before or after the shift starting time")
            #         if NOW < data["shift"].started_at + datetime.timedelta(minutes=data["shift"].employer.maximum_clockin_delta_minutes) :
            #             raise serializers.ValidationError("You can only clockin "+data["shift"].employer.maximum_clockin_delta_minutes+" minutes before or after the shift starting time")
            #     else:
            #         if data["shift"].started_at > NOW:
            #             raise serializers.ValidationError("The shift has eneded, you cannot clockin anymore")
            
        elif 'ended_at' in data:
            if 'latitude_out' not in data or 'longitude_out' not in data:
                raise serializers.ValidationError("You need to specify latitude_out,longitude_out")
            else:
                distance = haversine(data['latitude_out'], data['longitude_out'], data["shift"].venue.latitude, data["shift"].venue.longitude)
                if distance > 0.1: # 0.1 miles
                    raise serializers.ValidationError("You need to be 0.1 miles near "+data["shift"].venue.title+" to clock out and right now your are at "+str(distance)+" miles")
        elif 'ended_at' in request.data:

            try:
                clockin = Clockin.objects.get(shift=data["shift"], employee=data["employee"], ended_at=None)
            except Clockin.DoesNotExist:
                raise serializers.ValidationError("You have not clocked in yet or the shift does not exists")
            except Clockin.MultipleObjectsReturned:
                raise serializers.ValidationError("It seems there is more than one clockin without clockout for this shif")
            
            try:
                validate_clock_out(clockin, data["shift"].employer.maximum_clockout_delta_minutes)
            except ValueError as e:
                raise serializers.ValidationError(str(e))
                 
            # if clockin.started_at == None:
            #     raise serializers.ValidationError("You need to clock in first to this shift")
            # if clockin.ended_at != None:
            #     raise serializers.ValidationError("You have already clock out of this shift")
                
            # # check for last clockout
            # if data["shift"].employer.maximum_clockout_delta_minutes is not None:
            #     if data["shift"].ended_at + datetime.timedelta(minutes=data["shift"].employer.maximum_clockin_delta_minutes) < NOW:
            #         raise serializers.ValidationError("You can only clockin "+data["shift"].employer.maximum_clockin_delta_minutes+" minutes before or after the shift starting time")
                
        if 'started_at' in data and 'ended_at' in data:
            raise serializers.ValidationError("You cannot clock in and out at the same time, you need to specify only the started or ended time, but not both at the same time")
            
        if 'started_at' not in data and 'ended_at' not in data:
            raise serializers.ValidationError("You need to specify the started or ended time")
                
        return data

class ClockinGetSerializer(serializers.ModelSerializer):
    shift = shift_serializer.ShiftGetSmallSerializer()
    employee = employee_serializer.EmployeeGetSmallSerializer()

    class Meta:
        model = Clockin
        exclude = ()
        
class ClockinPayrollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clockin
        exclude = ()
        
    def validate(self, data):
        
        if 'started_at' not in data and 'ended_at' not in data:
            raise serializers.ValidationError("You need to specify the started or ended time")
                
        return data


    
def validate_clock_in(started_at, ended_at, maximum_clockin_delta_minutes=None):
    now = timezone.now()
    
    if now > ended_at:
        raise ValueError("You can't Clock In after the Shift ending time")
    
    if maximum_clockin_delta_minutes is None:
        if now < started_at:
           raise ValueError("You can't Clock In before the Shift starting time")
        return
    
    # Delta exists
    delta = datetime.timedelta(minutes=maximum_clockin_delta_minutes)
    if now < started_at - delta:
       raise ValueError("You can't Clock In before the Shift starting time")
           
    if now > started_at + delta:
        raise ValueError("You can't Clock In after the Shift starting time")


def validate_clock_out(clockin_object, maximum_clockout_delta_minutes=None):
    if clockin.started_at == None:    
       raise ValueError("You need to clock in first to this Shift")
    if clockin.ended_at != None:
        raise ValueErrorr("You have already clock out of this Shift")
    
    if maximum_clockout_delta_minutes is None:
        return
    
    now = timezone.now()
    
    if now > clockin.ended_at +  datetime.timedelta(minutes=maximum_clockout_delta_minutes):
        raise ValueError("The system has already clock you out of this Shift")