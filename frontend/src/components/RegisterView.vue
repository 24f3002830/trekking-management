<template>
  <div class="row justify-content-center">
    <div class="col-md-7 col-lg-6">
      <div class="card shadow-sm border-0 mt-3">
        <div class="card-body p-4">
          <div class="text-center mb-4">
            <i class="bi bi-person-plus-fill display-4" style="color: var(--accent);"></i>
            <h3 class="fw-bold mt-2">Join TMA Community</h3>
            <p class="text-muted">Register as a Trekker to discover and book adventures</p>
          </div>

          <div v-if="errorMessage" class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="bi bi-exclamation-triangle-fill me-2"></i>{{ errorMessage }}
            <button type="button" class="btn-close" @click="errorMessage = ''"></button>
          </div>

          <div v-if="successMessage" class="alert alert-success alert-dismissible fade show" role="alert">
            <i class="bi bi-check-circle-fill me-2"></i>{{ successMessage }}
          </div>

          <form @submit.prevent="submitRegister">
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label fw-semibold">Full Name *</label>
                <input type="text" v-model="form.full_name" class="form-control" placeholder="John Doe" required />
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label fw-semibold">Username *</label>
                <input type="text" v-model="form.username" class="form-control" placeholder="johndoe" required />
              </div>
            </div>

            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label fw-semibold">Email Address *</label>
                <input type="email" v-model="form.email" class="form-control" placeholder="john@example.com" required />
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label fw-semibold">Phone Number</label>
                <input type="tel" v-model="form.phone" class="form-control" placeholder="9876543210" />
              </div>
            </div>

            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label fw-semibold">Password *</label>
                <input type="password" v-model="form.password" class="form-control" placeholder="Min. 6 characters" required />
              </div>
              <div class="col-md-6 mb-4">
                <label class="form-label fw-semibold">Confirm Password *</label>
                <input type="password" v-model="form.confirmPassword" class="form-control" placeholder="Re-enter password" required />
              </div>
            </div>

            <button type="submit" class="btn btn-primary w-100 py-2 fw-semibold" :disabled="loading">
              <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
              {{ loading ? 'Creating Account...' : 'Complete Registration' }}
            </button>
          </form>

          <div class="text-center mt-3">
            <p class="small text-muted mb-0">
              Already have an account?
              <router-link to="/login" class="fw-bold text-decoration-none" style="color: var(--accent);">Log in here</router-link>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RegisterView',
  data() {
    return {
      form: {
        full_name: '',
        username: '',
        email: '',
        phone: '',
        password: '',
        confirmPassword: ''
      },
      loading: false,
      errorMessage: '',
      successMessage: ''
    };
  },
  methods: {
    async submitRegister() {
      this.errorMessage = '';
      this.successMessage = '';

      if (this.form.password.length < 6) {
        this.errorMessage = 'Password must be at least 6 characters.';
        return;
      }

      if (this.form.password !== this.form.confirmPassword) {
        this.errorMessage = 'Passwords do not match.';
        return;
      }

      this.loading = true;

      try {
        const response = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            full_name: this.form.full_name,
            username: this.form.username,
            email: this.form.email,
            phone: this.form.phone,
            password: this.form.password
          })
        });

        const data = await response.json();

        if (response.ok && data.success) {
          this.successMessage = 'Account created successfully! Redirecting to login...';
          setTimeout(() => {
            this.$router.push('/login');
          }, 1500);
        } else {
          this.errorMessage = data.message || 'Registration failed.';
        }
      } catch (err) {
        this.errorMessage = 'Network error. Please verify backend status.';
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
