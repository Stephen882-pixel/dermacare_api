# patients/models.py

from django.db import models
from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField


class Patient(models.Model):
    BLOOD_TYPES = (
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('unknown', 'Unknown'),
    )
    
    SKIN_TYPES = (
        ('I', 'Type I - Always burns, never tans'),
        ('II', 'Type II - Usually burns, tans minimally'),
        ('III', 'Type III - Sometimes burns, tans gradually'),
        ('IV', 'Type IV - Burns minimally, always tans well'),
        ('V', 'Type V - Very rarely burns, tans very easily'),
        ('VI', 'Type VI - Never burns, always tans darkly'),
    )
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_profile')
    patient_id = models.CharField(max_length=20, unique=True, help_text="Auto-generated patient ID")
    
    # Personal information
    middle_name = models.CharField(max_length=50, blank=True)
    preferred_name = models.CharField(max_length=50, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    
    # Medical information
    blood_type = models.CharField(max_length=10, choices=BLOOD_TYPES, default='unknown')
    skin_type = models.CharField(max_length=5, choices=SKIN_TYPES, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Height in cm")
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Weight in kg")
    
    # Contact preferences
    preferred_contact_method = models.CharField(
        max_length=10,
        choices=[('email', 'Email'), ('sms', 'SMS'), ('call', 'Phone Call')],
        default='email'
    )
    preferred_language = models.CharField(max_length=50, default='English')
    
    # Insurance information
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_number = models.CharField(max_length=50, blank=True)
    insurance_valid_until = models.DateField(null=True, blank=True)
    
    # Referral information
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    referral_source = models.CharField(
        max_length=50,
        choices=[
            ('doctor', 'Doctor Referral'),
            ('friend', 'Friend/Family'),
            ('online', 'Online Search'),
            ('social_media', 'Social Media'),
            ('advertisement', 'Advertisement'),
            ('other', 'Other')
        ],
        blank=True
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient_id} - {self.user.get_full_name()}"

    def save(self, *args, **kwargs):
        if not self.patient_id:
            # Generate patient ID: PAT + year + sequential number
            from datetime import datetime
            year = datetime.now().year
            last_patient = Patient.objects.filter(
                patient_id__startswith=f'PAT{year}'
            ).order_by('-patient_id').first()
            
            if last_patient:
                last_number = int(last_patient.patient_id[-4:])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.patient_id = f'PAT{year}{new_number:04d}'
        
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'patients_patient'
        ordering = ['-created_at']


class MedicalHistory(models.Model):
    CONDITION_TYPES = (
        ('skin', 'Skin Condition'),
        ('allergy', 'Allergy'),
        ('surgery', 'Surgery'),
        ('medication', 'Medication'),
        ('family_history', 'Family History'),
        ('other', 'Other'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_history')
    condition_type = models.CharField(max_length=20, choices=CONDITION_TYPES)
    condition_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date_diagnosed = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=True)
    severity = models.CharField(
        max_length=10,
        choices=[('mild', 'Mild'), ('moderate', 'Moderate'), ('severe', 'Severe')],
        blank=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.patient_id} - {self.condition_name}"

    class Meta:
        db_table = 'patients_medical_history'
        ordering = ['-date_diagnosed', '-created_at']


class PatientDocument(models.Model):
    DOCUMENT_TYPES = (
        ('id', 'ID Card'),
        ('insurance', 'Insurance Card'),
        ('medical_report', 'Medical Report'),
        ('prescription', 'Prescription'),
        ('lab_result', 'Lab Result'),
        ('consent_form', 'Consent Form'),
        ('other', 'Other'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='patient_documents/')
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_sensitive = models.BooleanField(default=True)
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.patient_id} - {self.title}"

    class Meta:
        db_table = 'patients_document'
        ordering = ['-created_at']