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
| 0x64|100| Suppongo sia una funzionalità di handshaking oppure keep alive | 70-72-60-100-1-0-1-check |riga 42 file 2.java|




