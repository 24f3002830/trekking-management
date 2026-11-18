<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h2 class="fw-bold mb-1"><i class="bi bi-shield-lock me-2" style="color: var(--accent);"></i>Admin Control Console</h2>
        <p class="text-muted mb-0">System-wide management for treks, staff, users, bookings, and reports.</p>
      </div>
      <button class="btn btn-outline-secondary btn-sm" @click="loadAll">
        <i class="bi bi-arrow-clockwise me-1"></i>Refresh
      </button>
    </div>

    <!-- Alert -->
    <div v-if="alertMessage" :class="['alert', 'alert-' + alertType, 'alert-dismissible fade show']">
      {{ alertMessage }}
      <button type="button" class="btn-close" @click="alertMessage = ''"></button>
    </div>

    <!-- Dashboard Metric Cards -->
    <div class="row g-3 mb-4">
      <div class="col-6 col-md-3" v-for="card in metricCards" :key="card.label">
        <div class="card shadow-sm p-3">
          <div class="d-flex align-items-center">
            <div class="p-3 rounded-3 me-3 fs-3" style="background-color: var(--accent-tint); color: var(--accent);">
              <i :class="['bi', card.icon]"></i>
            </div>
            <div>
              <p class="text-muted mb-0 small">{{ card.label }}</p>
              <h4 class="fw-bold mb-0">{{ card.value }}</h4>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Nav Tabs -->
    <ul class="nav nav-tabs mb-4" id="adminTabs">
      <li class="nav-item" v-for="tab in tabs" :key="tab.key">
        <button
          class="nav-link fw-semibold"
          :class="{ active: currentTab === tab.key }"
          @click="currentTab = tab.key"
        >
          <i :class="['bi', tab.icon, 'me-1']"></i>{{ tab.label }}
        </button>
      </li>
    </ul>

    <!-- ===================== TAB: TREK MANAGEMENT ===================== -->
    <div v-if="currentTab === 'treks'">
      <div class="d-flex justify-content-between mb-3">
        <h5 class="fw-bold mb-0">All Treks</h5>
        <button class="btn btn-primary btn-sm" @click="openTrekModal()">
          <i class="bi bi-plus-lg me-1"></i>Add New Trek
        </button>
      </div>

      <div class="table-responsive">
        <table class="table table-hover align-middle shadow-sm">
          <thead class="table-light">
            <tr>
              <th>#</th><th>Name</th><th>Location</th><th>Difficulty</th>
              <th>Slots</th><th>Price</th><th>Assigned Staff</th><th>Status</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in treks" :key="t.id">
              <td>{{ t.id }}</td>
              <td class="fw-semibold">{{ t.name }}</td>
              <td>{{ t.location }}</td>
              <td><span :class="['badge', getDiffBadge(t.difficulty)]">{{ t.difficulty }}</span></td>
              <td>{{ t.available_slots }}/{{ t.total_slots }}</td>
              <td>₹{{ t.price.toLocaleString() }}</td>
              <td>{{ t.assigned_staff_name || '—' }}</td>
              <td><span :class="['badge', t.status==='Open'?'bg-success':'bg-secondary']">{{ t.status }}</span></td>
              <td>
                <button class="btn btn-outline-primary btn-sm me-1" @click="openTrekModal(t)">Edit</button>
                <button class="btn btn-outline-danger btn-sm" @click="deleteTrek(t.id, t.name)">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ===================== TAB: STAFF MANAGEMENT ===================== -->
    <div v-if="currentTab === 'staff'">
      <div class="d-flex justify-content-between mb-3">
        <h5 class="fw-bold mb-0">Trek Staff</h5>
        <button class="btn btn-primary btn-sm" @click="openStaffModal()">
          <i class="bi bi-person-plus me-1"></i>Add Staff Member
        </button>
      </div>

      <div class="row g-3">
        <div class="col-md-4" v-for="s in staff" :key="s.id">
          <div class="card border-0 shadow-sm h-100">
            <div class="card-body">
              <div class="d-flex align-items-center mb-3">
                <div class="bg-warning bg-opacity-10 text-warning rounded-circle p-3 me-3">
                  <i class="bi bi-person-badge fs-3"></i>
                </div>
                <div>
                  <h6 class="mb-0 fw-bold">{{ s.full_name }}</h6>
                  <small class="text-muted">{{ s.email }}</small>
                </div>
              </div>
              <div class="d-flex justify-content-between small mb-2">
                <span class="text-muted">Assigned Treks:</span>
                <span class="fw-semibold">{{ s.assigned_treks_count }}</span>
              </div>
              <div class="d-flex justify-content-between small mb-3">
                <span class="text-muted">Account Status:</span>
                <span :class="s.is_active ? 'text-success fw-bold' : 'text-danger fw-bold'">
                  {{ s.is_active ? 'Active' : 'Deactivated' }}
                </span>
              </div>
              <button
                class="btn btn-sm w-100"
                :class="s.is_active ? 'btn-outline-danger' : 'btn-outline-success'"
                @click="toggleUserStatus(s.id, s.full_name, s.is_active)"
              >
                {{ s.is_active ? 'Deactivate / Blacklist' : 'Reactivate' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================== TAB: USER MANAGEMENT ===================== -->
    <div v-if="currentTab === 'users'">
      <div class="card border-0 shadow-sm">
        <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
          <h5 class="fw-bold mb-0">Registered Trekkers</h5>
          <div class="d-flex gap-2">
            <input type="text" v-model="userSearch" class="form-control form-control-sm" placeholder="Search name, username or email..." @input="searchUsers" style="width:220px;" />
          </div>
        </div>
        <div class="card-body p-0">
          <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
              <thead class="table-light">
                <tr><th>ID</th><th>Full Name</th><th>Username</th><th>Email</th><th>Phone</th><th>Status</th><th>Actions</th></tr>
              </thead>
              <tbody>
                <tr v-for="u in users" :key="u.id">
                  <td>{{ u.id }}</td>
                  <td class="fw-semibold">{{ u.full_name }}</td>
                  <td><code>{{ u.username }}</code></td>
                  <td>{{ u.email }}</td>
                  <td>{{ u.phone || '—' }}</td>
                  <td>
                    <span :class="u.is_active ? 'badge bg-success' : 'badge bg-danger'">
                      {{ u.is_active ? 'Active' : 'Blacklisted' }}
                    </span>
                  </td>
                  <td>
                    <button
                      class="btn btn-sm"
                      :class="u.is_active ? 'btn-outline-danger' : 'btn-outline-success'"
                      @click="toggleUserStatus(u.id, u.full_name, u.is_active)"
                    >
                      {{ u.is_active ? 'Blacklist' : 'Reactivate' }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================== TAB: BOOKINGS ===================== -->
    <div v-if="currentTab === 'bookings'">
      <div class="card border-0 shadow-sm">
        <div class="card-header bg-white py-3">
          <h5 class="fw-bold mb-0">All System Bookings</h5>
        </div>
        <div class="card-body p-0">
          <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
              <thead class="table-light">
                <tr><th>#</th><th>Trekker</th><th>Trek</th><th>Location</th><th>Slots</th><th>Amount</th><th>Booking Date</th><th>Status</th></tr>
              </thead>
              <tbody>
                <tr v-for="b in bookings" :key="b.id">
                  <td>#{{ b.id }}</td>
                  <td class="fw-semibold">{{ b.user_name }}</td>
                  <td>{{ b.trek_name }}</td>
                  <td>{{ b.trek_location }}</td>
                  <td><span class="badge bg-secondary">{{ b.slots_booked }}</span></td>
                  <td class="text-success fw-bold">₹{{ b.total_price.toLocaleString() }}</td>
                  <td><small>{{ b.booking_date }}</small></td>
                  <td>
                    <span :class="getBookingBadge(b.status)">{{ b.status }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================== TAB: REPORTS ===================== -->
    <div v-if="currentTab === 'reports'">
      <!-- Chart.js Visualization Card (Recommended Functionality) -->
      <div class="card border-0 shadow-sm mb-4">
        <div class="card-header bg-white py-3">
          <h6 class="fw-bold mb-0"><i class="bi bi-bar-chart-line-fill text-primary me-2"></i>Trek Analytics & Slot Utilization (ChartJS)</h6>
        </div>
        <div class="card-body">
          <canvas id="analyticsChart" style="max-height: 280px;"></canvas>
        </div>
      </div>

      <div class="row g-3 mb-4">
        <div class="col-md-6">
          <div class="card border-0 shadow-sm">
            <div class="card-body">
              <h6 class="fw-bold">Trek Status Breakdown</h6>
              <div v-for="(count, status) in reports.status_summary" :key="status" class="d-flex justify-content-between border-bottom py-2">
                <span>{{ status }}</span>
                <span class="badge bg-primary rounded-pill">{{ count }}</span>
              </div>
              <div class="d-flex justify-content-between pt-2 fw-bold">
                <span>Total Participants</span>
                <span class="text-success">{{ reports.total_participants }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card border-0 shadow-sm">
            <div class="card-header bg-white">
              <h6 class="fw-bold mb-0">🔥 Most Popular Treks (by Slots Booked)</h6>
            </div>
            <div class="card-body p-0">
              <table class="table table-sm mb-0">
                <thead class="table-light"><tr><th>Trek</th><th>Booked</th><th>Difficulty</th></tr></thead>
                <tbody>
                  <tr v-for="t in reports.popular_treks" :key="t.trek_id">
                    <td class="fw-semibold">{{ t.name }}</td>
                    <td><span class="badge bg-success">{{ t.slots_booked }}</span></td>
                    <td>{{ t.difficulty }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <div class="d-flex gap-2">
        <button class="btn btn-primary" @click="triggerMonthlyReport" :disabled="triggeringReport">
          <span v-if="triggeringReport" class="spinner-border spinner-border-sm me-1"></span>
          <i class="bi bi-file-earmark-bar-graph me-1"></i>Generate Monthly Report
        </button>
        <button class="btn btn-outline-primary" @click="triggerDailyReminders" :disabled="triggeringReminders">
          <span v-if="triggeringReminders" class="spinner-border spinner-border-sm me-1"></span>
          <i class="bi bi-bell me-1"></i>Send Daily Reminders
        </button>
      </div>

      <!-- Generated Monthly Reports List -->
      <div class="card border-0 shadow-sm mt-4">
        <div class="card-header bg-white py-3 d-flex justify-content-between align-items-center">
          <h6 class="fw-bold mb-0">
            <i class="bi bi-file-earmark-richtext text-success me-2"></i>Generated Monthly Reports (HTML)
          </h6>
          <button class="btn btn-outline-secondary btn-sm" @click="loadMonthlyReportsList">
            <i class="bi bi-arrow-clockwise me-1"></i>Refresh List
          </button>
        </div>
        <div class="card-body p-0">
          <div v-if="monthlyReports.length === 0" class="text-center py-4 text-muted small">
            No monthly reports generated yet. Click "Generate Monthly Report" above to create one.
          </div>
          <div v-else class="list-group list-group-flush">
            <div
              v-for="rep in monthlyReports"
              :key="rep"
              class="list-group-item d-flex justify-content-between align-items-center px-3 py-2"
            >
              <div>
                <i class="bi bi-file-earmark-check text-primary me-2"></i>
                <span class="fw-semibold">{{ rep }}</span>
              </div>
              <button class="btn btn-outline-primary btn-sm" @click="openReport(rep)">
                <i class="bi bi-box-arrow-up-right me-1"></i>View Report
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================== TREK ADD/EDIT MODAL ===================== -->
    <div class="modal fade show d-block" tabindex="-1" style="background:rgba(0,0,0,0.5);" v-if="showTrekModal">
      <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
        <div class="modal-content border-0 shadow">
          <div class="modal-header text-white" style="background-color: var(--accent);">
            <h5 class="modal-title"><i class="bi bi-map me-2"></i>{{ editingTrek ? 'Edit Trek' : 'Add New Trek' }}</h5>
            <button type="button" class="btn-close btn-close-white" @click="showTrekModal = false"></button>
          </div>
          <div class="modal-body p-4">
            <div class="row g-3">
              <div class="col-md-6">
                <label class="form-label fw-semibold">Trek Name *</label>
                <input type="text" v-model="trekForm.name" class="form-control" required />
              </div>
              <div class="col-md-6">
                <label class="form-label fw-semibold">Location *</label>
                <input type="text" v-model="trekForm.location" class="form-control" required />
              </div>
              <div class="col-12">
                <label class="form-label fw-semibold">Description</label>
                <textarea v-model="trekForm.description" class="form-control" rows="2"></textarea>
              </div>
              <div class="col-md-4">
                <label class="form-label fw-semibold">Difficulty *</label>
                <select v-model="trekForm.difficulty" class="form-select">
                  <option>Easy</option><option>Moderate</option><option>Hard</option>
                </select>
              </div>
              <div class="col-md-4">
                <label class="form-label fw-semibold">Duration (Days) *</label>
                <input type="number" v-model.number="trekForm.duration_days" class="form-control" min="1" required />
              </div>
              <div class="col-md-4">
                <label class="form-label fw-semibold">Total Slots *</label>
                <input type="number" v-model.number="trekForm.total_slots" class="form-control" min="1" required />
              </div>
              <div class="col-md-4">
                <label class="form-label fw-semibold">Price (₹) *</label>
                <input type="number" v-model.number="trekForm.price" class="form-control" min="0" step="0.01" required />
              </div>
              <div class="col-md-4">
                <label class="form-label fw-semibold">Start Date *</label>
                <input type="date" v-model="trekForm.start_date" class="form-control" required />
              </div>
              <div class="col-md-4">
                <label class="form-label fw-semibold">End Date *</label>
                <input type="date" v-model="trekForm.end_date" class="form-control" required />
              </div>
              <div class="col-md-6">
                <label class="form-label fw-semibold">Assign Staff</label>
                <select v-model="trekForm.assigned_staff_id" class="form-select">
                  <option :value="null">— Unassigned —</option>
                  <option v-for="s in staff" :key="s.id" :value="s.id">{{ s.full_name }}</option>
                </select>
              </div>
              <div class="col-md-6" v-if="editingTrek">
                <label class="form-label fw-semibold">Status</label>
                <select v-model="trekForm.status" class="form-select">
                  <option>Open</option><option>Closed</option><option>Completed</option>
                </select>
              </div>
            </div>
          </div>
          <div class="modal-footer border-0">
            <button type="button" class="btn btn-outline-secondary" @click="showTrekModal = false">Cancel</button>
            <button type="button" class="btn btn-primary" @click="saveTrek" :disabled="savingTrek">
              <span v-if="savingTrek" class="spinner-border spinner-border-sm me-1"></span>
              {{ editingTrek ? 'Save Changes' : 'Create Trek' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================== STAFF ADD MODAL ===================== -->
    <div class="modal fade show d-block" tabindex="-1" style="background:rgba(0,0,0,0.5);" v-if="showStaffModal">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content border-0 shadow">
          <div class="modal-header text-white" style="background-color: var(--accent);">
            <h5 class="modal-title"><i class="bi bi-person-badge me-2"></i>Add Trek Staff</h5>
            <button type="button" class="btn-close btn-close-white" @click="showStaffModal = false"></button>
          </div>
          <div class="modal-body p-4">
            <div class="row g-3">
              <div class="col-md-6">
                <label class="form-label fw-semibold">Full Name *</label>
                <input type="text" v-model="staffForm.full_name" class="form-control" required />
              </div>
              <div class="col-md-6">
                <label class="form-label fw-semibold">Username *</label>
                <input type="text" v-model="staffForm.username" class="form-control" required />
              </div>
              <div class="col-md-6">
                <label class="form-label fw-semibold">Email *</label>
                <input type="email" v-model="staffForm.email" class="form-control" required />
              </div>
              <div class="col-md-6">
                <label class="form-label fw-semibold">Phone</label>
                <input type="tel" v-model="staffForm.phone" class="form-control" />
              </div>
              <div class="col-md-6">
                <label class="form-label fw-semibold">Password *</label>
                <input type="password" v-model="staffForm.password" class="form-control" required />
              </div>
              <div class="col-md-6">
                <label class="form-label fw-semibold">Years of Experience</label>
                <input type="number" v-model.number="staffForm.experience_years" class="form-control" min="0" />
              </div>
              <div class="col-12">
                <label class="form-label fw-semibold">Bio / Specialty</label>
                <textarea v-model="staffForm.bio" class="form-control" rows="2" placeholder="e.g. Certified mountaineering guide..."></textarea>
              </div>
            </div>
          </div>
          <div class="modal-footer border-0">
            <button type="button" class="btn btn-outline-secondary" @click="showStaffModal = false">Cancel</button>
            <button type="button" class="btn btn-primary fw-bold" @click="saveStaff" :disabled="savingStaff">
              <span v-if="savingStaff" class="spinner-border spinner-border-sm me-1"></span>
              Create Staff Account
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AdminDashboard',
  inject: ['auth'],
  data() {
    return {
      currentTab: 'treks',
      tabs: [
        { key: 'treks', label: 'Treks', icon: 'bi-map' },
        { key: 'staff', label: 'Staff', icon: 'bi-person-badge' },
        { key: 'users', label: 'Trekkers', icon: 'bi-people' },
        { key: 'bookings', label: 'Bookings', icon: 'bi-journal-check' },
        { key: 'reports', label: 'Reports', icon: 'bi-bar-chart' }
      ],
      treks: [],
      staff: [],
      users: [],
      bookings: [],
      metrics: {
        total_treks: 0,
        total_users: 0,
        total_staff: 0,
        total_bookings: 0,
        total_revenue: 0
      },
      reports: {
        status_summary: {},
        popular_treks: [],
        total_participants: 0
      },
      alertMessage: '',
      alertType: 'success',
      userSearch: '',

      // Trek modal state
      showTrekModal: false,
      editingTrek: null,
      savingTrek: false,
      trekForm: {
        name: '',
        location: '',
        description: '',
        difficulty: 'Moderate',
        duration_days: 3,
        total_slots: 20,
        price: 0,
        start_date: '',
        end_date: '',
        assigned_staff_id: null,
        status: 'Open'
      },

      // Staff modal state
      showStaffModal: false,
      savingStaff: false,
      staffForm: {
        full_name: '',
        username: '',
        email: '',
        phone: '',
        password: '',
        experience_years: 0,
        bio: ''
      },

      triggeringReport: false,
      triggeringReminders: false,
      monthlyReports: []
    };
  },
  watch: {
    currentTab(newTab) {
      if (newTab === 'reports') {
        this.$nextTick(() => {
          this.renderChart();
          this.loadMonthlyReportsList();
        });
      }
    }
  },
  computed: {
    metricCards() {
      return [
        { label: 'Total Treks', value: this.metrics.total_treks, icon: 'bi-map-fill' },
        { label: 'Trekkers', value: this.metrics.total_users, icon: 'bi-people-fill' },
        { label: 'Staff Members', value: this.metrics.total_staff, icon: 'bi-person-badge' },
        { label: 'Total Bookings', value: this.metrics.total_bookings, icon: 'bi-journal-text' }
      ];
    }
  },
  mounted() {
    this.loadAll();
  },
  methods: {
    showAlert(msg, type = 'success') {
      this.alertMessage = msg;
      this.alertType = type;
      setTimeout(() => {
        this.alertMessage = '';
      }, 4500);
    },

    async apiFetch(url, options = {}) {
      const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.auth.token}`,
        ...(options.headers || {})
      };
      return fetch(url, {
        ...options,
        headers: headers
      });
    },

    async loadAll() {
      await Promise.all([
        this.loadDashboard(),
        this.loadTreks(),
        this.loadStaff(),
        this.loadUsers(),
        this.loadBookings(),
        this.loadReports(),
        this.loadMonthlyReportsList()
      ]);
    },

    async loadDashboard() {
      try {
        const res = await this.apiFetch('/api/admin/dashboard');
        const data = await res.json();
        if (data.success) {
          this.metrics = data.metrics;
        }
      } catch (err) {
        console.error('Error loading dashboard metrics', err);
      }
    },

    async loadTreks() {
      try {
        const res = await fetch('/api/treks');
        const data = await res.json();
        if (data.success) {
          this.treks = data.treks;
        }
      } catch (err) {
        console.error('Error loading treks', err);
      }
    },

    async loadStaff() {
      try {
        const res = await this.apiFetch('/api/admin/staff');
        const data = await res.json();
        if (data.success) {
          this.staff = data.staff;
        }
      } catch (err) {
        console.error('Error loading staff', err);
      }
    },

    async loadUsers() {
      let url = '/api/admin/users?role=user';
      if (this.userSearch) {
        url = `/api/admin/users?role=user&search=${encodeURIComponent(this.userSearch)}`;
      }
      try {
        const res = await this.apiFetch(url);
        const data = await res.json();
        if (data.success) {
          this.users = data.users;
        }
      } catch (err) {
        console.error('Error loading users', err);
      }
    },

    async searchUsers() {
      await this.loadUsers();
    },

    async loadBookings() {
      try {
        const res = await this.apiFetch('/api/admin/bookings');
        const data = await res.json();
        if (data.success) {
          this.bookings = data.bookings;
        }
      } catch (err) {
        console.error('Error loading bookings', err);
      }
    },

    async loadReports() {
      try {
        const res = await this.apiFetch('/api/admin/reports');
        const data = await res.json();
        if (data.success) {
          this.reports = data;
          this.$nextTick(() => {
            this.renderChart();
          });
        }
      } catch (err) {
        console.error('Error loading reports', err);
      }
    },

    renderChart() {
      if (typeof Chart === 'undefined') {
        return;
      }
      const canvas = document.getElementById('analyticsChart');
      if (!canvas) {
        return;
      }
      if (this.chartInstance) {
        this.chartInstance.destroy();
      }

      const popularTreks = this.reports.popular_treks || [];
      const labels = popularTreks.map(t => t.name);
      const bookedData = popularTreks.map(t => t.slots_booked);
      const totalData = popularTreks.map(t => t.total_slots);

      this.chartInstance = new Chart(canvas, {
        type: 'bar',
        data: {
          labels: labels.length > 0 ? labels : ['No Treks'],
          datasets: [
            {
              label: 'Slots Booked',
              data: bookedData.length > 0 ? bookedData : [0],
              backgroundColor: '#1F6F5C'
            },
            {
              label: 'Total Capacity',
              data: totalData.length > 0 ? totalData : [0],
              backgroundColor: '#E4F1ED',
              borderColor: '#1F6F5C',
              borderWidth: 1
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'top' },
            title: { display: true, text: 'Trek Popularity & Capacity Utilization' }
          },
          scales: {
            y: { beginAtZero: true }
          }
        }
      });
    },

    getDiffBadge(difficulty) {
      if (difficulty === 'Easy') {
        return 'badge-easy';
      }
      if (difficulty === 'Moderate') {
        return 'badge-moderate';
      }
      return 'badge-hard';
    },

    getBookingBadge(status) {
      if (status === 'Booked') {
        return 'badge bg-success';
      }
      if (status === 'Cancelled') {
        return 'badge bg-danger';
      }
      return 'badge bg-info text-dark';
    },

    openTrekModal(trek = null) {
      this.editingTrek = trek;
      if (trek) {
        this.trekForm = {
          name: trek.name,
          location: trek.location,
          description: trek.description || '',
          difficulty: trek.difficulty,
          duration_days: trek.duration_days,
          total_slots: trek.total_slots,
          price: trek.price,
          start_date: trek.start_date,
          end_date: trek.end_date,
          assigned_staff_id: trek.assigned_staff_id,
          status: trek.status
        };
      } else {
        this.trekForm = {
          name: '',
          location: '',
          description: '',
          difficulty: 'Moderate',
          duration_days: 3,
          total_slots: 20,
          price: 0,
          start_date: '',
          end_date: '',
          assigned_staff_id: null,
          status: 'Open'
        };
      }
      this.showTrekModal = true;
    },

    async saveTrek() {
      this.savingTrek = true;
      try {
        let url = '/api/treks';
        let method = 'POST';
        if (this.editingTrek) {
          url = `/api/treks/${this.editingTrek.id}`;
          method = 'PUT';
        }

        const res = await this.apiFetch(url, {
          method: method,
          body: JSON.stringify(this.trekForm)
        });
        const data = await res.json();
        if (data.success) {
          this.showAlert(data.message, 'success');
          this.showTrekModal = false;
          this.loadTreks();
          this.loadDashboard();
        } else {
          this.showAlert(data.message, 'danger');
        }
      } catch (e) {
        this.showAlert('Network error saving trek.', 'danger');
      } finally {
        this.savingTrek = false;
      }
    },

    async deleteTrek(id, name) {
      const confirmed = confirm(`Delete trek "${name}"? Active bookings will block this action.`);
      if (!confirmed) {
        return;
      }

      try {
        const res = await this.apiFetch(`/api/treks/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
          this.showAlert(data.message, 'success');
          this.loadTreks();
          this.loadDashboard();
        } else {
          this.showAlert(data.message, 'danger');
        }
      } catch (err) {
        this.showAlert('Error deleting trek.', 'danger');
      }
    },

    openStaffModal() {
      this.staffForm = {
        full_name: '',
        username: '',
        email: '',
        phone: '',
        password: '',
        experience_years: 0,
        bio: ''
      };
      this.showStaffModal = true;
    },

    async saveStaff() {
      this.savingStaff = true;
      try {
        const res = await this.apiFetch('/api/admin/staff', {
          method: 'POST',
          body: JSON.stringify(this.staffForm)
        });
        const data = await res.json();
        if (data.success) {
          this.showAlert(data.message, 'success');
          this.showStaffModal = false;
          this.loadStaff();
          this.loadDashboard();
        } else {
          this.showAlert(data.message, 'danger');
        }
      } catch (e) {
        this.showAlert('Error creating staff member.', 'danger');
      } finally {
        this.savingStaff = false;
      }
    },

    async toggleUserStatus(userId, name, currentStatus) {
      let action = 'reactivate';
      if (currentStatus) {
        action = 'deactivate/blacklist';
      }
      const confirmed = confirm(`Are you sure you want to ${action} "${name}"?`);
      if (!confirmed) {
        return;
      }

      try {
        const res = await this.apiFetch(`/api/admin/users/${userId}/status`, {
          method: 'PUT',
          body: JSON.stringify({ is_active: !currentStatus })
        });
        const data = await res.json();
        if (data.success) {
          this.showAlert(data.message, 'success');
          this.loadStaff();
          this.loadUsers();
        } else {
          this.showAlert(data.message, 'danger');
        }
      } catch (err) {
        this.showAlert('Error updating user status.', 'danger');
      }
    },

    async triggerMonthlyReport() {
      this.triggeringReport = true;
      try {
        const res = await this.apiFetch('/api/admin/trigger-monthly-report', { method: 'POST' });
        const data = await res.json();
        this.showAlert(data.message || 'Monthly report generated!', 'success');
        this.loadMonthlyReportsList();
      } catch (e) {
        this.showAlert('Report generation failed.', 'danger');
      } finally {
        this.triggeringReport = false;
      }
    },

    async loadMonthlyReportsList() {
      try {
        const res = await this.apiFetch('/api/admin/reports/monthly');
        const data = await res.json();
        if (data.success) {
          this.monthlyReports = data.reports;
        }
      } catch (err) {
        console.error('Error loading monthly reports list', err);
      }
    },

    async openReport(filename) {
      try {
        const res = await fetch(`/api/admin/reports/monthly/${filename}`, {
          headers: { 'Authorization': `Bearer ${this.auth.token}` }
        });
        if (res.ok) {
          const html = await res.text();
          const win = window.open('', '_blank');
          if (win) {
            win.document.write(html);
            win.document.close();
          }
        } else {
          this.showAlert('Could not load report file.', 'danger');
        }
      } catch (err) {
        this.showAlert('Error opening report.', 'danger');
      }
    },

    async triggerDailyReminders() {
      this.triggeringReminders = true;
      try {
        const res = await this.apiFetch('/api/admin/trigger-daily-reminders', { method: 'POST' });
        const data = await res.json();
        this.showAlert(data.message || 'Reminders sent!', 'success');
      } catch (e) {
        this.showAlert('Reminder dispatch failed.', 'danger');
      } finally {
        this.triggeringReminders = false;
      }
    }
  }
};
</script>
