# Generatore Bitcoin con verifica API

Versione separata del generatore che verifica il saldo di una singola chiave alla volta tramite API pubbliche indicizzate.

## Avvio

1. Esegui `AVVIA_VERIFICA_API.bat`.
2. Lascia aperta la finestra del servizio.
3. Apri `bitcoin-api.html`.
4. Premi `Controlla servizio API`.
5. Genera le chiavi e premi `Verifica` sulla riga desiderata.

## Funzionamento

La WIF viene elaborata localmente. Il programma deriva tre indirizzi pubblici:

- Legacy;
- Nested SegWit;
- Native SegWit.

Solo questi indirizzi pubblici vengono inviati a:

1. mempool.space;
2. Blockstream, se il primo servizio non risponde.

La chiave privata WIF non viene inviata online e non viene salvata automaticamente.

## Privacy e limiti

Gli explorer pubblici possono vedere gli indirizzi consultati e applicare limiti di richiesta. La verifica va usata soltanto per chiavi di propria proprietà.

Il servizio locale ascolta esclusivamente su:

```text
127.0.0.1:18766
```
