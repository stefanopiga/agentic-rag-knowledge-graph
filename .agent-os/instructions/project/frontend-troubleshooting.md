# Frontend Troubleshooting - FisioRAG

## 🚨 PROBLEMI ATTUALI

### Problema Critico: Tailwind CSS 4.x Configuration

**Stato**: ❌ BLOCCANTE per visualizzazione UI

**Errore**:

```
Error: Cannot apply unknown utility class `text-text-primary`.
Are you using CSS modules or similar and missing @reference?
```

**Files interessati**:

- `frontend/src/index.css` (linea 28, 34, 46, 50, 54)
- Tutti i componenti che usano classi custom Tailwind

**Analisi tecnica**:

1. Tailwind CSS 4.x ha cambiato architettura interna
2. Le classi custom definite in `tailwind.config.js` non vengono elaborate
3. Plugin `@tailwindcss/postcss` non legge configurazione extend

## 🔧 SOLUZIONI PROPOSTE

### Soluzione A: Downgrade a Tailwind CSS 3.x (CONSIGLIATA)

**Razionale**: Stabilità e compatibilità testata

**Steps**:

```bash
cd frontend
pnpm remove tailwindcss @tailwindcss/postcss
pnpm add -D tailwindcss@^3.4.0
```

**Aggiornare**: `frontend/postcss.config.js`

```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

**Pro**: ✅ Soluzione immediata, configurazione testata
**Contro**: ❌ Non utilizza ultime features Tailwind

### Soluzione B: Fix Tailwind CSS 4.x Configuration

**Razionale**: Mantenere versioni più recenti

**Steps da testare**:

1. Verificare se `tailwind.config.js` è compatibile con v4
2. Testare approccio CSS variables only
3. Verificare documentazione ufficiale v4

**Pro**: ✅ Versioni aggiornate, features moderne
**Contro**: ❌ Complessità, documentazione limitata

### Soluzione C: CSS Variables + Standard Tailwind

**Razionale**: Approccio ibrido

**Modificare**: `frontend/src/index.css`

```css
@layer base {
  :root {
    --color-primary: #2563eb;
    --color-text-primary: #1f2937;
    /* etc... */
  }
}

/* Utilizzare: text-gray-800 invece di text-text-primary */
```

### Soluzione D: Migrazione a Bootstrap 5.x (NUOVA - ALTAMENTE CONSIGLIATA)

**Razionale**: Eliminazione completa del problema CSS

**Steps**:

```bash
cd frontend
pnpm remove tailwindcss @tailwindcss/postcss @tailwindcss/typography postcss autoprefixer
pnpm add bootstrap@^5.3.0 bootstrap-icons
```

**Vantaggi principali**:

- ✅ **ZERO problemi di configurazione**
- ✅ **Setup immediato** (15 minuti)
- ✅ **Componenti medical-ready**
- ✅ **Documentazione eccellente**
- ✅ **Stabilità comprovata**

**Conversione componenti**:

- `text-text-primary` → `text-body`
- `bg-primary` → `bg-primary`
- `border border-border` → `border`
- `px-4 py-2` → `px-3 py-2`

**Pro**: ✅ Soluzione definitiva, medical UI ready, timeline certa
**Contro**: ❌ Richiede conversione componenti (4-6h totali)

## 📊 IMPATTO PROBLEMA

### Funzionalità Bloccate

- ❌ Rendering componenti UI
- ❌ Visualizzazione pagine
- ❌ Test integrazione frontend
- ❌ Build di produzione

### Funzionalità Non Influenzate

- ✅ Server Vite si avvia (porta 3001)
- ✅ TypeScript compilation
- ✅ Hot module replacement (HMR)
- ✅ React components logic

## 🎯 RACCOMANDAZIONE

**SCELTA CONSIGLIATA**: **Soluzione D (Bootstrap)**

**Motivazioni**:

1. **CERTEZZA**: Eliminazione definitiva del problema CSS
2. **MEDICAL-READY**: Componenti UI ottimizzati per healthcare
3. **ZERO CONFIG**: Nessun setup complesso o file di configurazione
4. **FUTURO-PROOF**: Tecnologia matura senza breaking changes
5. **TIME-TO-MARKET**: Timeline certa vs debugging incerto

**Timeline stimata**:

- Soluzione A (Tailwind 3.x): ~30 minuti
- Soluzione B (Fix Tailwind 4.x): ~2-4 ore (incerta)
- Soluzione C (CSS Variables): ~1-2 ore
- **Soluzione D (Bootstrap)**: ~4-6 ore (certa) ⭐

## 📋 NEXT STEPS

1. **IMMEDIATO**: Implementare Soluzione A
2. **TEST**: Verificare caricamento LoginPage
3. **VALIDATION**: Test completo routing e componenti
4. **FUTURE**: Considerare upgrade a Tailwind 4.x quando documentazione sarà completa

## 🔍 LOG ERRORI

**Terminal Output**:

```
Error: Cannot apply unknown utility class `text-text-primary`
Plugin: vite:css
File: frontend/src/index.css:undefined:NaN
```

**Server Status**:

- ✅ Vite running su http://localhost:3001/
- ❌ CSS compilation failed
- ⏳ HMR in attesa di fix

**Files da verificare dopo fix**:

- [ ] LoginPage.tsx rendering
- [ ] Button.tsx styling
- [ ] ChatInterface.tsx layout
- [ ] AppLayout.tsx navigation

---

**Ultimo aggiornamento**: Post Milestone 3 completion
**Priorità**: 🔥 CRITICA - Blocca sviluppo UI
