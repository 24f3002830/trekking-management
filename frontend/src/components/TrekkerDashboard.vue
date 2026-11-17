<template>
  <div>
    <!-- Hero Banner -->
    <div class="hero-banner shadow-sm text-center">
      <h1 class="display-6 fw-bold">Discover & Book Himalayan Adventures</h1>
      <p class="lead mb-0">Explore thrilling trekking trails with certified guides and real-time slot tracking.</p>
    </div>

    <!-- Alert Notices -->
    <div v-if="alertMessage" :class="['alert', 'alert-' + alertType, 'alert-dismissible fade show']">
      {{ alertMessage }}
      <button type="button" class="btn-close" @click="alertMessage = ''"></button>
    </div>

    <!-- Main Navigation Tabs -->
    <ul class="nav nav-pills mb-4 justify-content-center">
      <li class="nav-item">
        <button
          class="nav-link px-4 fw-semibold"
          :class="{ active: currentTab === 'explore' }"
          @click="currentTab = 'explore'"
        >
          <i class="bi bi-compass me-1"></i> Available Treks
        </button>
      </li>
      <li class="nav-item" v-if="auth.isAuthenticated() && auth.user.role === 'user'">
        <button
          class="nav-link px-4 fw-semibold"
          :class="{ active: currentTab === 'bookings' }"
          @click="loadMyBookings(); currentTab = 'bookings'"
        >
          <i class="bi bi-journal-check me-1"></i> My Bookings & History
        </button>
      </li>
    </ul>

    <!-- TAB 1: EXPLORE TREKS -->
    <div v-if="currentTab === 'explore'">
      <!-- Search & Filter Card -->
      <div class="card shadow-sm border-0 mb-4">
        <div class="card-body p-3">
          <form class="row g-2 align-items-center" @submit.prevent="fetchTreks">
            <div class="col-md-4">
              <div class="input-group">
                <span class="input-group-text"><i class="bi bi-search"></i></span>
                <input
                  type="text"
                  v-model="filters.search"
                  class="form-control"
                  placeholder="Search by trek name or location..."
                />
              </div>
            </div>
            <div class="col-md-3">
              <select v-model="filters.difficulty" class="form-select">
                <option value="">All Difficulties</option>
                <option value="Easy">Easy</option>
                <option value="Moderate">Moderate</option>
                <option value="Hard">Hard</option>
              </select>
            </div>
            <div class="col-md-3">
              <input
                type="text"
                v-model="filters.location"
                class="form-control"
                placeholder="Filter by location (e.g. Uttarakhand)"
              />
            </div>
            <div class="col-md-2 d-flex gap-1">
              <button type="submit" class="btn btn-primary flex-fill">
                <i class="bi bi-funnel"></i> Filter
              </button>
              <button type="button" class="btn btn-outline-secondary" @click="resetFilters">
                Reset
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Treks Grid -->
      <div v-if="loadingTreks" class="text-center py-5">
        <div class="spinner-border text-primary" role="status"></div>
        <p class="text-muted mt-2">Loading treks...</p>
      </div>

      <div v-else-if="treks.length === 0" class="card text-center p-5 border-0 shadow-sm">
        <i class="bi bi-search display-3 text-muted"></i>
        <h4 class="mt-3">No Treks Found</h4>
        <p class="text-muted">Try adjusting your search criteria or filters.</p>
      </div>

      <div v-else class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
        <div class="col" v-for="trek in treks" :key="trek.id">
          <div class="card h-100 shadow-sm border-0">
            <div class="card-header bg-white border-0 d-flex justify-content-between align-items-center pt-3">
              <span :class="['badge', getDifficultyBadge(trek.difficulty)]">{{ trek.difficulty }}</span>
              <span class="badge" :class="trek.status === 'Open' ? 'bg-success' : 'bg-secondary'">
                {{ trek.status }}
              </span>
            </div>

            <div class="card-body">
              <h5 class="card-title fw-bold text-dark mb-1">{{ trek.name }}</h5>
              <div class="d-flex align-items-center mb-2">
                <span class="text-warning me-1"><i class="bi bi-star-fill"></i></span>
                <span class="fw-bold small me-1">{{ trek.average_rating || 5.0 }}</span>
                <span class="text-muted small">({{ trek.review_count || 0 }} reviews)</span>
                <button class="btn btn-link btn-sm text-decoration-none p-0 ms-2" @click="openReviewsModal(trek)">View Reviews</button>
              </div>
              <p class="text-muted small mb-2">
                <i class="bi bi-geo-alt-fill text-danger me-1"></i>{{ trek.location }}
              </p>
              <p class="card-text text-secondary small">{{ trek.description }}</p>

              <div class="border-top pt-2 mt-3">
                <div class="d-flex justify-content-between small text-muted mb-1">
                  <span><i class="bi bi-clock me-1"></i>{{ trek.duration_days }} Days</span>
                  <span><i class="bi bi-calendar-event me-1"></i>{{ trek.start_date }}</span>
                </div>
                <div class="d-flex justify-content-between align-items-center mt-2">
                  <span class="fw-bold text-success fs-5">₹{{ trek.price.toLocaleString() }}</span>
                  <span class="badge" :class="trek.available_slots > 0 ? 'bg-info text-dark' : 'bg-danger'">
                    {{ trek.available_slots }} / {{ trek.total_slots }} slots
                  </span>
                </div>
              </div>
            </div>

            <div class="card-footer bg-white border-0 pb-3 pt-0">
              <div class="d-flex gap-2">
                <button class="btn btn-outline-secondary btn-sm flex-fill" @click="openItineraryModal(trek)">
                  <i class="bi bi-compass me-1"></i>Itinerary
                </button>
                <button
                  class="btn btn-primary btn-sm flex-fill fw-semibold"
                  :disabled="trek.status !== 'Open' || trek.available_slots === 0"
                  @click="openBookingModal(trek)"
                >
                  <i class="bi bi-ticket-perforated me-1"></i>
                  {{ trek.available_slots === 0 ? 'Sold Out' : 'Book' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 2: MY BOOKINGS & HISTORY -->
    <div v-if="currentTab === 'bookings'">
      <div class="card shadow-sm border-0">
        <div class="card-header bg-white d-flex justify-content-between align-items-center py-3">
          <h5 class="mb-0 fw-bold"><i class="bi bi-journal-text me-2"></i>My Bookings History</h5>
          <button class="btn btn-outline-success btn-sm" @click="exportHistoryCsv" :disabled="exportingCsv">
            <span v-if="exportingCsv" class="spinner-border spinner-border-sm me-1"></span>
            <i class="bi bi-file-earmark-spreadsheet me-1"></i>Export History (CSV)
          </button>
        </div>

        <div class="card-body p-0">
          <div v-if="loadingBookings" class="text-center py-5">
            <div class="spinner-border text-primary"></div>
          </div>

          <div v-else-if="myBookings.length === 0" class="text-center py-5">
            <i class="bi bi-backpack display-4 text-muted"></i>
            <h5 class="mt-2 text-muted">You have no booking records yet.</h5>
            <button class="btn btn-primary mt-2" @click="currentTab = 'explore'">Explore Treks</button>
          </div>

          <div v-else class="table-responsive">
            <table class="table table-hover align-middle mb-0">
              <thead class="table-light">
                <tr>
                  <th>Booking #</th>
                  <th>Trek Name</th>
                  <th>Location</th>
                  <th>Booked Date</th>
                  <th>Slots</th>
                  <th>Total Amount</th>
                  <th>Payment / Ref</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="b in myBookings" :key="b.id">
                  <td><strong>#{{ b.id }}</strong></td>
                  <td class="fw-semibold">{{ b.trek_name }}</td>
                  <td>{{ b.trek_location }}</td>
                  <td>{{ b.booking_date }}</td>
                  <td><span class="badge bg-secondary">{{ b.slots_booked }}</span></td>
                  <td class="text-success fw-bold">₹{{ b.total_price.toLocaleString() }}</td>
                  <td>
                    <span class="badge bg-light text-dark border">
                      <i class="bi bi-receipt me-1"></i>{{ b.transaction_id || 'PRE_SIM_PAID' }}
                    </span>
                  </td>
                  <td>
                    <span :class="['badge', getBookingStatusBadge(b.status)]">{{ b.status }}</span>
                  </td>
                  <td>
                    <button
                      v-if="b.status === 'Booked'"
                      class="btn btn-outline-danger btn-sm"
                      @click="cancelBooking(b.id)"
                    >
                      Cancel
                    </button>
                    <span v-else class="text-muted small">-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- BOOKING MODAL -->
    <div class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5);" v-if="selectedTrek">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content border-0 shadow">
          <div class="modal-header bg-primary text-white">
            <h5 class="modal-title"><i class="bi bi-ticket-perforated me-2"></i>Book Trek</h5>
            <button type="button" class="btn-close btn-close-white" @click="selectedTrek = null"></button>
          </div>
          <div class="modal-body p-4">
            <h4 class="fw-bold mb-1">{{ selectedTrek.name }}</h4>
            <p class="text-muted small mb-3">
              <i class="bi bi-geo-alt me-1"></i>{{ selectedTrek.location }} |
              <i class="bi bi-clock me-1"></i>{{ selectedTrek.duration_days }} Days
            </p>

            <div class="alert alert-info py-2">
              <small><strong>Dates:</strong> {{ selectedTrek.start_date }} to {{ selectedTrek.end_date }}</small>
            </div>

            <div class="mb-3">
              <label class="form-label fw-semibold">Slots to Book</label>
              <input
                type="number"
                v-model.number="bookingSlots"
                class="form-control"
                min="1"
                :max="selectedTrek.available_slots"
                required
              />
              <small class="text-muted">Available slots: {{ selectedTrek.available_slots }}</small>
            </div>

            <div class="mb-3">
              <label class="form-label fw-semibold">Payment Method (Simulation)</label>
              <select v-model="paymentMethod" class="form-select">
                <option value="Simulated UPI (GooglePay / PhonePe)">⚡ UPI (GooglePay / PhonePe / Paytm)</option>
                <option value="Simulated Credit / Debit Card">💳 Credit / Debit Card</option>
                <option value="Simulated Net Banking">🏦 Net Banking</option>
              </select>
              <div class="form-text text-success"><i class="bi bi-shield-check me-1"></i>Safe test payment simulation</div>
            </div>

            <div class="card bg-light border-0 p-3 mb-3">
              <div class="d-flex justify-content-between mb-1">
                <span>Price per slot:</span>
                <span>₹{{ selectedTrek.price.toLocaleString() }}</span>
              </div>
              <div class="d-flex justify-content-between mb-1">
                <span>Number of slots:</span>
                <span>{{ bookingSlots }}</span>
              </div>
              <hr class="my-2">
              <div class="d-flex justify-content-between fw-bold fs-5 text-success">
                <span>Total Amount:</span>
                <span>₹{{ (bookingSlots * selectedTrek.price).toLocaleString() }}</span>
              </div>
            </div>
          </div>
          <div class="modal-footer border-0">
            <button type="button" class="btn btn-secondary" @click="selectedTrek = null">Close</button>
            <button type="button" class="btn btn-success" :disabled="bookingInProgress" @click="confirmBooking">
              <span v-if="bookingInProgress" class="spinner-border spinner-border-sm me-1"></span>
              Confirm & Book
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- TREK REVIEWS & RATINGS MODAL -->
    <div class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5);" v-if="reviewTrek">
      <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable">
        <div class="modal-content border-0 shadow">
          <div class="modal-header bg-warning text-dark">
            <h5 class="modal-title"><i class="bi bi-star-fill me-2"></i>Reviews: {{ reviewTrek.name }}</h5>
            <button type="button" class="btn-close" @click="reviewTrek = null"></button>
          </div>
          <div class="modal-body p-4">
            <!-- Review Submission Form (if logged in) -->
            <div v-if="auth.isAuthenticated()" class="card bg-light border-0 p-3 mb-4">
              <h6 class="fw-bold mb-2">Leave a Review</h6>
              <div class="mb-2">
                <label class="form-label small mb-1">Rating</label>
                <select v-model.number="newReview.rating" class="form-select form-select-sm">
                  <option :value="5">⭐⭐⭐⭐⭐ (5 Stars - Outstanding)</option>
                  <option :value="4">⭐⭐⭐⭐ (4 Stars - Very Good)</option>
                  <option :value="3">⭐⭐⭐ (3 Stars - Good)</option>
                  <option :value="2">⭐⭐ (2 Stars - Needs Improvement)</option>
                  <option :value="1">⭐ (1 Star - Poor)</option>
                </select>
              </div>
              <div class="mb-2">
                <label class="form-label small mb-1">Feedback Comment</label>
                <textarea v-model="newReview.comment" class="form-control form-control-sm" rows="2" placeholder="Share your experience on this trail..."></textarea>
              </div>
              <button class="btn btn-warning btn-sm fw-bold align-self-end" :disabled="submittingReview" @click="submitReview">
                <span v-if="submittingReview" class="spinner-border spinner-border-sm me-1"></span>
                Post Review
              </button>
            </div>
            <div v-else class="alert alert-info py-2 small mb-4">
              <router-link to="/login">Log in</router-link> as a Trekker to write a review.
            </div>

            <!-- Existing Reviews List -->
            <h6 class="fw-bold mb-3">Trekker Feedback ({{ trekReviews.length }})</h6>
            <div v-if="loadingReviews" class="text-center py-3">
              <div class="spinner-border spinner-border-sm text-warning"></div>
            </div>
            <div v-else-if="trekReviews.length === 0" class="text-center py-3 text-muted small">
              No reviews yet. Be the first to share your experience!
            </div>
            <div v-else class="list-group list-group-flush">
              <div v-for="r in trekReviews" :key="r.id" class="list-group-item px-0 py-2">
                <div class="d-flex justify-content-between align-items-center">
                  <span class="fw-semibold small">{{ r.user_name }}</span>
                  <span class="text-warning small">
                    <span v-for="star in r.rating" :key="star">★</span>
                  </span>
                </div>
                <p class="small text-secondary mb-1">{{ r.comment || 'No written comment.' }}</p>
                <small class="text-muted" style="font-size: 0.7rem;">{{ r.created_at }}</small>
              </div>
            </div>
          </div>
          <div class="modal-footer border-0">
            <button type="button" class="btn btn-secondary" @click="reviewTrek = null">Close</button>
          </div>
        </div>
      </div>
    </div>

    <!-- TREK ITINERARY & GEAR CHECKLIST MODAL -->
    <div class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5);" v-if="itineraryTrek">
      <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable">
        <div class="modal-content border-0 shadow">
          <div class="modal-header bg-success text-white">
            <h5 class="modal-title"><i class="bi bi-compass-fill me-2"></i>{{ itineraryTrek.name }}</h5>
            <button type="button" class="btn-close btn-close-white" @click="itineraryTrek = null"></button>
          </div>
          <div class="modal-body p-4">
            <div class="mb-4">
              <h6 class="fw-bold text-success mb-2">
                <i class="bi bi-signpost-split me-1"></i>Day-Wise Itinerary ({{ itineraryTrek.duration_days }} Days)
              </h6>
              <div class="bg-light p-3 rounded small text-secondary" style="white-space: pre-line;">{{ itineraryTrek.itinerary || 'Day 1: Base camp orientation & fitness walk\nDay 2: Ascent to high ridge campsite\nDay 3: Scenic pass crossing & alpine meadows\nDay 4: Summit push (breathtaking panoramic vistas)\nDay 5: Controlled return trek to base' }}</div>
            </div>
            <div>
              <h6 class="fw-bold text-danger mb-2">
                <i class="bi bi-backpack4 me-1"></i>Mandatory Packing & Gear Checklist
              </h6>
              <div class="bg-light p-3 rounded small text-secondary" style="white-space: pre-line;">{{ itineraryTrek.gear_checklist || '• Sturdy high-ankle trekking shoes with good grip\n• 50L Rucksack with waterproof rain cover\n• 2 pairs of thermal fleece inners & windproof jacket\n• UV protection sunglasses & quick-dry trekking pants\n• 2x 1L reusable water bottles & electrolyte sachets\n• Headlamp with extra batteries\n• Personal blister kit & prescribed Diamox (if recommended)' }}</div>
            </div>
          </div>
          <div class="modal-footer border-0">
            <button type="button" class="btn btn-secondary" @click="itineraryTrek = null">Close</button>
            <button
              type="button"
              class="btn btn-primary"
              :disabled="itineraryTrek.status !== 'Open' || itineraryTrek.available_slots === 0"
              @click="openBookingModal(itineraryTrek); itineraryTrek = null"
            >
              Book Now
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TrekkerDashboard',
  inject: ['auth'],
  data() {
    return {
      currentTab: 'explore',
      treks: [],
      myBookings: [],
      loadingTreks: false,
      loadingBookings: false,
      exportingCsv: false,
      selectedTrek: null,
      bookingSlots: 1,
      paymentMethod: 'Simulated UPI (GooglePay / PhonePe)',
      bookingInProgress: false,
      itineraryTrek: null,
      reviewTrek: null,
      trekReviews: [],
      loadingReviews: false,
      submittingReview: false,
      newReview: { rating: 5, comment: '' },
      alertMessage: '',
      alertType: 'success',
      filters: {
        search: '',
        difficulty: '',
        location: ''
      }
    };
  },
  mounted() {
    this.fetchTreks();
    if (this.auth.isAuthenticated() && this.auth.user.role === 'user') {
      this.loadMyBookings();
    }
  },
  methods: {
    showAlert(msg, type = 'success') {
      this.alertMessage = msg;
      this.alertType = type;
      setTimeout(() => { this.alertMessage = ''; }, 4000);
    },
    getDifficultyBadge(difficulty) {
      if (difficulty === 'Easy') return 'badge-easy';
      if (difficulty === 'Moderate') return 'badge-moderate';
      return 'badge-hard';
    },
    getBookingStatusBadge(status) {
      if (status === 'Booked') return 'bg-success';
      if (status === 'Cancelled') return 'bg-danger';
      return 'bg-info text-dark';
    },
    resetFilters() {
      this.filters = { search: '', difficulty: '', location: '' };
      this.fetchTreks();
    },
    async fetchTreks() {
      this.loadingTreks = true;
      try {
        const queryParams = new URLSearchParams();
        if (this.filters.search) queryParams.append('search', this.filters.search);
        if (this.filters.difficulty) queryParams.append('difficulty', this.filters.difficulty);
        if (this.filters.location) queryParams.append('location', this.filters.location);

        const res = await fetch(`/api/treks?${queryParams.toString()}`);
        const data = await res.json();
        if (res.ok && data.success) {
          this.treks = data.treks;
        }
      } catch (err) {
        this.showAlert('Failed to load treks.', 'danger');
      } finally {
        this.loadingTreks = false;
      }
    },
    async loadMyBookings() {
      if (!this.auth.isAuthenticated()) return;
      this.loadingBookings = true;
      try {
        const res = await fetch('/api/bookings/my-bookings', {
          headers: { 'Authorization': `Bearer ${this.auth.token}` }
        });
        const data = await res.json();
        if (res.ok && data.success) {
          this.myBookings = data.bookings;
        }
      } catch (err) {
        console.error(err);
      } finally {
        this.loadingBookings = false;
      }
    },
    openBookingModal(trek) {
      if (!this.auth.isAuthenticated()) {
        this.$router.push('/login');
        return;
      }
      this.selectedTrek = trek;
      this.bookingSlots = 1;
    },
    async confirmBooking() {
      if (!this.selectedTrek) return;
      this.bookingInProgress = true;

      try {
        const res = await fetch('/api/bookings', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.auth.token}`
          },
          body: JSON.stringify({
            trek_id: this.selectedTrek.id,
            slots_booked: this.bookingSlots,
            payment_method: this.paymentMethod
          })
        });

        const data = await res.json();
        if (res.ok && data.success) {
          this.showAlert(data.message, 'success');
          this.selectedTrek = null;
          this.fetchTreks();
          this.loadMyBookings();
        } else {
          this.showAlert(data.message || 'Booking failed.', 'danger');
        }
      } catch (err) {
        this.showAlert('Network error while booking.', 'danger');
      } finally {
        this.bookingInProgress = false;
      }
    },
    async cancelBooking(bookingId) {
      if (!confirm('Are you sure you want to cancel this booking? Slots will be released.')) return;

      try {
        const res = await fetch(`/api/bookings/${bookingId}/cancel`, {
          method: 'PUT',
          headers: { 'Authorization': `Bearer ${this.auth.token}` }
        });
        const data = await res.json();
        if (res.ok && data.success) {
          this.showAlert(data.message, 'success');
          this.loadMyBookings();
          this.fetchTreks();
        } else {
          this.showAlert(data.message || 'Cancellation failed.', 'danger');
        }
      } catch (err) {
        this.showAlert('Error cancelling booking.', 'danger');
      }
    },
    async exportHistoryCsv() {
      this.exportingCsv = true;
      try {
        const res = await fetch('/api/bookings/export-csv', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${this.auth.token}` }
        });
        const data = await res.json();

        if (res.ok && data.success) {
          let downloadUrl = '';
          if (data.export && data.export.download_url) {
            downloadUrl = data.export.download_url;
          } else if (data.task_id) {
            this.showAlert('CSV export job initiated in background.', 'info');
          }

          if (downloadUrl) {
            // Trigger direct file download with auth token
            const fileRes = await fetch(downloadUrl, {
              headers: { 'Authorization': `Bearer ${this.auth.token}` }
            });
            const blob = await fileRes.blob();
            const link = document.createElement('a');
            link.href = window.URL.createObjectURL(blob);
            link.download = data.export.filename;
            link.click();
            this.showAlert('Trekking history CSV downloaded successfully!', 'success');
          }
        } else {
          this.showAlert(data.message || 'Export failed.', 'danger');
        }
      } catch (err) {
        this.showAlert('Error exporting CSV.', 'danger');
      } finally {
        this.exportingCsv = false;
      }
    },
    async openReviewsModal(trek) {
      this.reviewTrek = trek;
      this.loadingReviews = true;
      this.trekReviews = [];
      this.newReview = { rating: 5, comment: '' };
      try {
        const res = await fetch(`/api/treks/${trek.id}/reviews`);
        const data = await res.json();
        if (res.ok && data.success) {
          this.trekReviews = data.reviews;
        }
      } catch (err) {
        console.error(err);
      } finally {
        this.loadingReviews = false;
      }
    },
    async submitReview() {
      if (!this.reviewTrek || !this.auth.isAuthenticated()) return;
      this.submittingReview = true;
      try {
        const res = await fetch(`/api/treks/${this.reviewTrek.id}/reviews`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.auth.token}`
          },
          body: JSON.stringify(this.newReview)
        });
        const data = await res.json();
        if (res.ok && data.success) {
          this.showAlert(data.message, 'success');
          this.newReview.comment = '';
          this.openReviewsModal(this.reviewTrek);
          this.fetchTreks();
        } else {
          this.showAlert(data.message || 'Review submission failed.', 'danger');
        }
      } catch (err) {
        this.showAlert('Error posting review.', 'danger');
      } finally {
        this.submittingReview = false;
      }
    },
    openItineraryModal(trek) {
      this.itineraryTrek = trek;
    }
  }
};
</script>
