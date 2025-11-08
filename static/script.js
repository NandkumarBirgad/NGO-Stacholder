// Enhanced JavaScript for NGO Management System

document.addEventListener("DOMContentLoaded", () => {
  // Initialize page-specific functions
  const elActiveVol = document.getElementById("activeVolunteers");
  if (elActiveVol) loadSummary();

  const donationCanvas = document.getElementById("donationTrend");
  if (donationCanvas) loadDonationTrend();

  const recentEntriesEl = document.getElementById("recentEntries");
  if (recentEntriesEl) loadRecentEntries();

  // Animate cards on load
  animateCards();
});

// Load dashboard summary
function loadSummary() {
  showLoading('activeVolunteers');
  showLoading('activeProjects');
  showLoading('totalDonations');
  
  fetch('/api/summary')
    .then(res => res.json())
    .then(data => {
      animateNumber('activeVolunteers', data.active_volunteers ?? 0, 0);
      animateNumber('activeProjects', data.total_projects ?? 0, 0);
      animateCurrency('totalDonations', data.total_donations ?? 0, 0);
    })
    .catch(err => {
      console.error("Failed to load summary:", err);
      hideLoading('activeVolunteers');
      hideLoading('activeProjects');
      hideLoading('totalDonations');
      document.getElementById("activeVolunteers").textContent = '0';
      document.getElementById("activeProjects").textContent = '0';
      document.getElementById("totalDonations").textContent = '$0.00';
    });
}

// Load donation trend chart
function loadDonationTrend() {
  fetch('/api/analytics/donations_trend')
    .then(res => res.json())
    .then(rows => {
      if (rows && rows.length > 0) {
        const labels = rows.map(r => {
          const date = new Date(r.month + '-01');
          return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
        });
        const data = rows.map(r => parseFloat(r.total) || 0);
        renderDonationChart(labels, data);
      } else {
        document.getElementById('donationTrend').parentElement.innerHTML = 
          '<div class="empty-box">No donation data available</div>';
      }
    })
    .catch(err => {
      console.error("Failed to load donation trend:", err);
      document.getElementById('donationTrend').parentElement.innerHTML = 
        '<div class="empty-box">Error loading donation data</div>';
    });
}

// Render donation chart with enhanced styling
function renderDonationChart(labels, data) {
  const ctx = document.getElementById('donationTrend').getContext('2d');
  
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Donations ($)',
        data: data,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointRadius: 5,
        pointHoverRadius: 8,
        pointBackgroundColor: '#3b82f6',
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            font: {
              size: 14,
              weight: '600'
            },
            padding: 20
          }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          padding: 12,
          titleFont: {
            size: 14,
            weight: '600'
          },
          bodyFont: {
            size: 13
          },
          borderColor: '#3b82f6',
          borderWidth: 1,
          displayColors: true,
          callbacks: {
            label: function(context) {
              return '$' + context.parsed.y.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function(value) {
              return '$' + value.toLocaleString();
            },
            font: {
              size: 12
            }
          },
          grid: {
            color: 'rgba(226, 232, 240, 0.5)'
          }
        },
        x: {
          ticks: {
            font: {
              size: 12
            }
          },
          grid: {
            display: false
          }
        }
      },
      animation: {
        duration: 1500,
        easing: 'easeInOutQuart'
      }
    }
  });
}

// Load recent entries
function loadRecentEntries() {
  fetch('/api/recent_entries')
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById('recentEntries');
      if (!data || !data.length) {
        container.innerHTML = '<div style="text-align:center; color:var(--muted);">No recent entries</div>';
        return;
      }
      
      container.innerHTML = data.map((entry, index) => {
        const date = new Date(entry.date);
        const typeColors = {
          'Volunteer': '#3b82f6',
          'Donor': '#10b981',
          'Beneficiary': '#f59e0b',
          'Event': '#8b5cf6',
          'Donation': '#ef4444'
        };
        const color = typeColors[entry.type] || '#64748b';
        
        return `
          <div style="padding:12px 0; border-bottom:1px solid var(--border-light); display:flex; justify-content:space-between; align-items:center; animation: fadeInUp 0.3s ease-out ${index * 0.05}s both;">
            <div style="display:flex; align-items:center; gap:12px;">
              <div style="width:8px; height:8px; border-radius:50%; background:${color};"></div>
              <div>
                <strong style="color:#0f172a;">${entry.type}</strong>: 
                <span style="color:var(--muted);">${entry.name}</span>
              </div>
            </div>
            <div style="color:var(--muted); font-size:13px; font-weight:500;">
              ${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
            </div>
          </div>
        `;
      }).join('');
    })
    .catch(err => {
      console.error("Failed to load recent entries:", err);
      document.getElementById('recentEntries').innerHTML = 
        '<div style="text-align:center; color:var(--danger);">Error loading entries</div>';
    });
}

// Animate number counting
function animateNumber(elementId, targetValue, duration = 1000) {
  const element = document.getElementById(elementId);
  if (!element) return;
  
  const startValue = 0;
  const increment = targetValue / (duration / 16);
  let current = startValue;
  
  const timer = setInterval(() => {
    current += increment;
    if (current >= targetValue) {
      element.textContent = Math.round(targetValue);
      clearInterval(timer);
    } else {
      element.textContent = Math.round(current);
    }
  }, 16);
}

// Animate currency counting
function animateCurrency(elementId, targetValue, duration = 1000) {
  const element = document.getElementById(elementId);
  if (!element) return;
  
  const startValue = 0;
  const increment = targetValue / (duration / 16);
  let current = startValue;
  
  const timer = setInterval(() => {
    current += increment;
    if (current >= targetValue) {
      element.textContent = `$${targetValue.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
      clearInterval(timer);
    } else {
      element.textContent = `$${current.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    }
  }, 16);
}

// Show loading state
function showLoading(elementId) {
  const element = document.getElementById(elementId);
  if (element) {
    element.innerHTML = '<span class="loading"></span>';
  }
}

// Hide loading state
function hideLoading(elementId) {
  // Loading will be replaced by actual content
}

// Animate cards on page load
function animateCards() {
  const cards = document.querySelectorAll('.card');
  cards.forEach((card, index) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    setTimeout(() => {
      card.style.transition = 'all 0.5s ease-out';
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, index * 100);
  });
}

// Close modal function (can be called from anywhere)
function closeForm() {
  const modals = document.querySelectorAll('.modal');
  modals.forEach(modal => {
    modal.style.display = 'none';
  });
  
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.reset();
  });
}

// Function to trigger dashboard refresh after form submission
function triggerDashboardRefresh() {
  // Use localStorage to trigger refresh in dashboard (if open in another tab)
  localStorage.setItem('dashboardRefresh', Date.now().toString());
  
  // Also trigger refresh if dashboard is open in current page
  if (typeof loadRecentEntries === 'function') {
    loadRecentEntries();
  }
  if (typeof loadRecentActivities === 'function') {
    loadRecentActivities();
  }
  if (typeof loadActiveProjectsList === 'function') {
    loadActiveProjectsList();
  }
  if (typeof loadSummary === 'function') {
    loadSummary();
  }
}

// Show notification/toast (simple implementation)
function showNotification(message, type = 'success') {
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 16px 24px;
    background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
    color: white;
    border-radius: 10px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    z-index: 10000;
    animation: slideInRight 0.3s ease-out;
    font-weight: 600;
  `;
  notification.textContent = message;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.style.animation = 'slideOutRight 0.3s ease-out';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// Format currency
function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2
  }).format(amount);
}

// Format date
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

// Add CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
  @keyframes slideInRight {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOutRight {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);
