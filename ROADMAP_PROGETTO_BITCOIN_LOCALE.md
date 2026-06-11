# Roadmap del progetto Bitcoin locale

## 1. Visione del progetto

Costruire un ambiente Bitcoin autonomo e completamente locale per:

- conservare e verificare l'intera blockchain;
- indicizzare blocchi, transazioni e indirizzi;
- effettuare ricerche senza API o servizi esterni;
- derivare tre tipi di indirizzo da chiavi controllate;
- interrogare saldi e cronologie tramite Fulcrum;
- eseguire elaborazioni sequenziali con checkpoint e ripresa;
- sviluppare un modello sperimentale di ricerca sequenziale completamente
  locale.

Architettura prevista:

```text
Bitcoin Core
    |
    v
Fulcrum
    |
    v
Servizio locale di interrogazione
    |
    v
Interfaccia bitcoin-key-balance-checker
```

## 2. Infrastruttura disponibile

### Archiviazione

```text
D:\Block       Blockchain e dati di Bitcoin Core su HDD
E:\FulcrumDB   Indice Fulcrum su SSD NVMe
E:\fulcrum     Programma e configurazione di Fulcrum
```

Il database dell'indice e stato collocato sull'SSD per rendere rapide le
scritture, gli accessi casuali e le future interrogazioni. La blockchain resta
sull'HDD per contenere l'uso dello spazio SSD.

### Risorse del computer

- RAM installata: 32 GB.
- Cache Bitcoin Core: 12 GB durante le operazioni intensive.
- Memoria Fulcrum: 12 GB.
- Disco blockchain: HDD da 4 TB.
- Disco indice: SSD NVMe `E:`.

## 3. Attivita completate

### Fase A - Nodo Bitcoin Core

Stato: **completata**

- Installato e configurato Bitcoin Core.
- Scaricata e verificata l'intera blockchain Bitcoin mainnet.
- Blockchain non potata: `pruned: false`.
- Server RPC locale abilitato su `127.0.0.1:8332`.
- `txindex=1` abilitato.
- `txindex` sincronizzato fino all'altezza corrente.
- Download iniziale terminato: `initialblockdownload: false`.
- Cookie RPC disponibile localmente in `D:\Block\.cookie`.

Configurazione rilevante:

```ini
server=1
rpcallowip=127.0.0.1
rpcport=8332
txindex=1
prune=0
dbcache=12288
```

### Fase B - Installazione di Fulcrum

Stato: **completata**

- Scaricato Fulcrum 2.1.1 per Windows.
- Estratto in `E:\fulcrum`.
- Creato il database in `E:\FulcrumDB`.
- Configurato l'accesso locale a Bitcoin Core tramite cookie RPC.
- Servizio Electrum limitato a `127.0.0.1:50001`.
- Interfaccia amministrativa limitata a `127.0.0.1:8000`.
- Statistiche disponibili su `127.0.0.1:8080`.
- Peering e annunci pubblici disabilitati.
- Indicizzazione iniziale avviata correttamente.

Configurazione:

```ini
datadir = E:/FulcrumDB
bitcoind = 127.0.0.1:8332
rpccookie = D:/Block/.cookie

tcp = 127.0.0.1:50001
admin = 127.0.0.1:8000
stats = 127.0.0.1:8080

peering = false
announce = false
db_mem = 12288
```

### Fase C - Analisi delle prestazioni

Stato: **completata**

- Confermato che l'HDD `D:` e il limite durante l'indicizzazione iniziale.
- Verificata la lettura dei file `blk*.dat` e dell'indice `txindex`.
- Verificata la scrittura dei file RocksDB di Fulcrum sull'SSD.
- Confermati tempi di risposta bassi dell'SSD.
- Stabilito che, dopo l'indicizzazione iniziale, la configurazione ottimale e:

```text
Blockchain su HDD
Indice Fulcrum su SSD
```

### Fase D - Sincronizzazione dei repository GitHub

Stato: **completata**

- Installata e autenticata GitHub CLI.
- Creato uno script PowerShell per sincronizzare i repository.
- Creato un avvio `.cmd` utilizzabile con doppio clic.
- Destinazione configurata: `D:\Dropbox\GitHub`.
- Supportati repository pubblici e privati.
- I repository mancanti vengono clonati.
- I repository esistenti e puliti vengono aggiornati.
- In presenza di modifiche locali viene eseguito soltanto il recupero degli
  aggiornamenti remoti, senza sovrascrivere il lavoro locale.

File:

```text
sync-github-repos.ps1
Sincronizza repository GitHub.cmd
```

### Fase E - Analisi di bitcoin-key-balance-checker

Stato: **completata**

Repository:

```text
D:\Dropbox\GitHub\bitcoin-key-balance-checker
```

E stato verificato che l'applicazione:

