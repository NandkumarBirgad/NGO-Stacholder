document.addEventListener("DOMContentLoaded", () => {
  // Only run summary fetch if element exists
  const elActiveVol = document.getElementById("activeVolunteers");
  if (elActiveVol) loadSummary();

  // If analytics chart canvas exists, load donation trend
  const donationCanvas = document.getElementById("donationTrend");
  if (donationCanvas) loadDonationTrend();
});

function loadSummary() {
  fetch('/api/summary')
    .then(res => res.json())
    .then(data => {
      document.getElementById("activeVolunteers").textContent = data.active_volunteers ?? 0;
      document.getElementById("activeProjects").textContent = data.total_projects ?? 0;
      document.getElementById("totalDonations").textContent = `$${(data.total_donations ?? 0).toFixed(2)}`;
    })
    .catch(err => {
      console.error("Failed to load summary:", err);
    });
}

function loadDonationTrend() {
  fetch('/api/analytics/donations_trend')
    .then(res => res.json())
    .then(rows => {
      // rows: [{month:'2025-06', total: 120.0}, ...]
      const labels = rows.map(r => r.month);
      const data = rows.map(r => r.total);
      renderDonationChart(labels, data);
    })
    .catch(err => console.error("Failed to load donation trend:", err));
}

function renderDonationChart(labels, data) {
  // Chart.js is loaded via CDN in the template
  const ctx = document.getElementById('donationTrend').getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Donations',
        data: data,
        fill: false,
        borderWidth: 2,
        tension: 0.3,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}

// Function to close the stakeholder form modal
function closeForm() {
  document.getElementById('addStakeholderModal').style.display = 'none';
  document.getElementById('stakeholderForm').reset();
}
