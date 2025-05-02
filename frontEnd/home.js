document.addEventListener('DOMContentLoaded', function() {
    const trendingPlayers = [
        { name: "Christian McCaffrey", pos: "RB", team: "SF", points: 28.5, trend: "up" },
        { name: "Tyreek Hill", pos: "WR", team: "MIA", points: 24.1, trend: "up" },
        { name: "Josh Allen", pos: "QB", team: "BUF", points: 22.3, trend: "down" },
        { name: "Bijan Robinson", pos: "RB", team: "ATL", points: 18.7, trend: "new" }
    ];

    const container = document.getElementById('trending-players');
    
    trendingPlayers.forEach(player => {
        const trendIcon = player.trend === 'up' ? '📈' : 
                         player.trend === 'down' ? '📉' : '🆕';
        
        container.innerHTML += `
            <div class="trending-player">
                <div class="player-info">
                    <h3>${player.name}</h3>
                    <span class="player-meta">${player.pos} • ${player.team}</span>
                </div>
                <div class="player-points ${player.trend}">
                    ${trendIcon} ${player.points} PPG
                </div>
            </div>
        `;
    });
});