- genera chiavi private numeriche sequenziali;
- parte dalla chiave numerica `1`;
- usa pagine e quantita per determinare la posizione iniziale;
- converte ogni numero in WIF compresso;
- deriva la chiave pubblica compressa;
- deriva tre indirizzi:
  - P2PKH Legacy;
  - P2SH-P2WPKH Nested SegWit;
  - P2WPKH Native SegWit;
- consulta attualmente explorer pubblici;
- mantiene la WIF nel browser.

Formula iniziale:

```text
start = ((pagina - 1) * quantita) + 1
```

## 4. Attivita in corso

### Fase F - Completamento dell'indice Fulcrum

Stato: **in corso**

Attivita:

- lasciare Bitcoin Core in esecuzione;
- lasciare Fulcrum in esecuzione;
- controllare avanzamento e altezza indicizzata;
- verificare lo spazio disponibile sull'SSD;
- attendere il raggiungimento del 100%;
- verificare che l'altezza Fulcrum coincida con Bitcoin Core;
- eseguire un riavvio controllato per confermare la ripresa del database.

Criteri di completamento:

- Fulcrum sincronizzato con il blocco corrente;
- nessun errore del database;
- statistiche locali raggiungibili;
- arresto con `Ctrl+C` e riavvio completati correttamente.

## 5. Attivita da realizzare

### Fase G - Client locale Fulcrum

Stato: **da fare**

Creare un componente locale che:

- si connetta a `127.0.0.1:50001`;
- utilizzi il protocollo Electrum;
- trasformi ogni `scriptPubKey` nel relativo Electrum script hash;
- richieda saldo e cronologia;
- gestisca timeout, disconnessioni e riconnessioni;
- non utilizzi Internet;
- non registri chiavi private nei log.

Metodi Electrum principali:

```text
server.version
blockchain.headers.subscribe
blockchain.scripthash.get_balance
blockchain.scripthash.get_history
```

Criteri di completamento:

- connessione a Fulcrum verificata;
- interrogazione riuscita per indirizzi di test noti;
- risultati confrontati con Bitcoin Core;
- errori gestiti senza perdita dello stato.

### Fase H - Servizio locale per il browser

Stato: **da fare**

Il browser non puo collegarsi direttamente alla porta TCP di Fulcrum. Occorre
un piccolo servizio locale che:

- esponga un'interfaccia HTTP soltanto su `127.0.0.1`;
- riceva indirizzi pubblici o script;
- interroghi Fulcrum;
- restituisca saldo, cronologia e stato;
- consenta richieste soltanto dall'applicazione locale;
- non accetti o registri WIF e chiavi private.

Esempio:

```text
Browser -> http://127.0.0.1:porta -> Fulcrum 127.0.0.1:50001
```

Criteri di completamento:

- nessuna chiamata agli explorer pubblici;
- servizio non esposto sulla rete locale o Internet;
- risposta coerente per tutti e tre i tipi di indirizzo.

### Fase I - Integrazione dell'interfaccia esistente

Stato: **da fare**

Modificare `bitcoin-key-balance-checker` per:

- mantenere la derivazione locale dei tre indirizzi;
- sostituire mempool.space, Blockstream e BlockCypher;
- interrogare esclusivamente il servizio locale;
- mostrare saldo confermato;
- mostrare saldo non confermato;
- mostrare presenza e numero di transazioni;
- visualizzare chiaramente lo stato di Core, Fulcrum e servizio locale;
- mantenere la verifica manuale per dati mainnet.

Criteri di completamento:

- nessuna richiesta Internet durante la verifica;
- i tre indirizzi vengono interrogati localmente;
- risultati verificati con indirizzi di prova controllati.

### Fase J - Checkpoint e ripresa

Stato: **da fare**

Realizzare un sistema generico di avanzamento sequenziale che memorizzi:

```json
{
  "last_completed_private_key_number": "0",
  "next_private_key_number": "1",
  "checked_keys": "0",
  "updated_at": null
}
```

Requisiti:

- scrittura atomica tramite file temporaneo e sostituzione;
- aggiornamento soltanto dopo una verifica completata;
- nessun avanzamento in caso di errore Fulcrum;
- ripresa dalla posizione successiva all'ultima completata;
- gestione di `Ctrl+C`;
- log separato dallo stato;
- numeri conservati come stringhe per evitare perdita di precisione.

Criteri di completamento:

- arresto e ripresa testati più volte;
- nessuna posizione saltata;
- nessuna posizione elaborata due volte, salvo quella interrotta a meta;
- checkpoint recuperabile dopo un arresto improvviso simulato.

### Fase K - Modello sperimentale richiesto

Stato: **da fare**

Il modello richiesto dall'utente prevede un'elaborazione automatica e
sequenziale delle chiavi private numeriche sulla blockchain Bitcoin mainnet
indicizzata localmente.

Attivita:

