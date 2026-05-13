# DebugDroneNMY_N300
Debug del protocollo di comunicazione del drone NMY_N300 la cui comunicazione è tra drone e cellulare.

# Analisi di come arrivare al debug
La scelta per svolgere il debug è stata considerare l'applicazione ` Rx_Drone ` recuperare l'APK e con un decompilatore estrarre tutto il codice. A quel punto avendo poche informazioni a riguardo le ho usate sul codice con un agente AI che mi ha aiutato con il debug dell'applicazione riuscendo a trovare delle informazioni utili che di seguito vado a riportare.

# Analisi comunicazione App-Drone

Ho identificato la struttura del pacchetto a livello genrico e cosa invia l'utente al drone per comunicare:

| byte 0 | byte 1 | byte 2| byte 3 | byte 4-5 | byte payload | byte finale |
| -----: | ------ | ----- | ------ | -------- | ------------ | ----------- |
|  0x46  |  0x48  |  0x3C | opcode | lenght payload  | payload | checksum |

Questa la pseudo struttura, da questa vado ad analizzare ogni opcode che significato dovrebbe avere sempre in base a quanto letto dal codice:

| Opcode(Hex) | Decimale | Funzionalità | Pseudo costruzione del pacchetto | Riga di riferimento nel codice |
| ----------: | -------- | ------------ | -------------------------------- | ------------------------------ |
| 0x64 | 100 | Suppongo sia una funzionalità di handshaking oppure keep alive | 70-72-60-100-1-0-1-check |riga 42 file e.java|
| 0x65 | 101 | Suppongo sia una funzionalita di telemetria e aggiornamento di stato | 70-72-60-101-1-0-1-check | riga 42 file e.java| 
| 0x66 | 102 | Suppongo sia una funzionalità che permette la calibrazione ad esempio | 70-72-60-102-1-0-variabile-check | riga 614 e.java | 
| 0x67 | 103 | Suppongo sia una funzionalità booleana che permette di attivare o disattivare quello che dall'app sarebbe il lucchetto per cui attiva i motori in un certo senso | 70-72-60-103-1-0-0/1-check | riga 56 file e.java |
| 0x68 | 104 | Suppongo permetta di cambiare varie modalità di utilizzo | 70-72-60-104-1-0-comando-check | riga 76 file e.java | 
| 0x69 | 105 | Suppongo sia un comando di configurazione per settare la mod in casa, GPS | 70-72-60-105-1-0-comando-check | riga 284 file e.java | 
| 0x6A | 106 | Suppongo sia il comando per inviare i comandi di volo | 70-72-60-106-4-0-rollio-becheggio-gas-imbardata-check | riga 206 file e.java | 
| 0x6B | 107 | Suppongo sia una funzione per usare due parametri interi utili per definire coordinate | 70-72-60-107-4-0-val16bit-val16bit-check | riga 511 file e.java | 
| 0x6C | 108 | Suppongo sia una funzione per impostare i punti del GPS | 70-72-60-108-variabile_2byte-valori_GPS-check | riga 151 file e.java |
| 0x6D | 109 | Suppongo sia una funzione che costruisce il payload delle coordinate | 70-72-60-109-variabile_2byte-coordinate-check | riga 119 file e.java | 
| 0x6E | 110 | Suppongo sia una funzione che ha un riferimento al GPS che prevede la funzione di circondare il soggetto | 70-72-60-110-variabile_2byte-coordinate-check | riga 569/148 e.java | 

**IMPORTATE**
La checksum è uguale per tutti e sembra essere un calcolo di una XOR ma allo stesso tempo gli unici opcode dove tale funzione sembra essere differente **Opcode 100 e 101**.

