from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['app_config_secret_key']
Bootstrap(app)

# _________________________________________ API and URL for MOVIEDB _____________________________________________
URL_MOVIEDB = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
API_KEY = os.environ['movie_db_api_key']

# _________________________________________ Creating database and table _____________________________________________
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


db.create_all()


# _________________________________________ WTForms classes _____________________________________________
class EditForm(FlaskForm):
    rating = StringField('Your rating out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your review', validators=[DataRequired()])
    submit = SubmitField('Done')


class AddForm(FlaskForm):
    title = StringField('Movie title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


# _________________________________________ Backend _____________________________________________
@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=['GET', 'POST'])
def rate_movie():
    form = EditForm()
    movie_id = request.args.get('id')
    movie_selected = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie_selected.rating = float(form.rating.data)
        movie_selected.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("edit.html", form=form, movie=movie_selected)


@app.route("/add", methods=['GET', 'POST'])
def add_movie():
    form = AddForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(url=URL_MOVIEDB, params={"api_key": API_KEY, "query": movie_title})
        movie_data = response.json()['results']
        print(movie_data)
        return render_template('select.html', options=movie_data)

    return render_template('add.html', form=form)


@app.route("/find")
def find_movie():
    movie_id = request.args.get('id')
    if movie_id:
        movie_id_url = f"{MOVIE_DB_INFO_URL}/{movie_id}"
        response = requests.get(url=movie_id_url, params={"api_key": API_KEY, "language": "en-US"})
        data = response.json()
        print(data)
        new_movie_to_add = Movie(
            title=data['title'],
            year=data['release_date'],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data['overview']
        )
        db.session.add(new_movie_to_add)
        db.session.commit()
        return redirect(url_for('rate_movie', id=new_movie_to_add.id))

    return render_template('index.html')


@app.route("/delete")
def delete_movie():
    movie_id = request.args.get('id')
    movie_to_delete = Book.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
