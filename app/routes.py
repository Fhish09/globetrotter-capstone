from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

# NOTE: /destinations HTML is served from destinations_bp (Accept: text/html)
# so the same path can also return JSON for fetch() calls.

@main_bp.route('/destinations/<int:dest_id>')
def destination_detail(dest_id):
    return render_template('destination_detail.html', dest_id=dest_id)

@main_bp.route('/recommendations')
def recommendations():
    return render_template('recommendations.html')

@main_bp.route('/itineraries')
def itineraries():
    return render_template('itineraries.html')
