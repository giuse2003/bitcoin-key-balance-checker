# Indicazioni per assistenti di programmazione

Leggere prima `README.md` e `CONTEXT.md`.

## Vincoli

- Il progetto deve restare statico e compatibile con GitHub Pages.
- Non usare backend, servizi locali, CDN o librerie esterne.
- Non trasmettere mai WIF o chiavi private.
- Le richieste di rete possono contenere soltanto indirizzi pubblici.
- La verifica del saldo deve restare manuale e limitata a una riga per azione.
- Non implementare scansioni massive, automatiche o concorrenti delle chiavi generate.
- Non usare cookie, `localStorage`, telemetria o salvataggi automatici.
- Conservare il limite di 20.000 chiavi per pagina.
- Conservare la compatibilità con Firefox e Chrome su Windows e con browser mobili.

## File principali

`index.html` è la fonte della pagina. Dopo ogni modifica funzionale:

1. verificare localmente;
2. copiare `index.html` in `bitcoin-api.html`;
3. aggiornare `CONTEXT.md` e `CHANGELOG.md` se necessario;
4. controllare che i due HTML siano identici;
5. pubblicare sul ramo `main`.

## Verifiche minime

- quantità e pagina producono il corretto intervallo;
- Avanti e Indietro modificano la pagina;
- l'ultima pagina non supera il limite secp256k1;
- le WIF sono compresse;
- il CSV contiene solo WIF, una per riga;
- il pulsante Verifica è visibile su mobile;
- la WIF può andare a capo su mobile;
- la chiave numerica 1 genera gli indirizzi noti elencati in `CONTEXT.md`;
- nessun riferimento a `127.0.0.1` è presente.

