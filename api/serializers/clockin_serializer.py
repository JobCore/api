import decimal
from api.serializers import shift_serializer, employee_serializer
from rest_framework import serializers
from django.db.models import Q
from api.models import Clockin
from api.utils.utils import haversine

class ClockinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clockin
        exclude = ()
        
    def validate(self, data):
        # @todo: you need to be part of the shift to be able to clockin or clockout
        print("Empezando a validar...")
        if 'started_at' in data:
            print("Es un checkin...")    
            if 'latitude_in' not in data or 'longitude_in' not in data:
                raise serializers.ValidationError("You need to specify latitude_in,longitude_in")
            else:
                print("Llego estas latitudes..."+str(data['latitude_in'])+" - "+str(data['latitude_in']))   
                data['latitude_in'] = round(decimal.Decimal(data['latitude_in']), 11)
                data['longitude_in'] = round(decimal.Decimal(data['longitude_in']), 11)
                print("Se transformaron en esto..."+str(data['latitude_in'])+" - "+str(data['latitude_in']))   
                
                distance = haversine(data['latitude_in'], data['longitude_in'], data["shift"].venue.latitude, data["shift"].venue.longitude)
                if distance > 0.1: # 0.1 miles
                    raise serializers.ValidationError("You need to be 0.1 miles near "+data["shift"].venue.title+" to clock in and right now your are at "+str(distance)+" miles")
    
                    
            # previous clockin opened
            clockins = Clockin.objects.filter(ended_at=None, employee=data["employee"])
            if len(clockins) > 0:
                raise serializers.ValidationError("You need to clock out first from all your previous shifts before attempting to clockin again")
                
            # previous clockin opened
            # clockins = Clockin.objects.filter(ended_at=None, employee=data["employee"])
            # if len(clockins) > 0:
            #     raise serializers.ValidationError("You need to clock out first from all your previous shifts before attempting to clockin again")

        elif 'ended_at' in data:
   
            if 'latitude_out' not in data or 'longitude_out' not in data:
                raise serializers.ValidationError("You need to specify latitude_out,longitude_out")
            else:
                data['latitude_out'] = round(decimal.Decimal(data['latitude_out']), 11)
                data['longitude_out'] = round(decimal.Decimal(data['longitude_out']), 11)
                print(data)
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
                
            if clockin.started_at == None:
                raise serializers.ValidationError("You need to clock in first to this shift")
            if clockin.ended_at != None:
                raise serializers.ValidationError("You have already check out of this shift")
                
        print("Terminando la validacion...") 
        
        if 'started_at' in data and 'ended_at' in data:
            raise serializers.ValidationError("You cannot clock in and out at the same time, you need to specify only the started or ended time, but not both at the same time")
            
        if 'started_at' not in data and 'ended_at' not in data:
            raise serializers.ValidationError("You need to specify the started or ended time")
            
                
        print("Fin del validate..") 
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