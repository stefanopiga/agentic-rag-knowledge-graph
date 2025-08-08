from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class Tenant(models.Model):
    """
    Rappresenta un tenant nel sistema multi-tenant.
    Ogni tenant può essere un'istituzione educativa, uno studio medico, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="Nome Tenant")
    slug = models.SlugField(unique=True, max_length=100, verbose_name="Slug")
    description = models.TextField(blank=True, null=True, verbose_name="Descrizione")
    
    # Subscription info
    subscription_type = models.CharField(
        max_length=50, 
        choices=[
            ('free', 'Gratuito'),
            ('premium', 'Premium'),
            ('enterprise', 'Enterprise'),
        ],
        default='free',
        verbose_name="Tipo Abbonamento"
    )
    
    # Limits
    max_users = models.PositiveIntegerField(default=5, verbose_name="Massimo Utenti")
    max_documents = models.PositiveIntegerField(default=100, verbose_name="Massimo Documenti")
    max_storage_mb = models.PositiveIntegerField(default=1000, verbose_name="Massimo Storage (MB)")
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name="Attivo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creato il")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aggiornato il")
    
    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        db_table = 'accounts_tenant'
        
    def __str__(self):
        return self.name


class User(AbstractUser):
    """
    Utente personalizzato per il sistema medico multi-tenant.
    """
    # Usando AutoField per compatibilità con Django admin
    
    # Tenant association
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name='users',
        verbose_name="Tenant"
    )
    
    # Profile info
    display_name = models.CharField(max_length=255, blank=True, verbose_name="Nome Visualizzato")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Avatar")
    bio = models.TextField(blank=True, null=True, verbose_name="Biografia")
    
    # Professional info
    profession = models.CharField(
        max_length=100,
        choices=[
            ('student', 'Studente'),
            ('physiotherapist', 'Fisioterapista'),
            ('doctor', 'Medico'),
            ('researcher', 'Ricercatore'),
            ('educator', 'Docente'),
            ('other', 'Altro'),
        ],
        blank=True,
        verbose_name="Professione"
    )
    
    institution = models.CharField(max_length=255, blank=True, verbose_name="Istituzione")
    
    # Permissions
    role = models.CharField(
        max_length=50,
        choices=[
            ('admin', 'Amministratore'),
            ('educator', 'Docente'),
            ('student', 'Studente'),
            ('viewer', 'Visualizzatore'),
        ],
        default='student',
        verbose_name="Ruolo"
    )
    
    # Usage tracking
    last_activity = models.DateTimeField(null=True, blank=True, verbose_name="Ultima Attività")
    quiz_taken = models.PositiveIntegerField(default=0, verbose_name="Quiz Completati")
    documents_accessed = models.PositiveIntegerField(default=0, verbose_name="Documenti Consultati")
    
    # Preferences
    preferred_language = models.CharField(max_length=10, default='it', verbose_name="Lingua Preferita")
    notifications_enabled = models.BooleanField(default=True, verbose_name="Notifiche Abilitate")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creato il")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aggiornato il")
    
    class Meta:
        verbose_name = "Utente"
        verbose_name_plural = "Utenti"
        db_table = 'accounts_user'
        
    def __str__(self):
        return f"{self.display_name or self.username} ({self.tenant.name})"
        
    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = f"{self.first_name} {self.last_name}".strip() or self.username
        super().save(*args, **kwargs)
