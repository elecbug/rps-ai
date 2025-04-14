let previewEnabled = false;
let nextAIMove = null;

// 누적 그래프 데이터
const roundLabels = [];
const aiWins = [];
const playerWins = [];
const draws = [];

const ctx = document.getElementById('scoreChart').getContext('2d');
const scoreChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: roundLabels,
        datasets: [
            {
                label: 'AI 승리',
                data: aiWins,
                borderColor: 'red',
                fill: false
            },
            {
                label: '플레이어 승리',
                data: playerWins,
                borderColor: 'blue',
                fill: false
            },
            {
                label: '무승부',
                data: draws,
                borderColor: 'gray',
                fill: false
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        scales: {
            x: {
                title: {
                    display: true,
                    text: '라운드'
                }
            },
            y: {
                title: {
                    display: true,
                    text: '누적 승수'
                },
                beginAtZero: true
            }
        }
    }
});

function updateCustomLabel(id) {
    const value = document.getElementById(id).value;
    document.getElementById(id + 'Label').innerText = value;
}

function updateChart(data) {
    roundLabels.push(data.round_num);
    aiWins.push(data.ai_win);
    playerWins.push(data.player_win);
    draws.push(data.draw);

    scoreChart.update();
}

function togglePreview() {
    previewEnabled = !previewEnabled;
    document.getElementById('preview-status').innerText = previewEnabled ? 'ON' : 'OFF';
    updatePreviewDisplay();
}

function updatePreviewDisplay() {
    const previewText = document.getElementById('ai-preview');
    if (previewEnabled && nextAIMove) {
        previewText.innerText = `다음 AI 패: ${nextAIMove}`;
    } else {
        previewText.innerText = previewEnabled ? 'AI 패를 대기 중...' : 'OFF 상태입니다.';
    }
}

function fetchNextAIMove() {
    fetch('/predict')
        .then(response => response.json())
        .then(data => {
            nextAIMove = data.ai_move;
            updatePreviewDisplay();
        });
}

function playGame(move) {
    fetch('/play', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ move: move })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('strategy-log').textContent = data.strategy_log;
        document.getElementById('result').innerText =
            `플레이어: ${data.player_move} | AI: ${data.ai_move} -> ${data.result}`;

        document.getElementById('score').innerText =
            `AI: ${data.ai_win} | 플레이어: ${data.player_win} | 무승부: ${data.draw}`;

        nextAIMove = data.next_ai_move;
        updatePreviewDisplay();

        updateChart(data);
    });
}

function setDifficulty() {
    const selectedDifficulty = document.getElementById('difficulty').value;
    const customSettings = document.getElementById('custom-settings');

    if (selectedDifficulty === 'custom') {
        customSettings.style.display = 'block';
    } else {
        customSettings.style.display = 'none';
        fetch('/set_difficulty', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ difficulty: selectedDifficulty })
        }).then(() => {
            console.log('난이도 변경 완료:', selectedDifficulty);
            fetchNextAIMove();
        });
    }
}

function applyCustomDifficulty() {
    const randomRate = parseFloat(document.getElementById('randomRate').value);
    const baitRate = parseFloat(document.getElementById('baitRate').value);
    const memoryDepth = parseInt(document.getElementById('memoryDepth').value, 10);
    const advancedStrategy = document.getElementById('advancedStrategy').checked;
    const adaptiveDepth = document.getElementById('adaptiveDepth').checked;

    fetch('/set_custom_difficulty', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            random_rate: randomRate,
            bait_rate: baitRate,
            memory_depth: memoryDepth,
            advanced_strategy: advancedStrategy,
            adaptive_depth: adaptiveDepth
        })
    }).then(() => {
        console.log('커스텀 난이도 적용 완료');
        fetchNextAIMove();
    });
}

function toggleStrategyLog() {
    const log = document.getElementById('strategy-log');
    log.style.display = log.style.display === 'none' ? 'block' : 'none';
}

// 시작 시 AI 패 가져오기
fetchNextAIMove();

// 페이지 로드 시 서버 초기화
window.addEventListener('load', () => {
    fetch('/reset', { method: 'POST' })
        .then(() => {
            console.log('서버 상태가 초기화되었습니다.');
            fetchNextAIMove();
        });
    fetch('/get_difficulty')
        .then(response => response.json())
        .then(data => {
            document.getElementById('difficulty').value = data.difficulty;
            setDifficulty(); // 드롭다운 초기화 후 커스텀 패널 반영
        });
    
});