from rest_framework import serializers

from api.models import EmployerDeduction


class DeductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployerDeduction
        exclude = ()

    def validate_lock(self, value):
        """
        Check that the deduction is not locked.
        """
        if value is True:
            raise serializers.ValidationError("Lock deductions can't be updated / or deleted")
        return value
