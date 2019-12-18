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

    def create(self, validated_data):

        validates_employment = validated_data['document_type'].validates_employment
        validates_identity = validated_data['document_type'].validates_identity
        is_form = validated_data['document_type'].is_form

        if validates_employment:
            EmployeeDocument.objects.filter(employee__id=validated_data['employee'].id,
                                            status__in=['PENDING', 'REJECTED'],
                                            document_type__validates_employment=True).update(status='DELETED')
            EmployeeDocument.objects.filter(employee__id=validated_data['employee'].id, status='APPROVED',
                                            document_type__validates_employment=True).update(status='ARCHIVED')

        if validates_identity:
            EmployeeDocument.objects.filter(employee__id=validated_data['employee'].id,
                                            status__in=['PENDING', 'REJECTED'],
                                            document_type__validates_identity=True).update(status='DELETED')
            EmployeeDocument.objects.filter(employee__id=validated_data['employee'].id, status='APPROVED',
                                            document_type__validates_identity=True).update(status='ARCHIVED')

        if is_form:
            EmployeeDocument.objects.filter(employee__id=validated_data['employee'].id,
                                            status__in=['PENDING', 'REJECTED'], document_type__is_form=True).update(
                status='DELETED')
            EmployeeDocument.objects.filter(employee__id=validated_data['employee'].id, status='APPROVED',
                                            document_type__is_form=True).update(status='ARCHIVED')

        new_document = EmployeeDocument(**validated_data)
        new_document.save()

        # pick the new status for the employee
        pending_and_approved_documents = EmployeeDocument.objects.filter(employee__id=validated_data['employee'].id,
                                                                         status__in=['PENDING', 'APPROVED'])
        validations = {"employment": False, "identity": False, "form": False}
        # you need to have one of each type at least
        for doc in pending_and_approved_documents:
            if doc.document_type.validates_employment:
                validations["employment"] = True
            if doc.document_type.validates_identity:
                validations["identity"] = True
            if doc.document_type.is_form:
                validations["form"] = True

        employee = new_document.employee
        if validations["form"] and validations["identity"] and validations["employment"]:
            employee.employment_verification_status = 'BEING_REVIEWED'
        else:
            employee.employment_verification_status = 'MISSING_DOCUMENTS'
        employee.save()

        return new_document


class EmployeeDocumentGetSerializer(serializers.ModelSerializer):
    document_type = DocumentSerializer(many=False)
    name = serializers.SerializerMethodField('_name', read_only=True)

    def _name(self, object):
        return object.document_type.title

    class Meta:
        model = EmployeeDocument
        exclude = ()
