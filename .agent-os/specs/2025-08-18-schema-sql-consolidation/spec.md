# Spec Requirements Document

> Spec: SQL Schema Consolidation and Migration Strategy
> Created: 2025-08-18
> Status: Planning

## Overview

Consolidare i tre file di schema SQL esistenti (schema.sql legacy, schema_with_auth.sql production, section_tracking_schema.sql extension) in un singolo schema unificato e definire strategia di migrazione chiara. Questo elimina confusione nella gestione database, riduce maintenance overhead e garantisce coerenza tra ambienti development e production.

## User Stories

### Story 1: Schema Unificato per Development e Production

Come sviluppatore, voglio un singolo file schema che contenga tutte le tabelle e funzioni necessarie per development e production, così che non ci sia ambiguità su quale schema utilizzare e tutti gli ambienti siano consistenti.

Il sistema deve consolidare schema_with_auth.sql (production main) con section_tracking_schema.sql (extension) mantenendo tutte le feature di multi-tenancy e tracking, deprecando schema.sql legacy.

### Story 2: Migrazione Guidata da Legacy Schema

Come database administrator, voglio una strategia di migrazione chiara e script automatizzati per portare database esistenti da schema legacy a schema consolidato, così che possa aggiornare ambienti production senza data loss o downtime significativo.

Il sistema deve fornire migration scripts SQL che gestiscono ADD COLUMN, CREATE TABLE, data migration tra strutture legacy e consolidated schema.

### Story 3: Documentazione Schema Chiara

Come nuovo sviluppatore o ops engineer, voglio documentazione aggiornata che spieghi la struttura finale del database e come le tabelle si relazionano, così che possa comprendere rapidamente l'architettura senza dover analizzare file multipli.

Il sistema deve produrre documentazione schema consolidata che sostituisca DATABASE_ARCHITECTURE_EXPLAINED.md con informazioni accurate sul schema finale.

## Spec Scope

1. **Schema Analysis** - Analizzare differenze e sovrapposizioni tra i tre file schema esistenti per identificare conflicts e dependencies
2. **Consolidated Schema Creation** - Creare schema_consolidated.sql che combina production + extension features
3. **Migration Scripts** - Sviluppare migration SQL scripts per upgrade da legacy a consolidated schema
4. **Deprecation Strategy** - Definire piano per deprecare schema.sql legacy e transition plan
5. **Documentation Update** - Aggiornare DATABASE_ARCHITECTURE_EXPLAINED.md per riflettere schema consolidated

## Out of Scope

- Modifica dell'application code per adattarsi a schema changes (mantenere backward compatibility)
- Performance optimization del nuovo schema (focus su consolidation)
- Advanced migration tools oltre SQL scripts (no complex ETL)
- Database backup/restore automation (manual backup recommendation)
- Multi-version schema support (single target consolidated schema)

## Expected Deliverable

1. File schema_consolidated.sql che combina tutte le feature necessarie da production + extension schemas
2. Migration scripts SQL per upgrade da schema legacy a consolidated con data preservation
3. Documentazione aggiornata che descrive schema finale e deprecation plan per file legacy