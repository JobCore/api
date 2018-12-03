from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.contrib.postgres.fields import JSONField
from django.dispatch import receiver
from django.core.validators import RegexValidator

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

class Employer(models.Model):
    title = models.TextField(max_length=100, blank=True)
    website = models.CharField(max_length=30, blank=True)
    bio = models.TextField(max_length=250, blank=True)
    response_time = models.IntegerField(blank=True, default=0)  # in minutes
    rating = models.DecimalField(
        max_digits=2, decimal_places=1, default=0, blank=True)
    automatically_accept_from_favlists = models.BooleanField(default=True)
    total_ratings = models.IntegerField(blank=True, default=0)  # in minutes
    badges = models.ManyToManyField(Badge, blank=True)
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
    maximum_job_distance_miles = models.IntegerField(default=50)
    positions = models.ManyToManyField(
        Position, blank=True)
    job_count = models.IntegerField(default=0, blank=True)
    badges = models.ManyToManyField(Badge, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    
    def __str__(self):
        return self.user.email

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
    state = models.CharField(max_length=30, blank=True)
    zip_code = models.IntegerField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=14, decimal_places=11, default=0)
    longitude = models.DecimalField(max_digits=14, decimal_places=11, default=0)
    
    birth_date = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=17, blank=True) # validators should be a list
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, blank=True, null=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, blank=True, null=True)
    status = models.CharField(
        max_length=25,
        choices=PROFILE_STATUS,
        default=PENDING,
        blank=True)

    def __str__(self):
        return self.user.username
        
WEEKLY = 'WEEKLY'
MONTHLY = 'MONTHLY'
RECURRENCY_TYPE = (
    (WEEKLY, 'Weekly'),
    (MONTHLY, 'Monthly'),
)
class AvailabilityBlock(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, blank=True)
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
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.title

class Venue(models.Model):
    title = models.TextField(max_length=100, blank=True)
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
EXPIRED = 'EXPIRED' #si todavia no ha sido pagado
COMPLETED = 'COMPLETED' #si ya fue pagado
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
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, blank=True)
    position = models.ForeignKey(
        Position, on_delete=models.CASCADE, blank=True)
    application_restriction = models.CharField(
        max_length=20,
        choices=SHIFT_APPLICATION_RESTRICTIONS,
        default=ANYONE,
        blank=True)
    maximum_allowed_employees = models.IntegerField(default=0, blank=True)
    #maximum_checkin_delay_minutes = models.IntegerField(default=30, blank=True)
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
        Employee, blank=True, related_name="shift_accepted_employees", through='ShiftEmployee')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return "{} at {} on {}".format(self.position, self.venue, self.starting_at)
        
class ShiftEmployee(models.Model):
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, blank=True)
    success = models.BooleanField(default=True)
    comments = models.TextField(max_length=450, blank=True)
        
class ShiftApplication(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, blank=True)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

PENDING = 'PENDING'
APPLIED = 'APPLIED'
REJECTED = 'REJECTED'
SHIFT_INVITE_STATUS_CHOICES = (
    (PENDING, 'Pending'),
    (APPLIED, 'Applied'),
    (REJECTED, 'Rejected'),
)
class ShiftInvite(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, blank=True)
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=True, default=None)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, blank=True)
    status = models.CharField(
        max_length=9,
        choices=SHIFT_INVITE_STATUS_CHOICES,
        default=PENDING,
        blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

PENDING = 'PENDING'
ACCEPTED = 'ACCEPTED'
JOBCORE_INVITE_STATUS_CHOICES = (
    (PENDING, 'Pending'),
    (ACCEPTED, 'Accepted'),
)
class JobCoreInvite(models.Model):
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=True)
    first_name = models.TextField(max_length=100, blank=True)
    last_name = models.TextField(max_length=100, blank=True)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, blank=True, default=None, null=True)
    email = models.TextField(max_length=100, blank=True)
    status = models.CharField(
        max_length=9,
        choices=JOBCORE_INVITE_STATUS_CHOICES,
        default=PENDING,
        blank=True)
    phone_number = models.CharField(max_length=17, blank=True) # validators should be a list
    token = models.TextField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

class Rate(models.Model):
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, blank=True, null=True)
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, blank=True, null=True)
    rating = models.DecimalField(
        max_digits=2, decimal_places=1, default=0, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    
class FCMDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    registration_id = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return self.user.username


class Notification(models.Model):
    user = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE, blank=True, null=True)
    title = models.TextField()
    body = models.TextField()
    data = models.TextField(max_length=1500)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.user.username


APPROVED = 'APPROVED'
PENDING = 'PENDING'
PAID = 'PAID'
CLOCKIN_STATUS = (
    (APPROVED, 'Approved'),
    (PENDING, 'Pending'),
    (PAID, 'Paid')
)  

class Clockin(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, blank=True)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, blank=True)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=True, null=True)
    started_at = models.DateTimeField(blank=True)
    latitude = models.DecimalField(max_digits=14, decimal_places=11, default=0)
    longitude = models.DecimalField(max_digits=14, decimal_places=11, default=0)
    ended_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    status = models.CharField(
        max_length=9,
        choices=CLOCKIN_STATUS,
        default=PENDING)