- Considera che ci sono per **Opcode 100 e 101** una serie di varianti nel senso che nel codice se l'opcode è 100 o 101 può anche presentarsi una valutazione differente riportata da riga 507 del file e.java. 
- Altra valutazione riguarda l'**Opcode 102** con "variabile" che può rappresentare ad esempio calibrazione gps o magnetica e in quel caso sono numeri specifici.
- Per **Opcode 103** quello che avviene è banalmente l'attivazione o toggle dell'avvio dei motori.
- Per **Opcode 104** è da ben valutare tutta il vero uso ci sono valori multipli per un valore Y che non è ben chiaro ancora cosa sia ma che può assumere valori molteplici da inserire nel payload. 
- Per **Opcode 105** il valore di comando sembrerebbe assumere tre possibili valori, _0 = non fine_, _1 = GPS mode_, _2 = opticalFlow mode_.
- Per **Opcode 106** sarebbero i veri comandi di volo da inviare al drone con tutte le informazioni necessarie, da valutare se i campi riportati sono corretti.
- Per **Opcode 107** serve a definire delle coordinate da riferire, attenzione che per leggere le coordinate son due numeri da 16 bit quindi la lettura dei byte va due a due.
- Per **Opcode 108** la lunghezza come si vede dalla costruzione è variabile mentre i valori del GPS usati nel payload dipendono appunto dalla grandezza precedentemente definita.
- Per **Opcode 109** mi sembra molto simile a quanto visto per il precedente opcode però questo vedo che immette comandi di latitudine e longitudine.
- Per **Opcode 110** usata in combinazione con qualche altra funzione ma come descritto prevede di circondare il soggetto.

# Analisi della comunicazione Drone-App

La struttura del pacchetto a livello generico della telemetria è la seguente:

| Campo del frame | Significato della frame | 
| ---------------:| ----------------------- |
| byte 0 | Primo byte identificativo che permette di segnare il pacchetto e sarebbe 0x46 |
| byte 1 | Secondo byte è un altro identificativo che permette di segnare il pacchetto 0x48 | 
| byte 2 | Terzo byte è l'ultimo identificativo che permette di segnare il pacchetto 0x3E | 
| byte 3 | Quarto byte rispedisce all'app l'opcode che si sta eseguendo e quindi il tipo di operazione in cui ci troviamo probabilmente | 
| byte 4-5 | Quinto e sesto byte vanno ad identificare in realtà quello che sarbebe la grandezza del payload, viene usato solo uno dei due in teoria se la lunghezza è breve altrimenti entrambi | 
| byte 6-7 | Rappresentano il rollio a destra e il rollio a sinistra | 
| byte 8-9 | Rappresentano il beccheggio avanti e indietro | 
| byte 10-11 | Rappersentano l'imbardata o rotazione | 
| byte 12 ultimi 4 bit | Viene fatta una divisione tra primi e ultimi 4 bit di questo byte, viene fatta una AND bit a bit tra i 4 bit e tutti 1 così da avere in output una maschera che assume significati di vario genere, se _0000_ allora significa che i motori non sono armati, se pari a _0001_ allora significa ad esempio motori armati | 
| byte 12 primi 4 bit | Anche in questo caso viene svolta una AND bit a bit che va ad identificare le azioni di volo intese come ritorno GPS o cose del genere | 
| byte 13-14 | Questi rappresentano la velocità del drone e va a dividere il risultato per 10 | --> dubbio su questo valore 
| byte 15 | Rappresenta la velocità del drone che viene poi divisia per 10 | 
| byte 16-17 | Rappresenta la quota/altezza |
| byte 18 | Rappresenta la velocità vertiale del drone |
| byte 19 | Ha una duplice funzionalità, la prima è indicare il numero di satelliti agganciati, la seconda gestione riguarda lo stato della batteria, si va a spacchettare il byte se il primo bit è 1 c'è un allarme batteria grave, se invece il secondo bit è 1 allora l'allarme batteria è lieve | 
| byte 20 | È un campo dove si vanno a leggere i bit per confermare lo stato dei sensori quali barometro, bussola, giroscopio e poi l'ultimo bit ossia 7 se pari a 0 è in mod casalinga con il sensore ottico altrimenit se pari a 1 sta usando il GPS. | 
| byte 21-28 | Rappresenta dal byte 21 a 24 le coordintate che vengono unite in un unico numero a 32 bit diviso per 10 milioni per ottenere longitudine e latitudine, analogamente per i byte da 25 a 28. | 
| byte 29 | Sembra essere un byte speciale di telemetria la cui utilità è ignota | 
| byte 30-31 | È ignoto dai file la presenza di questi byte | 

