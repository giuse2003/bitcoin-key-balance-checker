# Bitcoin Key Balance Checker

Applicazione web statica che genera chiavi private Bitcoin sequenziali in formato WIF compresso e permette di verificare manualmente il saldo associato a una singola riga.

## Versione online

https://giuse2003.github.io/bitcoin-key-balance-checker/

## Caratteristiche

- funziona in un solo file HTML, senza server applicativo;
- consente di scegliere il numero di chiavi per pagina e il numero di pagina;
- genera al massimo 20.000 chiavi per pagina;
- mostra le WIF compresse e consente di copiarle o scaricarle senza intestazione;
- adatta la tabella agli schermi di computer e cellulari;
- verifica manualmente una chiave alla volta;
- non usa cookie, `localStorage` o salvataggi automatici.

## Verifica del saldo

Quando si preme `Verifica`, la pagina:

1. deriva localmente la chiave pubblica;
2. genera gli indirizzi Legacy, Nested SegWit e Native SegWit;
3. consulta mempool.space;
4. usa Blockstream come servizio di riserva;
5. somma il saldo dei tre indirizzi.

La WIF non viene trasmessa. Gli explorer ricevono esclusivamente gli indirizzi pubblici consultati.

## Uso locale

Scarica o clona il repository e apri `index.html` con Firefox o Chrome. La generazione funziona offline; la verifica del saldo richiede Internet.

```powershell
git clone https://github.com/giuse2003/bitcoin-key-balance-checker.git
cd bitcoin-key-balance-checker
```

## Aggiornare da un altro computer

Le istruzioni complete sono in [CONTRIBUTING.md](CONTRIBUTING.md). In breve:

```powershell
git pull
# modifica e prova index.html
git add .
git commit -m "Descrizione della modifica"
git push
```

GitHub Pages pubblica automaticamente il contenuto del ramo `main`.

## Struttura

- `index.html`: pagina pubblicata da GitHub Pages;
- `bitcoin-api.html`: copia alternativa identica a `index.html`;
- `README.md`: descrizione e uso;
- `CONTEXT.md`: stato tecnico e decisioni del progetto;
- `CONTRIBUTING.md`: procedura di aggiornamento;
- `AGENTS.md`: indicazioni per assistenti di programmazione;
- `CHANGELOG.md`: modifiche principali.

## Privacy e uso responsabile

Gli explorer pubblici possono conoscere gli indirizzi verificati e applicare limiti temporanei. Usa la verifica esclusivamente per chiavi di tua proprietà. Il progetto non deve introdurre verifiche automatiche o massive di chiavi.

