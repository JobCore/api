import math
from decimal import Decimal
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField, ArrayField
from django.db import models
from django.db.models import Avg, Count
from django.utils import timezone

from api.utils.loggers import log_debug

NOW = timezone.now()
MIDNIGHT = NOW.replace(hour=0, minute=0, second=0)

ACTIVE = 'ACTIVE'
DELETED = 'DELETED'
POSITION_STATUS = (
    (ACTIVE, 'Active'),
    (DELETED, 'Deleted'),
)


class Badge(models.Model):
    title = models.TextField(max_length=100, blank=True)
    image_url = models.TextField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.title


DAYS = 'DAYS'
MONTHS = 'MONTHS'
PAYROLL_LENGTH_TYPE = (
    (DAYS, 'Days'),
    (MONTHS, 'Months'),
)


class City(models.Model):
    name = models.CharField(max_length=30, blank=False, null=False)

    def __str__(self):
        return self.name


PENDING = 'PENDING'
NOT_APPROVED = 'NOT_APPROVED'
BEING_REVIEWED = 'BEING_REVIEWED'
APPROVED = 'APPROVED'
DELETED = 'DELETED'
EMPLOYER_STATUS = (
    (NOT_APPROVED, 'Not Approved'),
    (PENDING, 'Pending'),
    (BEING_REVIEWED, 'Being Reviewed'),
    (DELETED, 'Deleted'),
    (APPROVED, 'Approved'),
)

class SubscriptionPlan(models.Model):
    unique_name = models.CharField(max_length=25, unique=True)
    visible_to_users = models.BooleanField(default=True)
    title = models.CharField(max_length=25, unique=True)
    image_url = models.TextField(max_length=255, blank=True)

    feature_talent_search = models.BooleanField(default=True)
    feature_payroll_report = models.BooleanField(default=True)
    feature_smart_calendar = models.BooleanField(default=True)
    feature_trusted_talents = models.BooleanField(default=True)
    feature_ach_payments = models.BooleanField(default=True)
    feature_calculate_deductions = models.BooleanField(default=True)
    feature_quickbooks_integration = models.BooleanField(default=True)

    feature_max_clockins = models.IntegerField(blank=True, default=999999999)
    feature_max_invites = models.IntegerField(blank=True, default=9999999)
    feature_max_shifts = models.IntegerField(blank=True, default=9999999)
    feature_max_active_employees = models.IntegerField(blank=True, default=9999999)
    feature_max_favorite_list_size = models.IntegerField(blank=True, default=9999999)

    price_month = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    price_year = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    price_per_clockins = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    price_per_invites = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    price_per_shifts = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    price_per_active_employees = models.DecimalField(max_digits=4, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.title + " (" + self.unique_name + "), " + str(self.price_month)

class Employer(models.Model):
    title = models.TextField(max_length=100, blank=True)
    picture = models.URLField(blank=True)
    website = models.CharField(max_length=30, blank=True)
    bio = models.TextField(max_length=250, blank=True)
    response_time = models.IntegerField(blank=True, default=0)  # in minutes
    rating = models.DecimalField(
        max_digits=2, decimal_places=1, default=0, blank=True)
    total_ratings = models.IntegerField(blank=True, default=0)  # in minutes
    badges = models.ManyToManyField(Badge, blank=True)
    status = models.CharField(max_length=25, choices=EMPLOYER_STATUS, default=APPROVED, blank=True)

    # talents on employer's favlist's will be automatically accepted
    automatically_accept_from_favlists = models.BooleanField(default=True)

    # the company can configure how it wants the payroll period
    payroll_period_starting_time = models.DateTimeField(blank=True, null=True)  # 12:00am GMT

    payroll_period_length = models.IntegerField(blank=True, default=7)
    payroll_period_type = models.CharField(
        max_length=25,
        choices=PAYROLL_LENGTH_TYPE,
        default=DAYS,
        blank=True)
    last_payment_period = models.DateTimeField(default=None, null=True)

    # if this option is None, the talent will be able to checkout anytime
    # he wants By default, he can only checkout within 15 min of the starting
    # time (before or after)

    maximum_clockin_delta_minutes = models.IntegerField(
        blank=True, default=None, null=True)

    # if this option is None, the talent will be able to checkout anytime,
    # by default the application will auto checkout after 15 min

    maximum_clockout_delay_minutes = models.IntegerField(
        blank=True, default=None, null=True)  # in minutes

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.title

    def get_bank_accounts(self):
        """Get bank accounts of all profiles related to this Employer"""
        bank_account_list = []
        for profile in self.profile_set.all():
            for bank_account in profile.bank_accounts.all():
                bank_account_list.append(bank_account)
        return bank_account_list


ACTIVE = 'ACTIVE'
EXPIRED = 'EXPIRED'
CANCELLED = 'CANCELLED'
SUBSCRIPTION_STATUS = (
    (ACTIVE, 'Active'),
    (EXPIRED, 'Expired'),
    (CANCELLED, 'Cancelled'),
)

MONTHLY = 'MONTHLY'
YEARLY = 'YEARLY'
SUBSCRIPTION_MODE = (
    (MONTHLY, 'Monthly'),
    (YEARLY, 'Yearly'),
)

class Position(models.Model):
    picture = models.URLField(blank=True)
    title = models.TextField(max_length=100, blank=True)
    description = models.TextField(max_length=1050, blank=True)
    meta_description = models.TextField(max_length=250, blank=True)
    meta_keywords = models.TextField(max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    status = models.CharField(max_length=9, choices=POSITION_STATUS, default=ACTIVE, blank=True)
    pay_rate = models.ManyToManyField(
        Employer, blank=True, related_name="pay_rate", through="Payrates")

    def __str__(self):
        return self.title

class Payrates(models.Model):
    position = models.ForeignKey(
        Position, on_delete=models.CASCADE, blank=True, related_name="employer_payrates_positions")
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, blank=True, related_name="employer_payrates_employer")
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, blank=True, null=True)

    hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, blank=True)    
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.position.title + " " + str(self.hourly_rate)

