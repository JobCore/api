import datetime
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Position(models.Model):
    title = models.TextField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self):
        return self.title

class Badge(models.Model):
    title = models.TextField(max_length=100, blank=True)
    image_url = models.TextField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self):
        return self.title

class Employer(models.Model):
    title = models.TextField(max_length=100, blank=True)
    website = models.CharField(max_length=30, blank=True)
    bio = models.TextField(max_length=250, blank=True)
    response_time = models.IntegerField(blank=True, default=0)  # in minutes
    rating = models.DecimalField(
        max_digits=2, decimal_places=1, default=0, blank=True)
    badges = models.ManyToManyField(Badge, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self):
        return self.title

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True)
    picture = models.URLField(blank=True)
    bio = models.TextField(max_length=250, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.user.username

class Employee(models.Model):
    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, blank=True)
    response_time = models.IntegerField(blank=True, default=0)  # in minutes
    minimum_hourly_rate = models.DecimalField(
        max_digits=3, decimal_places=1, default=0, blank=True)
    rating = models.DecimalField(
        max_digits=2, decimal_places=1, default=0, blank=True)
    positions = models.ManyToManyField(
        Position, blank=True)
    badges = models.ManyToManyField(Badge, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    
    def __str__(self):
        return self.profile.user.username

class FavoriteList(models.Model):
    title = models.TextField(max_length=100, blank=True)
    employees = models.ManyToManyField(Employee, blank=True)
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self):
        return self.title

class Venue(models.Model):
    title = models.TextField(max_length=100, blank=True)
    street_address = models.CharField(max_length=60, blank=True)
    country = models.CharField(max_length=30, blank=True)
    state = models.CharField(max_length=30, blank=True)
    zip_code = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self):
        return self.title


OPEN = 'OPEN'
FILLED = 'FILLED'
PAUSED = 'PAUSED'
DRAFT = 'DRAFT'
CANCELLED = 'CANCELLED'
SHIFT_STATUS_CHOICES = (
    (OPEN, 'Receiving candidates'),
    (FILLED, 'Filled'),
    (PAUSED, 'Paused'),
    (DRAFT, 'Draft'),
    (CANCELLED, 'Cancelled'),
)

FAVORITES = 'FAVORITES'
ANYONE = 'ANYONE'
SHIFT_APPLICATION_RESTRICTIONS = (
    (FAVORITES, 'Favorites Only'),
    (ANYONE, 'Anyone can apply')
)


class Shift(models.Model):
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, blank=True)
    position = models.ForeignKey(
        Position, on_delete=models.CASCADE, blank=True)
    application_restriction = models.CharField(
        max_length=9,
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
    status = models.CharField(
        max_length=9,
        choices=SHIFT_STATUS_CHOICES,
        default=DRAFT,
        blank=True)
    date = models.DateTimeField(blank=True)
    start_time = models.TimeField(blank=True)
    finish_time = models.TimeField(blank=True)
    rating = models.DecimalField(
        max_digits=2, decimal_places=1, default=0, blank=True)
    candidates = models.ManyToManyField(
        Employee, blank=True, through="ShiftApplication")
    employees = models.ManyToManyField(
        Employee, blank=True, related_name="shift_accepted_employees")
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self):
        return "{} at {} on {}".format(self.position, self.venue, self.date)
        
class ShiftApplication(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, blank=True)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)

DRAFT = 'DRAFT'
APPLIED = 'APPLIED'
REJECTED = 'CANCELLED'
SHIFT_INVITE_STATUS_CHOICES = (
    (DRAFT, 'Pending'),
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
        default=DRAFT,
        blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)

class JobCoreInvite(models.Model):
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=True)
    first_name = models.TextField(max_length=100, blank=True)
    last_name = models.TextField(max_length=100, blank=True)
    email = models.TextField(max_length=100, blank=True)
    token = models.TextField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)

class Rate(models.Model):
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, blank=True, null=True)
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, blank=True, null=True)
    rating = models.DecimalField(
        max_digits=2, decimal_places=1, default=0, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
