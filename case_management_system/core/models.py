import uuid
from django.db import models

class ClientStatus(models.Model):
    code = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(null=True, blank=True)
    color_hex = models.CharField(max_length=7, null=True, blank=True)

    def __str__(self):
        return self.name

class Language(models.Model):
    code = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=255)
    native_name = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

class Pronoun(models.Model):
    code = models.CharField(max_length=50, primary_key=True)
    display_text = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.display_text

class SexValue(models.Model):
    code = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

class Client(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    status = models.ForeignKey(
        ClientStatus,
        on_delete=models.PROTECT,
        to_field='code'
    )
    primary_language = models.ForeignKey(
        Language,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        to_field='code'
    )
    pronoun = models.ForeignKey(
        Pronoun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        to_field='code'
    )
    sex = models.ForeignKey(
        SexValue,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        to_field='code'
    )
    interpreter_needed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField()  # Placeholder
    updated_by = models.UUIDField()  # Placeholder
    deleted_at = models.DateTimeField(null=True, blank=True) # Added for soft delete

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        indexes = [
            models.Index(fields=['last_name', 'first_name'], name='idx_clients_name'),
            models.Index(fields=['email'], name='idx_clients_email'),
            models.Index(fields=['phone'], name='idx_clients_phone'),
        ]
