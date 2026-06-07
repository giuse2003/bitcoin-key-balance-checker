# Bitcoin Key Balance Checker

Generatore di chiavi private Bitcoin sequenziali con verifica manuale del saldo tramite explorer pubblici.

## Uso

Apri `index.html` nel browser oppure visita:

https://giuse2003.github.io/bitcoin-key-balance-checker/

Non occorre installare o avviare alcun servizio sul PC.

## Funzionamento

Tutti i calcoli crittografici avvengono nel browser. Per la riga scelta, la pagina:

1. deriva localmente la chiave pubblica;
2. genera gli indirizzi Legacy, Nested SegWit e Native SegWit;
3. consulta mempool.space, usando Blockstream come servizio di riserva;
4. somma il saldo dei tre indirizzi.

La chiave privata WIF non viene trasmessa. Gli explorer ricevono soltanto gli indirizzi pubblici consultati.

## Privacy

Gli explorer pubblici possono conoscere gli indirizzi sottoposti a verifica e applicare limiti temporanei alle richieste. Usa la funzione esclusivamente per chiavi di tua proprieta.
