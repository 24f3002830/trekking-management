/**
 * Trekking Management Application (TMA) - Frontend Application Entry
 * Uses Vue 3, Vue Router 4, and vue3-sfc-loader to load Single File Components (.vue)
 */

const { createApp, reactive } = Vue;
const { createRouter, createWebHashHistory } = VueRouter;

// When opening the application via the local link (base URL), start fresh on the login page
if (!window.location.hash || window.location.hash === '#/' || window.location.hash === '#') {
    localStorage.removeItem('tma_token');
    localStorage.removeItem('tma_user');
    sessionStorage.removeItem('tma_token');
    sessionStorage.removeItem('tma_user');
    window.location.hash = '#/login';
}

// Global authentication and user state using sessionStorage (resets when browser/tab is closed)
export const authState = reactive({
    token: sessionStorage.getItem('tma_token') || null,
    user: JSON.parse(sessionStorage.getItem('tma_user') || 'null'),

    isAuthenticated() {
        if (this.token && this.user) {
            return true;
        }
        return false;
    },

    login(token, user) {
        this.token = token;
        this.user = user;
        sessionStorage.setItem('tma_token', token);
        sessionStorage.setItem('tma_user', JSON.stringify(user));
    },

    logout() {
        this.token = null;
        this.user = null;
        sessionStorage.removeItem('tma_token');
        sessionStorage.removeItem('tma_user');
        localStorage.removeItem('tma_token');
        localStorage.removeItem('tma_user');
        window.location.hash = '#/login';
    }
});

// Configure vue3-sfc-loader to load .vue components directly in the browser
const sfcOptions = {
    moduleCache: {
        vue: Vue
    },
    async getFile(url) {
        const res = await fetch(url);
        if (!res.ok) {
            throw new Error(`Failed to load ${url}: ${res.statusText}`);
        }
        return await res.text();
    },
    addStyle(textContent) {
        const style = document.createElement('style');
        style.textContent = textContent;
        const ref = document.head.getElementsByTagName('style')[0] || null;
        document.head.insertBefore(style, ref);
    }
};

const { loadModule } = window['vue3-sfc-loader'];

// Helper function to asynchronously load .vue components
function loadComponent(name) {
    return function() {
        return loadModule(`/frontend/src/components/${name}.vue`, sfcOptions);
    };
}

// Route definitions for the Single Page Application
const routes = [
    { path: '/', redirect: '/login' },
    { path: '/login', component: loadComponent('LoginView'), meta: { title: 'Login' } },
    { path: '/treks', component: loadComponent('TrekkerDashboard'), meta: { title: 'Explore Treks' } },
    { path: '/register', component: loadComponent('RegisterView'), meta: { title: 'Register' } },
    { path: '/profile', component: loadComponent('ProfileView'), meta: { requiresAuth: true } },
    { path: '/staff', component: loadComponent('StaffDashboard'), meta: { requiresAuth: true, role: 'staff' } },
    { path: '/admin', component: loadComponent('AdminDashboard'), meta: { requiresAuth: true, role: 'admin' } },
    { path: '/:pathMatch(.*)*', redirect: '/login' }
];

const router = createRouter({
    history: createWebHashHistory(),
    routes: routes
});

// Navigation Guards for Role-Based Access Control
router.beforeEach((to, from, next) => {
    // Check if route requires login
    if (to.meta.requiresAuth && !authState.isAuthenticated()) {
        return next('/login');
    }

    // Check if user has required role
    if (to.meta.role) {
        const currentRole = authState.user ? authState.user.role : null;
        if (currentRole !== to.meta.role && currentRole !== 'admin') {
            alert('Access denied: insufficient permissions.');
            return next('/treks');
        }
    }

    next();
});

// Root App Component
const App = {
    components: {
        'nav-bar': Vue.defineAsyncComponent(loadComponent('Navbar'))
    },
    template: `
        <div class="d-flex flex-column min-vh-100">
            <nav-bar></nav-bar>
            <main class="main-content container py-4">
                <router-view></router-view>
            </main>
        </div>
    `
};

const app = createApp(App);
app.use(router);
app.provide('auth', authState);
app.mount('#app');
