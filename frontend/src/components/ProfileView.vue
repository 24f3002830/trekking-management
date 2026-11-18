<template>
  <div class="row justify-content-center">
    <div class="col-md-8 col-lg-6">
      <div class="card shadow-sm border-0 mt-3">
        <div class="card-body p-4">
          <div class="text-center mb-4">
            <div class="rounded-circle d-inline-flex align-items-center justify-content-center" style="width:80px;height:80px; background-color: var(--accent-tint); color: var(--accent);">
              <i class="bi bi-person-circle" style="font-size:3rem; color: var(--accent);"></i>
            </div>
            <h4 class="fw-bold mt-3">My Profile</h4>
            <span class="badge text-uppercase" style="background-color: var(--accent); color: var(--text-on-accent);">{{ auth.user?.role }}</span>
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

            <!-- Trekker Emergency & Medical Safety Profile (Trekkers & Staff only) -->
            <div v-if="auth.user?.role !== 'admin'" class="card p-3 mb-4" style="background-color: var(--bg-page); border: 1px solid var(--border-color);">
              <h6 class="fw-bold mb-3" style="color: var(--status-error);">
                <i class="bi bi-heart-pulse-fill me-2"></i>Emergency & Medical Safety Profile
              </h6>
              <div class="row g-2 mb-2">
                <div class="col-md-6">
                  <label class="form-label small fw-semibold">Emergency Contact Name</label>
                  <input type="text" v-model="form.emergency_contact_name" class="form-control form-control-sm" placeholder="e.g. Next of kin" />
                </div>
                <div class="col-md-6">
                  <label class="form-label small fw-semibold">Emergency Contact Phone</label>
                  <input type="tel" v-model="form.emergency_contact_phone" class="form-control form-control-sm" placeholder="e.g. 9811223344" />
                </div>
              </div>
              <div class="row g-2 mb-2">
                <div class="col-md-4">
                  <label class="form-label small fw-semibold">Blood Group</label>
                  <select v-model="form.blood_group" class="form-select form-select-sm">
                    <option value="">Select</option>
                    <option value="A+">A+</option>
                    <option value="A-">A-</option>
                    <option value="B+">B+</option>
                    <option value="B-">B-</option>
                    <option value="O+">O+</option>
                    <option value="O-">O-</option>
                    <option value="AB+">AB+</option>
                    <option value="AB-">AB-</option>
                  </select>
                </div>
                <div class="col-md-8">
                  <label class="form-label small fw-semibold">Medical / Allergy Notes</label>
                  <input type="text" v-model="form.medical_notes" class="form-control form-control-sm" placeholder="e.g. Asthma, Penicillin allergy, or None" />
                </div>
              </div>
              <small class="text-muted" style="font-size: 0.75rem;">
                <i class="bi bi-shield-check me-1"></i>Crucial for expedition safety and wilderness first-response coordination.
              </small>
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
        phone: this.auth?.user?.phone || '',
        emergency_contact_name: this.auth?.user?.emergency_contact_name || '',
        emergency_contact_phone: this.auth?.user?.emergency_contact_phone || '',
        blood_group: this.auth?.user?.blood_group || '',
        medical_notes: this.auth?.user?.medical_notes || ''
      },
      saving: false,
      alertMessage: '',
      alertType: 'success'
    };
  },
  async created() {
    // Refresh user profile details from backend
    if (this.auth?.isAuthenticated()) {
      try {
        const res = await fetch('/api/auth/profile', {
          headers: { 'Authorization': `Bearer ${this.auth.token}` }
        });
        const data = await res.json();
        if (res.ok && data.success && data.user) {
          this.form.full_name = data.user.full_name || '';
          this.form.phone = data.user.phone || '';
          this.form.emergency_contact_name = data.user.emergency_contact_name || '';
          this.form.emergency_contact_phone = data.user.emergency_contact_phone || '';
          this.form.blood_group = data.user.blood_group || '';
          this.form.medical_notes = data.user.medical_notes || '';
        }
      } catch (e) {}
    }
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
