from rest_framework import serializers

from api.models import EmployeeDocument, Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        exclude = ()


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDocument
        exclude = ()


class EmployeeDocumentGetSerializer(serializers.ModelSerializer):
    document_type = DocumentSerializer(many=False)
    name = serializers.SerializerMethodField('_name', read_only=True)

    def _name(self, object):
        return object.document_type.title

    class Meta:
        model = EmployeeDocument
        exclude = ()
