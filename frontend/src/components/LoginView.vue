<template>
  <div class="row justify-content-center">
    <div class="col-md-6 col-lg-5">
      <div class="card shadow-sm border-0 mt-4">
        <div class="card-body p-4">
          <div class="text-center mb-4">
            <i class="bi bi-person-circle display-4" style="color: var(--accent);"></i>
            <h3 class="fw-bold mt-2">Welcome Back</h3>
            <p class="text-muted">Log in to your Trekking Account</p>
          </div>

          <!-- Alert error message -->
          <div v-if="errorMessage" class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="bi bi-exclamation-triangle-fill me-2"></i>{{ errorMessage }}
            <button type="button" class="btn-close" @click="errorMessage = ''"></button>
          </div>

          <form @submit.prevent="submitLogin">
            <div class="mb-3">
              <label class="form-label fw-semibold">Username or Email</label>
              <div class="input-group">
                <span class="input-group-text"><i class="bi bi-person"></i></span>
                <input
                  type="text"
                  v-model="identifier"
                  class="form-control"
                  placeholder="Enter username or email"
                  required
                />
              </div>
            </div>

            <div class="mb-3">
              <label class="form-label fw-semibold">Password</label>
              <div class="input-group">
                <span class="input-group-text"><i class="bi bi-lock"></i></span>
                <input
                  type="password"
                  v-model="password"
                  class="form-control"
                  placeholder="Enter password"
                  required
                />
              </div>
            </div>

            <button type="submit" class="btn btn-primary w-100 py-2 fw-semibold" :disabled="loading">
              <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
              {{ loading ? 'Signing in...' : 'Sign In' }}
            </button>
          </form>

          <!-- Quick Fill Demo Helper -->
          <div class="mt-4 pt-3 border-top text-center">
            <small class="text-muted d-block mb-2">Quick Demo Accounts:</small>
            <button class="btn btn-outline-secondary btn-sm me-1" @click="quickFill('admin', 'Admin@123')">
              Admin
            </button>
            <button class="btn btn-outline-secondary btn-sm me-1" @click="quickFill('staff_arjun', 'StaffPassword123')">
              Staff
            </button>
            <button class="btn btn-outline-secondary btn-sm" @click="quickFill('trekker_rahul', 'Password123')">
              Trekker
            </button>
          </div>

          <div class="text-center mt-3">
            <p class="small text-muted mb-0">
              Don't have an account?
              <router-link to="/register" class="fw-bold text-decoration-none" style="color: var(--accent);">Register as Trekker</router-link>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LoginView',
  inject: ['auth'],
  data() {
    return {
      identifier: '',
      password: '',
      loading: false,
      errorMessage: ''
    };
  },
  methods: {
    quickFill(user, pass) {
      this.identifier = user;
      this.password = pass;
    },
    async submitLogin() {
      this.loading = true;
      this.errorMessage = '';

      try {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: this.identifier,
            password: this.password
          })
        });

        const data = await response.json();

        if (response.ok && data.success) {
          this.auth.login(data.token, data.user);

          // Route to appropriate dashboard
          if (data.user.role === 'admin') {
            this.$router.push('/admin');
          } else if (data.user.role === 'staff') {
            this.$router.push('/staff');
          } else {
            this.$router.push('/treks');
          }
        } else {
          this.errorMessage = data.message || 'Login failed. Please check credentials.';
        }
      } catch (err) {
        this.errorMessage = 'Network error. Please ensure the backend server is running.';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
