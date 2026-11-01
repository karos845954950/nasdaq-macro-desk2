# NASDAQ Macro Desk

Dashboard personale in italiano per seguire alcuni driver macro/intermarket rilevanti per NQ1! (Nasdaq-100 futures).

## Cosa fa
- Snapshot di NQ futures, ES futures, VIX, Treasury USA 10Y, DXY, oro e petrolio, quando disponibili su Yahoo Finance.
- Grafico candlestick del Nasdaq futures.
- Feed RSS della Federal Reserve e del Bureau of Labor Statistics.
- Signal brief **euristico e trasparente**: bullish / bearish / neutral basato su pochi input di mercato.
- Sezione di interpretazione macro.
- Grafici FRED opzionali, usando una API key gratuita.

## Limiti importanti
- `NQ=F` su Yahoo Finance **non è il ticker TradingView `NQ1!`** e i dati possono differire, essere ritardati o non disponibili. Per decisioni operative, verifica prezzi e grafici direttamente su TradingView/broker.
- Il segnale non è un modello predittivo, non analizza automaticamente ogni notizia e non costituisce consulenza finanziaria.
- Il calendario macro non viene inventato: controlla gli orari e i dati ufficiali nelle fonti primarie.
- Non è inclusa una chiamata a un LLM a pagamento. L'analisi testuale è una guida strutturata; generare un vero briefing AI personalizzato richiederebbe collegare un provider e la relativa API key, che può avere costi.
- Yahoo Finance, RSS e FRED possono cambiare disponibilità/struttura. Controlla i termini d'uso dei dati.

## Avvio locale sul PC
Richiede Python 3.10 o superiore.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Il browser aprirà la dashboard in locale.

## Pubblicarla gratis e usarla su PC e cellulare
1. Crea un account GitHub e un nuovo repository, per esempio `nasdaq-macro-desk`.
2. Carica `app.py` e `requirements.txt` (puoi caricare anche questo README).
3. Crea un account su Streamlit Community Cloud e collega GitHub.
4. Seleziona il repository, branch `main` e file principale `app.py`, poi premi Deploy.
5. Apri il link HTTPS fornito da Streamlit sul PC e sul telefono.
6. Sul telefono: apri il link in Safari/Chrome e scegli **Aggiungi alla schermata Home**. Si comporterà come una web app; non è un'app nativa pubblicata sugli store.

La disponibilità gratuita e i limiti dei servizi possono cambiare nel tempo. Se l'app va in sleep, il primo caricamento potrebbe essere più lento.

## Aggiungere dati FRED
1. Crea una API key gratuita sul sito ufficiale FRED: https://fred.stlouisfed.org/docs/api/api_key.html
2. In Streamlit Community Cloud apri le impostazioni/secrets dell'app e inserisci:

```toml
FRED_API_KEY = "la_tua_api_key"
```

Per l'esecuzione locale, puoi impostare la variabile d'ambiente `FRED_API_KEY`.

## Come funziona l'aggiornamento
- I prezzi vengono memorizzati in cache per 15 minuti.
- I feed RSS vengono memorizzati in cache per 30 minuti.
- I dati FRED vengono memorizzati in cache per 60 minuti.
- La dashboard ricalcola il signal brief quando i dati vengono ricaricati. Puoi premere “Aggiorna dati adesso”.
- Questo non equivale a un report AI schedulato che viene generato e inviato ogni mattina. Per un aggiornamento garantito a orario fisso servirebbe un job schedulato esterno; per un briefing AI completo, anche un provider AI.

## Fonti consigliate da verificare ogni giorno
- Federal Reserve: https://www.federalreserve.gov/newsevents.htm
- BLS: https://www.bls.gov/schedule/
- BEA (PCE/PIL): https://www.bea.gov/news/schedule
- Calendario ufficiale Treasury: https://home.treasury.gov/resource-center/data-chart-center/quarterly-refunding
- FRED: https://fred.stlouisfed.org/
- TradingView: https://www.tradingview.com/

## Nota
Questa app è uno starter tecnico e va testata prima dell'uso. Non usarla come unico input per operare futures, che comportano rischio elevato.
