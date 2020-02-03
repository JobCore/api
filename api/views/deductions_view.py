import logging

from django.db.models import BooleanField, IntegerField, Value

from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from api.mixins import EmployerView
from api.models import EmployerDeduction, PreDefinedDeduction
from api.serializers.deductions_serializer import DeductionSerializer

log = logging.getLogger('api.views.deductions_view')


class DeductionAPIView(EmployerView):
    def post(self, request):
        data = request.data.copy()
        data['employer'] = request.user.profile.employer_id
        serializer = DeductionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        deducts1 = PreDefinedDeduction.objects.annotate(lock=Value(True, output_field=BooleanField()),
                                                        employer=Value(self.employer.id, output_field=IntegerField()))\
            .order_by('id')
        deducts2 = EmployerDeduction.objects.filter(employer_id=self.employer.id).order_by('id')
        deductions_data = DeductionSerializer(deducts1, many=True).data + DeductionSerializer(deducts2, many=True).data
        return Response(deductions_data, status=status.HTTP_200_OK)


class DeductionDetailAPIView(ListAPIView, EmployerView):
    def delete(self, request, id):
        queryset = EmployerDeduction.objects.filter(id=id)
        deduction = queryset.first()
        if deduction is None:
            return Response({"detail": "Object Not Found!"}, status=404)

        if deduction.employer.id != self.employer.id:
            return Response({"detail": "Only the owner can delete this Deduction!"}, status=400)

        if deduction.lock is True:
            return Response({"detail": "Lock deduction"}, status=400)

        deduction.delete()

        return Response({"detail": "Object Deleted"}, status=202)

    def put(self, request, id):
        queryset = EmployerDeduction.objects.filter(id=id)
        deduction = queryset.first()
        if deduction is None:
            return Response({"detail": "Object Not Found!"}, status=404)

        if deduction.employer.id != self.employer.id:
            return Response({"detail": "Only the owner can update this Deduction!"}, status=400)

        if deduction.lock is True:
            return Response({"detail": "Lock deduction"}, status=400)

        new_data = request.data.copy()
        # we can't update type or data
        new_data.pop("type", None)
        new_data.pop("lock", None)

        serializer = DeductionSerializer(deduction, data=new_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
