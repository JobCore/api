from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from api.models import *
from api.utils import validators
from api.serializers import documents_serializer
from django.http import JsonResponse
from api.mixins import EmployeeView
import cloudinary.uploader


class EmployeeDocumentAPI(EmployeeView):

    def post(self, request):
        if 'document' not in request.FILES:
            return Response(
                validators.error_object('No Document'),
                status=status.HTTP_400_BAD_REQUEST)

        try:
            result = cloudinary.uploader.upload(
                request.FILES['document'],
                public_id='profile' + str(self.request.user.id),
                tags=['i9_document'],
                use_filename=1,
                unique_filename=1,
                resource_type='auto'
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
        request.data['document'] = result['secure_url']
        serializer = documents_serializer.EmployeeDocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        documents = EmployeeDocument.objects.filter(employee_id=self.employee.id)
        data = documents_serializer.EmployeeDocumentSerializer(documents, many=True).data
        return JsonResponse(data, status=200, safe=False)


class EmployeeDocumentDetailAPI(EmployeeView):
    def delete(self, request, document_id):
        try:
            document = EmployeeDocument.objects.get(id=document_id)
        except EmployeeDocument.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
