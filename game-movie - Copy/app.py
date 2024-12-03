from flask import Flask, render_template
from flask import Flask, render_template, request, redirect, url_for, session
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_talisman import Talisman
from flask import send_from_directory, current_app
import bleach
import os
import mimetypes
from flask import Flask, jsonify, request

from flask import render_template, request, redirect, url_for



app = app = Flask(__name__, static_folder='static', template_folder='template')






# Setup CSP (Content Security Policy) to allow external resources like jQuery
Talisman(app, content_security_policy={
    'default-src': ["'self'"],
    'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'", 'https://code.jquery.com'],
    'style-src': ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com'],
    'img-src': ["'self'", 'data:'],
    'connect-src': ["'self'"],
    'font-src': ["'self'", 'https://fonts.gstatic.com'],
    'object-src': ['none'],
    'media-src': ["'self'", "http://127.0.0.1:5000"],
    'frame-src': ["'self'", "https://www.youtube.com"]
})	
# Configurations
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///d://shwetha//pwa//reviews.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class MovieReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie_title = db.Column(db.String(100), nullable=False)
    review = db.Column(db.Text, nullable=False)
    reviewer_name = db.Column(db.String(50), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
   
class GameReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_title = db.Column(db.String(100), nullable=False)
    review = db.Column(db.Text, nullable=False)
    reviewer_name = db.Column(db.String(50), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index1.html')


@app.after_request
def apply_csp(response):
    # Use a single-line string for the CSP header without newlines
    response.headers['Content-Security-Policy'] = "default-src 'self'; media-src 'self' http://127.0.0.1:5000; frame-src 'self' https://www.youtube.com;"
    return response

# Route for Movie Reviews Page
@app.route('/movie-reviews')
def movie_reviews():
    return render_template('movie1.html')  # Create this template

# Route for Game Reviews Page
@app.route('/game-reviews')
def game_reviews():
    return render_template('game_reviews.html')  # Create this template




@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", 'success')
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password!", 'error')
    return render_template('login.html')


@app.route('/get_reviews', methods=['GET'])
def get_reviews():
    category = request.args.get('category')  # Get the selected category (movie/game)
    item_title = request.args.get('item_title')  # Get the selected item (movie title/game title)

    # Fetch distinct movie or game titles based on the category
    if category == 'movie':
        movie_titles = [movie.movie_title for movie in MovieReview.query.distinct(MovieReview.movie_title).all()]
        game_titles = []  # No games when category is movie
        
        # Fetch reviews for the selected movie or all movies if no title is selected
        if item_title == "":
            reviews = MovieReview.query.all()
        else:
            reviews = MovieReview.query.filter_by(movie_title=item_title).all()

    elif category == 'game':
        game_titles = [game.game_title for game in GameReview.query.distinct(GameReview.game_title).all()]
        movie_titles = []  # No movies when category is game
        
        # Fetch reviews for the selected game or all games if no title is selected
        if item_title == "":
            reviews = GameReview.query.all()
        else:
            reviews = GameReview.query.filter_by(game_title=item_title).all()

    else:
        movie_titles = []
        game_titles = []
        reviews = []

    return render_template('reviews.html', 
                           movie_titles=movie_titles, 
                           game_titles=game_titles, 
                           reviews=reviews, 
                           category=category,
                           selected_item=item_title)

@app.route('/add_review', methods=['GET', 'POST'])
@login_required
def add_review():
    if request.method == 'POST':
        category = request.form.get('category')  # 'movie' or 'game'
        title = request.form.get('title')  # Title from the dropdown or text input
        review = request.form['review']
        rating = int(request.form['rating'])

        # Debugging: Print form data to see what is being passed
        print(f"Category: {category}, Title: {title}, Review: {review}, Rating: {rating}")

        # Check for duplicate review by the same user
        if category == 'movie':
            # If the title is 'other', use the custom movie title
            if title == "other":
                title = request.form.get('custom_movie_title')  # Get the custom movie title from input field
                if not title:
                    flash('Please provide a custom movie title.', 'danger')
                    return redirect(url_for('add_review'))

            # Check if the user already reviewed this movie
            existing_review = MovieReview.query.filter_by(movie_title=title, reviewer_name=current_user.username).first()
            if existing_review:
                flash('You have already reviewed this movie.', 'danger')
                return redirect(url_for('add_review'))

            # Add movie review
            sanitized_review = bleach.clean(review, tags=['b', 'i', 'u', 'em', 'strong', 'a'])
            new_review = MovieReview(
                movie_title=title,
                review=sanitized_review,
                reviewer_name=current_user.username,
                rating=rating
            )
            db.session.add(new_review)
            db.session.commit()
            flash('Movie review added successfully!', 'success')

        elif category == 'game':
            # If the title is 'other', use the custom game title
            if title == "other":
                title = request.form.get('custom_game_title')  # Get the custom game title from input field
                if not title:
                    flash('Please provide a custom game title.', 'danger')
                    return redirect(url_for('add_review'))

            # Check if the user already reviewed this game
            existing_review = GameReview.query.filter_by(game_title=title, reviewer_name=current_user.username).first()
            if existing_review:
                flash('You have already reviewed this game.', 'danger')
                return redirect(url_for('add_review'))

            # Add game review
            sanitized_review = bleach.clean(review, tags=['b', 'i', 'u', 'em', 'strong', 'a'])
            new_review = GameReview(
                game_title=title,
                review=sanitized_review,
                reviewer_name=current_user.username,
                rating=rating
            )
            db.session.add(new_review)
            db.session.commit()
            flash('Game review added successfully!', 'success')

        return redirect(url_for('index'))  # Redirect to the home page or wherever you like

    # Get distinct movie and game titles from the database
    movie_titles = [movie.movie_title for movie in MovieReview.query.distinct(MovieReview.movie_title).all()]
    game_titles = [game.game_title for game in GameReview.query.distinct(GameReview.game_title).all()]

    # Render the form and pass the titles
    return render_template('add_review.html', movie_titles=movie_titles, game_titles=game_titles)
@app.route('/edit_review/<int:review_id>', methods=['POST'])
def edit_review(review_id):
    review = MovieReview.query.get_or_404(review_id)  # Fetch the review by ID

    # Check if the current user is the owner of the review
    if review.reviewer_name != current_user.username:  # Check if the reviewer is the current user
        flash("You are not authorized to edit this review.", 'danger')
        return redirect(url_for('get_reviews'))  # Redirect to reviews page if unauthorized

    if request.method == 'POST':
        review.movie_title = request.form['movie_title']
        review.review = request.form['review']
        review.rating = request.form['rating']
        db.session.commit()  # Commit the changes to the database
        flash("Review updated successfully!", 'success')
        return redirect(url_for('get_reviews'))  # Redirect to the reviews page after edit

    return render_template('edit_review.html', review=review)

@app.route('/delete_review/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    review = MovieReview.query.get_or_404(review_id)

    # Check if the current user is the owner of the review
    if review.reviewer_name != current_user.username:  # Check if the reviewer is the current user
        flash("You are not authorized to delete this review.", 'danger')
        return redirect(url_for('get_reviews'))  # Redirect to reviews page if unauthorized

    db.session.delete(review)
    db.session.commit()  # Commit the deletion
    flash("Review deleted successfully.", 'success')
    return redirect(url_for('get_reviews'))  # Redirect to the reviews page after deletion


@app.route('/api/items', methods=['GET'])
def get_items():
    category = request.args.get('category')
    if category == 'movie':
        items = MovieReview.query.with_entities(MovieReview.movie_title).distinct().all()
    elif category == 'game':
        items = GameReview.query.with_entities(GameReview.game_title).distinct().all()
    else:
        return jsonify({"error": "Invalid category"}), 400

    # Extract titles from the query result
    item_titles = [item[0] for item in items]
    return jsonify(item_titles)


@app.route('/api/check_title', methods=['GET'])
def check_title():
    category = request.args.get('category')
    title = request.args.get('title')
    username = current_user.username  # Assuming you're using Flask-Login

    if category == 'movie':
        exists = MovieReview.query.filter_by(movie_title=title, reviewer_name=username).first()
    elif category == 'game':
        exists = GameReview.query.filter_by(game_title=title, reviewer_name=username).first()
    else:
        return jsonify({'error': 'Invalid category'}), 400

    return jsonify({'exists': bool(exists)})
@app.route('/get_movies', methods=['GET'])
def get_movies():
    # Query for distinct movie titles
    movie_titles = db.session.query(MovieReview.movie_title).distinct().all()
    movie_titles = [title[0] for title in movie_titles]  # Convert tuple to list
    return jsonify({'movies': movie_titles})

@app.route('/get_games', methods=['GET'])
def get_games():
    # Query for distinct game titles
    game_titles = db.session.query(GameReview.game_title).distinct().all()
    game_titles = [title[0] for title in game_titles]  # Convert tuple to list
    return jsonify({'games': game_titles})


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)