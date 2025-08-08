from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class ChatSession(models.Model):
    """
    Sessioni di chat per le conversazioni RAG degli utenti
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE, verbose_name="Tenant")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions', verbose_name="Utente")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadata")
    is_active = models.BooleanField(default=True, verbose_name="Attiva")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creata il")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aggiornata il")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Scade il")
    
    class Meta:
        verbose_name = "Sessione Chat"
        verbose_name_plural = "Sessioni Chat"
        db_table = 'rag_engine_chatsession'
        ordering = ['-updated_at']
        
    def __str__(self):
        return f"Chat {self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class ChatMessage(models.Model):
    """
    Messaggi individuali all'interno delle sessioni di chat
    """
    MESSAGE_TYPES = [
        ('user', 'Utente'),
        ('assistant', 'Assistente'),
        ('system', 'Sistema'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages', verbose_name="Sessione")
    content = models.TextField(verbose_name="Contenuto")
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, verbose_name="Tipo Messaggio")
    
    # RAG-specific metadata
    sources = models.JSONField(default=list, blank=True, verbose_name="Fonti")
    search_query = models.TextField(blank=True, null=True, verbose_name="Query di Ricerca")
    retrieved_chunks = models.JSONField(default=list, blank=True, verbose_name="Chunks Recuperati")
    processing_time_ms = models.PositiveIntegerField(null=True, blank=True, verbose_name="Tempo Elaborazione (ms)")
    model_used = models.CharField(max_length=100, blank=True, null=True, verbose_name="Modello Utilizzato")
    
    # Feedback and quality
    user_rating = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Valutazione Utente")
    is_helpful = models.BooleanField(null=True, blank=True, verbose_name="Utile")
    feedback_text = models.TextField(blank=True, null=True, verbose_name="Feedback Testuale")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creato il")
    
    class Meta:
        verbose_name = "Messaggio Chat"
        verbose_name_plural = "Messaggi Chat"
        db_table = 'rag_engine_chatmessage'
        ordering = ['created_at']
        
    def __str__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.message_type}: {content_preview}"


class QueryAnalytics(models.Model):
    """
    Analytics per tracciare le performance e i pattern delle query RAG
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('accounts.Tenant', on_delete=models.CASCADE, verbose_name="Tenant")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Utente")
    
    # Query information
    query_text = models.TextField(verbose_name="Testo Query")
    query_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="Tipo Query")
    query_intent = models.CharField(max_length=100, blank=True, null=True, verbose_name="Intento Query")
    
    # Results and performance
    results_count = models.PositiveIntegerField(default=0, verbose_name="Numero Risultati")
    response_time_ms = models.PositiveIntegerField(verbose_name="Tempo Risposta (ms)")
    search_time_ms = models.PositiveIntegerField(null=True, blank=True, verbose_name="Tempo Ricerca (ms)")
    generation_time_ms = models.PositiveIntegerField(null=True, blank=True, verbose_name="Tempo Generazione (ms)")
    
    # Model and sources
    embedding_model = models.CharField(max_length=100, blank=True, null=True, verbose_name="Modello Embedding")
    llm_model = models.CharField(max_length=100, blank=True, null=True, verbose_name="Modello LLM")
    sources_used = models.JSONField(default=list, blank=True, verbose_name="Fonti Utilizzate")
    chunks_retrieved = models.PositiveIntegerField(default=0, verbose_name="Chunks Recuperati")
    
    # Quality metrics
    relevance_score = models.FloatField(null=True, blank=True, verbose_name="Score Rilevanza")
    confidence_score = models.FloatField(null=True, blank=True, verbose_name="Score Confidenza")
    user_satisfaction = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Soddisfazione Utente")
    
    # Success flags
    was_successful = models.BooleanField(default=True, verbose_name="Successo")
    error_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tipo Errore")
    error_message = models.TextField(blank=True, null=True, verbose_name="Messaggio Errore")
    
    # Context
    session_id = models.UUIDField(null=True, blank=True, verbose_name="ID Sessione")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Indirizzo IP")
    user_agent = models.TextField(blank=True, null=True, verbose_name="User Agent")
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")
    
    class Meta:
        verbose_name = "Query Analytics"
        verbose_name_plural = "Query Analytics"
        db_table = 'rag_engine_queryanalytics'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['tenant', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['was_successful', 'timestamp']),
        ]
        
    def __str__(self):
        user_info = f"{self.user.username}" if self.user else "Anonymous"
        return f"Query {user_info} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
