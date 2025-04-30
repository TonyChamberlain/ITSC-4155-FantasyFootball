// TODO: Replace this hardcoded roster with fetch('/api/myteam') later

/*

let roster = {};

fetch('/api/myteam')
  .then(response => response.json())
  .then(data => {
    roster = data;
    updateDisplay();
  })
  .catch(err => console.error("Error loading roster:", err));
// add connection with api and deleat const roster 



*/
const roster = {
    QB: { name: "Josh Allen", yards: 300, tds: 2, pos: "QB", team: "Buffalo Bills" },
    RB1: { name: "Christian McCaffrey", yards: 120, tds: 1, pos: "RB", team: "San Francisco 49ers" },
    RB2: { name: "Derrick Henry", yards: 80, tds: 0, pos: "RB", team: "Baltimore Ravens" },
    WR1: { name: "Tyreek Hill", yards: 100, tds: 1, pos: "WR", team: "Miami Dolphins" },
    WR2: { name: "CeeDee Lamb", yards: 95, tds: 1, pos: "WR", team: "Dallas Cowboys" },
    TE: { name: "Travis Kelce", yards: 60, tds: 1, pos: "TE", team: "Kansas City Chiefs" },
    FLEX: { name: "Amon-Ra St. Brown", yards: 70, tds: 0, pos: "WR", team: "Detroit Lions" },
    K: { name: "Justin Tucker", points: 10, pos: "K", team: "Baltimore Ravens" },
    DEF: { name: "Jalen Milroe", sacks: 3, turnovers: 1, tds: 1, pos: "DEF", team: "San Francisco 49ers" },
  
    // Bench
    QB2: { name: "Lamar Jackson", yards: 250, tds: 1, pos: "QB", team: "Baltimore Ravens" },
    RB3: { name: "Austin Ekeler", yards: 60, tds: 0, pos: "RB", team: "Los Angeles Chargers" },
    WR3: { name: "Stefon Diggs", yards: 85, tds: 1, pos: "WR", team: "New England Patriots" },
    TE2: { name: "George Kittle", yards: 40, tds: 0, pos: "TE", team: "San Francisco 49ers" },
    FLEX2: { name: "Bijan Robinson", yards: 50, tds: 0, pos: "RB", team: "Atlanta Falcons" },
    Fill1: { name: "Brandon Aiyuk", yards: 77, tds: 1, pos: "WR", team: "San Francisco 49ers" },
    Fill2: { name: "Eagles DEF", sacks: 2, turnovers: 2, tds: 0, pos: "DEF", team: "Philadelphia Eagles" }
  };
  
  function calculatePoints(player) {
    if (!player) return 0;
    switch (player.pos) {
      case "QB":
      case "RB":
      case "WR":
      case "TE":
        return Math.floor(player.yards / 50) + player.tds * 3;
      case "K":
        return player.points || 0;
      case "DEF":
        return (player.sacks || 0) + (player.turnovers || 0) * 2 + (player.tds || 0) * 6;
      default:
        return 0;
    }
  }
  
  function updateDisplay() {
    let total = 0;
  
    for (const pos in roster) {
      const player = roster[pos];
      const span = document.querySelector(`span[data-pos="${pos}"]`);
      if (span && player) {
        span.textContent = `${player.name} - ${player.team} (${calculatePoints(player)} pts)`;
        if (!pos.includes("2") && !pos.includes("3") && !pos.includes("Fill")) {
          total += calculatePoints(player); // Only count starters
        }
      }
    }
  
    document.getElementById("total-points").textContent = total;
  }
  
  // Later: replace with fetch('/api/myteam').then(...).catch(...)
  document.addEventListener("DOMContentLoaded", updateDisplay);
  