- **Byte 12 primi 4 bit**: Preliminarmente viene fatto uno shift a destra di 4 e fatta una AND con una maschera di tutti 1 --> **0** la maschera significa _Operazione Manuale_, **1** significa _Hovering/Sospensione_, **2** significa _Decollo_, **3** significa _Atterraggio_, **4** significa _Ritorno a casa_, **5** significa _Volo a Wayppoint_, **6** significa _Follow Me_, **7** significa _Volo circolare/orbita_, **8** significa _Volo Indoor/ Volo senza GPS_.
- **Byte 30-31**: Questi byte non sono presenti di base nell'applicazione però sono presenti nei dati di telemetria che vengono scambiati e visti da wireshark.

# Operazioni per l'avvio del drone 
Affinché avvenga la comunicazione con il drone un'idea potrebbe essere eseguire questi step affinché si possa comandare tramite ad esempio uno script python:

- _Fase di connessione_: Nella fase di connesione bisogna istanziare una comunicazione UDP con una socket e fare in modo di connettersi alla rete wifi del drone, il pacchetto da inviare per essere sicuri della connessione che si sta istanziando sarebbe **0x46, 0x48, 0x3C, 0x65, 0x01, 0x00, 0x01, 0x65**.
- _Definizione della mod di volo_: In questa fase si deve definire una modalità di volo del dispositivo e pertanto la costruzione del pacchetto deve essere la seguente **0x46, 0x48, 0x3C, 0x69, 0x01, 0x00, 0x02, checksum**.
- _Toggle del lucchetto di volo_: In questa fase si devono per così dire sbloccare i motori e avviarli per tale motivo la costruzione del pacchetto è la seguente, **0x46, 0x48, 0x3C, 0x67, 0x01, 0x00, 0x01, checksum**.

# Attivazione dei comandi di volo 
Una volta aver avviato motori e settato la modalità di interesse del drone la cosa da fare e farlo alzare in volo, mentre per istanziare una connessione si mantiene una comunicazione di _keep alive_ costante, nel caso del volo va mantenuto l'opcode di volo in maniera costante e se non vi è variazione invierà sempre i valori di default, altrimenti quelli che prende in input dal controller di volo:

- _Definizione del pacchetto di volo_: In questa fase va utilizzato come opcode 106, **0x46, 0x48, 0x3C, 0x6A, 0x04, 0x00, rollio, beccheggio, gas, imbardata, check**

# Lettura della telemetria 
La lettura della telemetria è utile per ottenere una serie di informazioni che sono riportate in tabella nella sezione superiore, nonostante ciò è utile osservare i cambi del payload e dei singoli byte:

- **Byte 12**: Scenari di interesse posso essere due in particolare, motori **non attivi** significa in pratica che il byte 12 sarà con gli ultimi 4 bit del byte pari a 0, da vari dump usando solo optical flow sarà **0x10** (_0001 0000_). Secondo scenario con motori **attivi** signficia in pratica che il byte 12 sarà con l'ultimo bit pari a 1, da vari dump usando solo optical flow sarà **0x81** (_1000 0001_).

# Mappa comandi (tastiera)

- W / S: throttle su/giu (altezza)
- A / D: yaw sinistra/destra (imbardata)
- Frecce su/giu: pitch avanti/indietro (beccheggio)
- Frecce sinistra/destra: roll sinistra/destra (rollio)
- Spazio: reset emergenza (tutti i canali a 128)
- M: attiva invio comandi di volo
- N: disattiva invio comandi di volo
- U: toggle arm (sblocco motori)
- G: modalita GPS
- O: modalita Optical Flow
- Q: uscita
