from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/destinations/<int:dest_id>')
def destination_detail(dest_id):
    return render_template('destination_detail.html', dest_id=dest_id)

# /recommendations HTML handled in recommendations_bp (same Accept pattern as destinations)
# /destinations HTML handled in destinations_bp

@main_bp.route('/itineraries')
def itineraries():
    return render_template('itineraries.html')

@main_bp.route('/testimonials')
def testimonials():
    return render_template('testimonials.html')
