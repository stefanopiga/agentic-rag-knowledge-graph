# Spec Summary (Lite)

Allineare signatures di funzioni API/DB per supporto completo tenant_id nelle operazioni sessioni, messaggi e ricerca semantica. Risolve incongruenze identificate che causano errori runtime per parametri non riconosciuti e problemi di isolamento tenant tra create_session, get_session, add_message, get_session_messages, match_chunks, hybrid_search.