class EmployerSubscription(models.Model):
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, blank=True)
    subscription = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, blank=True)
    status = models.CharField(max_length=25, choices=SUBSCRIPTION_STATUS, default=ACTIVE, blank=True)
    payment_mode = models.CharField(max_length=9,choices=SUBSCRIPTION_MODE,default=MONTHLY,blank=True)
    due_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.employer.title + " for " + self.subscription.title + ": " + self.status + " until " + str(self.due_at)

PENDING = 'PENDING'
NOT_APPROVED = 'NOT_APPROVED'
BEING_REVIEWED = 'BEING_REVIEWED'
MISSING_DOCUMENTS = 'MISSING_DOCUMENTS'
APPROVED = 'APPROVED'
EMPLOYEMNT_STATUS = (
    (NOT_APPROVED, 'Not Approved'),
    (PENDING, 'Pending'),
    (MISSING_DOCUMENTS, 'Missing Documents'),
    (BEING_REVIEWED, 'Being Reviewed'),
    (APPROVED, 'Approved'),
)

SINGLE = 'SINGLE'
MARRIED_JOINTLY = 'MARRIED_JOINTLY'
MARRIED_SEPARATELY = 'MARRIED_SEPARATELY'
HEAD = 'HEAD'
WIDOWER = 'WIDOWER'
FILING_STATUS = (
    (SINGLE, 'Single'),
    (MARRIED_JOINTLY, 'Married filing jointly'),
    (MARRIED_SEPARATELY, 'Married filing separately'),
    (HEAD, 'Head of household'),
    (WIDOWER, 'Qualifying widow(er) with dependent child'),
)


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True)
    minimum_hourly_rate = models.DecimalField(
        max_digits=3, decimal_places=1, default=8, blank=True)
    stop_receiving_invites = models.BooleanField(default=False)
    rating = models.DecimalField(
        max_digits=2, decimal_places=1, default=None, blank=True, null=True)
    total_ratings = models.IntegerField(blank=True, default=0)  # in minutes
    total_pending_payments = models.IntegerField(blank=True, default=0)
    maximum_job_distance_miles = models.IntegerField(default=50)
    positions = models.ManyToManyField(
        Position, blank=True)
    job_count = models.IntegerField(default=0, blank=True)
    badges = models.ManyToManyField(Badge, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    # reponse time calculation
    response_time = models.IntegerField(blank=True, default=0)  # in minutes
    total_invites = models.IntegerField(blank=True, default=0)  # in minutes

    # employment and deductions
    employment_verification_status = models.CharField(max_length=25, choices=EMPLOYEMNT_STATUS, default=NOT_APPROVED,
                                                      blank=True)
    filing_status = models.CharField(max_length=25, choices=FILING_STATUS, default=SINGLE, blank=True)
    allowances = models.IntegerField(blank=True, default=0)
    w4_year = models.IntegerField(blank=True, default=0)
    step2c_checked = models.BooleanField(blank=True, default=False)
    dependants_deduction = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    other_income = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    additional_deductions = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    extra_withholding = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name + "(" + self.user.email + ")"

    def calculate_tax_amount(self, period_wage, period_quantity):
        from api.utils.taxes_functions import get_tentative_withholding
        adjusted_wage = period_wage * period_quantity + self.other_income - self.additional_deductions
        if adjusted_wage < 0:
            adjusted_wage = Decimal('0.00')
        tentative_withholding = get_tentative_withholding(adjusted_wage, self.filing_status, self.step2c_checked)
        annual_withholding = tentative_withholding - self.dependants_deduction
        if annual_withholding < 0:
            annual_withholding = Decimal('0.00')
        annual_withholding += self.extra_withholding
        return Decimal(str(math.trunc(annual_withholding / period_quantity * 100) / 100))


ACTIVE = 'ACTIVE'
PAUSED = 'PAUSED'
PENDING = 'PENDING_EMAIL_VALIDATION'
SUSPENDED = 'SUSPENDED'
PROFILE_STATUS = (
    (ACTIVE, 'Active'),
    (PAUSED, 'Paused'),
    (SUSPENDED, 'Suspended'),
    (PENDING, 'PENDING_EMAIL_VALIDATION'),
)

ADMIN = 'ADMIN'
MANAGER = 'MANAGER'
SUPERVISOR = 'SUPERVISOR'
COMPANY_ROLES = (
    (ADMIN, 'Admin'),
    (MANAGER, 'Manager'),
    (SUPERVISOR, 'Supervisor'),
)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True)
    picture = models.URLField(blank=True)
    bio = models.TextField(max_length=250, blank=True)
    show_tutorial = models.BooleanField(default=True)

    # location information
    location = models.CharField(max_length=250, blank=True)
    street_address = models.CharField(max_length=250, blank=True)
    country = models.CharField(max_length=30, blank=True)
    city = models.CharField(max_length=30, blank=True, null=True)
    profile_city = models.ForeignKey(City, null=True, on_delete=models.SET_NULL)
    state = models.CharField(max_length=30, blank=True)
    zip_code = models.IntegerField(null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=14, decimal_places=11, default=0)
    longitude = models.DecimalField(
        max_digits=14, decimal_places=11, default=0)

    birth_date = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=17, blank=True)
    last_4dig_ssn = models.CharField(max_length=4, default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, blank=True, null=True)

    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, blank=True, null=True)
    employer_role = models.CharField(max_length=25, choices=COMPANY_ROLES, default=ADMIN, blank=True)
    other_employers = models.ManyToManyField(Employer, blank=True, related_name="other_employers", through="EmployerUsers")

    status = models.CharField(max_length=25, choices=PROFILE_STATUS, default=PENDING, blank=True)

    def __str__(self):
        return self.user.username

    @property
    def get_city(self):
        if self.profile_city_id is None:
            return self.city
        return self.profile_city.name


