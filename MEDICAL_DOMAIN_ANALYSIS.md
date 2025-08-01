# Medical Domain Analysis - Agent OS Customization

## 🎯 Domain Overview

**Primary Use Case**: Sistema di studio per studenti universitari e medici
**Goal**: Permettere conversazione con documenti medici caricati per facilitare apprendimento
**Target Users**: Studenti medicina, medici in aggiornamento
**Value Proposition**: Estrazione precisa con riferimenti specifici ai documenti fonte

## 📚 Content Specification

### Document Formats

- ✅ PDF (primary format for medical texts)
- ✅ DOCX (editable medical documents)
- ✅ TXT (plain text medical notes)

### Language

- 🇮🇹 **Italiano** (primary language)
- **Medical terminology** in Italian

### Medical Specializations

1. **Caviglia e piede** (Ankle and foot)
2. **Ginocchio** (Knee)
3. **Lombopelvico** (Lumbopelvic)
4. **Lombare** (Lumbar)
5. **Toracico** (Thoracic)

## 🏥 Entity Structure Analysis

### Anatomical Structures (Strutture Anatomiche)

**Upper Limb**: Spalla, Gomito, Polso, Mano
**Lower Limb**: Anca, Ginocchio, Caviglia, Piede  
**Spine**: Colonna, Cervicale, Lombare, Toracica, Sacrale, Coccige
**Muscles**: Quadricipite, Bicipite, Tricipite, Deltoide, Trapezio, etc.
**Bones**: Femore, Tibia, Fibula, Omero, Radio, Ulna, etc.
**Soft Tissues**: Legamento, Tendine, Cartilagine, Menisco, Capsula, Fascia

### Pathological Conditions (Condizioni Patologiche)

**Trauma**: Lesione, Trauma, Strappo, Distorsione, Frattura, Lussazione
**Inflammation**: Infiammazione, Tendinite, Borsite, Artrite, Sinovite
**Degenerative**: Artrosi, Degenerazione, Usura, Deterioramento
**Symptoms**: Dolore, Algia, Sindrome, Rigidità, Edema, Instabilità

### Treatment Procedures (Procedure Terapeutiche)

**Manual Therapy**: Mobilizzazione, Manipolazione, Massaggio, Terapia manuale
**Exercise**: Esercizio, Rinforzo, Stretching, Propriocezione, Stabilizzazione
**Physical Agents**: Ultrasuoni, Laser, TENS, Crioterapia, Termoterapia
**Rehabilitation**: Riabilitazione, Fisioterapia, Chinesiologia, Recupero

### Medical Devices (Dispositivi Medici)

**Furniture**: Lettino, Panca, Cyclette, Tapis roulant
**Assessment**: Goniometro, Dinamometro, Test, Scala
**Support**: Tutore, Bendaggio, Ortesi, Plantare, Bastone
**Technology**: Elettrodo, Sonda, Sensore, Monitor

## 🎓 Educational Use Cases

### Typical Student Queries

- "Quali sono i muscoli coinvolti nella flessione del ginocchio?"
- "Come si tratta una distorsione di caviglia?"
- "Differenze tra tendinite e borsite alla spalla"
- "Protocollo riabilitativo per frattura del femore"
- "Anatomia del compartimento anteriore della gamba"

### Medical Professional Queries

- "Ultime evidenze per trattamento lombalgia cronica"
- "Controindicazioni elettrostimolazione in presenza di..."
- "Diagnosi differenziale dolore anteriore ginocchio"
- "Progressione esercizi post-intervento LCA"

## 💡 Customization Requirements

### System Prompt Specialization

```python
MEDICAL_PROMPT = """Sei un assistente AI specializzato in medicina riabilitativa e fisioterapia.
Hai accesso a una base di conoscenza di documenti medici in italiano e puoi analizzare
anatomia, patologie e trattamenti. Fornisci sempre riferimenti precisi ai documenti fonte."""
```

### Entity Extraction Priority

1. **High Priority**: Anatomical structures, pathological conditions
2. **Medium Priority**: Treatment procedures, symptoms
3. **Low Priority**: Medical devices, general terms

### Search Strategy

- **Vector Search**: Per sintomi, descrizioni cliniche, procedure
- **Graph Search**: Per relazioni anatomiche, progressioni patologiche
- **Hybrid Search**: Per casi clinici complessi, diagnosi differenziali

## 🔍 Next Information Needed

Per completare la pianificazione, ho bisogno di sapere:

### C. Requisiti Tecnici

1. **Volume documenti previsto**: Quanti documenti pensi di caricare inizialmente e nel tempo?
2. **Dimensioni tipiche**: I documenti sono brevi (articoli) o lunghi (libri di testo)?
3. **Frequenza aggiornamento**: Quanto spesso aggiungerai nuovi documenti?

### D. Performance & Usage

1. **Numero utenti**: Quanti studenti/medici useranno il sistema contemporaneamente?
2. **Response time**: Quanto veloce deve essere la risposta? (< 5 secondi OK?)
3. **Precision requirements**: È più importante non perdere informazioni o evitare risultati non rilevanti?

### E. Interface & Technical

1. **Interfaccia preferita**: Web UI, CLI, o entrambe?
2. **Budget API**: Preferisci OpenAI (costo moderato) o modelli locali Ollama (gratis ma meno performanti)?
3. **Privacy**: I documenti medici possono essere processati da servizi cloud o preferisci solo locale?

### F. Specific Features

1. **Citation style**: Come vuoi che vengano mostrati i riferimenti ai documenti?
2. **Multi-document queries**: Serve confrontare informazioni tra più documenti?
3. **Visual elements**: Serve supporto per immagini/diagrammi nei documenti?

Le informazioni che hai fornito sono **perfette** per iniziare. La struttura delle entità è molto professionale e completa!
