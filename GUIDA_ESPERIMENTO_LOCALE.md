# Guida alla Replicazione dell'Esperimento Bitcoin Locale

Questo documento contiene tutte le informazioni, le configurazioni e le istruzioni necessarie per ricreare da zero l'intero ambiente di scansione Bitcoin locale e sequenziale su qualsiasi computer.

---

## 1. Architettura dell'Ambiente

L'intero sistema funziona offline, in locale, senza dipendere da alcuna API o servizio esterno su Internet:

```text
[Bitcoin Core] (Valida la blockchain)
      |
      v (Legge blocchi e cookie RPC)
[Fulcrum Indexer] (Indicizza indirizzi e risponde in TCP su 127.0.0.1:50001)
      |
      v (Interroga Fulcrum tramite JSON-RPC batch)
[local_checker.py] (Deriva chiavi/indirizzi e salva i risultati con fondi)
```

---

## 2. Requisiti e Configurazione dei Servizi

### A. Bitcoin Core (Nodo Completo)
1. **Download**: Scarica e installa Bitcoin Core da [bitcoincore.org](https://bitcoincore.org/).
2. **Spazio su disco**: Assicurati di avere spazio sufficiente per la blockchain completa non potata (mainnet).
3. **File di configurazione (`bitcoin.conf`)**:
   Colloca o modifica il file `bitcoin.conf` (nella directory dei dati di Bitcoin Core, es. `D:\Block`) con i seguenti parametri:
   ```ini
   server=1
   rpcallowip=127.0.0.1
   rpcport=8332
   txindex=1
   prune=0
   dbcache=12288
   ```
4. **Sincronizzazione**: Avvia Bitcoin Core e attendi che la blockchain sia sincronizzata al 100% (`initialblockdownload` deve essere `false` e `txindex` completato).

### B. Fulcrum (Indicizzatore Electrum)
1. **Download**: Scarica l'eseguibile di Fulcrum (consigliata versione 2.1.1 o successive per Windows) da [GitHub di Fulcrum](https://github.com/cculianu/Fulcrum).
2. **File di configurazione (`fulcrum.conf`)**:
   Crea un file di configurazione `fulcrum.conf` (ad esempio in `E:\fulcrum\`) contenente:
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
   *Nota: Adatta i percorsi `datadir`, `rpccookie` e `db_mem` in base ai tuoi dischi (consigliato l'uso di un SSD per `datadir` di Fulcrum).*
3. **Indicizzazione**: Avvia Fulcrum ed attendi che l'altezza dei blocchi indicizzati raggiunga il 100% allineandosi con Bitcoin Core. Le statistiche saranno visibili su `http://127.0.0.1:8080/stats`.

---

## 3. Configurazione dell'Ambiente Python

Lo script di scansione richiede Python 3 (consigliata versione 3.10 o successive) e due librerie esterne per la crittografia e la codifica Base58.

1. **Installazione librerie**:
   Apri il terminale e digita:
   ```powershell
   pip install cryptography base58
   ```

---

## 4. File del Progetto

Tutti i file di codice sorgente sono salvati nel repository Git. Di seguito i file necessari per il funzionamento:

### A. `.gitignore`
Esclude i file di stato locali del PC per evitare di caricarli su GitHub pubblico:
```text
__pycache__/
*.pyc
.DS_Store
*.tmp
*.bak
.vscode/

# Local checker files
checkpoint.json
checkpoint.json.tmp
risultati.json
app.log
```

### B. `checkpoint.json` (Stato del Checkpoint)
File utilizzato per salvare il progresso e riprendere la scansione. Se manca, viene creato automaticamente partendo dalla chiave 1. Struttura:
```json
{
  "last_completed_private_key_number": "0",
  "next_private_key_number": "1",
  "checked_keys": "0",
  "updated_at": null
}
```

### C. `local_checker.py`
Lo script principale che esegue le seguenti operazioni:
1. Legge il checkpoint.
2. Deriva per ciascuna chiave gli indirizzi **Legacy (P2PKH)**, **Nested SegWit (P2SH-P2WPKH)** e **Native SegWit (P2WPKH)**.
3. Trasforma gli indirizzi in `scripthash` Electrum.
4. Invia una singola richiesta TCP Batch a Fulcrum per verificare saldi confermati/non confermati.
5. Se trova una chiave con saldo maggiore di 0 satoshi:
   - Salva i dati (WIF spendibile incluso) in `risultati.json`.
   - Aggiorna il checkpoint all'ultima chiave completata.
   - Ferma l'esecuzione dello script mostrando un avviso ed attende l'intervento dell'utente.
6. Scrive il checkpoint atomicamente per evitare corruzione in caso di crash o interruzione improvvisa.
7. Gestisce la riprova a intervalli di 10 secondi in caso di disconnessione o indicizzazione di Fulcrum.

---

## 5. Istruzioni per l'Esecuzione

### Test di Derivazione Crittografica
Per assicurarti che i calcoli delle chiavi e degli indirizzi siano matematicamente corretti, esegui:
```powershell
python local_checker.py --test-derivation
```
*Se i test passano, la derivazione è corretta (Legacy, Nested e Native SegWit corrispondono ai vettori di test).*

### Avvio del Verificatore
Per avviare la ricerca sequenziale:
```powershell
python local_checker.py
```
*Lo script può essere interrotto in qualsiasi momento premendo `Ctrl+C`. Si arresterà in modo pulito salvando l'ultimo checkpoint calcolato.*

---

## 6. Sincronizzazione dei Progetti su GitHub

Per sincronizzare i tuoi repository locali con GitHub (incluso il backup automatico di questo progetto) mantenendo le modifiche locali committate in automatico, sono presenti due file nella cartella `D:\Dropbox\GitHub\`:

1. **`sync-local-to-github.ps1`**: Lo script PowerShell che automatizza il `git add`, `git commit -m "Auto-sync..."`, `git pull --rebase` e `git push` per ogni cartella Git trovata.
2. **`Sincronizza tutti i progetti su GitHub.cmd`**: Il file lanciabile con doppio clic che esegue lo script PowerShell bypassando le restrizioni di esecuzione di Windows e tenendo aperta la finestra per leggere i log.
