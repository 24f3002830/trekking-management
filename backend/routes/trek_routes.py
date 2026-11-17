"""
Trek Routes for Trekking Management Application.
Supports trek browsing, filtering, search, and Admin CRUD operations with Redis caching.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from backend.models import db, Trek, User, Review
from backend.routes.auth_routes import token_required, role_required
from backend.cache import get_cache, set_cache, clear_cache

trek_bp = Blueprint('treks', __name__, url_prefix='/api/treks')


@trek_bp.route('', methods=['GET'])
def get_all_treks():
    """
    Get all treks with optional search and filtering.
    Filters:
      - search: string (matches trek name or location)
      - difficulty: 'Easy', 'Moderate', 'Hard'
      - location: string
      - status: 'Open', 'Closed', 'Completed', etc. (default: all visible)
    Utilizes Redis cache for rapid retrieval.
    """
    search = request.args.get('search', '').strip().lower()
    difficulty = request.args.get('difficulty', '').strip()
    location = request.args.get('location', '').strip()
    status = request.args.get('status', '').strip()

    # Generate cache key based on query parameters
    cache_key = f"treks:search={search}&diff={difficulty}&loc={location}&st={status}"

    # Attempt to retrieve from Redis cache
    cached_data = get_cache(cache_key)
    if cached_data is not None:
        return jsonify({
            'success': True,
            'source': 'cache',
            'count': len(cached_data),
            'treks': cached_data
        }), 200

    # Query from SQLite database
    query = Trek.query

    if search:
        query = query.filter(
            (Trek.name.ilike(f'%{search}%')) | (Trek.location.ilike(f'%{search}%'))
        )
    if difficulty:
        query = query.filter(Trek.difficulty.ilike(difficulty))
    if location:
        query = query.filter(Trek.location.ilike(f'%{location}%'))
    if status:
        query = query.filter_by(status=status)

    treks = query.order_by(Trek.start_date.asc()).all()
    treks_data = [t.to_dict() for t in treks]

    # Store result in Redis cache with 5 minute expiration
    set_cache(cache_key, treks_data, expire_seconds=300)

    return jsonify({
        'success': True,
        'source': 'database',
        'count': len(treks_data),
        'treks': treks_data
    }), 200


@trek_bp.route('/<int:trek_id>', methods=['GET'])
def get_trek(trek_id):
    
    #Get detailed information for a single trek.
    
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found.'}), 404

    return jsonify({
        'success': True,
        'trek': trek.to_dict()
    }), 200


@trek_bp.route('', methods=['POST'])
@token_required
@role_required(['admin'])
def create_trek(current_user):
    """
    Admin only: Create a new trekking route/event.
    """
    data = request.get_json() or {}

    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    location = data.get('location', '').strip()
    difficulty = data.get('difficulty', 'Moderate').strip()
    duration_days = data.get('duration_days')
    total_slots = data.get('total_slots')
    price = data.get('price', 0.0)
    assigned_staff_id = data.get('assigned_staff_id')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')

    # Basic validations
    if not name or not location or not duration_days or not total_slots or not start_date_str or not end_date_str:
        return jsonify({
            'success': False,
            'message': 'Name, location, duration_days, total_slots, start_date, and end_date are required.'
        }), 400

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Invalid date format. Use YYYY-MM-DD.'
        }), 400

    if end_date < start_date:
        return jsonify({
            'success': False,
            'message': 'End date cannot be earlier than start date.'
        }), 400

    # If assigned_staff_id is provided, verify they are indeed staff
    if assigned_staff_id:
        staff_user = User.query.filter_by(id=assigned_staff_id, role='staff').first()
        if not staff_user:
            return jsonify({
                'success': False,
                'message': f'Staff user with ID {assigned_staff_id} does not exist or is not a staff member.'
            }), 400

    itinerary = data.get('itinerary', '')
    gear_checklist = data.get('gear_checklist', '')

    new_trek = Trek(
        name=name,
        description=description,
        location=location,
        difficulty=difficulty,
        duration_days=int(duration_days),
        total_slots=int(total_slots),
        available_slots=int(total_slots),  # Initially all slots are available
        price=float(price),
        itinerary=itinerary.strip() if itinerary else None,
        gear_checklist=gear_checklist.strip() if gear_checklist else None,
        assigned_staff_id=assigned_staff_id,
        status='Open',
        start_date=start_date,
        end_date=end_date
    )

    db.session.add(new_trek)
    db.session.commit()

    # Clear cached trek listings
    clear_cache("treks:*")

    return jsonify({
        'success': True,
        'message': 'Trek created successfully.',
        'trek': new_trek.to_dict()
    }), 201


@trek_bp.route('/<int:trek_id>', methods=['PUT'])
@token_required
@role_required(['admin'])
def update_trek(current_user, trek_id):
    """
    Admin only: Update an existing trekking route.
    """
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found.'}), 404

    data = request.get_json() or {}

    if 'name' in data:
        trek.name = data['name'].strip()
    if 'description' in data:
        trek.description = data['description'].strip()
    if 'location' in data:
        trek.location = data['location'].strip()
    if 'difficulty' in data:
        trek.difficulty = data['difficulty'].strip()
    if 'duration_days' in data:
        trek.duration_days = int(data['duration_days'])
    if 'price' in data:
        trek.price = float(data['price'])
    if 'status' in data:
        trek.status = data['status'].strip()
    if 'itinerary' in data:
        trek.itinerary = data['itinerary'].strip() if data['itinerary'] else None
    if 'gear_checklist' in data:
        trek.gear_checklist = data['gear_checklist'].strip() if data['gear_checklist'] else None

    if 'total_slots' in data:
        new_total = int(data['total_slots'])
        # Adjust available slots proportionally
        slots_booked = trek.total_slots - trek.available_slots
        if new_total < slots_booked:
            return jsonify({
                'success': False,
                'message': f'Cannot reduce total slots below currently booked slots ({slots_booked}).'
            }), 400
        trek.total_slots = new_total
        trek.available_slots = new_total - slots_booked

    if 'assigned_staff_id' in data:
        staff_id = data['assigned_staff_id']
        if staff_id:
            staff_user = User.query.filter_by(id=staff_id, role='staff').first()
            if not staff_user:
                return jsonify({'success': False, 'message': 'Specified staff member does not exist.'}), 400
        trek.assigned_staff_id = staff_id

    if 'start_date' in data:
        trek.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    if 'end_date' in data:
        trek.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()

    db.session.commit()
    clear_cache("treks:*")

    return jsonify({
        'success': True,
        'message': 'Trek updated successfully.',
        'trek': trek.to_dict()
    }), 200


@trek_bp.route('/<int:trek_id>', methods=['DELETE'])
@token_required
@role_required(['admin'])
def delete_trek(current_user, trek_id):
    """
    Admin only: Remove a trekking route.
    """
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found.'}), 404

    # Check if there are active bookings
    active_bookings = [b for b in trek.bookings if b.status == 'Booked']
    if active_bookings:
        return jsonify({
            'success': False,
            'message': f'Cannot delete trek because it has {len(active_bookings)} active booking(s). Cancel the bookings first or set trek status to Closed.'
        }), 400

    db.session.delete(trek)
    db.session.commit()
    clear_cache("treks:*")

    return jsonify({
        'success': True,
        'message': f'Trek "{trek.name}" was successfully removed.'
    }), 200


# ==========================================
# TREK REVIEWS & RATINGS ENDPOINTS
# ==========================================

@trek_bp.route('/<int:trek_id>/reviews', methods=['GET'])
def get_trek_reviews(trek_id):
    """
    Get all public reviews and star ratings for a specific trek.
    """
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found.'}), 404

    reviews = Review.query.filter_by(trek_id=trek.id).order_by(Review.created_at.desc()).all()
    return jsonify({
        'success': True,
        'trek_id': trek.id,
        'trek_name': trek.name,
        'average_rating': trek.average_rating,
        'review_count': len(reviews),
        'reviews': [r.to_dict() for r in reviews]
    }), 200


@trek_bp.route('/<int:trek_id>/reviews', methods=['POST'])
@token_required
def add_trek_review(current_user, trek_id):
    """
    Trekker submits a rating (1 to 5 stars) and review feedback for a trek.
    """
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found.'}), 404

    data = request.get_json() or {}
    rating = data.get('rating')
    comment = data.get('comment', '').strip()

    if rating is None:
        return jsonify({'success': False, 'message': 'Rating is required.'}), 400

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return jsonify({'success': False, 'message': 'Rating must be between 1 and 5 stars.'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid rating number.'}), 400

    new_review = Review(
        user_id=current_user.id,
        trek_id=trek.id,
        rating=rating,
        comment=comment
    )

    db.session.add(new_review)
    db.session.commit()
    clear_cache("treks:*")

    return jsonify({
        'success': True,
        'message': 'Thank you! Your trek review was posted successfully.',
        'review': new_review.to_dict(),
        'average_rating': trek.average_rating
    }), 201
