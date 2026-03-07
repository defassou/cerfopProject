/* ── PRLG CNT Guinée — Main JS ─────────────────────────── */

// Auto-dismiss alerts
document.addEventListener('DOMContentLoaded', function () {
  // Dismiss alerts after 5s
  document.querySelectorAll('.alert').forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity .5s';
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 500);
    }, 5000);
  });

  // Vote selection
  document.querySelectorAll('.vote-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.vote-btn').forEach(function (b) { b.classList.remove('selected'); });
      btn.classList.add('selected');
      var input = document.getElementById('vote-choix');
      if (input) input.value = btn.dataset.choix;
      var submitBtn = document.getElementById('btn-confirmer-vote');
      if (submitBtn) submitBtn.disabled = false;
    });
  });

  // Confirm dialogs
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // Presence toggle (checkboxes visual)
  document.querySelectorAll('.presence-toggle').forEach(function (chk) {
    chk.addEventListener('change', function () {
      var item = chk.closest('.presence-item');
      if (chk.checked) {
        item.classList.add('present');
        item.classList.remove('absent');
      } else {
        item.classList.remove('present');
        item.classList.add('absent');
      }
    });
  });

  // Charts — résultats
  var ctx = document.getElementById('voteChart');
  if (ctx && window.voteData) {
    new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Pour (OUI)', 'Contre (NON)', 'Abstention'],
        datasets: [{
          data: [window.voteData.oui, window.voteData.non, window.voteData.abstentions],
          backgroundColor: ['#1a5c2a', '#cc0000', '#888888'],
          borderWidth: 0,
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom' },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                var pct = window.voteData.total > 0
                  ? Math.round(ctx.raw / window.voteData.total * 100)
                  : 0;
                return ctx.label + ': ' + ctx.raw + ' (' + pct + '%)';
              }
            }
          }
        }
      }
    });
  }

  // Mobile sidebar toggle
  var toggleBtn = document.getElementById('sidebar-toggle');
  var sidebar   = document.querySelector('.sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', function () {
      sidebar.classList.toggle('open');
    });
  }
});
