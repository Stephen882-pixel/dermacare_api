# clinic_config/models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from phonenumber_field.modelfields import PhoneNumberField


class ClinicSettings(models.Model):
    """Single instance model for clinic-wide settings"""
    # Clinic Information
    clinic_name = models.CharField(max_length=200, default="DermaCare Clinic")
    tagline = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='clinic/', blank=True, null=True)
    favicon = models.ImageField(upload_to='clinic/', blank=True, null=True)
    
    # Contact Information
    phone = PhoneNumberField()
    email = models.EmailField()
    website = models.URLField(blank=True)
    
    # Address
    address_line_1 = models.CharField(max_length=200)
    address_line_2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default="Kenya")
    
    # Social Media
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    
    # Business Hours
    timezone = models.CharField(max_length=50, default='Africa/Nairobi')
    
    # Appointment Settings
    appointment_buffer_minutes = models.PositiveIntegerField(
        default=15, 
        help_text="Buffer time between appointments in minutes"
    )
    max_advance_booking_days = models.PositiveIntegerField(
        default=60, 
        help_text="Maximum days in advance patients can book"
    )
    min_advance_booking_hours = models.PositiveIntegerField(
        default=24, 
        help_text="Minimum hours in advance for booking"
    )
    cancellation_deadline_hours = models.PositiveIntegerField(
        default=24, 
        help_text="Hours before appointment when cancellation is allowed"
    )
    
    # Notification Settings
    send_appointment_confirmations = models.BooleanField(default=True)
    send_appointment_reminders = models.BooleanField(default=True)
    reminder_hours_before = models.PositiveIntegerField(default=24)
    send_follow_up_reminders = models.BooleanField(default=True)
    
    # Financial Settings
    currency = models.CharField(max_length=3, default='KES')
    tax_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Emergency Contact
    emergency_phone = PhoneNumberField(blank=True, null=True)
    emergency_email = models.EmailField(blank=True)
    
    # System Settings
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.clinic_name

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and ClinicSettings.objects.exists():
            raise ValueError('Only one ClinicSettings instance is allowed')
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'clinic_config_settings'
        verbose_name = 'Clinic Settings'
        verbose_name_plural = 'Clinic Settings'


class BusinessHours(models.Model):
    DAYS_OF_WEEK = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )
    
    clinic = models.ForeignKey(ClinicSettings, on_delete=models.CASCADE, related_name='business_hours')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    is_open = models.BooleanField(default=True)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    
    # Lunch break (optional)
    lunch_break = models.BooleanField(default=False)
    lunch_start = models.TimeField(null=True, blank=True)
    lunch_end = models.TimeField(null=True, blank=True)
    
    notes = models.CharField(max_length=200, blank=True)

    def __str__(self):
        if self.is_open:
            return f"{self.get_day_of_week_display()}: {self.opening_time} - {self.closing_time}"
        return f"{self.get_day_of_week_display()}: Closed"

    class Meta:
        db_table = 'clinic_config_business_hours'
        unique_together = ['clinic', 'day_of_week']
        ordering = ['day_of_week']


class Holiday(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField()
    is_recurring = models.BooleanField(default=False, help_text="Recurring annually")
    description = models.TextField(blank=True)
    affects_appointments = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.date}"

    class Meta:
        db_table = 'clinic_config_holiday'
        ordering = ['date']


class EmailTemplate(models.Model):
    TEMPLATE_TYPES = (
        ('appointment_confirmation', 'Appointment Confirmation'),
        ('appointment_reminder', 'Appointment Reminder'),
        ('appointment_cancellation', 'Appointment Cancellation'),
        ('appointment_rescheduled', 'Appointment Rescheduled'),
        ('welcome_new_patient', 'Welcome New Patient'),
        ('follow_up_reminder', 'Follow-up Reminder'),
        ('birthday_wishes', 'Birthday Wishes'),
        ('newsletter', 'Newsletter'),
        ('lab_results_ready', 'Lab Results Ready'),
        ('payment_receipt', 'Payment Receipt'),
        ('custom', 'Custom Template'),
    )
    
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES, unique=True)
    subject = models.CharField(max_length=200)
    body_html = models.TextField(help_text="HTML email body")
    body_text = models.TextField(help_text="Plain text email body")
    is_active = models.BooleanField(default=True)
    
    # Template variables help text
    variables_help = models.TextField(
        blank=True,
        help_text="Available variables for this template (for admin reference)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"

    class Meta:
        db_table = 'clinic_config_email_template'
        ordering = ['template_type', 'name']


class SMSTemplate(models.Model):
    TEMPLATE_TYPES = (
        ('appointment_confirmation', 'Appointment Confirmation'),
        ('appointment_reminder', 'Appointment Reminder'),
        ('appointment_cancellation', 'Appointment Cancellation'),
        ('lab_results_ready', 'Lab Results Ready'),
        ('payment_reminder', 'Payment Reminder'),
        ('custom', 'Custom Template'),
    )
    
    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPES, unique=True)
    message = models.TextField(max_length=160, help_text="SMS message (max 160 characters)")
    is_active = models.BooleanField(default=True)
    
    # Template variables help text
    variables_help = models.TextField(
        blank=True,
        help_text="Available variables for this template (for admin reference)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"

    class Meta:
        db_table = 'clinic_config_sms_template'
        ordering = ['template_type', 'name']


class PaymentSettings(models.Model):
    # Payment gateway settings would be stored securely
    # This is a simplified version
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('insurance', 'Insurance'),
    )
    
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS, unique=True)
    is_enabled = models.BooleanField(default=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    processing_fee_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    processing_fee_fixed = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00
    )
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name

    class Meta:
        db_table = 'clinic_config_payment_settings'
        ordering = ['order', 'display_name']


class SystemNotification(models.Model):
    NOTIFICATION_TYPES = (
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
        ('maintenance', 'Maintenance'),
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    is_active = models.BooleanField(default=True)
    show_to_patients = models.BooleanField(default=False)
    show_to_staff = models.BooleanField(default=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'clinic_config_system_notification'
        ordering = ['-created_at']