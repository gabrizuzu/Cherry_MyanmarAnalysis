import streamlit as st
import pandas as pd
import plotly.express as px
import geopandas as gpd

# Funzione per estrarre tema, indicatore e sentiment
def estrai_temi_indicatori_sentiment(row):
    if pd.isna(row["temi_indicatori_sentiment"]):  # Se il valore è mancante, restituisci una lista vuota
        return []
    try:
        # Dividi la stringa in gruppi separati da ";"
        gruppi = row["temi_indicatori_sentiment"].split(";")
        risultati = []
        for gruppo in gruppi:
            if "|" in gruppo:  # Verifica che il formato sia corretto
                tema, indicatore, sentiment = gruppo.split("|")
                risultati.append((tema, indicatore, float(sentiment)))
        return risultati
    except ValueError:  # Se il formato non è corretto, restituisci una lista vuota
        return []

def estrai_dati_geografici_e_sentiment(row):
    dati = []
    if isinstance(row["V2Locations"], float):
        return dati
        
    # Estrai sentiment per l'indicatore selezionato
    sentiment = 0
    count = 0
    if isinstance(row["temi_indicatori_sentiment"], str):
        for item in row["temi_indicatori_sentiment"].split(";"):
            if "|" in item:
                tema, indicatore, sent = item.split("|")
                if indicatore == indicatore_selezionato:
                    sentiment += float(sent)
                    count += 1
    
    if count == 0:
        return dati
        
    # Calcola sentiment medio
    avg_sentiment = sentiment / count
    
    # Estrai locations
    for loc in row["V2Locations"].split(";"):
        parti = loc.split("#")
        if len(parti) >= 8:
            regione = parti[1]
            latitudine = float(parti[5])
            longitudine = float(parti[6])
            dati.append((regione, latitudine, longitudine, avg_sentiment, count))
    return dati


# Carica i dati principali
df = pd.read_csv("/Volumes/CHERRY_SSD/gkg_myanmar_filtered.csv") 
# dati salvati sull'ssd di cherry

# Carica i temi disponibili da un altro file
df_themes = pd.read_csv("../Data/themes.csv")
temi_disponibili = df_themes["theme"].unique()

# Carica il file processed_gdelt per l'analisi degli indicatori
processed_df = pd.read_csv("../Data/gkg_data.csv")

# Converti DATE in formato datetime per facilitare il filtraggio
df["DATE"] = pd.to_datetime(df["DATE"], format="%Y%m%d%H%M%S")
processed_df["DATE"] = pd.to_datetime(processed_df["DATE"], format="%Y%m%d%H%M%S")

st.set_page_config(layout="wide", page_title="GDELT Dashboard")
# Header section
st.title("📊 Dashboard GDELT - Analisi dei Temi Relativi al Myanmar")

# Date selection
st.subheader("🗓️ Filtra per data")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Seleziona data di inizio", df["DATE"].min().date())
with col2:
    end_date = st.date_input("Seleziona data di fine", df["DATE"].max().date())

# Data processing
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)
df_filtered = df[(df["DATE"] >= start_date) & (df["DATE"] <= end_date)]
processed_df_filtered = processed_df[(processed_df["DATE"] >= start_date) & (processed_df["DATE"] <= end_date)]
volume_totale = len(df_filtered)

# Theme analysis section
with st.container():
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader(f"📌 Selezione Tema")
        tema_selezionato = st.selectbox("Seleziona un tema:", temi_disponibili)
        df_tema = df_filtered[df_filtered["V2Themes"].str.contains(tema_selezionato, na=False)]
        st.write(df_tema[["DATE", "GKGRECORDID", "SourceCommonName"]].reset_index(drop=True))
    with col2:
        st.subheader("📈 Distribuzione temporale degli articoli")
        fig_time = px.histogram(df_tema, x="DATE", title="Numero di articoli nel tempo", nbins=20)
        st.plotly_chart(fig_time, use_container_width=True)

# **1. Visualizzazione dei temi più frequenti in termini di volume**
# **2. Analisi degli indicatori**
st.subheader("📊 Analisi degli indicatori")

# Process data first
risultati = processed_df_filtered.apply(estrai_temi_indicatori_sentiment, axis=1).explode()
risultati_df = pd.DataFrame(risultati.tolist(), columns=["tema", "indicatore", "sentiment"], index=risultati.index)
processed_df_filtered = processed_df_filtered.join(risultati_df)
processed_df_filtered = processed_df_filtered.dropna(subset=["tema", "indicatore", "sentiment"])

# Volume and Sentiment Analysis
col1, col2 = st.columns(2)

with col1:
    st.write("### Volume degli articoli per indicatore")
    volume_indicatori = processed_df_filtered["indicatore"].value_counts().reset_index()
    volume_indicatori.columns = ["Indicatore", "Volume"]
    
    # Compact dataframe display
    st.dataframe(volume_indicatori, height=200)
    
    # Volume bar chart
    fig_volume_indicatori = px.bar(volume_indicatori, 
                                 x="Indicatore", 
                                 y="Volume", 
                                 title="Volume degli articoli per indicatore")
    st.plotly_chart(fig_volume_indicatori, use_container_width=True)

with col2:
    st.write("### Sentiment medio per indicatore")
    sentiment_indicatori = processed_df_filtered.groupby("indicatore")["sentiment"].mean().reset_index()
    sentiment_indicatori.columns = ["Indicatore", "Sentiment Medio"]
    
    # Compact dataframe display
    st.dataframe(sentiment_indicatori, height=200)
    
    # Sentiment bar chart
    fig_sentiment_indicatori = px.bar(sentiment_indicatori, 
                                    x="Indicatore", 
                                    y="Sentiment Medio", 
                                    title="Sentiment medio per indicatore")
    st.plotly_chart(fig_sentiment_indicatori, use_container_width=True)

