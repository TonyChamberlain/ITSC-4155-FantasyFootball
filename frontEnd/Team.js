console.log('team.js loaded');

document.addEventListener('DOMContentLoaded', init);

let rosterDisplay, rosterList, allTeamsList;
async function init() {
  console.log('init() start');
  const newTeamForm    = document.getElementById('new-team-form');
  const teamSelect     = document.getElementById('team-select');
  const rosterBuilder  = document.getElementById('roster-builder');
  const rosterForm     = document.getElementById('roster-form');
  const benchContainer = document.getElementById('bench-slots');
  rosterDisplay = document.getElementById('roster-display');
  rosterList = document.getElementById('roster-list');
  allTeamsList = document.getElementById('all-teams-list');

  console.log({ newTeamForm, teamSelect, rosterBuilder, rosterForm, benchContainer });

  newTeamForm.addEventListener('submit', createTeam);
  teamSelect.addEventListener('change', selectTeam);
  rosterForm.addEventListener('submit', saveRoster);

  benchContainer.innerHTML = '';
  for (let i = 1; i <= 7; i++) {
    const sel = document.createElement('select');
    sel.id = `bench-${i}`;
    sel.required = true;
    benchContainer.appendChild(sel);
  }

  await loadTeams();
  await loadAllTeamsSummaries();
  console.log('init() end');
}

async function createTeam(e) {
  e.preventDefault();
  console.log('createTeam() fired');

  const nameInput = document.getElementById('team-name');
  const name = nameInput.value.trim();
  console.log('  Team name:', name);
  if (!name) return;

  try {
    const resp = await fetch('/api/teams', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    console.log('  POST /api/teams →', resp.status);
    if (!resp.ok) {
      const errText = await resp.text();
      console.error('  createTeam error body:', errText);
      return;
    }
  } catch (err) {
    console.error('  createTeam network error:', err);
    return;
  }

  nameInput.value = '';
  await loadTeams();
}

async function loadTeams() {
  console.log('loadTeams()');
  try {
    const resp = await fetch('/api/teams');
    console.log('  GET /api/teams →', resp.status);
    const teams = await resp.json();
    console.log('  Teams data:', teams);

    const select = document.getElementById('team-select');
    select.innerHTML = '<option disabled selected>-- Select a team --</option>';
    teams.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.id;
      opt.textContent = t.name;
      select.appendChild(opt);
    });
  } catch (err) {
    console.error('  loadTeams error:', err);
  }
}

async function selectTeam(e) {
  const teamId = e.target.value;
  console.log('selectTeam() teamId =', teamId);
  if (!teamId) return;

  document.getElementById('selected-team-name').textContent =
    e.target.options[e.target.selectedIndex].text;
  document.getElementById('roster-builder').style.display = 'block';

  await loadPlayersIntoPositions();
  await loadRoster(teamId);
}

async function loadPlayersIntoPositions() {
  console.log('loadPlayersIntoPositions()');
  const starters = [
    { selectId: 'pos-QB',  pos: 'QB'  },
    { selectId: 'pos-RB1', pos: 'RB'  },
    { selectId: 'pos-RB2', pos: 'RB'  },
    { selectId: 'pos-WR1', pos: 'WR'  },
    { selectId: 'pos-WR2', pos: 'WR'  },
    { selectId: 'pos-TE',  pos: 'TE'  },
    { selectId: 'pos-K',   pos: 'K'   }
  ];

  for (const { selectId, pos } of starters) {
    const sel = document.getElementById(selectId);
    sel.innerHTML = '';
    const players = await fetch(`/api/search?pos=${pos}`).then(r => r.json());
    console.log(`  ${pos} players:`, players);
    players.forEach(p => {
      const opt = document.createElement('option');
      opt.value = JSON.stringify(p);
      opt.textContent = `${p.name} (${p.team})`;
      sel.appendChild(opt);
    });
  }

  const allPlayers = await fetch('/api/search').then(r => r.json());
  console.log('  All players for bench:', allPlayers.length);
  for (let i = 1; i <= 7; i++) {
    const sel = document.getElementById(`bench-${i}`);
    sel.innerHTML = '';
    allPlayers.forEach(p => {
      const opt = document.createElement('option');
      opt.value = JSON.stringify(p);
      opt.textContent = `${p.name} (${p.team} - ${p.position})`;
      sel.appendChild(opt);
    });
  }
}

