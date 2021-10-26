from django.core.management.base import BaseCommand, CommandError
from api.models import (PayrollPeriod)
from django.db.models import Count, F

"""
Loops all the periods in re-calculates all the total payments they have

This was created because period.total_payments was a new calculated propery and 
we had to update the historical data
"""
class Command(BaseCommand):
    help = 'Loops all the periods in re-calculates all the total payments they have'

    def handle(self, *args, **options):

        payments = PayrollPeriod.objects.annotate(total=Count('payments')).all()
        for payment in payments:
            payment.total_payments = payment.payments.count()
            payment.total_employees = 
            payment.save()

        self.stdout.write(self.style.SUCCESS("Successfully updated all total_payments on every period"))