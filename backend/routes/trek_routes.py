from datetime import datetime
from flask import Blueprint, request, jsonify
from backend.models import db, Trek, User, Review
from backend.routes.auth_routes import token_required, role_required
from backend.cache import get_cache, set_cache, clear_cache

trek_bp = Blueprint('treks', __name__, url_prefix='/api/treks')


@trek_bp.route('', methods=['GET'])
def get_all_treks():
    # Get all treks with optional search, difficulty, location, status, and date filters
    search = request.args.get('search', '').strip().lower()
    difficulty = request.args.get('difficulty', '').strip()
    location = request.args.get('location', '').strip()
    status = request.args.get('status', '').strip()
    date_str = request.args.get('date', '').strip() or request.args.get('start_date', '').strip()

    # Try cache first
    cache_key = f"treks:search={search}&diff={difficulty}&loc={location}&st={status}&date={date_str}"
    cached = get_cache(cache_key)
    if cached is not None:
        return jsonify({'success': True, 'source': 'cache', 'count': len(cached), 'treks': cached}), 200

    # Query database
    query = Trek.query
    if search:
        query = query.filter((Trek.name.ilike(f'%{search}%')) | (Trek.location.ilike(f'%{search}%')))
    if difficulty:
        query = query.filter(Trek.difficulty.ilike(difficulty))
    if location:
        query = query.filter(Trek.location.ilike(f'%{location}%'))
    if status:
        query = query.filter_by(status=status)
    if date_str:
        try:
            filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter(Trek.start_date >= filter_date)
        except Exception:
            pass

    treks = query.order_by(Trek.start_date.asc()).all()
    treks_list = [t.to_dict() for t in treks]

    # Save in cache for 5 minutes
    set_cache(cache_key, treks_list, expire_seconds=300)

    return jsonify({'success': True, 'source': 'database', 'count': len(treks_list), 'treks': treks_list}), 200


@trek_bp.route('/<int:trek_id>', methods=['GET'])
def get_trek(trek_id):
    # Fetch details for one trek
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found'}), 404
    return jsonify({'success': True, 'trek': trek.to_dict()}), 200


@trek_bp.route('', methods=['POST'])
@token_required
@role_required(['admin'])
def create_trek(_current_user):
    # Admin creates a new trek
    data = request.get_json() or {}

    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    location = data.get('location', '').strip()
    difficulty = data.get('difficulty', 'Moderate').strip()
    duration_days = data.get('duration_days')
    total_slots = data.get('total_slots')
    price = data.get('price', 0)
    assigned_staff_id = data.get('assigned_staff_id')
    start_str = data.get('start_date')
    end_str = data.get('end_date')

    if not name or not location or not duration_days or not total_slots or not start_str or not end_str:
        return jsonify({'success': False, 'message': 'Please fill all required fields'}), 400

    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
    except Exception:
        return jsonify({'success': False, 'message': 'Invalid date format (use YYYY-MM-DD)'}), 400

    if end_date < start_date:
        return jsonify({'success': False, 'message': 'End date cannot be before start date'}), 400

    # Handle optional staff assignment
    staff_id = None
    if assigned_staff_id:
        try:
            staff_id = int(assigned_staff_id)
            staff = User.query.filter_by(id=staff_id, role='staff').first()
            if not staff:
                return jsonify({'success': False, 'message': 'Selected staff member does not exist'}), 400
        except (ValueError, TypeError):
            staff_id = None

    try:
        total_slots_num = int(total_slots)
        duration_num = int(duration_days)
        price_num = float(price) if price else 0.0
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Duration, total slots, and price must be valid numbers'}), 400

    new_trek = Trek(
        name=name,
        description=description,
        location=location,
        difficulty=difficulty,
        duration_days=duration_num,
        total_slots=total_slots_num,
        available_slots=total_slots_num,
        price=price_num,
        itinerary=data.get('itinerary'),
        gear_checklist=data.get('gear_checklist'),
        assigned_staff_id=staff_id,
        status='Open',
        start_date=start_date,
        end_date=end_date
    )

    db.session.add(new_trek)
    db.session.commit()
    clear_cache("treks:*")

    return jsonify({'success': True, 'message': 'Trek created successfully', 'trek': new_trek.to_dict()}), 201


