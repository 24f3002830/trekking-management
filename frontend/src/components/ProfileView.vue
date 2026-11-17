<template>
  <div class="row justify-content-center">
    <div class="col-md-8 col-lg-6">
      <div class="card shadow-sm border-0 mt-3">
        <div class="card-body p-4">
          <div class="text-center mb-4">
            <div class="bg-primary bg-opacity-10 rounded-circle d-inline-flex align-items-center justify-content-center" style="width:80px;height:80px;">
              <i class="bi bi-person-circle text-primary" style="font-size:3rem;"></i>
            </div>
            <h4 class="fw-bold mt-3">My Profile</h4>
            <span class="badge bg-primary text-uppercase">{{ auth.user?.role }}</span>
          </div>

          <div v-if="alertMessage" :class="['alert', 'alert-' + alertType]">{{ alertMessage }}</div>

          <form @submit.prevent="saveProfile">
            <div class="mb-3">
              <label class="form-label fw-semibold">Full Name</label>
              <input type="text" v-model="form.full_name" class="form-control" required />
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">Email</label>
              <input type="email" :value="auth.user?.email" class="form-control" disabled />
              <div class="form-text">Email cannot be changed after registration.</div>
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">Username</label>
              <input type="text" :value="auth.user?.username" class="form-control" disabled />
            </div>
            <div class="mb-4">
              <label class="form-label fw-semibold">Phone Number</label>
              <input type="tel" v-model="form.phone" class="form-control" placeholder="e.g. 9876543210" />
            </div>

            <button type="submit" class="btn btn-primary w-100 py-2 fw-semibold" :disabled="saving">
              <span v-if="saving" class="spinner-border spinner-border-sm me-2"></span>
              {{ saving ? 'Saving...' : 'Save Changes' }}
            </button>
          </form>

          <hr class="my-4">

          <div class="text-center">
            <p class="text-muted small">Member since {{ auth.user?.created_at }}</p>
            <button class="btn btn-outline-danger btn-sm" @click="auth.logout()">
              <i class="bi bi-box-arrow-right me-1"></i>Logout
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ProfileView',
  inject: ['auth'],
  data() {
    return {
      form: {
        full_name: this.auth?.user?.full_name || '',
        phone: this.auth?.user?.phone || ''
      },
      saving: false,
      alertMessage: '',
      alertType: 'success'
    };
  },
  methods: {
    async saveProfile() {
      this.saving = true;
      this.alertMessage = '';
      try {
        const res = await fetch('/api/auth/profile', {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.auth.token}`
          },
          body: JSON.stringify(this.form)
        });
        const data = await res.json();
        if (res.ok && data.success) {
          this.auth.login(this.auth.token, data.user);
          this.alertMessage = 'Profile updated successfully!';
          this.alertType = 'success';
        } else {
          this.alertMessage = data.message || 'Update failed.';
          this.alertType = 'danger';
        }
      } catch (err) {
        this.alertMessage = 'Network error.';
        this.alertType = 'danger';
      } finally {
        this.saving = false;
      }
    }
  }
};
</script>
