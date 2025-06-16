# doctors/models.py

from django.db import models
from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField


class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'doctors_specialization'
        ordering = ['name']


class Doctor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_profile')
    title = models.CharField(max_length=50, default='Dr.')  # Dr., Prof., etc.
    specializations = models.ManyToManyField(Specialization, related_name='doctors')
    license_number = models.CharField(max_length=50, unique=True)
    years_of_experience = models.PositiveIntegerField()
    biography = models.TextField()
    education = models.TextField(help_text="Educational background")
    certifications = models.TextField(blank=True, help_text="Professional certifications")
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    profile_image = models.ImageField(upload_to='doctors/profiles/', blank=True, null=True)
    
    # Social media links
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    
    # Professional details
    hospital_affiliations = models.TextField(blank=True)
    research_interests = models.TextField(blank=True)
    publications = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} {self.user.first_name} {self.user.last_name}"

    @property
    def full_name(self):
        return f"{self.title} {self.user.first_name} {self.user.last_name}"

    class Meta:
        db_table = 'doctors_doctor'
        ordering = ['user__first_name', 'user__last_name']


class DoctorAvailability(models.Model):
    DAYS_OF_WEEK = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='availability')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    max_patients = models.PositiveIntegerField(default=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.doctor.full_name} - {self.get_day_of_week_display()} ({self.start_time}-{self.end_time})"

    class Meta:
        db_table = 'doctors_availability'
        unique_together = ['doctor', 'day_of_week', 'start_time']
        ordering = ['day_of_week', 'start_time']


class DoctorLeave(models.Model):
    LEAVE_TYPES = (
        ('vacation', 'Vacation'),
        ('sick', 'Sick Leave'),
        ('conference', 'Conference'),
        ('emergency', 'Emergency'),
        ('other', 'Other'),
    )
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.doctor.full_name} - {self.get_leave_type_display()} ({self.start_date} to {self.end_date})"

    class Meta:
        db_table = 'doctors_leave'
        ordering = ['-start_date']