# Themes and Time Analysis
col1, col2 = st.columns([1, 2])

with col1:
    st.write("### Temi più frequenti per indicatore")
    temi_indicatori = processed_df_filtered.groupby(["indicatore", "tema"]).size().reset_index(name="Volume")
    temi_indicatori = temi_indicatori.sort_values(by=["indicatore", "Volume"], ascending=[True, False]).reset_index(drop=True)
    st.dataframe(temi_indicatori, height=400, use_container_width=True)

with col2:
    st.write("### Evoluzione temporale del sentiment")
    sentiment_tempo = processed_df_filtered.groupby(["indicatore", pd.Grouper(key="DATE", freq="W")])["sentiment"].mean().reset_index()
    fig_sentiment_tempo = px.line(sentiment_tempo, 
                                x="DATE", 
                                y="sentiment", 
                                color="indicatore", 
                                title="Evoluzione del sentiment nel tempo per indicatore")
    st.plotly_chart(fig_sentiment_tempo, use_container_width=True)
#streamlit run app.py

# Titolo della dashboard
st.title("🌍 Mappa del Sentiment per Indicatore in Myanmar")

# Lista degli indicatori disponibili
indicatori = ["FreeSpeech", "Schooling", "Gender Inequality", "Corruption"]
indicatore_selezionato = st.selectbox("Seleziona l'indicatore da visualizzare:", indicatori)

dati_completi = []
for _, row in processed_df_filtered.iterrows():
    dati_completi.extend(estrai_dati_geografici_e_sentiment(row))

# Crea DataFrame con i dati
dati_mappa_df = pd.DataFrame(dati_completi, columns=["Regione", "Latitudine", "Longitudine", "Sentiment", "Count"])

# Aggrega dati per location
dati_aggregati = dati_mappa_df.groupby(["Regione", "Latitudine", "Longitudine"]).agg({
    "Sentiment": "mean",
    "Count": "sum"
}).reset_index()

# Crea la mappa
fig = px.scatter_mapbox(
    dati_aggregati,
    lat="Latitudine",
    lon="Longitudine",
    size="Count",  # Dimensione basata sul numero di menzioni
    color="Sentiment",  # Colore basato sul sentiment
    color_continuous_scale=[(0, "red"),(0.4, "yellow"), (1, "green")],  # Scala divergente
    color_continuous_midpoint=0,  # Punto centrale della scala (0)
    range_color=[-1,1],
    size_max=100,
    zoom=5,
    center={"lat": 21.9162, "lon": 95.9560},
    mapbox_style="open-street-map",
    title=f"Sentiment Analysis for {indicatore_selezionato} in Myanmar",
    height=800,
    hover_data={
        "Regione": True,
        "Sentiment": ":.2f",
        "Count": True
    }
)

# Aggiusta il layout
fig.update_layout(
    coloraxis_colorbar_title="Sentiment Score"
)

# Mostra la mappa
st.plotly_chart(fig)

# Mostra statistiche
st.subheader(f"📊 Statistics for {indicatore_selezionato}")
stats_df = dati_aggregati.sort_values("Sentiment", ascending=False).reset_index(drop=True)
st.dataframe(stats_df)

# Nuova mappa per regioni
st.title("🗺️ Mappa del Sentiment per Regione")


# Converti le coordinate in punti GeoDataFrame
from shapely.geometry import Point
geometry = [Point(xy) for xy in zip(dati_mappa_df['Longitudine'], dati_mappa_df['Latitudine'])]
points_gdf = gpd.GeoDataFrame(dati_mappa_df, geometry=geometry)

# Carica e prepara il GeoJSON delle regioni
myanmar_regions = gpd.read_file("../Data/gadm41_MMR_1.json")

# Spatial join tra punti e regioni
points_in_regions = gpd.sjoin(points_gdf, myanmar_regions, how="left", predicate="within")

# Aggrega sentiment per regione
sentiment_regioni = points_in_regions.groupby("NAME_1").agg({
    "Sentiment": "mean",
    "Count": "sum"
}).reset_index()

# Unisci con la geometria delle regioni
sentiment_regions_map = myanmar_regions.merge(sentiment_regioni, on="NAME_1", how="left")

# Crea la mappa coropletica
fig_regions = px.choropleth_mapbox(
    sentiment_regions_map,
    geojson=sentiment_regions_map.geometry.__geo_interface__,
    locations=sentiment_regions_map.index,
    color="Sentiment",
    color_continuous_scale=[(0, "red"), (0.4, "yellow"), (1, "green")],  # Scala divergente
    color_continuous_midpoint=0,  # Punto centrale della scala (0)
    range_color=[-1,1],
    mapbox_style="open-street-map",
    zoom=5,
    center={"lat": 21.9162, "lon": 95.9560},
    opacity=0.7,
    hover_data={
        "NAME_1": True,
        "Sentiment": ":.2f",
        "Count": True
    },
    title=f"Regional Sentiment Analysis for {indicatore_selezionato}"
)

fig_regions.update_layout(
    height=800,
    coloraxis_colorbar_title="Sentiment Score"
)

st.plotly_chart(fig_regions)

# Mostra statistiche per regione
st.subheader(f"📊 Regional Statistics for {indicatore_selezionato}")
st.dataframe(sentiment_regioni[["NAME_1", "Sentiment", "Count"]].sort_values("Sentiment", ascending=False).reset_index(drop=True))

