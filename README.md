# DebugDroneNMY_N300
Debug del protocollo di comunicazione del drone NMY_N300 la cui comunicazione è tra drone e cellulare.

# Analisi di come arrivare al debug
La scelta per svolgere il debug è stata considerare l'applicazione ` Rx_Drone ` recuperare l'APK e con un decompilatore estrarre tutto il codice. A quel punto avendo poche informazioni a riguardo [...]

# Analisi

## Rappresentazione analisi pacchetti (per opcode)
Qui sotto trovi un formato "riutilizzabile" per documentare ogni pacchetto identificato dal suo **opcode**, includendo:
- **Funzionamento** (cosa fa e quando viene usato)
- **Pseudo-costruzione del pacchetto** (come viene composto, a livello di campi)

### 1) Indice (tabella riassuntiva)
> Compila questa tabella man mano che identifichi nuovi opcode.

| Opcode | Nome (ipotesi) | Direzione | Funzionamento (breve) | Payload (breve) | Stato analisi |
|------:|-----------------|-----------|------------------------|-----------------|--------------|
| 0x00  | TBD             | App→Drone | TBD                    | TBD             | bozza        |

Legenda **Direzione**: `App→Drone`, `Drone→App`, `Entrambe`

---

### 2) Template dettagliato (copia/incolla per ogni opcode)
> Suggerimento: usa un titolo del tipo `### Opcode 0xNN — Nome` così lo trovi subito.

#### Opcode 0xNN — <Nome pacchetto / ipotesi>

**Contesto / Trigger**
- Quando viene inviato (azione utente, stato del drone, periodicità, ecc.)
- Prerequisiti (connessione, handshake già fatto, ecc.)

**Direzione**
- App→Drone / Drone→App / Entrambe

**Funzionamento**
- Spiegazione in linguaggio naturale di cosa fa il pacchetto
- Effetti osservati (cambi stato, risposta attesa, timeout, retry)
- Eventuali note/ambiguità (cosa è certo vs ipotesi)

**Campi / Struttura**
| Offset | Campo | Tipo/Len | Endianness | Valori noti | Note |
|------:|------|----------|------------|-------------|------|
| 0x00  | Header | u8/u16 | — | — | opzionale |
| 0x??  | Opcode | u8 | — | 0xNN | opcode del pacchetto |
| 0x??  | Lunghezza | u8/u16 | LE/BE | — | totale o payload |
| 0x??  | Payload | bytes | — | — | vedi sotto |
| 0x??  | Checksum/CRC | u8/u16/u32 | — | — | se presente |

**Pseudo-costruzione del pacchetto**
> Descrivi *come costruirlo* (anche se alcuni campi sono ancora TBD).

```text
PACKET := HEADER | OPCODE | LEN | PAYLOAD | CRC

HEADER := 0x?? 0x??                 (se presente)
OPCODE := 0xNN
LEN    := <len(payload)>            (o len totale, TBD)
PAYLOAD := <campo1> <campo2> ...
CRC    := <crc8/crc16/... su [ ... ]> (TBD)
```

**Esempio (hex dump)**
> Inserisci una cattura reale, se ce l’hai.

```text
AA 55 NN 05 01 02 03 04 CC
```

**Parsing (pseudo)**
> (Opzionale) come lo stai decodificando lato analisi.

```pseudo
if data[OPCODE_OFFSET] == 0xNN:
    len = read_len(...)
    payload = data[payload_off : payload_off+len]
    ...
```

**Risposta attesa / Pacchetto correlato**
- Risposta (opcode?)
- Relazioni request/response
- Sequenza (es. handshake → ack → streaming)

**Note di reverse engineering / Riferimenti**
- Classe/metodo nell’APK (se nota)
- PCAP / log / timestamp

---

### 3) Variante compatta: una riga “funzionamento” + blocco costruzione
Se preferisci evitare la tabella dei campi, puoi usare questa versione più rapida.

#### Opcode 0xNN — <Nome>
- **Funzionamento**: ...
- **Pseudo-costruzione**:
  ```text
  [HEADER] [0xNN] [LEN] [PAYLOAD...] [CRC]
  ```

