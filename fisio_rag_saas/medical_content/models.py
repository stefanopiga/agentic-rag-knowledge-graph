from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class MedicalCategory(models.Model):
    """
    Categorie mediche per l'organizzazione dei contenuti
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE, verbose_name="Tenant")
    name = models.CharField(max_length=255, verbose_name="Nome Categoria")
    slug = models.SlugField(max_length=100, verbose_name="Slug")
    description = models.TextField(blank=True, null=True, verbose_name="Descrizione")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Categoria Padre")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordine")
    is_active = models.BooleanField(default=True, verbose_name="Attiva")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creata il")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aggiornata il")
    
    class Meta:
        verbose_name = "Categoria Medica"
        verbose_name_plural = "Categorie Mediche"
        db_table = 'medical_content_medicalcategory'
        unique_together = [['tenant', 'slug']]
        ordering = ['order', 'name']
        
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class QuizCategory(models.Model):
    """
    Categorie specifiche per i quiz
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE, verbose_name="Tenant")
    name = models.CharField(max_length=255, verbose_name="Nome Categoria Quiz")
    description = models.TextField(blank=True, null=True, verbose_name="Descrizione")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creata il")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aggiornata il")
    
    class Meta:
        verbose_name = "Categoria Quiz"
        verbose_name_plural = "Categorie Quiz"
        db_table = 'medical_content_quizcategory'
        
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class Quiz(models.Model):
    """
    Quiz interattivi generati dall'AI dai documenti medici
    """
    DIFFICULTY_CHOICES = [
        ('easy', 'Facile'),
        ('medium', 'Medio'),
        ('hard', 'Difficile'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE, verbose_name="Tenant")
    title = models.CharField(max_length=255, verbose_name="Titolo Quiz")
    description = models.TextField(blank=True, null=True, verbose_name="Descrizione")
    category = models.ForeignKey(QuizCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Categoria")
    
    # Metadata documenti sorgente
    source_documents = models.JSONField(default=list, blank=True, verbose_name="Documenti Sorgente")
    
    # Configurazione quiz
    difficulty_level = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium', verbose_name="Difficoltà")
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name="Limite Tempo (min)")
    passing_score = models.PositiveIntegerField(default=60, verbose_name="Punteggio Minimo (%)")
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name="Attivo")
    is_public = models.BooleanField(default=False, verbose_name="Pubblico")
    
    # AI Generation
    generated_by_ai = models.BooleanField(default=True, verbose_name="Generato da AI")
    generation_prompt = models.TextField(blank=True, null=True, verbose_name="Prompt Generazione")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creato il")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aggiornato il")
    
    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quiz"
        db_table = 'medical_content_quiz'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} ({self.difficulty_level})"


class QuizQuestion(models.Model):
    """
    Domande dei quiz
    """
    QUESTION_TYPES = [
        ('multiple_choice', 'Scelta Multipla'),
        ('true_false', 'Vero/Falso'),
        ('fill_blank', 'Riempi Spazi'),
        ('short_answer', 'Risposta Breve'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions', verbose_name="Quiz")
    question_text = models.TextField(verbose_name="Testo Domanda")
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice', verbose_name="Tipo Domanda")
    explanation = models.TextField(blank=True, null=True, verbose_name="Spiegazione")
    points = models.PositiveIntegerField(default=1, verbose_name="Punti")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordine")
    source_text = models.TextField(blank=True, null=True, verbose_name="Testo Sorgente")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creata il")
    
    class Meta:
        verbose_name = "Domanda Quiz"
        verbose_name_plural = "Domande Quiz"
        db_table = 'medical_content_quizquestion'
        ordering = ['order']
        
    def __str__(self):
        return f"{self.quiz.title} - Q{self.order}"


class QuizAnswer(models.Model):
    """
    Risposte possibili per le domande dei quiz
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='answers', verbose_name="Domanda")
    answer_text = models.TextField(verbose_name="Testo Risposta")
    is_correct = models.BooleanField(default=False, verbose_name="Risposta Corretta")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordine")
    explanation = models.TextField(blank=True, null=True, verbose_name="Spiegazione")
    
    class Meta:
        verbose_name = "Risposta Quiz"
        verbose_name_plural = "Risposte Quiz"
        db_table = 'medical_content_quizanswer'
        ordering = ['order']
        
    def __str__(self):
        return f"{self.question} - {self.answer_text[:50]}"


class QuizAttempt(models.Model):
    """
    Tentativi di completamento quiz da parte degli utenti
    """
    STATUS_CHOICES = [
        ('in_progress', 'In Corso'),
        ('completed', 'Completato'),
        ('abandoned', 'Abbandonato'),
        ('timed_out', 'Tempo Scaduto'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts', verbose_name="Quiz")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts', verbose_name="Utente")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress', verbose_name="Status")
    score = models.PositiveIntegerField(null=True, blank=True, verbose_name="Punteggio")
    max_score = models.PositiveIntegerField(verbose_name="Punteggio Massimo")
    time_taken_seconds = models.PositiveIntegerField(null=True, blank=True, verbose_name="Tempo Impiegato (sec)")
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Iniziato il")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Completato il")
    
    class Meta:
        verbose_name = "Tentativo Quiz"
        verbose_name_plural = "Tentativi Quiz"
        db_table = 'medical_content_quizattempt'
        ordering = ['-started_at']
        
    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} ({self.status})"


class QuizResponse(models.Model):
    """
    Risposte specifiche dell'utente alle domande del quiz
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='responses', verbose_name="Tentativo")
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, verbose_name="Domanda")
    selected_answer = models.ForeignKey(QuizAnswer, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Risposta Selezionata")
    text_answer = models.TextField(blank=True, null=True, verbose_name="Risposta Testuale")
    is_correct = models.BooleanField(verbose_name="Corretta")
    points_awarded = models.PositiveIntegerField(default=0, verbose_name="Punti Assegnati")
    answered_at = models.DateTimeField(auto_now_add=True, verbose_name="Risposto il")
    
    class Meta:
        verbose_name = "Risposta Quiz"
        verbose_name_plural = "Risposte Quiz"
        db_table = 'medical_content_quizresponse'
        unique_together = [['attempt', 'question']]
        
    def __str__(self):
        return f"{self.attempt.user.username} - {self.question}"


class QuizAnalytics(models.Model):
    """
    Analytics sui quiz per tracking performance e insights
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.OneToOneField(Quiz, on_delete=models.CASCADE, related_name='analytics', verbose_name="Quiz")
    total_attempts = models.PositiveIntegerField(default=0, verbose_name="Tentativi Totali")
    total_completions = models.PositiveIntegerField(default=0, verbose_name="Completamenti Totali")
    average_score = models.FloatField(default=0.0, verbose_name="Punteggio Medio")
    average_time_seconds = models.PositiveIntegerField(default=0, verbose_name="Tempo Medio (sec)")
    completion_rate = models.FloatField(default=0.0, verbose_name="Tasso Completamento")
    difficulty_rating = models.FloatField(default=0.0, verbose_name="Valutazione Difficoltà")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Ultimo Aggiornamento")
    
    class Meta:
        verbose_name = "Analytics Quiz"
        verbose_name_plural = "Analytics Quiz"
        db_table = 'medical_content_quizanalytics'
        
    def __str__(self):
        return f"Analytics: {self.quiz.title}"
