"""
Milestone 4 Automated Verification Script for Trekking Management Application.
Tests:
1. Jinja2 SPA entry point rendering and CDN asset inclusion
2. Static serving of Vue frontend application (/frontend/src/app.js)
3. Direct serving and schema verification of all Vue SFC (.vue) components
4. Full integration between Vue frontend endpoints and Flask backend APIs
"""

import sys
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app import create_app


def run_tests():
    app = create_app()
    client = app.test_client()

    print("\n" + "="*65)
    print("🧪 RUNNING MILESTONE 4 (VUE.JS + BOOTSTRAP UI) VERIFICATION TESTS")
    print("="*65)

    # 1. Test Jinja2 Entry Point Route (GET /)
    res = client.get('/')
    assert res.status_code == 200, f"❌ GET / failed with {res.status_code}"
    html = res.get_data(as_text=True)
    assert '<div id="app"></div>' in html, "❌ Mounting div #app missing in index.html"
    assert 'vue@3' in html, "❌ Vue 3 CDN script tag missing in index.html"
    assert 'vue-router@4' in html, "❌ Vue Router 4 CDN script tag missing in index.html"
    assert 'bootstrap' in html, "❌ Bootstrap CDN link missing in index.html"
    assert '/frontend/src/app.js' in html, "❌ App bootstrap script missing in index.html"
    print("✅ Test 1 Passed: Jinja2 entry point (GET /) serves SPA skeleton with Vue 3 & Bootstrap 5.")

    # 2. Test Frontend Entry Script (/frontend/src/app.js)
    res = client.get('/frontend/src/app.js')
    assert res.status_code == 200, f"❌ Failed to fetch /frontend/src/app.js: {res.status_code}"
    app_js = res.get_data(as_text=True)
    assert 'createApp' in app_js, "❌ createApp not found in app.js"
    assert 'createRouter' in app_js, "❌ createRouter not found in app.js"
    assert 'vue3-sfc-loader' in app_js, "❌ vue3-sfc-loader configuration missing in app.js"
    print("✅ Test 2 Passed: Vue root application script /frontend/src/app.js served successfully.")

    # 3. Test All Vue Single File Components (.vue)
    components = [
        'Navbar.vue',
        'LoginView.vue',
        'RegisterView.vue',
        'TrekkerDashboard.vue',
        'StaffDashboard.vue',
        'AdminDashboard.vue',
        'ProfileView.vue'
    ]

    for comp in components:
        url = f'/frontend/src/components/{comp}'
        res = client.get(url)
        assert res.status_code == 200, f"❌ Component {comp} failed to load from {url}: {res.status_code}"
        content = res.get_data(as_text=True)
        assert '<template>' in content, f"❌ Component {comp} is missing <template> tag"
        assert '<script>' in content, f"❌ Component {comp} is missing <script> tag"
        assert '</template>' in content, f"❌ Component {comp} has unclosed <template>"
        assert '</script>' in content, f"❌ Component {comp} has unclosed <script>"
        print(f"✅ Test 3.{components.index(comp)+1} Passed: Component '{comp}' verified and served.")

    # 4. Verify API integration for Frontend Components
    # Explore treks API
    res = client.get('/api/treks')
    assert res.status_code == 200, f"❌ Treks API returned {res.status_code}"
    assert 'treks' in res.get_json(), "❌ 'treks' array missing in API response"

    # Health check
    res = client.get('/api/health')
    assert res.status_code == 200
    assert res.get_json()['success'] is True

    print("✅ Test 4 Passed: API endpoints cleanly return structured JSON for Vue components.")

    print("\n" + "="*65)
    print("🎉 ALL MILESTONE 4 FRONTEND TESTS PASSED PERFECTLY!")
    print("="*65 + "\n")


if __name__ == '__main__':
    run_tests()
