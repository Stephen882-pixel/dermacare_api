# services/models.py

from django.db import models


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text="Font Awesome icon class")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'services_category'
        ordering = ['order', 'name']
        verbose_name_plural = 'Service Categories'



class Service(models.Model):
    DURATION_UNITS = (
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
    )
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name='services')
    short_description = models.CharField(max_length=300)
    detailed_description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in KES")
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    duration_unit = models.CharField(max_length=10, choices=DURATION_UNITS, default='minutes')
    
    # Requirements and preparations
    preparation_instructions = models.TextField(blank=True, help_text="What patient should do before appointment")
    post_treatment_care = models.TextField(blank=True, help_text="Post-treatment care instructions")
    contraindications = models.TextField(blank=True, help_text="When this service should not be performed")
    
    # Service details
    is_consultation_required = models.BooleanField(default=True)
    requires_referral = models.BooleanField(default=False)
    min_age = models.PositiveIntegerField(null=True, blank=True, help_text="Minimum age for this service")
    max_age = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum age for this service")
    
    # Availability
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    available_online = models.BooleanField(default=False, help_text="Can be done via telemedicine")
    
    # SEO and display
    meta_description = models.CharField(max_length=160, blank=True)
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'services_service'
        ordering = ['category', 'name']


class ServiceDoctorSpecialty(models.Model):
    """Junction table for services and doctors with specialization levels"""
    PROFICIENCY_LEVELS = (
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    )
    
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE)
    proficiency_level = models.CharField(max_length=20, choices=PROFICIENCY_LEVELS, default='basic')
    is_preferred_provider = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.doctor.full_name} - {self.service.name} ({self.get_proficiency_level_display()})"

    class Meta:
        db_table = 'services_doctor_specialty'
        unique_together = ['service', 'doctor']


class ServicePackage(models.Model):
    """For bundled services with discounts"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    services = models.ManyToManyField(Service, related_name='packages')
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    package_price = models.DecimalField(max_digits=10, decimal_places=2)
    validity_days = models.PositiveIntegerField(default=30, help_text="Package validity in days")
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='packages/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def discount_amount(self):
        return self.original_price - self.package_price

    @property
    def discount_percentage(self):
        if self.original_price > 0:
            return (self.discount_amount / self.original_price) * 100
        return 0

    class Meta:
        db_table = 'services_package'
        ordering = ['name']