@trek_bp.route('/<int:trek_id>', methods=['PUT'])
@token_required
@role_required(['admin'])
def update_trek(_current_user, trek_id):
    # Admin updates a trek
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found'}), 404

    data = request.get_json() or {}

    if 'name' in data and data['name']:
        trek.name = data['name'].strip()
    if 'description' in data:
        trek.description = data['description'].strip() if data['description'] else ''
    if 'location' in data and data['location']:
        trek.location = data['location'].strip()
    if 'difficulty' in data and data['difficulty']:
        trek.difficulty = data['difficulty'].strip()
    if 'duration_days' in data and data['duration_days']:
        try:
            trek.duration_days = int(data['duration_days'])
        except (ValueError, TypeError):
            pass
    if 'price' in data and data['price'] != '' and data['price'] is not None:
        try:
            trek.price = float(data['price'])
        except (ValueError, TypeError):
            pass
    if 'status' in data and data['status']:
        trek.status = data['status'].strip()
    if 'itinerary' in data:
        trek.itinerary = data['itinerary']
    if 'gear_checklist' in data:
        trek.gear_checklist = data['gear_checklist']

    if 'total_slots' in data and data['total_slots']:
        try:
            new_slots = int(data['total_slots'])
            booked = trek.total_slots - trek.available_slots
            if new_slots < booked:
                return jsonify({'success': False, 'message': f'Cannot reduce slots below booked count ({booked})'}), 400
            trek.total_slots = new_slots
            trek.available_slots = new_slots - booked
        except (ValueError, TypeError):
            pass

    if 'assigned_staff_id' in data:
        val = data['assigned_staff_id']
        if val == '' or val is None:
            trek.assigned_staff_id = None
        else:
            try:
                trek.assigned_staff_id = int(val)
            except (ValueError, TypeError):
                trek.assigned_staff_id = None

    if data.get('start_date'):
        try:
            trek.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        except Exception:
            pass
    if data.get('end_date'):
        try:
            trek.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except Exception:
            pass

    db.session.commit()
    clear_cache("treks:*")

    return jsonify({'success': True, 'message': 'Trek updated successfully', 'trek': trek.to_dict()}), 200


@trek_bp.route('/<int:trek_id>', methods=['DELETE'])
@token_required
@role_required(['admin'])
def delete_trek(_current_user, trek_id):
    # Admin deletes a trek
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found'}), 404

    # Do not delete if active bookings exist
    active_bookings = [b for b in trek.bookings if b.status == 'Booked']
    if active_bookings:
        return jsonify({'success': False, 'message': 'Cannot delete trek with active bookings'}), 400

    db.session.delete(trek)
    db.session.commit()
    clear_cache("treks:*")

    return jsonify({'success': True, 'message': 'Trek deleted successfully'}), 200


@trek_bp.route('/<int:trek_id>/reviews', methods=['GET'])
def get_trek_reviews(trek_id):
    # Get reviews for a trek
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found'}), 404

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
    # Add a review and rating
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found'}), 404

    data = request.get_json() or {}
    rating = data.get('rating')
    comment = data.get('comment', '').strip()

    if rating is None:
        return jsonify({'success': False, 'message': 'Rating is required'}), 400

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return jsonify({'success': False, 'message': 'Rating must be between 1 and 5'}), 400
    except Exception:
        return jsonify({'success': False, 'message': 'Invalid rating'}), 400

    review = Review(
        user_id=current_user.id,
        trek_id=trek.id,
        rating=rating,
        comment=comment
    )
    db.session.add(review)
    db.session.commit()
    clear_cache("treks:*")

    return jsonify({
        'success': True,
        'message': 'Review added successfully',
        'review': review.to_dict(),
        'average_rating': trek.average_rating
    }), 201
