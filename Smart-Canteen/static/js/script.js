// Smart Canteen Interactive Frontend JavaScript

document.addEventListener('DOMContentLoaded', () => {
  initCartListeners();
  initAutoDismissAlerts();
  initAdminLiveRefresh();
  initThemeAndAccentSettings();
  initAiChatbot();
  initLiveRushGauge();
  initLiveTicker();
});

// Toast notification helper
function showToast(message, type = 'success') {
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.style.cssText = 'position: fixed; bottom: 75px; right: 20px; z-index: 10000; display: flex; flex-direction: column; gap: 8px;';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  const bg = type === 'success' ? '#22C55E' : type === 'info' ? '#3B82F6' : '#EF4444';
  toast.style.cssText = `background: ${bg}; color: #ffffff; padding: 10px 18px; border-radius: 8px; font-weight: 700; font-size: 0.88rem; box-shadow: 0 4px 15px rgba(0,0,0,0.4); transition: all 0.25s ease; opacity: 0; transform: translateY(10px);`;
  toast.innerHTML = `<i class="fa-solid ${type === 'success' ? 'fa-circle-check' : type === 'info' ? 'fa-circle-info' : 'fa-triangle-exclamation'}"></i> ${message}`;
  
  toastContainer.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
  }, 10);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 250);
  }, 3000);
}

// Copy Coupon Code Helper
function copyCouponCode(code) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(code).then(() => {
      showToast(`Coupon code '${code}' copied!`, 'info');
    });
  } else {
    showToast(`Code: ${code}`, 'info');
  }
}

// Theme & Accent Color Controller
function initThemeAndAccentSettings() {
  const savedTheme = localStorage.getItem('canteen_theme') || 'dark';
  const savedAccent = localStorage.getItem('canteen_accent') || 'orange';

  if (savedTheme === 'light') document.body.classList.add('theme-light');
  if (savedAccent !== 'orange') document.body.classList.add(`accent-${savedAccent}`);
}

function toggleLightDarkMode() {
  if (document.body.classList.contains('theme-light')) {
    document.body.classList.remove('theme-light');
    localStorage.setItem('canteen_theme', 'dark');
    showToast('Dark Mode Enabled', 'info');
  } else {
    document.body.classList.add('theme-light');
    localStorage.setItem('canteen_theme', 'light');
    showToast('Light Mode Enabled', 'info');
  }
}

function setAccentTheme(color) {
  document.body.classList.remove('accent-green', 'accent-blue', 'accent-purple');
  if (color !== 'orange') {
    document.body.classList.add(`accent-${color}`);
  }
  localStorage.setItem('canteen_accent', color);
  showToast(`Theme Accent Changed to ${color.toUpperCase()}`, 'success');
}

// Web Audio API Order Ready Sound Chime
function playReadyChime() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
    osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.3); // A5

    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + 0.5);
  } catch(e) {
    console.log('Audio chime error:', e);
  }
}