WEEKLY = 'WEEKLY'
MONTHLY = 'MONTHLY'
RECURRENCY_TYPE = (
    (WEEKLY, 'Weekly'),
    (MONTHLY, 'Monthly'),
)

class EmployerUsers(models.Model):
    employer = models.ForeignKey(
        Employer, on_delete=models.CASCADE, blank=True, related_name="company_users_employer")
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, blank=True, related_name="company_users_profile")

    employer_role = models.CharField(max_length=25, choices=COMPANY_ROLES, default=ADMIN, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.employer.title + " (" + self.employer_role + "), " + str(self.profile.user.email)


class AvailabilityBlock(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, blank=True)
    starting_at = models.DateTimeField()
    ending_at = models.DateTimeField()
    recurrent = models.BooleanField(default=True)
    allday = models.BooleanField(default=True)
    recurrency_type = models.CharField(
        max_length=25,
        choices=RECURRENCY_TYPE,
        default=WEEKLY,
        blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)


class FavoriteList(models.Model):
    title = models.TextField(max_length=100, blank=True)
    employees = models.ManyToManyField(Employee, blank=True)
    employer = models.ForeignKey(
        Employer, on_delete=models.CASCADE, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    # talents on employer's favlist's will be automatically accepted
    auto_accept_employees_on_this_list = models.BooleanField(default=True)

    def __str__(self):
        return self.title


ACTIVE = 'ACTIVE'
DELETED = 'DELETED'
VENUE_STATUS = (
    (ACTIVE, 'Active'),
    (DELETED, 'Deleted'),
)


class Venue(models.Model):
    title = models.TextField(max_length=100, blank=True)
    employer = models.ForeignKey(
        Employer, on_delete=models.CASCADE, blank=True, null=True)
    street_address = models.CharField(max_length=250, blank=True)
    country = models.CharField(max_length=30, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, default=0)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, default=0)
    state = models.CharField(max_length=30, blank=True)
    zip_code = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    status = models.CharField(max_length=9, choices=VENUE_STATUS, default=ACTIVE, blank=True)

    def __str__(self):
        return self.title


OPEN = 'OPEN'
FILLED = 'FILLED'
PAUSED = 'PAUSED'
EXPIRED = 'EXPIRED'  # si todavia no ha sido pagado
COMPLETED = 'COMPLETED'  # si ya fue pagado
DRAFT = 'DRAFT'
CANCELLED = 'CANCELLED'
SHIFT_STATUS_CHOICES = (
    (OPEN, 'Receiving candidates'),
    (FILLED, 'Filled'),
    (PAUSED, 'Paused'),
    (DRAFT, 'Draft'),
    (EXPIRED, 'Expired'),
    (COMPLETED, 'Completed'),
    (CANCELLED, 'Cancelled'),
)

FAVORITES = 'FAVORITES'
ANYONE = 'ANYONE'
SPECIFIC = 'SPECIFIC_PEOPLE'
SHIFT_APPLICATION_RESTRICTIONS = (
    (FAVORITES, 'Favorites Only'),
    (ANYONE, 'Anyone can apply'),
    (SPECIFIC, 'Specific People')
)


class Shift(models.Model):
    venue = models.ForeignKey(
        Venue, on_delete=models.CASCADE, blank=True)
    position = models.ForeignKey(
        Position, on_delete=models.CASCADE, blank=True)
    application_restriction = models.CharField(
        max_length=20,
        choices=SHIFT_APPLICATION_RESTRICTIONS,
        default=ANYONE,
        blank=True)
    maximum_allowed_employees = models.IntegerField(default=0, blank=True)
    minimum_hourly_rate = models.DecimalField(
        max_digits=3, decimal_places=1, default=0, blank=True)
    minimum_allowed_rating = models.DecimalField(
        max_digits=2, decimal_places=1, default=0, blank=True)
    allowed_from_list = models.ManyToManyField(
        FavoriteList, blank=True)
    required_badges = models.ManyToManyField(
        Badge, blank=True
    )

    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, blank=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=True, null=True)

    status = models.CharField(
        max_length=9,
        choices=SHIFT_STATUS_CHOICES,
        default=DRAFT,
        blank=True)
    starting_at = models.DateTimeField(blank=False)
    ending_at = models.DateTimeField(blank=False)
    rating = models.DecimalField(
        max_digits=2, decimal_places=1, default=0, blank=True)
    candidates = models.ManyToManyField(
        Employee, blank=True, through="ShiftApplication")
    employees = models.ManyToManyField(
        Employee, blank=True, related_name="shift_accepted_employees",
        through='ShiftEmployee')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    description = models.TextField(max_length=300, blank=True, default="")

    # if this option is None, the talent will be able to clockin anytime
    # he wants. By default, he can only clockin within 15 min of the starting
    # time (before or after)
    maximum_clockin_delta_minutes = models.IntegerField(
        blank=True, default=15, null=True)

    # if this option is None, the talent will be able to clockout anytome,
    # by default the application will auto clockout after 15 min
    maximum_clockout_delay_minutes = models.IntegerField(
        blank=True, default=15, null=True)  # in minutes

    def __str__(self):
        return "{} at {} on {} - {}".format(
            self.position, self.venue, self.starting_at, self.ending_at)


