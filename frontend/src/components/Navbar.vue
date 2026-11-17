<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark shadow-sm">
    <div class="container">
      <router-link class="navbar-brand fw-bold d-flex align-items-center" to="/">
        <i class="bi bi-compass me-2 text-success fs-4"></i>
        <span>Trekking TMA</span>
      </router-link>

      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarContent">
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="navbarContent">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          <li class="nav-item">
            <router-link class="nav-link" to="/"><i class="bi bi-map me-1"></i>Explore Treks</router-link>
          </li>
          <li class="nav-item" v-if="auth.user && auth.user.role === 'staff'">
            <router-link class="nav-link text-warning" to="/staff"><i class="bi bi-person-badge me-1"></i>Staff Dashboard</router-link>
          </li>
          <li class="nav-item" v-if="auth.user && auth.user.role === 'admin'">
            <router-link class="nav-link text-info" to="/admin"><i class="bi bi-shield-lock me-1"></i>Admin Console</router-link>
          </li>
        </ul>

        <div class="d-flex align-items-center">
          <!-- When Logged In -->
          <div v-if="auth.isAuthenticated()" class="d-flex align-items-center">
            <!-- Notification Bell with Dropdown -->
            <div class="dropdown me-3 position-relative">
              <button
                class="btn btn-outline-light btn-sm position-relative"
                type="button"
                id="notifDropdown"
                data-bs-toggle="dropdown"
                aria-expanded="false"
                @click="fetchNotifications"
              >
                <i class="bi bi-bell"></i>
                <span
                  v-if="unreadCount > 0"
                  class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger"
                  style="font-size: 0.65rem;"
                >
                  {{ unreadCount }}
                </span>
              </button>
              <ul class="dropdown-menu dropdown-menu-end shadow border-0 p-2" aria-labelledby="notifDropdown" style="width: 320px; max-height: 400px; overflow-y: auto;">
                <li class="d-flex justify-content-between align-items-center px-2 py-1 border-bottom">
                  <span class="fw-bold small text-muted">Notifications</span>
                  <button v-if="unreadCount > 0" class="btn btn-link btn-sm p-0 text-decoration-none" style="font-size: 0.75rem;" @click="markAllRead">
                    Mark all read
                  </button>
                </li>
                <li v-if="notifications.length === 0" class="text-center py-3 text-muted small">
                  No notifications yet.
                </li>
                <li v-for="n in notifications" :key="n.id" class="px-2 py-2 border-bottom">
                  <div class="d-flex align-items-start">
                    <i
                      :class="['bi me-2 fs-6', n.notification_type === 'booking' ? 'bi-check-circle-fill text-success' : n.notification_type === 'cancellation' ? 'bi-x-circle-fill text-danger' : 'bi-info-circle-fill text-primary']"
                    ></i>
                    <div class="flex-grow-1">
                      <div class="fw-semibold small" :class="{ 'text-dark': !n.is_read, 'text-muted': n.is_read }">{{ n.title }}</div>
                      <div class="small text-secondary" style="font-size: 0.75rem;">{{ n.message }}</div>
                      <div class="text-muted" style="font-size: 0.65rem;">{{ n.created_at }}</div>
                    </div>
                  </div>
                </li>
              </ul>
            </div>

            <span class="badge bg-secondary me-2 p-2 d-none d-sm-inline">
              <i class="bi bi-person-circle me-1"></i>{{ auth.user.full_name }} ({{ auth.user.role }})
            </span>
            <router-link class="btn btn-outline-light btn-sm me-2" to="/profile">
              <i class="bi bi-gear"></i> Profile
            </router-link>
            <button class="btn btn-danger btn-sm" @click="handleLogout">
              <i class="bi bi-box-arrow-right"></i> Logout
            </button>
          </div>

          <!-- When Logged Out -->
          <div v-else>
            <router-link class="btn btn-outline-light btn-sm me-2" to="/login">
              <i class="bi bi-box-arrow-in-right"></i> Login
            </router-link>
            <router-link class="btn btn-success btn-sm" to="/register">
              <i class="bi bi-person-plus"></i> Register
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'Navbar',
  inject: ['auth'],
  data() {
    return {
      notifications: [],
      unreadCount: 0
    };
  },
  mounted() {
    if (this.auth.isAuthenticated()) {
      this.fetchNotifications();
    }
  },
  methods: {
    handleLogout() {
      if (confirm('Are you sure you want to log out?')) {
        this.auth.logout();
      }
    },
    async fetchNotifications() {
      if (!this.auth.isAuthenticated()) return;
      try {
        const res = await fetch('/api/notifications', {
          headers: { 'Authorization': `Bearer ${this.auth.token}` }
        });
        const data = await res.json();
        if (res.ok && data.success) {
          this.notifications = data.notifications;
          this.unreadCount = data.unread_count;
        }
      } catch (err) {
        console.error('Failed to load notifications', err);
      }
    },
    async markAllRead() {
      try {
        const res = await fetch('/api/notifications/read-all', {
          method: 'PUT',
          headers: { 'Authorization': `Bearer ${this.auth.token}` }
        });
        if (res.ok) {
          this.unreadCount = 0;
          this.notifications.forEach(n => { n.is_read = true; });
        }
      } catch (err) {
        console.error(err);
      }
    }
  }
}
</script>