- partire dalla chiave numerica indicata nel checkpoint;
- convertire la chiave numerica in WIF compresso;
- derivare la relativa chiave pubblica compressa;
- derivare i tre indirizzi gia scelti:
  - P2PKH Legacy;
  - P2SH-P2WPKH Nested SegWit;
  - P2WPKH Native SegWit;
- interrogare Fulcrum localmente per ciascuno dei tre indirizzi;
- sommare i saldi confermati e non confermati;
- determinare se almeno uno dei tre indirizzi possiede un saldo positivo;
- se il saldo complessivo e zero, scartare il risultato e passare alla chiave
  numerica successiva;
- se il saldo e positivo, registrare la chiave privata WIF in un file di
  risultati dedicato insieme agli indirizzi e ai saldi rilevati;
- aggiornare il checkpoint dopo ogni chiave controllata;
- continuare automaticamente finche il processo non viene arrestato;
- intercettare `Ctrl+C` e chiudere ordinatamente file e connessioni;
- alla riapertura, leggere il checkpoint e riprendere dall'ultima chiave
  controllata senza ricominciare dall'inizio.

Flusso desiderato:

```text
Leggi checkpoint
      |
      v
Chiave privata numerica corrente
      |
      v
Deriva WIF e tre indirizzi
      |
      v
Interroga Fulcrum locale
      |
      v
Saldo totale maggiore di zero?
      |
      +-- No --> Aggiorna checkpoint --> Chiave successiva
      |
      +-- Si --> Salva WIF e risultati --> Aggiorna checkpoint
                                            |
                                            v
                                      Chiave successiva
```

Criteri di completamento:

- nessuna dipendenza da API o explorer pubblici;
- tutte le interrogazioni dirette a `127.0.0.1`;
- derivazione corretta dei tre tipi di indirizzo;
- avanzamento sequenziale senza salti;
- salvataggio separato dei soli risultati con saldo positivo;
- checkpoint aggiornato atomicamente;
- ripresa corretta dopo arresto ordinato o imprevisto;
- statistiche su chiavi controllate, velocita media e posizione corrente;
- nessuna chiave privata scritta nei log ordinari.

Nota sullo stato:

Questa sezione documenta fedelmente il comportamento richiesto dall'utente. La
relativa automazione non e stata implementata durante la presente assistenza.

## 6. Ordine consigliato dei prossimi lavori

1. Completare e verificare l'indicizzazione Fulcrum.
2. Creare il client Electrum locale.
3. Testare saldo e cronologia su indirizzi pubblici noti.
4. Creare il servizio HTTP limitato a `127.0.0.1`.
5. Collegare l'interfaccia esistente al servizio locale.
6. Eliminare le dipendenze dagli explorer pubblici.
7. Implementare checkpoint, log e arresto ordinato.
8. Integrare il ciclo sequenziale descritto nella Fase K.
9. Verificare arresto, checkpoint e ripresa.
10. Verificare il salvataggio separato dei risultati positivi.
11. Documentare installazione, avvio, arresto, backup e recupero.
12. Automatizzare l'avvio ordinato dei componenti locali.

## 7. Avvio operativo futuro

Una volta completato il progetto, l'ordine di avvio sara:

```text
1. Bitcoin Core
2. Fulcrum
3. Servizio locale
4. Interfaccia web
```

L'ordine di arresto sara inverso:

```text
1. Interfaccia o elaborazione
2. Servizio locale
3. Fulcrum con Ctrl+C
4. Bitcoin Core
```

## 8. Manutenzione prevista

- aggiornare Bitcoin Core dopo backup e verifica delle note di rilascio;
- aggiornare Fulcrum mantenendo una copia della configurazione;
- controllare periodicamente lo spazio libero su `D:` ed `E:`;
- eseguire backup di configurazioni, checkpoint e codice;
- non considerare il database Fulcrum un backup della blockchain;
- verificare periodicamente che i servizi ascoltino solo su `127.0.0.1`;
- sincronizzare i repository GitHub prima e dopo modifiche importanti;
- non versionare cookie RPC, chiavi, WIF o file sensibili.

## 9. Stato sintetico

```text
[COMPLETATO] Bitcoin Core mainnet sincronizzato
[COMPLETATO] txindex sincronizzato
[COMPLETATO] Fulcrum installato e avviato
[IN CORSO]   Indicizzazione completa Fulcrum
[COMPLETATO] Repository GitHub sincronizzati
[COMPLETATO] Analisi del generatore esistente
[DA FARE]    Client locale Fulcrum
[DA FARE]    Servizio HTTP locale
[DA FARE]    Integrazione dell'interfaccia
[DA FARE]    Checkpoint e ripresa
[DA FARE]   Ciclo sequenziale mainnet descritto nella Fase K
[DA FARE]   Salvataggio automatico delle chiavi con saldo positivo
[DA FARE]    Avvio automatico e documentazione finale
```