class ShiftEmployee(models.Model):
    shift = models.ForeignKey(
        Shift, on_delete=models.CASCADE, blank=True)
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, blank=True)
    success = models.BooleanField(default=True)
    comments = models.TextField(max_length=450, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)


class ShiftApplication(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, blank=True)
    shift = models.ForeignKey(
        Shift, on_delete=models.CASCADE, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)


PENDING = 'PENDING'
APPLIED = 'APPLIED'
REJECTED = 'REJECTED'
EXPIRED = 'EXPIRED'
SHIFT_INVITE_STATUS_CHOICES = (
    (PENDING, 'Pending'),
    (APPLIED, 'Applied'),
    (REJECTED, 'Rejected'),
    (EXPIRED, 'Expired'),
)


class ShiftInvite(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, blank=True)
    sender = models.ForeignKey(
        Profile, on_delete=models.CASCADE, blank=True, default=None)
    shift = models.ForeignKey(
        Shift, on_delete=models.CASCADE, blank=True)
    status = models.CharField(
        max_length=9,
        choices=SHIFT_INVITE_STATUS_CHOICES,
        default=PENDING,
        blank=True)
    manually_created = models.BooleanField(default=False)
    responded_at = models.DateTimeField(blank=False, null=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return str(self.employee) + " for " + str(self.shift) + " on " + self.created_at.strftime(
            "%m/%d/%Y, %H:%M:%S") + " (" + self.status + ")"


class UserToken(models.Model):
    token = models.TextField(max_length=255, blank=True)
    email = models.TextField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    expires_at = models.DateTimeField()

    def __str__(self):
        return self.email + " " + self.token


PENDING = 'PENDING'
ACCEPTED = 'ACCEPTED'
COMPANY_PENDING = 'COMPANY'
JOBCORE_INVITE_STATUS_CHOICES = (
    (PENDING, 'Pending'),
    (COMPANY_PENDING, 'Company Pending'),
    (ACCEPTED, 'Accepted'),
)


class JobCoreInvite(models.Model):
    sender = models.ForeignKey(
        Profile, on_delete=models.CASCADE, blank=True)
    first_name = models.TextField(max_length=100, blank=True)
    last_name = models.TextField(max_length=100, blank=True)

    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, blank=True, default=None, null=True)
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, blank=True, default=None, null=True)

    email = models.TextField(max_length=100, blank=True)
    status = models.CharField(
        max_length=9,
        choices=JOBCORE_INVITE_STATUS_CHOICES,
        default=PENDING,
        blank=True)
    phone_number = models.CharField(max_length=17, blank=True)
    employer_role = models.CharField(max_length=17, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.first_name + " " + self.last_name + " on " + self.created_at.strftime(
            "%m/%d/%Y, %H:%M:%S") + " (" + self.status + ")"


class Rate(models.Model):
    sender = models.ForeignKey(
        Profile, on_delete=models.CASCADE, blank=True)
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, blank=True, null=True)
    employer = models.ForeignKey(
        Employer, on_delete=models.CASCADE, blank=True, null=True)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, blank=True, null=True)
    comments = models.TextField(default="",blank=True)
    rating = models.DecimalField(
        max_digits=2, decimal_places=1, default=0, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def save(self, *args, **kwargs):
        log_debug('general', 'save_rate')

        super().save(*args, **kwargs)  # Call the "real" save() method.

        # Calculate avg and sumatory
        obj = None
        if self.employee is not None:
            obj = self.employee
            new_ratings = (
                Employee.objects.aggregate(new_avg=Avg('rate__rating'), new_total=Count('rate__id'))
            )
        elif self.employer is not None:
            obj = self.employer
            new_ratings = (
                Employer.objects.aggregate(new_avg=Avg('rate__rating'), new_total=Count('rate__id'))
            )

        if obj is not None:
            obj.total_ratings = new_ratings['new_total']
            obj.rating = new_ratings['new_avg']
            obj.save()


class FCMDevice(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True)
    registration_id = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.user.username


class Notification(models.Model):
    owner = models.ForeignKey(
        Profile, related_name='notifications', on_delete=models.CASCADE,
        blank=True, null=True)
    title = models.TextField()
    body = models.TextField()
    data = models.TextField(max_length=1500)
    read = models.BooleanField(default=False)
    sent = models.BooleanField(default=False)
    scheduled_at = models.DateTimeField(blank=False, null=True)
    sent_at = models.DateTimeField(blank=False, null=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.owner.user.email + ":" + self.title


APPROVED = 'APPROVED'
PENDING = 'PENDING'
CLOCKIN_STATUS = (
    (APPROVED, 'Approved'),
    (PENDING, 'Pending'),
)


class Clockin(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, blank=True)
    shift = models.ForeignKey(
        Shift, on_delete=models.CASCADE, blank=True)
    author = models.ForeignKey(
        Profile, on_delete=models.CASCADE, blank=True, null=True)
    started_at = models.DateTimeField(blank=True)

    latitude_in = models.DecimalField(max_digits=16, decimal_places=11, default=0)
    longitude_in = models.DecimalField(max_digits=16, decimal_places=11, default=0)
    distance_in_miles = models.DecimalField(max_digits=8, decimal_places=3, default=0)

    latitude_out = models.DecimalField(max_digits=16, decimal_places=11, default=0)
    longitude_out = models.DecimalField(max_digits=16, decimal_places=11, default=0)
    distance_out_miles = models.DecimalField(max_digits=8, decimal_places=3, default=0)

    ended_at = models.DateTimeField(blank=True, null=True)

    automatically_closed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    status = models.CharField(
        max_length=9,
        choices=CLOCKIN_STATUS,
        default=PENDING)

    def __str__(self):
        return self.employee.user.first_name + " " + self.employee.user.last_name + ", from " + str(
            self.started_at) + " to " + str(self.ended_at)


OPEN = 'OPEN'
FINALIZED = 'FINALIZED'
PAID = 'PAID'
PERIOD_STATUS = (
    (OPEN, 'Open'),
    (FINALIZED, 'Finalized'),
    (PAID, 'Paid')
)


class PayrollPeriod(models.Model):
    employer = models.ForeignKey(
        Employer, on_delete=models.CASCADE, blank=True)
    length = models.IntegerField(blank=True, default=7)
    length_type = models.CharField(
        max_length=25,
        choices=PAYROLL_LENGTH_TYPE,
        default=DAYS,
        blank=True)
    status = models.CharField(
        max_length=9,
        choices=PERIOD_STATUS,
        default=OPEN)

    starting_at = models.DateTimeField(blank=False)
    ending_at = models.DateTimeField(blank=False)

    total_payments = models.IntegerField(blank=True, default=0)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return "From " + str(self.starting_at) + " to " + str(self.ending_at)


PENDING = 'PENDING'
PAID = 'PAID'
APPROVED = 'APPROVED'
REJECTED = 'REJECTED'
PAYMENT_STATUS = (
    (PENDING, 'Pending'),
    (APPROVED, 'Approved'),
    (REJECTED, 'Rejected'),
    (PAID, 'Paid')
)


class PayrollPeriodPayment(models.Model):
    payroll_period = models.ForeignKey(
        PayrollPeriod, related_name='payments', on_delete=models.CASCADE,
        blank=True)
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, blank=True)
    employer = models.ForeignKey(
        Employer, on_delete=models.CASCADE, blank=True)
    shift = models.ForeignKey(
        Shift, on_delete=models.CASCADE, blank=True)
    clockin = models.ForeignKey(
        Clockin, on_delete=models.CASCADE, blank=True, null=True)
    splited_payment = models.BooleanField(default=True)
    status = models.CharField(
        max_length=9,
        choices=PAYMENT_STATUS,
        default=PENDING)
    approved_clockin_time = models.DateTimeField(blank=True, null=True)
    approved_clockout_time= models.DateTimeField(blank=True, null=True)
    breaktime_minutes = models.IntegerField(blank=True, default=0)
    regular_hours = models.DecimalField(
        max_digits=10, decimal_places=5, default=0, blank=True)   # This value has breaktime deducted already
    over_time = models.DecimalField(
        max_digits=10, decimal_places=5, default=0, blank=True)
    hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, blank=True)
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)


