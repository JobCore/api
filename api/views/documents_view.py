from rest_framework import status
from rest_framework.response import Response
from api.models import *
from api.utils import validators
from api.serializers import documents_serializer
from django.http import JsonResponse
from api.mixins import EmployeeView
import cloudinary.uploader
import logging
from django.utils.crypto import get_random_string
from datetime import datetime

u'rRXVe68NO7m3mHoBS488KdHaqQPD6Ofv'

log = logging.getLogger('api.views.documents_views')



class EmployeeDocumentAPI(EmployeeView):

    def post(self, request):
        if 'document_type' not in request.data:
            return Response(validators.error_object('You need to specify the type of document you are uploading'),
                            status=status.HTTP_400_BAD_REQUEST)

        if 'document' not in request.FILES:
            return Response(validators.error_object('Please specify a document'), status=status.HTTP_400_BAD_REQUEST)

        public_id = f'profile-{str(self.request.user.id)}-{datetime.now().strftime("%d-%m")}-{get_random_string(length=32)}'
        file_name = f'{str(self.request.user.id)}/i9_documents/{public_id}'

        try:
            result = cloudinary.uploader.upload(
                request.FILES['document'],
                public_id=file_name,
                tags=['i9_document', 'profile-' + str(self.request.user.id), ],
                use_filename=1,
                unique_filename=1,
                resource_type='auto'
            )
            print(result)
        except Exception as e:
            print(e)
            return JsonResponse({"error": str(e)}, status=400)
            
        data = {
            'document': result['secure_url'],
            'employee': self.employee.id,
            'document_type': request.data['document_type'],
            'public_id': public_id,
        }
        print('data picker', data)
        serializer = documents_serializer.EmployeeDocumentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        cloudinary.uploader.destroy(public_id)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        documents = EmployeeDocument.objects.filter(employee_id=self.employee.id)

        qStatus = request.GET.get('status')
        if qStatus:
            documents = documents.filter(status=qStatus)
        else:
            # by default, archived documents will be hidden
            documents = documents.filter(status__in=['PENDING', 'APPROVED', 'REJECTED'])

        qType = request.GET.get('type')
        if qType:
            if qType == 'identity':
                documents = documents.filter(document_type__validates_identity=True)
            elif qType == 'employment':
                documents = documents.filter(document_type__validates_employment=True)
            elif qType == 'form':
                documents = documents.filter(document_type__is_form=True)

        qTypeId = request.GET.get('type_id')
        if qTypeId:
            documents = documents.filter(document_type=qTypeId)

        serializer = documents_serializer.EmployeeDocumentGetSerializer(documents, many=True)
        return JsonResponse(serializer.data, status=200, safe=False)
    
    # def put(self, request):
    #     documents = EmployeeDocument.objects.filter(employee_id=self.employee.id)

class EmployeeDocumentDetailAPI(EmployeeView):
    def delete(self, request, document_id):
        try:
            document = EmployeeDocument.objects.get(id=document_id)

            cloudinary.uploader.destroy(document.public_id)

            document.delete()
        except EmployeeDocument.DoesNotExist:
            return Response(validators.error_object(
                'Not found.'), status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentAPI(EmployeeView):

    def get(self, request):

        documents = Document.objects.all()

        qType = request.GET.get('type')
        if qType:
            if qType == 'identity':
                documents = documents.filter(validates_identity=True)
            elif qType == 'employment':
                documents = documents.filter(validates_employment=True)
            elif qType == 'form':
                documents = documents.filter(is_form=True)

        serializer = documents_serializer.DocumentSerializer(documents, many=True)
        return JsonResponse(serializer.data, status=200, safe=False)
