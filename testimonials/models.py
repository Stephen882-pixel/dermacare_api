from django.db import models
from django.conf import settings


class Testimonial(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name='testimonials'
    )
    content = models.TextField()
    rating = models.PositiveIntegerField(
        default=5,
        help_text="Rating out of 5"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='testimonials'
    )
    doctor = models.ForeignKey(
        'doctors.Doctor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='testimonials'
    )
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_testimonials'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Testimonial by {self.patient.user.get_full_name()}"

    class Meta:
        db_table = 'testimonials_testimonial'
        ordering = ['-submitted_at']