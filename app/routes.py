from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/destinations')
def destinations():
    return render_template('destinations.html')

@main_bp.route('/recommendations')
def recommendations():
    return render_template('recommendations.html')

@main_bp.route('/itineraries')
def itineraries():
    return render_template('itineraries.html')