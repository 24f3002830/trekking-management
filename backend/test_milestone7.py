"""
Milestone 7 Automated Verification Test Suite.
Tests:
1. Trekker authentication for review operations
2. Trek review retrieval (GET /api/treks/<id>/reviews)
3. Valid review submission (POST /api/treks/<id>/reviews)
4. Review validation and rating boundary checks (1-5 stars)
5. Average rating computation and review count update
6. Progressive Web App (PWA) manifest verification (name, display, start_url)
7. Service Worker verification for 'Add to Desktop' functionality
8. Frontend template & component review/PWA integration check
"""
import sys
import os
import json

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app import create_app
from backend.models import db, User, Trek, Review


def run_tests():
    app = create_app()
    client = app.test_client()

    print("\n" + "="*65)
    print("🧪 RUNNING MILESTONE 7 (REVIEWS, RATINGS & PWA) TESTS")
    print("="*65)

    # 1. Authenticate Trekker
    login_res = client.post('/api/auth/login', json={'username': 'trekker_ananya', 'password': 'Password123'})
    if login_res.status_code != 200:
        login_res = client.post('/api/auth/login', json={'username': 'trekker_rahul', 'password': 'Password123'})
    assert login_res.status_code == 200, "❌ Trekker authentication failed"
    token = login_res.get_json()['token']
    headers = {'Authorization': f'Bearer {token}'}
    print("✅ Test 1 Passed: Trekker authenticated successfully.")

    # 2. Pick a Trek for testing reviews
    with app.app_context():
        trek = Trek.query.first()
        assert trek is not None, "❌ No treks found in database for review testing"
        trek_id = trek.id
        trek_name = trek.name

    # 3. Retrieve Reviews for the Trek
    res = client.get(f'/api/treks/{trek_id}/reviews')
    assert res.status_code == 200, f"❌ Failed to fetch reviews: {res.get_json()}"
    review_data = res.get_json()
    assert 'reviews' in review_data
    assert 'average_rating' in review_data
    assert 'review_count' in review_data
    initial_count = review_data['review_count']
    print(f"✅ Test 2 Passed: Retrieved reviews for '{trek_name}' (Current count: {initial_count}).")

    # 4. Submit Valid Review
    new_review_payload = {
        'rating': 5,
        'comment': 'Spectacular Himalayan views and wonderfully organized camp!'
    }
    res = client.post(f'/api/treks/{trek_id}/reviews', headers=headers, json=new_review_payload)
    assert res.status_code == 201, f"❌ Review submission failed: {res.get_json()}"
    post_res = res.get_json()
    assert post_res['success'] is True
    assert post_res['review']['rating'] == 5
    print(f"✅ Test 3 Passed: Successfully submitted 5-star review for '{trek_name}'.")

    # 5. Rating Boundary Validation Checks
    # Too high (6)
    res_high = client.post(f'/api/treks/{trek_id}/reviews', headers=headers, json={'rating': 6, 'comment': 'Invalid'})
    assert res_high.status_code == 400, "❌ System should reject ratings greater than 5"
    # Too low (0)
    res_low = client.post(f'/api/treks/{trek_id}/reviews', headers=headers, json={'rating': 0, 'comment': 'Invalid'})
    assert res_low.status_code == 400, "❌ System should reject ratings less than 1"
    # Missing rating
    res_missing = client.post(f'/api/treks/{trek_id}/reviews', headers=headers, json={'comment': 'Missing rating'})
    assert res_missing.status_code == 400, "❌ System should reject submissions without rating"
    print("✅ Test 4 Passed: Rating boundaries (1-5) and validation enforced correctly.")

    # 6. Verify Average Rating and Count Update
    res = client.get(f'/api/treks/{trek_id}/reviews')
    updated_data = res.get_json()
    assert updated_data['review_count'] == initial_count + 1, "❌ Review count did not increment"
    assert updated_data['average_rating'] is not None and updated_data['average_rating'] >= 1.0
    print(f"✅ Test 5 Passed: Average rating ({updated_data['average_rating']}★) and count updated.")

    # 7. Progressive Web App (PWA) Manifest Checks
    res_manifest = client.get('/manifest.json')
    assert res_manifest.status_code == 200, "❌ /manifest.json route failed"
    manifest_data = json.loads(res_manifest.get_data(as_text=True))
    assert 'name' in manifest_data and 'Trekking' in manifest_data['name'], "❌ Manifest name missing or invalid"
    assert manifest_data.get('display') == 'standalone', "❌ PWA display must be 'standalone'"
    assert manifest_data.get('start_url') == '/', "❌ PWA start_url must be '/'"
    print("✅ Test 6 Passed: PWA Manifest verified (standalone mode, proper start_url and theme).")

    # 8. Service Worker Script Verification
    res_sw = client.get('/sw.js')
    assert res_sw.status_code == 200, "❌ /sw.js route failed"
    sw_code = res_sw.get_data(as_text=True)
    assert 'addEventListener' in sw_code, "❌ Service Worker event listeners missing"
    assert 'fetch' in sw_code and 'install' in sw_code, "❌ Service Worker install/fetch handlers missing"
    print("✅ Test 7 Passed: Service Worker script verified for 'Add to Desktop' caching.")

    # 9. Frontend HTML & Component Integration Checks
    res_index = client.get('/')
    assert res_index.status_code == 200
    html = res_index.get_data(as_text=True)
    assert 'rel="manifest"' in html, "❌ Manifest link tag missing from index.html"
    assert 'serviceWorker' in html, "❌ Service worker registration script missing from index.html"

    res_comp = client.get('/frontend/src/components/TrekkerDashboard.vue')
    assert res_comp.status_code == 200
    vue_code = res_comp.get_data(as_text=True)
    assert 'openReviewsModal' in vue_code, "❌ openReviewsModal missing in TrekkerDashboard.vue"
    assert 'submitReview' in vue_code, "❌ submitReview missing in TrekkerDashboard.vue"
    print("✅ Test 8 Passed: Frontend index.html and TrekkerDashboard.vue integration verified.")

    print("\n" + "="*65)
    print("🎉 ALL 8 MILESTONE 7 TESTS PASSED SUCCESSFULLY!")
    print("="*65 + "\n")


if __name__ == '__main__':
    run_tests()
