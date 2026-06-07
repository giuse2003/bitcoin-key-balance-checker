# Aggiornare il progetto

Questa guida permette di lavorare da qualsiasi computer Windows con Git installato.

## Prima configurazione

1. Installa Git:
   https://git-scm.com/download/win
2. Installa GitHub CLI:
   https://cli.github.com/
3. Accedi a GitHub:

```powershell
gh auth login
gh auth setup-git
```

4. Clona il progetto:

```powershell
git clone https://github.com/giuse2003/bitcoin-key-balance-checker.git
cd bitcoin-key-balance-checker
```

Non copiare la cartella `.git` manualmente e non salvare token o password nei file del progetto.

## Iniziare una sessione di lavoro

Prima di modificare i file:

```powershell
git status
git pull
```

Apri `CONTEXT.md` per conoscere lo stato corrente e le decisioni già prese.

## Modificare

La pagina principale è `index.html`. Dopo averla modificata e provata, mantieni aggiornata anche la copia alternativa:

```powershell
Copy-Item index.html bitcoin-api.html -Force
```

Aggiorna `CONTEXT.md` e `CHANGELOG.md` quando cambia il comportamento del progetto.

## Pubblicare

```powershell
git status
git add .
git commit -m "Descrizione chiara della modifica"
git push
```

GitHub Pages aggiornerà automaticamente:

https://giuse2003.github.io/bitcoin-key-balance-checker/

La pubblicazione può richiedere qualche minuto. Se il browser mostra ancora la vecchia versione, ricarica ignorando la cache.

## Verificare l'allineamento

```powershell
git status
git fetch
git status -sb
```

Una copia allineata non deve mostrare file modificati e il ramo locale non deve risultare avanti o indietro rispetto a `origin/main`.

La cartella deve contenere la directory nascosta `.git`. Se hai ricevuto soltanto i singoli file, esegui nuovamente `git clone` invece di crearla o copiarla manualmente.

## Risolvere modifiche concorrenti

Se un altro computer ha già pubblicato modifiche:

```powershell
git pull
```

Se Git segnala un conflitto, non forzare il push. Apri i file indicati, conserva le modifiche corrette, verifica nuovamente la pagina e poi esegui commit e push.
