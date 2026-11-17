<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h2 class="fw-bold mb-1"><i class="bi bi-person-badge text-warning me-2"></i>Staff Operations Dashboard</h2>
        <p class="text-muted mb-0">Manage your assigned trekking expeditions, participant lists, and slot capacities.</p>
      </div>
      <button class="btn btn-outline-primary btn-sm" @click="fetchStaffData">
        <i class="bi bi-arrow-clockwise"></i> Refresh
      </button>
    </div>

    <!-- Alert Message -->
    <div v-if="alertMessage" :class="['alert', 'alert-' + alertType, 'alert-dismissible fade show']">
      {{ alertMessage }}
      <button type="button" class="btn-close" @click="alertMessage = ''"></button>
    </div>

    <!-- Metrics Cards -->
    <div class="row g-3 mb-4">
      <div class="col-md-6">
        <div class="card border-0 shadow-sm bg-white p-3">
          <div class="d-flex align-items-center">
            <div class="p-3 bg-primary bg-opacity-10 text-primary rounded-3 me-3">
              <i class="bi bi-map fs-3"></i>
            </div>
            <div>
              <h6 class="text-muted mb-0">Assigned Treks</h6>
              <h3 class="fw-bold mb-0">{{ metrics.assigned_treks_count }}</h3>
            </div>
          </div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card border-0 shadow-sm bg-white p-3">
          <div class="d-flex align-items-center">
            <div class="p-3 bg-success bg-opacity-10 text-success rounded-3 me-3">
              <i class="bi bi-people fs-3"></i>
            </div>
            <div>
              <h6 class="text-muted mb-0">Total Registered Trekkers</h6>
              <h3 class="fw-bold mb-0">{{ metrics.total_participants }}</h3>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Assigned Treks Table -->
    <div class="card border-0 shadow-sm">
      <div class="card-header bg-white py-3">
        <h5 class="mb-0 fw-bold">My Assigned Treks</h5>
      </div>
      <div class="card-body p-0">
        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border text-primary"></div>
        </div>

        <div v-else-if="treks.length === 0" class="text-center py-5 text-muted">
          <i class="bi bi-clipboard-x display-4"></i>
          <h5 class="mt-2">No treks assigned yet.</h5>
          <p>Contact the Administrator to have trekking routes assigned to your profile.</p>
        </div>

        <div v-else class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th>Trek Name</th>
                <th>Location</th>
                <th>Dates</th>
                <th>Available Slots</th>
                <th>Registered Trekkers</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in treks" :key="t.id">
                <td class="fw-bold">{{ t.name }}</td>
                <td>{{ t.location }}</td>
                <td><small>{{ t.start_date }} to {{ t.end_date }}</small></td>
                <td>
                  <span class="badge bg-secondary">{{ t.available_slots }} / {{ t.total_slots }}</span>
                  <button class="btn btn-link btn-sm text-primary p-0 ms-1" @click="openSlotModal(t)">Edit</button>
                </td>
                <td>
                  <span class="badge bg-info text-dark">{{ t.total_registered_participants }} Trekkers</span>
                </td>
                <td>
                  <select
                    class="form-select form-select-sm w-auto"
                    :value="t.status"
                    @change="updateStatus(t.id, $event.target.value)"
                  >
                    <option value="Open">Open</option>
                    <option value="Closed">Closed</option>
                    <option value="Started">Started</option>
                    <option value="Completed">Completed</option>
                  </select>
                </td>
                <td>
                  <button class="btn btn-outline-primary btn-sm" @click="viewParticipants(t)">
                    <i class="bi bi-people me-1"></i> Participants
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- PARTICIPANTS MODAL -->
    <div class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5);" v-if="activeTrekParticipants">
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content border-0 shadow">
          <div class="modal-header bg-dark text-white">
            <h5 class="modal-title">
              <i class="bi bi-people-fill me-2"></i>Participants: {{ activeTrekParticipants.trek_name }}
            </h5>
            <button type="button" class="btn-close btn-close-white" @click="activeTrekParticipants = null"></button>
          </div>
          <div class="modal-body p-4">
            <div v-if="loadingParticipants" class="text-center py-4">
              <div class="spinner-border text-primary"></div>
            </div>

            <div v-else-if="participants.length === 0" class="text-center py-4 text-muted">
              <h6>No participants registered for this trek yet.</h6>
            </div>

            <div v-else class="table-responsive">
              <table class="table table-sm table-hover align-middle">
                <thead>
                  <tr>
                    <th>Booking #</th>
                    <th>Participant Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Slots</th>
                    <th>Booking Date</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="p in participants" :key="p.booking_id">
                    <td>#{{ p.booking_id }}</td>
                    <td class="fw-semibold">{{ p.user_name }}</td>
                    <td>{{ p.user_email }}</td>
                    <td>{{ p.user_phone || 'N/A' }}</td>
                    <td><span class="badge bg-success">{{ p.slots_booked }}</span></td>
                    <td><small>{{ p.booking_date }}</small></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          <div class="modal-footer border-0">
            <button type="button" class="btn btn-secondary" @click="activeTrekParticipants = null">Close</button>
          </div>
        </div>
      </div>
    </div>

    <!-- UPDATE SLOTS MODAL -->
    <div class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5);" v-if="slotTrek">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content border-0 shadow">
          <div class="modal-header bg-primary text-white">
            <h5 class="modal-title">Manage Slots: {{ slotTrek.name }}</h5>
            <button type="button" class="btn-close btn-close-white" @click="slotTrek = null"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Available Slots (Max: {{ slotTrek.total_slots }})</label>
              <input type="number" v-model.number="newSlots" class="form-control" min="0" :max="slotTrek.total_slots" />
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="slotTrek = null">Cancel</button>
            <button type="button" class="btn btn-success" @click="saveSlots">Save Changes</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StaffDashboard',
  inject: ['auth'],
  data() {
    return {
      metrics: { assigned_treks_count: 0, total_participants: 0 },
      treks: [],
      loading: false,
      alertMessage: '',
      alertType: 'success',
      activeTrekParticipants: null,
      participants: [],
      loadingParticipants: false,
      slotTrek: null,
      newSlots: 0
    };
  },
  mounted() {
    this.fetchStaffData();
  },
  methods: {
    showAlert(msg, type = 'success') {
      this.alertMessage = msg;
      this.alertType = type;
      setTimeout(() => { this.alertMessage = ''; }, 4000);
    },
    async fetchStaffData() {
      this.loading = true;
      try {
        const res = await fetch('/api/staff/dashboard', {
          headers: { 'Authorization': `Bearer ${this.auth.token}` }
        });
        const data = await res.json();
        if (res.ok && data.success) {
          this.metrics = data.metrics;
          this.treks = data.treks;
        } else {
          this.showAlert(data.message || 'Error loading dashboard.', 'danger');
        }
      } catch (err) {
        this.showAlert('Network error fetching staff dashboard.', 'danger');
      } finally {
        this.loading = false;
      }
    },
    async updateStatus(trekId, newStatus) {
      try {
        const res = await fetch(`/api/staff/treks/${trekId}/status`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.auth.token}`
          },
          body: JSON.stringify({ status: newStatus })
        });
        const data = await res.json();
        if (res.ok && data.success) {
          this.showAlert(`Trek status updated to "${newStatus}".`, 'success');
          this.fetchStaffData();
        } else {
          this.showAlert(data.message || 'Status update failed.', 'danger');
        }
      } catch (err) {
        this.showAlert('Error updating status.', 'danger');
      }
    },
    openSlotModal(trek) {
      this.slotTrek = trek;
      this.newSlots = trek.available_slots;
    },
    async saveSlots() {
      if (!this.slotTrek) return;
      try {
        const res = await fetch(`/api/staff/treks/${this.slotTrek.id}/slots`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.auth.token}`
          },
          body: JSON.stringify({ available_slots: this.newSlots })
        });
        const data = await res.json();
        if (res.ok && data.success) {
          this.showAlert('Available slots updated successfully.', 'success');
          this.slotTrek = null;
          this.fetchStaffData();
        } else {
          this.showAlert(data.message || 'Slot update failed.', 'danger');
        }
      } catch (err) {
        this.showAlert('Error updating slots.', 'danger');
      }
    },
    async viewParticipants(trek) {
      this.activeTrekParticipants = trek;
      this.loadingParticipants = true;
      try {
        const res = await fetch(`/api/staff/treks/${trek.id}/participants`, {
          headers: { 'Authorization': `Bearer ${this.auth.token}` }
        });
        const data = await res.json();
        if (res.ok && data.success) {
          this.participants = data.participants;
        } else {
          this.showAlert(data.message || 'Failed to load participants.', 'danger');
        }
      } catch (err) {
        this.showAlert('Error loading participant list.', 'danger');
      } finally {
        this.loadingParticipants = false;
      }
    }
  }
};
</script>
