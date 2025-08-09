# Spec Tasks: Fix frontend chat to enable usable LLM conversation on documentation

## Contesto

- Backend attivo e sano su `http://localhost:8000` (health OK)
- Frontend attivo su `http://localhost:3000`
- Obiettivo: chat utilizzabile end-to-end con LLM sulla documentazione ingerita.

Fonti:

- `agent/api.py` — endpoint `/chat` e `/chat/stream` (SSE), risposta `ChatResponse` con `message`, `session_id`, `tools_used`, `sources`.
- `agent/models.py` — modelli `ChatRequest`, `ChatResponse`, `ToolCall`, `DocumentMetadata`.
- `frontend/src/services/chat.ts` — invio payload in snake_case; mapping `tools_used`→`toolCalls`, `session_id`→`sessionId`.
- `frontend/src/services/websocket.ts` — integrazione WS esistente; backend offre SSE, non WS, per streaming.

## Problemi rilevati (verificabili nelle sorgenti)

1. Streaming mismatch: frontend usa `websocket.ts`, backend espone SSE su `/chat/stream` (`agent/api.py`, righe 569-679). Nessun server WS lato backend.
2. Mancata gestione streaming lato store: `useChatStore` non mostra metodi `appendMessageChunk`/`completeMessage` menzionati da `websocket.ts` (assenza nello store reale). Necessario adeguamento allo stream SSE.
3. Mapping campi: `frontend/src/services/chat.ts` gestisce snake_case per `/chat` ma non esiste client per `/chat/stream` con SSE.
4. Visualizzazione sources/tool calls: UI componenti presenti (`components/chat/*`) ma non garantita propagazione dei campi `sources` e `tools_used` dalla risposta al rendering.

## Obiettivi

- Implementare client SSE per `/chat/stream` e integrazione nello store chat.
- Garantire invio messaggi non-streaming `/chat` già funzionante, mantenendo compatibilità.
- Visualizzare correttamente `sources` e `tools_used` nella UI.
- Gestire `session_id` persistente nello store per continuità conversazione.

## Cambiamenti tecnici

- Aggiungere `frontend/src/services/stream.ts` con client SSE generico (EventSource) per `/chat/stream` con gestione eventi: `session`, `text`, `tools`, `end`, `error` (vedi emissione in `agent/api.py`, righe 579-657).
- Estendere `frontend/src/stores/chatStore.ts` con:
  - stato: `currentSession`, `isStreaming`, `streamError`.
  - azioni: `startStream(message)`, `appendMessageChunk(delta)`, `completeStream(tools)`, `abortStream()`.
- Adeguare `ChatInterface.tsx`/`MessageInput.tsx` a usare `startStream` per invii con streaming; fallback a `chatService.sendMessage` se richiesto.
- Propagare `sources` e `toolCalls` nel messaggio assistant alla fine dello stream o nella risposta non-streaming.

## Task Breakdown

- [ ] Creare `services/stream.ts` (SSE):
  - [ ] Funzione `startChatStream({ message, sessionId, tenantId, userId })` che apre `EventSource` su `POST /chat/stream` via fetch-to-ES workaround (readable stream) o EventSource polyfill con query params; in alternativa usare `fetch` con `ReadableStream` e parser a linee `data:`.
  - [ ] Emettere callback per tipi evento: `session`, `text`, `tools`, `end`, `error`.
- [ ] Estendere `stores/chatStore.ts`:
  - [ ] Stato `isStreaming`, `streamController`, `currentSession` persistita.
  - [ ] `startStream` invia richiesta SSE e crea messaggio assistant "in progress" da popolare con chunk.
  - [ ] `appendMessageChunk` concatena testo al messaggio assistant corrente.
  - [ ] `completeMessage`/`completeStream` segna fine, applica `toolCalls` e `sources` se disponibili.
  - [ ] `sendMessage` mantiene percorso non-streaming via `chatService.sendMessage` come fallback.
