
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import pickle
import gdown
import pandas as pd
import requests


load_dotenv()
TMDB_KEY = os.getenv("TMDB_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB setup (optional, for feed or future)
client = MongoClient(MONGO_URI)
db = client.get_database("movie_db")


app = Flask(__name__)
CORS(app)



if not os.path.exists("movie_dict.pkl"):
    gdown.download("https://drive.google.com/uc?id=12Sh28ShORcmuqvauHP7ugk92qlgM9CUM", "movie_dict.pkl", quiet=False)

if not os.path.exists("similarity.pkl"):
    gdown.download("https://drive.google.com/uc?id=1ZaK4ZfFz746g0enih_CEbsL3AMJNO7z0", "similarity.pkl", quiet=False)



with open("movie_dict.pkl", "rb") as f:
    movies = pickle.load(f)
if not isinstance(movies, pd.DataFrame):
    movies = pd.DataFrame(movies)

with open("similarity.pkl", "rb") as f:
    similarity = pickle.load(f)

def fetch_poster(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_KEY}&language=en-US"
        response = requests.get(url)
        data = response.json()
        poster_path = data.get('poster_path', '')
        return f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else None
    except:
        return None

def recommend(movie_title):
    if movie_title not in movies['title'].values:
        return [], []

    index = movies[movies['title'] == movie_title].index[0]
    distances = sorted(list(enumerate(similarity[index])), key=lambda x: x[1], reverse=True)[1:6]

    recommended_titles = []
    recommended_posters = []

    for i in distances:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_titles.append(movies.iloc[i[0]].title)
        recommended_posters.append(fetch_poster(movie_id))

    return recommended_titles, recommended_posters

@app.route("/recommend", methods=["POST"])
def recommend_route():
    data = request.get_json()
    movie_title = data.get("movie")
    titles, posters = recommend(movie_title)
    if not titles:
        return jsonify({
            "message": "No similar movies found. Showing top-rated instead.",
            "recommendations": []
        })
    return jsonify({
        "recommendations": [
            {"title": t, "poster": p} for t, p in zip(titles, posters)
        ]
    })

if __name__ == "__main__":
    app.run(debug=True)