async function loadRoster(teamId) {
  console.log('loadRoster() for team', teamId);
  const resp = await fetch(`/api/teams/${teamId}`);
  console.log('  GET /api/teams/${teamId} →', resp.status);
  const roster = await resp.json();
  console.log('  Roster data:', roster);

  ['QB','RB1','RB2','WR1','WR2','TE','K'].forEach(posKey => {
    const sel = document.getElementById(`pos-${posKey}`);
    const player = roster[posKey];
    if (player) sel.value = JSON.stringify(player);
  });

  roster.bench.forEach((player, idx) => {
    const sel = document.getElementById(`bench-${idx + 1}`);
    if (player) sel.value = JSON.stringify(player);
  });
  showRosterSummary(roster);
}

async function saveRoster(e) {
  e.preventDefault();
  console.log('saveRoster()');
  const teamId = document.getElementById('team-select').value;
  const roster = {};

  ['QB','RB1','RB2','WR1','WR2','TE','K'].forEach(posKey => {
    roster[posKey] = JSON.parse(
      document.getElementById(`pos-${posKey}`).value
    );
  });

  roster.bench = [];
  for (let i = 1; i <= 7; i++) {
    roster.bench.push(
      JSON.parse(document.getElementById(`bench-${i}`).value)
    );
  }

  const resp = await fetch(`/api/teams/${teamId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ roster })
  });
  console.log('  PUT /api/teams/${teamId} →', resp.status);

  await loadRoster(teamId);
  if (resp.ok) {
    await loadRoster(teamId);
    alert('Roster saved!');
  }
  else console.error('saveRoster failed', await resp.text());
}

function showRosterSummary(roster) {
  rosterList.innerHTML = '';               
  ['QB','RB1','RB2','WR1','WR2','TE','K'].forEach(key => {
    const p = roster[key];
    if (p) {
      const li = document.createElement('li');
      li.textContent = `${key}: ${p.name} (${p.team})`;
      rosterList.appendChild(li);
    }
  });
  roster.bench.forEach((p, idx) => {
    if (p) {
      const li = document.createElement('li');
      li.textContent = `Bench ${idx+1}: ${p.name} (${p.team})`;
      rosterList.appendChild(li);
    }
  });
  rosterDisplay.style.display = 'block';
}

async function loadAllTeamsSummaries() {
  allTeamsList.innerHTML = '';
  const teams = await fetch('/api/teams').then(r => r.json());
  for (const { id, name } of teams) {
    const roster = await fetch(`/api/teams/${id}`).then(r => r.json());

    const card = document.createElement('div');
    card.className = 'team-card';

    const h3 = document.createElement('h3');
    h3.textContent = name;
    card.appendChild(h3);

    const ul = document.createElement('ul');
    // starters
    ['QB','RB1','RB2','WR1','WR2','TE','K'].forEach(key => {
      const p = roster[key];
      if (p) {
        const li = document.createElement('li');
        li.textContent = `${key}: ${p.name} (${p.team})`;
        ul.appendChild(li);
      }
    });
    roster.bench.forEach((p,i) => {
      if (p) {
        const li = document.createElement('li');
        li.textContent = `Bench ${i+1}: ${p.name} (${p.team})`;
        ul.appendChild(li);
      }
    });
    card.appendChild(ul);

    const btn = document.createElement('button');
    btn.textContent = 'Edit This Team';
    btn.onclick = () => {
      document.getElementById('team-select').value = id;
      selectTeam({ target: { value: id, options: [{}, { text: name }] } });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    };
    card.appendChild(btn);

    allTeamsList.appendChild(card);
  }
}