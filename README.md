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
| ----------: | -------- | ------------ | -------------------------------- | ------------------------------ |
| 0x64 | 100 | Suppongo sia una funzionalità di handshaking oppure keep alive | 70-72-60-100-1-0-1-check |riga 42 file e.java|
| 0x65 | 101 | Suppongo sia una funzionalita di telemetria e aggiornamento di stato | 70-72-60-101-1-0-1-check | riga 42 file e.java| 
| 0x66 | 102 | Suppongo sia una funzionalità che permette la calibrazione ad esempio | 70-72-60-102-1-0-variabile-check | riga 614 e.java | 
| 0x67 | 103 | Suppongo sia una funzionalità booleana che permette il cambio da GPS in uso in casa | 70-72-60-103-1-0-0/1-check | riga 56 file e.java |
| 0x68 | 104 | Suppongo permetta di cambiare varie modalità di utilizzo | 70-72-60-104-1-0-comando-check | riga 76 file e.java | 
| 0x69 | 105 | Suppongo sia un comando di configurazione o qualcosa del genere | 70-72-60-105-1-0-comando-check | riga 284 file e.java | 
| 0x6A | 106 | Suppongo sia il comando per inviare i comandi di volo | 70-72-60-106-4-0-rollio-becheggio-gas-imbardata-check | riga 206 file e.java | 
| 0x6B | 107 | Suppongo sia una funzione per usare due parametri interi utili per definire coordinate | 70-72-60-107-4-0-val16bit-val16bit-check | riga 511 file e.java | 
| 0x6C | 108 | Suppongo sia una funzione per impostare i punti del GPS | 70-72-60-108-variabile_2byte-valori_GPS-check | riga 151 file e.java |
| 0x6D | 109 | Suppongo sia una funzione che costruisce il payload delle coordinate | 70-72-60-109-variabile_2byte-coordinate-check | riga 119 file e.java | 
| 0x6E | 110 | Suppongo sia una funzione che ha un riferimento al GPS che prevede la funzione di circondare il soggetto | 70-72-60-110-variabile_2byte-coordinate-check | riga 569/148 e.java | 


Considera che ci sono per **Opcode 100 e 101** una serie di varianti nel senso che nel codice se l'opcode è 100 o 101 può anche presentarsi una valutazione differente riportata da riga 507 del file e.java. 
Altra valutazione riguarda l'**Opcode 102** con "variabile" che può rappresentare ad esempio calibrazione gps o magnetica e in quel caso sono numeri specifici. 
Per **Opcode 104** è da ben valutare tutta il vero uso ci sono valori multipli per un valore Y che non è ben chiaro ancora cosa sia ma che può assumere valori molteplici da inserire nel payload. 
Per **Opcode 105** c'è una valutazione sul comando, c'è una variabile "this.h0" che viene chiamata e assegnato il _byte b_ a questa variabile e usato come payload. 
Per **Opcode 106** sarebbero i veri comandi di volo da inviare al drone con tutte le informazioni necessarie, da valutare se i campi da riportati sono corretti.
Per **Opcode 107** serve a definire delle coordinate da riferire, attenzione che per leggere le coordinate son due numeri da 16 bit quindi la lettura dei byte va due a due.
Per **Opcode 108** la lunghezza come si vede dalla costruzione è variabile mentre i valori del GPS usati nel payload dipendono appunto dalla grandezza precedentemente definita.
Per **Opcode 109** mi sembra molto simile a quanto visto per il precedente opcode però questo vedo che immette comandi di latitudine e longitudine.
Per **Opcode 110** usata in combinazione con qualche altra funzione ma come descritto prevede di circondare il soggetto.