- [ ] Aggiornare `services/chat.ts`:
  - [ ] Esportare anche `sendStreamingMessage` che delega a `stream.ts`.
- [ ] Adeguare UI:
  - [ ] `ChatInterface.tsx`: usare `isStreaming` per mostrare `TypingIndicator` e disabilitare input.
  - [ ] `MessageBubble.tsx`/`SourceCitation.tsx`: assicurare rendering `sources` e indicare tool calls se presenti.
- [ ] Configurazione:
  - [ ] Variabile `VITE_API_BASE_URL` già usata in `services/api.ts`; riusarla per SSE.
- [ ] Test manuali e tecnici:
  - [ ] Verificare `/chat` non-streaming ritorna `session_id` e messaggio; mapping coerente con `models.ChatResponse`.
  - [ ] Verificare `/chat/stream` invia sequenza: `session`→`text` chunk n…→`tools` opzionale→`end`.

## Criteri di accettazione

- Avvio: FE su 3000 e BE su 8000; login stub funzionante (stub in `agent/api.py`, righe 208-220).
- In chat:
  - Invio messaggio mostra typing e accumulo testo stream in tempo reale.
  - Al termine, il messaggio assistant contiene testo completo, eventuali `toolCalls` e `sources` se presenti.
  - `currentSession` preservato e riutilizzato alle richieste successive.
- Nessun errore console in FE durante sessione tipica.

## Piano di test

### DevTools: come trovare `POST /chat/stream`

### Troubleshooting: SSE ok ma UI non aggiorna

- Verifica in Console:
  - Log `SSE session <id>`, `SSE text chunk <chunk>`, `SSE end`, `SSE error`.
  - Log `appendMessageChunk called with: <chunk>`.
- Se i log arrivano ma non vedi testo in UI:
  - Conferma che in `MessageBubble` il contenuto è renderizzato da `message.content` con `whitespace-pre-wrap`.
  - Controlla che l’array `messages` cresca o che l’ultimo messaggio assistant venga aggiornato.
- Se i log non arrivano:
  - Controlla la richiesta Network `/chat/stream` e la presenza delle righe `data:` nel tab EventStream/Response.
  - Verifica che `sendMessage` sia invocato con streaming (parametro `useStream` di default `true`).

1. Apri Chrome DevTools → Network.
2. In alto, clicca sul filtro “Fetch/XHR” o “XHR/Fetch”.
3. Nel box Filter digita: `chat/stream`.
4. Invia un messaggio dalla chat per generare la richiesta.
5. Clicca sulla riga corrispondente:
   - Headers: Method `POST`, Request URL `http://localhost:8000/chat/stream`, Response Headers `Content-Type: text/event-stream`, `Connection: keep-alive`.
   - Payload: JSON con `message`, `tenant_id`, opzionale `session_id`.
   - EventStream/Response: righe `data: {"type":"session"...}`, molte `data: {"type":"text","content":"..."}`, eventuale `data: {"type":"tools"...}`, infine `data: {"type":"end"}`.

### Piano di test

- Non-streaming:
  - Inviare messaggio via `chatService.sendMessage`; verificare risposta coerente con `ChatResponse` (`agent/models.py`).
- Streaming SSE:
  - Tracciare eventi via log locale; validare ricezione `session`, `text`, `end`, e opzionale `tools` come in `agent/api.py`.
- UI:
  - Verificare rendering `SourceCitation` per ogni fonte presente.
  - Verificare indicatori di scrittura e disabilitazione input durante `isStreaming`.

## Note implementative

- Backend SSE headers: `Content-Type: text/event-stream` e formato `data: {...}\n\n` (`agent/api.py` righe 669-674). Il client deve fare parse per righe con prefisso `data:` e payload JSON.
- Campi request obbligatori: `message`, `tenant_id` (UUID o `DEV_TENANT_UUID` fallback lato BE), opzionale `session_id`, `user_id` (`agent/models.py`).