class EmployeePayment(models.Model):
    payroll_period = models.ForeignKey(PayrollPeriod, on_delete=models.PROTECT, related_name='employee_payments')
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='employee_payments')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payments')
    paid = models.BooleanField(blank=True, default=False)
    regular_hours = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)   # This value has breaktime deducted already
    over_time = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    legal_over_time = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)   # plus 40 hours/week
    breaktime_minutes = models.IntegerField(blank=True, default=0)
    earnings = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='gross earnings')
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0, verbose_name='net earnings')
    deductions = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    deduction_list = JSONField(blank=True, default=list)
    taxes = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    payment_transaction = models.OneToOneField('PaymentTransaction', on_delete=models.SET_NULL, blank=True, null=True,
                                               related_name='employee_payment')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)


class PaymentDeduction(models.Model):
    employer = models.ForeignKey(Employer, related_name='deductions', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    amount = models.FloatField()


class BankAccount(models.Model):
    """
    {'account': '1111222233330000', 'account_id': 'XJJ3KQ5A8eSVlvK4Mj61tgBerwEdp8cdXwgaZ',
    'routing': '011401533', 'wire_routing': '021000021'}
    """
    user = models.ForeignKey(
        Profile,
        related_name='bank_accounts',
        on_delete=models.CASCADE,
        blank=True,
        null=True)
    access_token = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    account_id = models.CharField(max_length=200, null=True, blank=True)
    account = models.CharField(max_length=200, null=True, blank=True)
    routing = models.CharField(max_length=200, null=True, blank=True)
    wire_routing = models.CharField(max_length=200, null=True, blank=True)
    institution_name = models.CharField(max_length=200, null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_account_id = models.CharField(max_length=100, blank=True)
    stripe_bankaccount_id = models.CharField(max_length=200, blank=True)


class PaymentTransaction(models.Model):
    """Record details about a payment transaction"""
    CHECK = 'CHECK'
    ELECT_TRANSF = 'ELECTRONIC TRANSFERENCE'
    FAKE = 'FAKE'   # to fake an electronic transfer
    PAYMENT_TYPES = (
        (CHECK, 'Check'),
        (ELECT_TRANSF, 'Electronic Transference'),
        (FAKE, 'Fake Electronic Transference'),
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=100, choices=PAYMENT_TYPES)
    payment_data = JSONField(blank=True, default=dict)
    sender_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_payments')
    receiver_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_payments')
    created_at = models.DateTimeField(auto_now_add=True)


class Document(models.Model):
    title = models.CharField(max_length=250, null=True, blank=True)

    validates_identity = models.BooleanField(default=False)
    validates_employment = models.BooleanField(default=False)
    is_form = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.title


class EmployeeDocument(models.Model):
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    ARCHIVED = 'ARCHIVED'
    DELETED = 'DELETED'
    REJECTED = 'REJECTED'
    DOCUMENT_STATUS = (
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (ARCHIVED, 'Archived'),
        (DELETED, 'Deleted'),
        (REJECTED, 'Rejected'),
    )
    document = models.URLField()

    public_id = models.CharField(max_length=80, null=True)

    rejected_reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=8, choices=DOCUMENT_STATUS, default=PENDING)
    expired_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    document_type = models.ForeignKey(Document, on_delete=models.CASCADE)


class AppVersion(models.Model):
    build_number = models.IntegerField(default=94)
    version = models.CharField(max_length=10, unique=True, default='94')
    change_log = models.TextField(max_length=450, blank=True)
    force_update = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)