// AI Chatbot Assistant Widget Controller
function initAiChatbot() {
  if (document.getElementById('ai-chatbot-widget')) return;

  const botHtml = `
    <div id="ai-chatbot-widget" style="position: fixed; bottom: 80px; right: 20px; z-index: 9999;">
      <button id="btn-toggle-chatbot" onclick="toggleAiChatbot()" style="width: 55px; height: 55px; border-radius: 50%; background: var(--primary-accent); color: #000; border: none; font-size: 1.4rem; box-shadow: var(--shadow-glow), var(--shadow-md); cursor: pointer; display: flex; align-items: center; justify-content: center;">
        <i class="fa-solid fa-robot"></i>
      </button>

      <div id="chatbot-box" class="solid-card" style="display: none; position: absolute; bottom: 70px; right: 0; width: 330px; height: 440px; border: 2px solid var(--primary-accent); border-radius: 16px; overflow: hidden; flex-direction: column; box-shadow: var(--shadow-md); background: var(--card-bg);">
        
        <div style="background: var(--bg-secondary); padding: 0.8rem 1rem; border-bottom: 1px solid var(--card-border); display: flex; justify-content: space-between; align-items: center;">
          <div style="font-weight: 800; font-size: 0.95rem; display: flex; align-items: center; gap: 0.5rem; color: var(--primary-accent);">
            <i class="fa-solid fa-robot"></i> CanteenBot AI
          </div>
          <button onclick="toggleAiChatbot()" style="background: none; border: none; color: var(--text-muted); cursor: pointer;"><i class="fa-solid fa-xmark"></i></button>
        </div>

        <div id="chatbot-messages" style="flex: 1; padding: 0.9rem; overflow-y: auto; display: flex; flex-direction: column; gap: 0.6rem; font-size: 0.85rem;">
          <div style="background: var(--card-elevated); padding: 0.6rem 0.8rem; border-radius: 10px; max-width: 85%;">
            👋 Hi! I'm CanteenBot. Ask me for recommendations! e.g., <em>"Food under 100"</em> or <em>"High protein"</em>
          </div>
        </div>

        <form onsubmit="handleAiSubmit(event)" style="padding: 0.6rem; border-top: 1px solid var(--card-border); display: flex; gap: 0.4rem; background: var(--bg-secondary);">
          <input type="text" id="ai-user-input" class="form-control" placeholder="Ask CanteenBot..." style="font-size: 0.82rem; padding: 0.5rem 0.8rem;" required>
          <button type="submit" class="btn-primary btn-sm"><i class="fa-solid fa-paper-plane"></i></button>
        </form>

      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', botHtml);
}

function toggleAiChatbot() {
  const box = document.getElementById('chatbot-box');
  box.style.display = box.style.display === 'none' ? 'flex' : 'none';
}

function handleAiSubmit(e) {
  e.preventDefault();
  const input = document.getElementById('ai-user-input');
  const msg = input.value.trim();
  if (!msg) return;

  const msgsContainer = document.getElementById('chatbot-messages');
  msgsContainer.insertAdjacentHTML('beforeend', `<div style="background: var(--primary-accent); color: #000; font-weight: 700; padding: 0.6rem 0.8rem; border-radius: 10px; align-self: flex-end; max-width: 85%;">${msg}</div>`);
  input.value = '';
  msgsContainer.scrollTop = msgsContainer.scrollHeight;

  fetch('/api/ai-assistant', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: msg })
  })
  .then(res => res.json())
  .then(data => {
    let itemsHtml = '';
    if (data.items && data.items.length > 0) {
      itemsHtml = data.items.map(item => `
        <div style="background: var(--bg-secondary); padding: 0.5rem; border-radius: 8px; margin-top: 4px; display: flex; justify-content: space-between; align-items: center; border: 1px solid var(--card-border);">
          <span style="font-weight: 700; font-size: 0.78rem;">${item.name} (₹${item.price})</span>
          <button onclick="addToCart(${item.id})" style="background: var(--primary-accent); border: none; color: #000; font-weight: 800; font-size: 0.7rem; padding: 3px 7px; border-radius: 4px; cursor: pointer;">+ Add</button>
        </div>
      `).join('');
    }

    msgsContainer.insertAdjacentHTML('beforeend', `
      <div style="background: var(--card-elevated); padding: 0.6rem 0.8rem; border-radius: 10px; max-width: 90%;">
        <div>${data.reply}</div>
        ${itemsHtml}
      </div>
    `);
    msgsContainer.scrollTop = msgsContainer.scrollHeight;
  });
}

// Update Cart Badge Count in Navbar
function updateCartBadge(count) {
  const badges = document.querySelectorAll('.badge-count');
  badges.forEach(badge => {
    badge.textContent = count;
    badge.style.display = count > 0 ? 'flex' : 'none';
  });
}

// Add Item to Cart via AJAX
function addToCart(itemId, quantity = 1, addons = [], instructions = '') {
  fetch('/api/cart/add', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ item_id: itemId, quantity: quantity, addons: addons, instructions: instructions })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      updateCartBadge(data.cart_count);
      playAddSound();
      showToast('Added to cart!');
    } else {
      showToast(data.message || 'Failed to add item', 'danger');
    }
  })
  .catch(err => {
    console.error('Cart Add Error:', err);
    showToast('Error updating cart', 'danger');
  });
}

// Update Item Quantity in Cart Page
function updateCartQty(itemId, action) {
  fetch('/api/cart/update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ item_id: itemId, action: action })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      window.location.reload();
    }
  });
}

// Remove Item from Cart Page
function removeCartItem(itemId) {
  fetch('/api/cart/remove', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ item_id: itemId })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      window.location.reload();
    }
  });
}

// Attach Event Listeners to Cart Add Buttons
function initCartListeners() {
  document.querySelectorAll('.btn-add-cart').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const itemId = btn.getAttribute('data-id');
      addToCart(itemId);
    });
  });
}

// Auto-dismiss Flash Alerts
function initAutoDismissAlerts() {
  setTimeout(() => {
    document.querySelectorAll('.alert').forEach(alert => {
      alert.style.transition = 'opacity 0.4s ease';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 400);
    });
  }, 4000);
}

// Admin Live Orders Dashboard Polling
function initAdminLiveRefresh() {
  const liveTable = document.getElementById('admin-live-orders-body');
  if (liveTable) {
    setInterval(() => {
      fetch('/api/admin/live-orders')
        .then(res => res.json())
        .then(data => {
          if (data.orders) {
            updateAdminDashboardTable(data.orders, data.stats);
          }
        })
        .catch(err => console.log('Polling error:', err));
    }, 10000);
  }
}

function updateAdminDashboardTable(orders, stats) {
  if (stats) {
    const totalEl = document.getElementById('stat-total-orders');
    const pendingEl = document.getElementById('stat-pending-orders');
    const completedEl = document.getElementById('stat-completed-orders');
    const revenueEl = document.getElementById('stat-today-revenue');
    if (totalEl) totalEl.textContent = stats.total_orders;
    if (pendingEl) pendingEl.textContent = stats.pending_orders;
    if (completedEl) completedEl.textContent = stats.completed_orders;
    if (revenueEl) revenueEl.textContent = '₹' + stats.today_revenue;
  }
}

// Web Audio API Audio Synthesizer Effects
function playAddSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(440, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.12);
    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.12);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.12);
  } catch(e) {}
}

function playSuccessSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const notes = [523.25, 659.25, 783.99, 1046.50];
    notes.forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(freq, ctx.currentTime + idx * 0.08);
      gain.gain.setValueAtTime(0.2, ctx.currentTime + idx * 0.08);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + idx * 0.08 + 0.2);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(ctx.currentTime + idx * 0.08);
      osc.stop(ctx.currentTime + idx * 0.08 + 0.2);
    });
  } catch(e) {}
}

// Live Canteen Rush Gauge Auto-Poller
function initLiveRushGauge() {
  fetchLiveRush();
  setInterval(fetchLiveRush, 12000);
}

function fetchLiveRush() {
  const badge = document.getElementById('live-rush-indicator');
  const rushText = document.getElementById('rush-text');
  if (!badge || !rushText) return;

  fetch('/api/live-rush')
    .then(res => res.json())
    .then(data => {
      badge.className = 'live-rush-badge';
      if (data.status === 'low') {
        badge.classList.add('rush-low');
      } else if (data.status === 'moderate') {
        badge.classList.add('rush-mod');
      } else {
        badge.classList.add('rush-peak');
      }
      rushText.textContent = data.rush_text;
    })
    .catch(err => console.log('Rush error:', err));
}

// Live Campus Ticker Auto-Poller
function initLiveTicker() {
  const feed = document.getElementById('live-ticker-feed');
  if (!feed) return;

  fetchLiveTickerFeed();
  setInterval(fetchLiveTickerFeed, 15000);
}

function fetchLiveTickerFeed() {
  const feed = document.getElementById('live-ticker-feed');
  if (!feed) return;

  fetch('/api/live-feed')
    .then(res => res.json())
    .then(data => {
      if (data.feed && data.feed.length > 0) {
        const text = data.feed.join(' &nbsp;•&nbsp; ');
        feed.innerHTML = `<span>${text} &nbsp;•&nbsp; ${text}</span>`;
      }
    })
    .catch(err => console.log('Ticker error:', err));
}

// Canvas Confetti Particles Cannon
function triggerConfetti() {
  let canvas = document.getElementById('confetti-canvas');
  if (!canvas) {
    canvas = document.createElement('canvas');
    canvas.id = 'confetti-canvas';
    canvas.style.cssText = 'position: fixed; inset: 0; pointer-events: none; z-index: 99999; width: 100vw; height: 100vh;';
    document.body.appendChild(canvas);
  }
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const colors = ['#FF9D00', '#FF6B35', '#22C55E', '#3B82F6', '#A855F7', '#EC4899'];
  const particles = [];
  for (let i = 0; i < 90; i++) {
    particles.push({
      x: canvas.width / 2,
      y: canvas.height / 2 - 100,
      vx: (Math.random() - 0.5) * 14,
      vy: (Math.random() - 0.7) * 16,
      size: Math.random() * 8 + 4,
      color: colors[Math.floor(Math.random() * colors.length)],
      rotation: Math.random() * 360,
      rSpeed: (Math.random() - 0.5) * 10
    });
  }

  let startTime = Date.now();
  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    let elapsed = Date.now() - startTime;

    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.35; // Gravity
      p.rotation += p.rSpeed;

      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate((p.rotation * Math.PI) / 180);
      ctx.fillStyle = p.color;
      ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
      ctx.restore();
    });

    if (elapsed < 3000) {
      requestAnimationFrame(animate);
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }

  requestAnimationFrame(animate);
}

// Voice Search Assistant (Web Speech API)
function startVoiceSearch() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    showToast('Voice Search not supported in this browser.', 'danger');
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = 'en-US';
  showToast('🎙️ Listening... Speak food item name', 'info');

  recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    showToast(`Voice heard: "${transcript}"`, 'success');
    const searchInputs = document.querySelectorAll('input[name="search"]');
    if (searchInputs.length > 0) {
      searchInputs[0].value = transcript;
      if (searchInputs[0].form) {
        searchInputs[0].form.submit();
      }
    }
  };

  recognition.onerror = () => {
    showToast('Could not hear voice input. Please try again.', 'danger');
  };

  recognition.start();
}

// Star Review Helper
function setReviewRating(rating) {
  const ratingInput = document.getElementById('review-rating-val');
  if (ratingInput) ratingInput.value = rating;

  const stars = document.querySelectorAll('.review-star');
  stars.forEach((star, idx) => {
    if (idx < rating) {
      star.style.color = '#FBBF24';
    } else {
      star.style.color = 'var(--text-muted)';
    }
  });
}

function submitReview(itemId) {
  const rating = document.getElementById('review-rating-val').value;
  const comment = document.getElementById('review-comment').value;

  if (!comment.trim()) {
    showToast('Please write a short review comment', 'warning');
    return;
  }

  fetch('/api/add-review', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ item_id: itemId, rating: rating, comment: comment })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      showToast('Review submitted! Thank you.', 'success');
      setTimeout(() => window.location.reload(), 1000);
    } else {
      showToast(data.message || 'Error submitting review', 'danger');
    }
  });
}
