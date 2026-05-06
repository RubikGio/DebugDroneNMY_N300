# DebugDroneNMY_N300
Debug del protocollo di comunicazione del drone NMY_N300 la cui comunicazione è tra drone e cellulare.

# Analisi di come arrivare al debug
La scelta per svolgere il debug è stata considerare l'applicazione ` Rx_Drone ` recuperare l'APK e con un decompilatore estrarre tutto il codice. A quel punto avendo poche informazioni a riguardo le ho usate sul codice con un agente AI che mi ha aiutato con il debug dell'applicazione riuscendo a trovare delle informazioni utili che di seguito vado a riportare.

# Analisi

Pacchetti analizzati **User-to-Drone**

Ho identificato la struttura del pacchetto a livello genrico e cosa invia l'utente al drone per comunicare:

| byte 1 | byte 2 | byte 3| byte 4 | byte 5-6 | byte payload | byte finale |
| -----: | ------ | ----- | ------ | -------- | ------------ | ----------- |
|  0x46  |  0x48  |  0x3C | opcode | lenght payload  | payload | checksum |

Questa la pseudo struttura, da questa vado ad analizzare ogni opcode che significato dovrebbe avere sempre in base a quanto letto dal codice:

| Opcode(Hex) | Decimale | Funzionalità | Pseudo costruzione del pacchetto | Riga di riferimento nel codice |
| -----------: | -------- | ------------ | -------------------------------- | ------------------------------ |
| 0x64 | 100 | Suppongo sia una funzionalità di handshaking oppure keep alive | 70-72-60-100-1-0-1-check |riga 42 file e.java|
| 0x65 | 101 | Suppongo sia una funzionalita di telemetria e aggiornamento di stato | 70-72-60-101-1-0-1-check | riga 42 file e.java| 
| 0x66 | 102 | Suppongo sia una funzionalità che permette la calibrazione ad esempio | 70-72-60-102-1-0-variabile-check | riga 614 e.java | 
| 0x67 | 103 | Suppongo sia una funzionalità booleana che permette il cambio da GPS in uso in casa | 70-72-60-103-1-0-0/1-check | riga 56 file e.java |
| 0x68 | 104 | Suppongo permetta di cambiare varie modalità di utilizzo | 70-72-60-104-1-0-comando-check | riga 76 file e.java | 
| 0x69 | 105 | Suppongo sia un comando di configurazione o qualcosa del genere | 70-72-60-105-1-0-comando-check | riga 284 file e.java | 
| 0x6A | 106 | 

Considera che ci sono per **Opcode 100 e 101** una serie di varianti nel senso che nel codice se l'opcode è 100 o 101 può anche presentarsi una valutazione differente riportata da riga 507 del file e.java. 
Altra valutazione riguarda l'**Opcode 102** con "variabile" che può rappresentare ad esempio calibrazione gps o magnetica e in quel caso sono numeri specifici. 
Per **Opcode 104** è da ben valutare tutta il vero uso ci sono valori multipli per un valore Y che non è ben chiaro ancora cosa sia ma che può assumere valori molteplici da inserire nel payload. 
Per **Opcode 105** c'è una valutazione 
