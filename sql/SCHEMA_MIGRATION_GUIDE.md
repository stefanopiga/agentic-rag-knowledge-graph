# 🚀 **SCHEMA MIGRATION GUIDE**

## 📋 **OVERVIEW**

Schema completo che integra:

- ✅ **Sistema RAG originale** (documents, chunks, embeddings)
- ✅ **Autenticazione Django** (auth_user, accounts_user)
- ✅ **Multi-tenancy** (tenant isolation + RLS)
- ✅ **Sistema Quiz** (completo per mobile app)
- ✅ **Analytics** (tracking query e performance)

---

## 🔄 **MIGRAZIONE DA SCHEMA LEGACY**

### **STEP 1: Deploy su Neon**

```sql
-- Esegui schema_with_auth.sql su Neon PostgreSQL
psql -h your-neon-host -d your-db -f sql/schema_with_auth.sql
```

### **STEP 2: Configurazione Django**

```python
# fisio-rag-saas/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_neon_db',
        'USER': 'your_neon_user',
        'PASSWORD': 'your_neon_password',
        'HOST': 'your-neon-host.neon.tech',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}
```

### **STEP 3: Fake Initial Migration**

```bash
cd fisio-rag-saas
python manage.py migrate --fake-initial
```

---

## 🏗️ **STRUTTURA SCHEMA**

### **🔐 MULTI-TENANCY**

```sql
accounts_tenant          -- Aziende/organizzazioni
├── accounts_user        -- Utenti del tenant
├── documents           -- Documenti per tenant
├── chunks              -- Chunks per tenant
└── rag_engine_*        -- Chat/analytics per tenant
```

### **📚 SISTEMA RAG**

```sql
documents                -- Documenti caricati
├── chunks              -- Chunks con embeddings
├── document_ingestion_status -- Tracking caricamento
└── medical_content_medicalcategory -- Categorie mediche
```

### **🧠 SISTEMA QUIZ**

```sql
medical_content_quiz            -- Quiz creati
├── medical_content_quizquestion -- Domande
├── medical_content_quizanswer   -- Risposte
├── medical_content_quizattempt  -- Tentativi utenti
└── medical_content_quizanalytics -- Analytics quiz
```

### **💬 CHAT ENGINE**

```sql
rag_engine_chatsession   -- Sessioni chat
├── rag_engine_chatmessage -- Messaggi
└── rag_engine_queryanalytics -- Analytics query
```

---

## 🔧 **FUNZIONI RAG (Multi-tenant)**

### **Vector Search**

```sql
SELECT * FROM match_chunks(
    'tenant-uuid',           -- ID tenant
    '[0.1, 0.2, ...]',      -- Embedding query
    10                       -- Limit risultati
);
```

### **Hybrid Search**

```sql
SELECT * FROM hybrid_search(
    'tenant-uuid',           -- ID tenant
    '[0.1, 0.2, ...]',      -- Embedding query
    'testo query',           -- Testo per full-text search
    10,                      -- Limit risultati
    0.3                      -- Peso text search (0-1)
);
```

### **Document Chunks**

```sql
SELECT * FROM get_document_chunks(
    'tenant-uuid',           -- ID tenant
    'document-uuid'          -- ID documento
);
```

---

## 🛡️ **SICUREZZA (RLS)**

### **Row Level Security**

- **Abilitato** su tutte le tabelle tenant-aware
- **Policies** configurate per isolamento completo
- **Django middleware** gestisce tenant context

### **Tenant Isolation**

```sql
-- Ogni query automaticamente filtrata per tenant
WHERE tenant_id = current_tenant_id()
```

---

## 📊 **DIFFERENZE SCHEMA LEGACY**

### **🆕 AGGIUNTE**

| Tabella             | Scopo            |
| ------------------- | ---------------- |
| `accounts_tenant`   | Multi-tenancy    |
| `accounts_user`     | Utenti avanzati  |
| `medical_content_*` | Categorie e quiz |
| `rag_engine_*`      | Chat e analytics |

### **🔄 MODIFICHE**

| Tabella     | Modifica                       |
| ----------- | ------------------------------ |
| `documents` | +`tenant_id`, +metadata medici |
| `chunks`    | +`tenant_id`, +denorm data     |
| `sessions`  | +`tenant_id` (legacy compat)   |
| `messages`  | +`tenant_id` (legacy compat)   |

### **🗂️ FUNZIONI**

| Funzione                | Modifica               |
| ----------------------- | ---------------------- |
| `match_chunks()`        | +`tenant_id` parameter |
| `hybrid_search()`       | +`tenant_id`, italiano |
| `get_document_chunks()` | +`tenant_id` parameter |

---

## 🎯 **UTILIZZO DEVELOPMENT**

### **1. Setup Locale**

```bash
# Installa PostgreSQL + pgvector
# Oppure usa Neon direttamente
```

### **2. Carica Schema**

```bash
psql -d your_db -f sql/schema_with_auth.sql
```

### **3. Django Setup**

```bash
cd fisio-rag-saas
python manage.py migrate --fake-initial
python manage.py createsuperuser
python manage.py runserver
```

### **4. Test Pipeline**

```bash
# Testa ingestion con tenant
python -c "from ingestion.ingest import DocumentIngestionPipeline; ..."
```

---

## 🚀 **PRODUCTION DEPLOYMENT**

### **Neon PostgreSQL**

1. Crea database su Neon
2. Abilita pgvector extension
3. Carica `schema_with_auth.sql`
4. Configura Django DATABASE_URL

### **Django + Vercel**

1. Deploy Django app su Vercel
2. Configura environment variables
3. Run migrations (fake-initial)
4. Setup admin user

### **Mobile App**

1. API endpoints già pronti
2. JWT authentication
3. Multi-tenant support
4. Quiz system integrato

---

## 📋 **CHECKLIST MIGRAZIONE**

- [ ] Schema deployato su Neon
- [ ] Django configurato per Neon
- [ ] Migrations fake-initial eseguite
- [ ] Admin user creato
- [ ] Categorie mediche caricate
- [ ] Test tenant default funzionante
- [ ] RAG functions testate
- [ ] Quiz system verificato
- [ ] Analytics tracking attivo

---

## 🆘 **TROUBLESHOOTING**

### **Errore: "relation does not exist"**

```bash
# Verifica che il schema sia stato caricato
psql -d your_db -c "\dt"
```

### **Errore: "permission denied"**

```bash
# Verifica RLS policies
psql -d your_db -c "SELECT * FROM pg_policies;"
```

### **Errore Django migrations**

```bash
# Reset migrations se necessario
python manage.py migrate --fake accounts zero
python manage.py migrate --fake-initial
```

---

## 📈 **PERFORMANCE NOTES**

### **Indexes Ottimizzati**

- ✅ Vector search (ivfflat)
- ✅ Text search (GIN trgm)
- ✅ Tenant isolation
- ✅ Foreign keys
- ✅ Created_at columns

### **Query Optimization**

- ✅ Denormalized data in chunks
- ✅ Proper JOIN strategies
- ✅ Limited result sets
- ✅ Tenant-aware functions

---

**Schema Version**: 2.0 - Production Ready  
**Compatibility**: Django 4.2+, PostgreSQL 14-17 (17 raccomandato), pgvector 0.5+  
**Optimized for**: PostgreSQL 17 performance improvements  
**Last Updated**: 2025-08-03
