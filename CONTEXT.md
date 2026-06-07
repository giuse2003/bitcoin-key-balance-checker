# Contesto del progetto

Ultimo aggiornamento: 7 giugno 2026.

## Obiettivo

Mantenere un generatore didattico di chiavi private Bitcoin sequenziali, utilizzabile localmente e su GitHub Pages, con verifica manuale del saldo di una sola chiave alla volta.

Repository:

https://github.com/giuse2003/bitcoin-key-balance-checker

Sito:

https://giuse2003.github.io/bitcoin-key-balance-checker/

## Stato attuale

- la cartella locale `verifica-api` è un repository Git collegato a `origin/main`;
- applicazione interamente statica;
- nessun servizio Python o Bitcoin Core richiesto;
- nessuna dipendenza esterna o CDN;
- quantità predefinita: 200;
- quantità massima: 20.000;
- selezione tramite quantità e numero di pagina;
- pagina 1 con quantità 200: chiavi numeriche 1-200;
- pagina 2 con quantità 200: chiavi numeriche 201-400;
- WIF compresse;
- CSV senza intestazione e senza numeri progressivi;
- layout mobile con WIF su più righe;
- verifica manuale in parallelo tramite mempool.space, Blockstream e BlockCypher;
- viene usata la prima risposta completa e valida.

## Architettura

Tutto il codice HTML, CSS e JavaScript è contenuto in `index.html`.

Il browser esegue localmente:

- aritmetica `BigInt`;
- SHA-256 e RIPEMD-160;
- operazioni secp256k1;
- Base58Check;
- Bech32;
- derivazione degli indirizzi P2PKH, P2SH-P2WPKH e P2WPKH.

Solo gli indirizzi pubblici vengono inviati ai tre explorer. Le WIF restano nel browser.

## Regole da conservare

- non inviare mai WIF o chiavi private a servizi remoti;
- non aggiungere cookie, telemetria o archiviazione automatica;
- non aggiungere verifica automatica di tutte le righe;
- mantenere la verifica come azione manuale per singola chiave;
- mantenere `index.html` e `bitcoin-api.html` identici;
- non reintrodurre il bridge locale su `127.0.0.1`;
- non inserire credenziali o token nel repository.

## Controlli prima della pubblicazione

1. Aprire `index.html` localmente.
2. Provare pagina 1 e pagina 2 con quantità 200.
3. Verificare che la pagina 2 inizi dal numero 201.
4. Controllare il layout su schermo stretto.
5. Provare `Copia CSV` e `Scarica CSV`.
6. Controllare che `Verifica` invii soltanto indirizzi pubblici.
7. Copiare `index.html` in `bitcoin-api.html`.
8. Eseguire commit e push sul ramo `main`.

## Test crittografico noto

La chiave privata numerica `1` deve produrre:

- Legacy: `1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH`
- Nested SegWit: `3JvL6Ymt8MVWiCNHC7oWU6nLeHNJKLZGLN`
- Native SegWit: `bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4`
