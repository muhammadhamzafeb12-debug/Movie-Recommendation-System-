# CineMatch - Movie Recommender System

An AI-powered movie recommendation application built with Python and Machine Learning.

## Features
- Movie search
- Five similar movie recommendations
- Movie posters
- Movie descriptions
- Movie ratings
- Professional Streamlit dashboard

## Technologies
- Python
- Pandas
- NumPy
- Scikit-learn
- NLTK
- Streamlit

## Machine Learning
- Content-Based Filtering
- CountVectorizer
- Porter Stemmer
- Cosine Similarity

## Installation
1. Install requirements: pip install -r requirements.txt
2. Run application: streamlit run app.py

## Dataset
TMDB 5000 Movies and Credits Dataset.

## Author
Muhammad Hamza


## Poster setup (no personal API key)

Run `python download_posters.py` once while connected to the internet. It looks up poster URLs from a public Hugging Face dataset and the bundled `9000plus.csv`, then downloads available images into `posters/`. The app prefers local poster files, so recommendation cards load quickly after the initial download. Some films may still have no poster in the public sources; no dataset can guarantee 100% coverage.

Then run `streamlit run app.py`.