class PreDefinedDeduction(models.Model):
    """
    This models will contain the Deductions that need to be copied to the Employer Deductions when one is created.
    This Pre defined deductions are copied to the Employer upon creation
    """
    PERCENTAGE_TYPE = 'PERCENTAGE'
    AMOUNT_TYPE = 'AMOUNT'
    TYPES = (
        (PERCENTAGE_TYPE, PERCENTAGE_TYPE.lower()),
        (AMOUNT_TYPE, AMOUNT_TYPE.lower()),
    )
    name = models.CharField(max_length=200, null=False, blank=False)
    description = models.TextField()
    type = models.CharField(max_length=200, null=False, blank=False, choices=TYPES, default=PERCENTAGE_TYPE)
    value = models.FloatField(blank=False, null=False)


class EmployerDeduction(models.Model):
    """
    Model for the deduction that each Employer wants to add to it's payments
    """
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=200, null=False, blank=False)
    description = models.TextField()
    type = models.CharField(max_length=200, null=False, blank=False, choices=PreDefinedDeduction.TYPES,
                            default=PreDefinedDeduction.PERCENTAGE_TYPE)
    value = models.FloatField(blank=False, null=False)
    # Attribute to block the deletion of a Deduction
    lock = models.BooleanField(default=False, null=False, blank=True)
