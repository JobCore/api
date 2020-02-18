import pytz
from datetime import datetime, timedelta
from dateutil import relativedelta
from mixer.backend.django import mixer

from django.conf import settings
from django.utils import timezone


class WithMakeUser:
    def _make_user(
            self, kind, userkwargs={}, employexkwargs={}, profilekwargs={}):

        if kind not in ['employee', 'employer']:
            raise RuntimeError('Do you know what are you doing?')

        user = mixer.blend('auth.User', **userkwargs)
        user.set_password('pass1234')
        user.save()

        emptype = 'api.Employee' if kind == 'employee' else 'api.Employer'

        if kind == 'employee':
            employexkwargs.update({
                'user': user
            })

        emp = mixer.blend(emptype, **employexkwargs)
        emp.save()

        profilekwargs = profilekwargs.copy()
        profilekwargs.update({
            'user': user,
            kind: emp,
        })

        profile = mixer.blend('api.Profile', **profilekwargs)
        profile.save()

        return user, emp, profile


class WithMakeShift:
    def _make_shift(self, employer,
                    shiftkwargs=None, venuekwargs=None, poskwargs=None):

        if shiftkwargs is None:
            shiftkwargs = {}
        if venuekwargs is None:
            venuekwargs = {}
        if poskwargs is None:
            poskwargs = {}

        venue = mixer.blend('api.Venue', employer=employer, **venuekwargs)

        if 'position' not in shiftkwargs:
            shiftkwargs['position'] = mixer.blend('api.Position', **poskwargs)

        shift = mixer.blend(
            'api.Shift',
            venue=venue,
            employer=employer,
            **shiftkwargs,)

        return shift, venue, shiftkwargs['position']


class WithMakePayrollPeriod:

    def _get_dates(self, start_dt=None, end_dt=None, elapse_value=7, elapse_unit='DAYS'):
        assert start_dt is None or end_dt is None
        if not end_dt and not start_dt:
            end_dt = timezone.now()
        if start_dt and not end_dt:
            if elapse_unit == 'DAYS':
                end_dt = start_dt + timedelta(days=elapse_value)
            else:
                end_dt = start_dt + relativedelta(months=elapse_value)
            end_dt = datetime(end_dt.year, end_dt.month, end_dt.day, 23, 59, 59, tzinfo=pytz.timezone(settings.TIME_ZONE))
        else:
            if elapse_unit == 'DAYS':
                start_dt = end_dt - timedelta(days=elapse_value)
            else:
                start_dt = end_dt - relativedelta(months=elapse_value)
            start_dt = datetime(start_dt.year, start_dt.month, start_dt.day, 0, 0, 0, tzinfo=pytz.timezone(settings.TIME_ZONE))
        return start_dt, end_dt

    def _make_period(self, employer, starting_at=None, ending_at=None, periodkwargs=None):
        if periodkwargs is None:
            periodkwargs = {}
        if not periodkwargs.get('length') and not periodkwargs.get('length_type'):
            starting_date, ending_date = self._get_dates(starting_at, ending_at)
        elif periodkwargs.get('length') and not periodkwargs.get('length_type'):
            starting_date, ending_date = self._get_dates(starting_at, ending_at, periodkwargs.get('length'))
        elif not periodkwargs.get('length') and periodkwargs.get('length_type'):
            starting_date, ending_date = self._get_dates(starting_at, ending_at,
                                                         elapse_unit=periodkwargs.get('length_type'))
        else:
            starting_date, ending_date = self._get_dates(starting_at, ending_at, periodkwargs.get('length'),
                                                         periodkwargs.get('length_type'))
        period = mixer.blend('api.PayrollPeriod', employer=employer, starting_at=starting_date,
                             ending_at=ending_date, **periodkwargs)
        return period


class WithMakePayrollPeriodPayment(WithMakeShift):

    def _make_periodpayment(self, employer, employee, period, mykwargs=None, relatedkwargs=None):
        if mykwargs is None:
            mykwargs = {}
        position = None
        if relatedkwargs and relatedkwargs.get('shift'):
            shift = relatedkwargs.get('shift')
        else:
            if relatedkwargs and relatedkwargs['position']:
                shift, position, _ = self._make_shift(employer=employer,
                                                      shiftkwargs={'position': relatedkwargs['position']})
            else:
                shift, position, _ = self._make_shift(employer=employer)
        if relatedkwargs and relatedkwargs.get('clockin'):
            clockin = relatedkwargs.get('clockin')
        else:
            clockin = mixer.blend('api.Clockin', employee=employee, shift=shift, profile=employee.profile_set.all()[0])
        periodpayment = mixer.blend('api.PayrollPeriodPayment', employer=employer, employee=employee,
                                    payroll_period=period, shift=shift, clockin=clockin, **mykwargs)
        return periodpayment, shift, position, clockin
