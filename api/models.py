from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from api.utils.loggers import log_debug

NOW = timezone.now()
MIDNIGHT = NOW.replace(hour=0, minute=0, second=0)


class Position(models.Model):
    picture = models.URLField(blank=True)
    title = models.TextField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.title


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

    documents = models.ManyToManyField('Document', blank=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.title


class Employee(models.Model):
    response_time = models.IntegerField(blank=True, default=0)  # in minutes
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

    def __str__(self):
        return self.user.first_name + " " + self.user.last_name + "(" + self.user.email + ")"


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


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True)
    picture = models.URLField(blank=True)
    bio = models.TextField(max_length=250, blank=True)
    show_tutorial = models.BooleanField(default=True)

    # location information
    location = models.CharField(max_length=250, blank=True)
    street_address = models.CharField(max_length=250, blank=True)
    country = models.CharField(max_length=30, blank=True)
    city = models.CharField(max_length=30, blank=True)
    profile_city_man = models.CharField(max_length=30, null=True, blank=True)
    profile_city = models.ForeignKey(City, null=True, on_delete=models.CASCADE)
    state = models.CharField(max_length=30, blank=True)
    zip_code = models.IntegerField(null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=14, decimal_places=11, default=0)
    longitude = models.DecimalField(
        max_digits=14, decimal_places=11, default=0)

    birth_date = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=17, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    employer = models.ForeignKey(
        Employer, on_delete=models.CASCADE, blank=True, null=True)
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, blank=True, null=True)
    status = models.CharField(
        max_length=25,
        choices=PROFILE_STATUS,
        default=PENDING,
        blank=True)

    def __str__(self):
        return self.user.username

    @property
    def get_city(self):
        if self.profile_city_id is None:
            return self.profile_city_man
        return self.profile_city.name


WEEKLY = 'WEEKLY'
MONTHLY = 'MONTHLY'
RECURRENCY_TYPE = (
    (WEEKLY, 'Weekly'),
    (MONTHLY, 'Monthly'),
)


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
    employer = models.ForeignKey(
        Employer, on_delete=models.CASCADE, blank=True)
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
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return str(self.employee) + " for " + str(self.shift) + " on " + self.created_at.strftime(
            "%m/%d/%Y, %H:%M:%S") + " (" + self.status + ")"


PENDING = 'PENDING'
ACCEPTED = 'ACCEPTED'
JOBCORE_INVITE_STATUS_CHOICES = (
    (PENDING, 'Pending'),
    (ACCEPTED, 'Accepted'),
)


class UserToken(models.Model):
    token = models.TextField(max_length=255, blank=True)
    email = models.TextField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    expires_at = models.DateTimeField()

    def __str__(self):
        return self.email + " " + self.token


class JobCoreInvite(models.Model):
    sender = models.ForeignKey(
        Profile, on_delete=models.CASCADE, blank=True)
    first_name = models.TextField(max_length=100, blank=True)
    last_name = models.TextField(max_length=100, blank=True)
    shift = models.ForeignKey(
        Shift, on_delete=models.CASCADE, blank=True, default=None, null=True)
    email = models.TextField(max_length=100, blank=True)
    status = models.CharField(
        max_length=9,
        choices=JOBCORE_INVITE_STATUS_CHOICES,
        default=PENDING,
        blank=True)
    phone_number = models.CharField(max_length=17, blank=True)
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
    shift = models.ForeignKey(
        Shift, on_delete=models.CASCADE, blank=True, null=True)
    comments = models.TextField()
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
    latitude_in = models.DecimalField(
        max_digits=14, decimal_places=11, default=0)

    longitude_in = models.DecimalField(
        max_digits=14, decimal_places=11, default=0)

    latitude_out = models.DecimalField(
        max_digits=14, decimal_places=11, default=0)

    longitude_out = models.DecimalField(
        max_digits=14, decimal_places=11, default=0)

    ended_at = models.DateTimeField(blank=True, null=True)
    # auto_closed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    status = models.CharField(
        max_length=9,
        choices=CLOCKIN_STATUS,
        default=PENDING)


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

    breaktime_minutes = models.IntegerField(blank=True, default=0)
    regular_hours = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, blank=True)
    over_time = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, blank=True)
    hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, blank=True)
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)


class PaymentDeduction(models.Model):
    employer = models.ForeignKey(Employer, related_name='deductions', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    amount = models.FloatField()


class BankAccount(models.Model):
    user = models.ForeignKey(
        Profile,
        related_name='bank_accounts',
        on_delete=models.CASCADE,
        blank=True,
        null=True)
    access_token = models.CharField(max_length=100)
    name = models.CharField(max_length=200)
    institution_name = models.CharField(max_length=200)
    item_id = models.CharField(max_length=100)


class Document(models.Model):
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    DOCUMENT_STATUS = (
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
    )
    document = models.FileField()
    state = models.CharField(max_length=7, choices=DOCUMENT_STATUS, default=PENDING)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
