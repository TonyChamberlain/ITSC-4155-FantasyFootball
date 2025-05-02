console.log('search.js loaded');

document.addEventListener('DOMContentLoaded', () => {
  const form    = document.querySelector('.search-form');
  const results = document.getElementById('results');

  console.log('Form element:', form);
  console.log('Results container:', results);

  if (!form || !results) {
    console.error('Missing form or results element!');
    return;
  }

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const q = form.querySelector('input').value.trim();
    console.log('Submitting search for:', q);

    results.innerHTML = '<p>Searching…</p>';

    try {
      const resp = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
      console.log('Fetch status:', resp.status);
      const players = await resp.json();
      console.log('Received players:', players);

      if (!players.length) {
        results.innerHTML = '<p>No players found.</p>';
        return;
      }

      results.innerHTML = players.map(p => `
        <div class="player-card">
          <img src="${p.headshot}" alt="${p.name}" />
          <div>
            <h4>${p.name} — ${p.team}</h4>
            <p>Position: ${p.position} | Points: ${p.points}</p>
            <a href="${p.profile}" target="_blank">Profile ↗</a>
          </div>
        </div>
      `).join('');

    } catch (err) {
      console.error('Error during fetch:', err);
      results.innerHTML = '<p>Error fetching players.</p>';
    }
  });
});