# appointments/models.py

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import datetime, timedelta


class AppointmentType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    color = models.CharField(max_length=7, default="#3498db", help_text="Hex color code for calendar display")
    is_consultation = models.BooleanField(default=True)
    requires_preparation = models.BooleanField(default=False)
    preparation_instructions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'appointments_type'
        ordering = ['name']


class Appointment(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    )

    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    CONSULTATION_TYPES = (
        ('in_person', 'In Person'),
        ('virtual', 'Virtual/Online'),
        ('phone', 'Phone Consultation'),
    )

    # Core appointment details
    appointment_id = models.CharField(max_length=20, unique=True, help_text="Auto-generated appointment ID")
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='appointments')
    service = models.ForeignKey('services.Service', on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments')
    appointment_type = models.ForeignKey(AppointmentType, on_delete=models.CASCADE, related_name='appointments')
    
    # Scheduling details
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    end_time = models.TimeField(null=True, blank=True)
    
    # Status and type
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    consultation_type = models.CharField(max_length=20, choices=CONSULTATION_TYPES, default='in_person')
    
    # Appointment details
    chief_complaint = models.TextField(blank=True, help_text="Primary reason for visit")
    symptoms = models.TextField(blank=True, help_text="Current symptoms described by patient")
    notes = models.TextField(blank=True, help_text="Additional notes or special instructions")
    
    # Follow-up information
    is_follow_up = models.BooleanField(default=False)
    previous_appointment = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='follow_ups')
    
    # Booking information
    booked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='booked_appointments')
    booking_source = models.CharField(
        max_length=20,
        choices=[
            ('online', 'Online Booking'),
            ('phone', 'Phone Call'),
            ('walk_in', 'Walk In'),
            ('staff', 'Staff Booking'),
            ('referral', 'Referral'),
        ],
        default='online'
    )
    
    # Confirmation and reminders
    is_confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Check-in information
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='checked_in_appointments'
    )
    
    # Completion information
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    actual_duration = models.PositiveIntegerField(null=True, blank=True, help_text="Actual duration in minutes")
    
    # Cancellation information
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='cancelled_appointments'
    )
    cancellation_reason = models.TextField(blank=True)
    
    # Virtual appointment details
    meeting_link = models.URLField(blank=True, help_text="Link for virtual consultations")
    meeting_id = models.CharField(max_length=100, blank=True)
    meeting_password = models.CharField(max_length=50, blank=True)
    
    # Billing
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.appointment_id} - {self.patient.user.get_full_name()} with {self.doctor.full_name}"

    def save(self, *args, **kwargs):
        if not self.appointment_id:
            # Generate appointment ID: APT + year + month + sequential number
            now = timezone.now()
            prefix = f'APT{now.year}{now.month:02d}'
            last_appointment = Appointment.objects.filter(
                appointment_id__startswith=prefix
            ).order_by('-appointment_id').first()
            
            if last_appointment:
                last_number = int(last_appointment.appointment_id[-4:])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.appointment_id = f'{prefix}{new_number:04d}'
        
        # Calculate end time if not provided
        if not self.end_time and self.appointment_time and self.duration:
            start_datetime = datetime.combine(self.appointment_date, self.appointment_time)
            end_datetime = start_datetime + timedelta(minutes=self.duration)
            self.end_time = end_datetime.time()
        
        super().save(*args, **kwargs)

    @property
    def is_past_due(self):
        """Check if appointment is past its scheduled time"""
        appointment_datetime = datetime.combine(self.appointment_date, self.appointment_time)
        return timezone.now() > timezone.make_aware(appointment_datetime)

    @property
    def can_be_cancelled(self):
        """Check if appointment can still be cancelled (24 hours before)"""
        appointment_datetime = datetime.combine(self.appointment_date, self.appointment_time)
        cutoff_time = timezone.make_aware(appointment_datetime) - timedelta(hours=24)
        return timezone.now() < cutoff_time

    class Meta:
        db_table = 'appointments_appointment'
        ordering = ['appointment_date', 'appointment_time']
        unique_together = ['doctor', 'appointment_date', 'appointment_time']


class AppointmentReschedule(models.Model):
    original_appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='reschedules')
    old_date = models.DateField()
    old_time = models.TimeField()
    new_date = models.DateField()
    new_time = models.TimeField()
    reason = models.TextField(blank=True)
    rescheduled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rescheduled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reschedule for {self.original_appointment.appointment_id}"

    class Meta:
        db_table = 'appointments_reschedule'


class AppointmentNote(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='appointment_notes')
    note_type = models.CharField(
        max_length=20,
        choices=[
            ('general', 'General Note'),
            ('medical', 'Medical Note'),
            ('billing', 'Billing Note'),
            ('follow_up', 'Follow-up Note'),
            ('reminder', 'Reminder'),
        ],
        default='general'
    )
    content = models.TextField()
    is_private = models.BooleanField(default=False, help_text="Only visible to staff")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note for {self.appointment.appointment_id}"

    class Meta:
        db_table = 'appointments_note'
        ordering = ['-created_at']


class WaitingList(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='waiting_list_entries')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='waiting_list')
    service = models.ForeignKey('services.Service', on_delete=models.CASCADE, null=True, blank=True)
    preferred_date = models.DateField(null=True, blank=True)
    preferred_time = models.TimeField(null=True, blank=True)
    earliest_date = models.DateField()
    latest_date = models.DateField()
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Waiting list: {self.patient.user.get_full_name()} for {self.doctor.full_name}"

    class Meta:
        db_table = 'appointments_waiting_list'
        ordering = ['created_at']