/**
 * Trekking Management Application (TMA) - Frontend Application Entry
 * Uses Vue 3, Vue Router 4, and vue3-sfc-loader to load Single File Components (.vue)
 */

const { createApp, ref, reactive } = Vue;
const { createRouter, createWebHashHistory } = VueRouter;

// Global authentication and user state
export const authState = reactive({
    token: localStorage.getItem('tma_token') || null,
    user: JSON.parse(localStorage.getItem('tma_user') || 'null'),
    isAuthenticated() {
        return !!this.token && !!this.user;
    },
    login(token, user) {
        this.token = token;
        this.user = user;
        localStorage.setItem('tma_token', token);
        localStorage.setItem('tma_user', JSON.stringify(user));
    },
    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('tma_token');
        localStorage.removeItem('tma_user');
        window.location.hash = '#/login';
    }
});

// Configure vue3-sfc-loader options to load .vue files directly
const sfcOptions = {
    moduleCache: {
        vue: Vue
    },
    async getFile(url) {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Failed to load ${url}: ${res.statusText}`);
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

// Helper to asynchronously load .vue components
const loadComponent = (name) => () => loadModule(`/frontend/src/components/${name}.vue`, sfcOptions);

// Define Vue Routes
const routes = [
    { path: '/', component: loadComponent('TrekkerDashboard'), meta: { title: 'Explore Treks' } },
    { path: '/login', component: loadComponent('LoginView'), meta: { title: 'Login' } },
    { path: '/register', component: loadComponent('RegisterView'), meta: { title: 'Register' } },
    { path: '/profile', component: loadComponent('ProfileView'), meta: { requiresAuth: true } },
    { path: '/staff', component: loadComponent('StaffDashboard'), meta: { requiresAuth: true, role: 'staff' } },
    { path: '/admin', component: loadComponent('AdminDashboard'), meta: { requiresAuth: true, role: 'admin' } },
    { path: '/:pathMatch(.*)*', redirect: '/' }
];

const router = createRouter({
    history: createWebHashHistory(),
    routes
});

// Navigation Guards for Role-Based Access Control
router.beforeEach((to, from, next) => {
    if (to.meta.requiresAuth && !authState.isAuthenticated()) {
        return next('/login');
    }
    if (to.meta.role && authState.user?.role !== to.meta.role && authState.user?.role !== 'admin') {
        alert('Access denied: insufficient permissions.');
        return next('/');
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
            <footer class="footer-custom text-center mt-auto">
                <div class="container">
                    <p class="mb-1"><strong>Trekking Management Application (TMA) - V2</strong></p>
                    <small>Built with Flask, Vue.js, Bootstrap & SQLite | Student ID: 24f3002830</small>
                </div>
            </footer>
        </div>
    `
};

const app = createApp(App);
app.use(router);
app.provide('auth', authState);
app.mount('#app');
