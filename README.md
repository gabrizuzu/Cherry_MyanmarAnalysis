# Report Lavoro - 12/03

## Data Source
Ho preso i dati da [GDELT Global Knowledge Graph](http://data.gdeltproject.org/gkg/index.html). 
Inizialmente ho provato a utilizzare **Google BigQuery** tramite API e la prova gratuita. (troppo costosa), i dati si possono tranquillamente scaricare manualmente o tramite un programma dal sito di gdelt

### Query utilizzata:
```sql
SELECT theme, COUNT(*) as count
FROM (
   SELECT REGEXP_REPLACE(SPLIT(Themes, ';')[SAFE_OFFSET(0)], r',.*', '') AS theme
   FROM `gdelt-bq.gdeltv2.gkg`
   WHERE DATE > 20210101000000
     AND DATE < 20241231000000
     AND Locations LIKE '%Myanmar%'
)
GROUP BY theme
ORDER BY count DESC;
```

## Analisi dei Temi
Ho estratto tutti i temi possibili e le loro occorrenze, mantenendo solo quelli con **più di 1000 occorrenze** (circa 700 temi in totale).

### Estrazione Temi con Python:
```python
def extract_themes(v2themes):
    if pd.isna(v2themes):  # Gestisce valori mancanti
        return []
    themes = v2themes.split(';')  # Divide i temi separati da ';'
    themes = [re.sub(r',.*', '', theme) for theme in themes]  # Rimuove il peso (tutto dopo la virgola)
    return themes

# Applica la funzione alla colonna V2Themes e "esplode" i temi in righe separate
df_themes = df[['DATE', 'Locations', 'V2Themes']].copy()
df_themes['theme'] = df_themes['V2Themes'].apply(extract_themes)
df_themes = df_themes.explode('theme')  # Crea una riga per ogni tema

# Filtra i dati per Myanmar e intervallo di date
df_filtered = df_themes[
   (df_themes['DATE'] > 20210101000000) &
   (df_themes['DATE'] < 20241231000000) &
   (df_themes['Locations'].str.contains('Myanmar', na=False))
]

# Conta i temi unici
theme_counts = df_filtered['theme'].value_counts().reset_index()
theme_counts.columns = ['theme', 'count']
```

## Associazione agli Indicatori
Ho associato manualmente i temi (solo quelli rilevanti) ai seguenti indicatori:
- **Corruption**
- **Free Speech**
- **Gender Inequality**
- **Schooling**

Ho tentato di creare un **classificatore ML** per assegnare automaticamente questi indicatori, ma la massima accuratezza ottenuta è stata **16%**.

Dopo l'associazione, ho filtrato il dataset lasciando solo le righe contenenti almeno un indicatore (una riga può avere più temi associati a diversi indicatori).

## Calcolo del Sentiment
Per ogni tema ho calcolato un **sentiment ponderato**:
```python
sentiment = V2Tone * relative_occurrence
```
Dove:
- **V2Tone** = Tono generale dell'evento
- **relative_occurrence** = (occorrenza del tema) / (occorrenza totale di tutti i temi)

### Esempio di Attributo Creato:
```
EDUCATION|Schooling|-0.2970; SOC_POINTSOFINTEREST_SCHOOL|Schooling|-0.2970; TAX_FNCACT_WOMEN|Gender_Inequality|-0.1281
```

## Analisi Geospaziale
Ho utilizzato l’attributo **V2Locations** per analizzare la distribuzione geografica dei temi in Myanmar.
Esempio di formato dati:
```
1#Mien#BM#BM##22#98#BM#605;1#Mien#BM#BM##22#98#BM#757
```

### Elaborazione Geospaziale:
- Pulizia dell’attributo mantenendo solo le voci relative al **Myanmar**
- Raggruppamento per **coordinate geografiche**, calcolando:
  - **Media del sentiment**
  - **Volume degli eventi**
- Aggregazione dei dati per **regioni del Myanmar**, utilizzando file **GeoJSON**.

## Dashboard
Tutte le elaborazioni sono state raccolte e mostrate in una **dashboard interattiva** per visualizzare:
- Distribuzione geografica dei temi
- Andamento dei sentimenti nel tempo
- Confronto tra i diversi indicatori

## Lavori Futuri
✅ **Espandere l’analisi su più anni** (i dati sono disponibili dal 2013)
✅ **Implementare un aggiornamento automatico** del dataset (GDELT si aggiorna ogni 15 minuti, quindi potremmo aggiornare i dati ogni giorno/settimana)
✅ **Analizzare correlazioni tra indicatori di stabilità e indici economici**
✅ **Migliorare il calcolo del sentiment**, magari utilizzando modelli NLP più avanzati.

---




cosa da fare:

1. scaricato dati dal 2019 al 2025 da ora in poi chiamato gkg_data 
2. estrazione temi unici, [temi,count] --> themes_extractor.py
3. assegnazione manuale degli indicatori [temi,count,indicatore] --> sbatti io
4. pulizia totale di gkg_data --> data_cleaning.py
  a. tenere solo le colonne utili
  b. tenere solo le coordinate in v2locations solo del myanmar
  c. modificare V2themes accorpando i temi che si ripetono e sommando le occorrenze
  d. calcolare il sentiment con la formula e generando così un nuovo attributo che contiene le info su temi, indicatore e sentiment
5. fare dashboard con tutti i dati --> Dashboard/app.py