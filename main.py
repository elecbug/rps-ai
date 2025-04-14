# Rock-Paper-Scissors AI Game (Cleaned Version)

from flask import Flask, request, jsonify, render_template
import random
from collections import defaultdict, deque

app = Flask(__name__)

# --- Game Configurations ---

move_mapping = {"1": "가위", "2": "바위", "3": "보"}
counter = {"가위": "바위", "바위": "보", "보": "가위"}

difficulty_settings = {
    'easy': {'random_rate': 0.99, 'bait_rate': 0.0, 'memory_depth': 1, 'advanced_strategy': False, 'adaptive_depth': False},
    'normal': {'random_rate': 0.75, 'bait_rate': 0.05, 'memory_depth': 10, 'advanced_strategy': False, 'adaptive_depth': False},
    'hard': {'random_rate': 0.85, 'bait_rate': 0.05, 'memory_depth': 20, 'advanced_strategy': False, 'adaptive_depth': False},
    'expert': {'random_rate': 0.95, 'bait_rate': 0.05, 'memory_depth': 100, 'advanced_strategy': False, 'adaptive_depth': False},
}

# --- Game State ---

difficulty = 'normal'
pattern_change_count = 0
player_history = []
ngram_stats = defaultdict(lambda: defaultdict(int))
history_window = deque(maxlen=difficulty_settings[difficulty]['memory_depth'])

ai_win = player_win = draw = round_num = 0
next_ai_move = None
previous_pattern = None
pattern_change_detected = False

# --- AI Core Logic ---

def is_single_move_pattern():
    if len(player_history) < 5:
        return False
    return all(move == player_history[-1] for move in player_history[-5:])

def basic_ai_predict(settings, strategy_log):
    if random.random() < settings['random_rate']:
        choice = random.choice(list(counter.keys()))
        strategy_log = f"전략: 무작위 선택\nAI 선택: {choice}"
        return choice, strategy_log

    if len(history_window) < history_window.maxlen:
        choice = random.choice(list(counter.keys()))
        strategy_log = f"전략: 데이터 부족 - 무작위 선택\nAI 선택: {choice}"
        return choice, strategy_log

    pattern = tuple(history_window)
    next_move_stats = ngram_stats.get(pattern, {})

    if not next_move_stats and len(pattern) > 1:
        reduced_pattern = pattern[1:]
        next_move_stats = ngram_stats.get(reduced_pattern, {})
        if next_move_stats:
            strategy_log += "전략: 부분 패턴 활용 (fallback)\n"
            pattern = reduced_pattern

    if not next_move_stats:
        choice = random.choice(list(counter.keys()))
        strategy_log += f"전략: 패턴 없음 - 무작위 선택\nAI 선택: {choice}"
        return choice, strategy_log

    predicted_player_move = max(next_move_stats, key=next_move_stats.get)
    strategy_log += f"예측한 플레이어 다음 수: {predicted_player_move}\n"

    if random.random() < settings['bait_rate']:
        choice = counter[counter[predicted_player_move]]
        strategy_log += f"전략: 미끼 전략\nAI 선택: {choice}"
        return choice, strategy_log

    choice = counter[predicted_player_move]
    strategy_log += f"전략: 패턴 기반 대응\nAI 선택: {choice}"
    return choice, strategy_log

def advanced_ai_predict(settings, strategy_log):
    global pattern_change_detected

    pattern = tuple(history_window)
    next_move_stats = ngram_stats.get(pattern, {})

    if not next_move_stats and len(pattern) > 1:
        reduced_pattern = pattern[1:]
        next_move_stats = ngram_stats.get(reduced_pattern, {})
        if next_move_stats:
            strategy_log += "전략: 적극적 부분 패턴 활용\n"
            pattern = reduced_pattern

    if pattern_change_detected:
        pattern_change_detected = False
        choice = random.choice(list(counter.keys()))
        strategy_log += "전략: 패턴 변화 감지 - 학습 재조정\nAI 선택: {choice}"
        return choice, strategy_log

    if not next_move_stats:
        choice = random.choice(list(counter.keys()))
        strategy_log += "전략: 패턴 없음 - 무작위 선택\nAI 선택: {choice}"
        return choice, strategy_log

    predicted_player_move = max(next_move_stats, key=next_move_stats.get)
    strategy_log += f"예측한 플레이어 다음 수: {predicted_player_move}\n"

    if random.random() < settings['bait_rate']:
        choice = counter[counter[predicted_player_move]]
        strategy_log += f"전략: 적극적 미끼 전략\nAI 선택: {choice}"
        return choice, strategy_log

    if random.random() < settings['random_rate']:
        choice = random.choice(list(counter.keys()))
        strategy_log += f"전략: 불규칙성 추가 - 무작위 선택\nAI 선택: {choice}"
        return choice, strategy_log

    choice = counter[predicted_player_move]
    strategy_log += f"전략: 고급 패턴 대응\nAI 선택: {choice}"
    return choice, strategy_log

def ai_predict():
    settings = difficulty_settings[difficulty]
    if settings.get('advanced_strategy', False):
        return advanced_ai_predict(settings, "")
    return basic_ai_predict(settings, "")

# --- Game Logic ---

def judge(player, ai):
    if player == ai:
        return "무승부"
    if (player, ai) in [("가위", "바위"), ("바위", "보"), ("보", "가위")]:
        return "AI 승리"
    return "플레이어 승리"

def update_ngram(player_move):
    if len(history_window) == history_window.maxlen:
        pattern = tuple(history_window)
        ngram_stats[pattern][player_move] += 1
    history_window.append(player_move)

def detect_pattern_change():
    global previous_pattern, pattern_change_detected, pattern_change_count
    if len(player_history) < 10:
        return
    recent_moves = player_history[-10:]
    most_common = max(set(recent_moves), key=recent_moves.count)
    if previous_pattern and previous_pattern != most_common:
        pattern_change_detected = True
        pattern_change_count += 1
    previous_pattern = most_common

def adjust_memory_depth():
    global history_window, difficulty_settings, difficulty, pattern_change_count

    if not difficulty_settings[difficulty].get('adaptive_depth', False):
        return

    current_depth = history_window.maxlen
    if pattern_change_count >= 3 and current_depth < 30:
        history_window = deque(maxlen=current_depth + 1)
    elif pattern_change_count == 0 and current_depth > 2:
        history_window = deque(maxlen=current_depth - 1)

# --- Flask Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['GET'])
def predict():
    global next_ai_move
    next_ai_move = ai_predict()
    return jsonify({'ai_move': next_ai_move})

@app.route('/play', methods=['POST'])
def play():
    global ai_win, player_win, draw, round_num, next_ai_move

    player_choice = request.json.get('move')
    player_move = move_mapping.get(player_choice)
    ai_move = next_ai_move

    result = judge(player_move, ai_move)

    player_history.append(player_move)
    update_ngram(player_move)
    detect_pattern_change()
    adjust_memory_depth()

    if result == "AI 승리":
        ai_win += 1
    elif result == "플레이어 승리":
        player_win += 1
    else:
        draw += 1

    round_num += 1
    next_ai_move, move_strategy_log = ai_predict()

    strategy_log = f"""
AI 전략 로그
--------------
난이도: {difficulty}
랜덤 선택 확률: {difficulty_settings[difficulty]['random_rate']}
미끼 전략 확률: {difficulty_settings[difficulty]['bait_rate']}
메모리 깊이: {history_window.maxlen}
고급 전략 사용: {difficulty_settings[difficulty].get('advanced_strategy', False)}
적응형 메모리 깊이: {difficulty_settings[difficulty].get('adaptive_depth', False)}

{move_strategy_log.strip()}
"""

    return jsonify({
        'player_move': player_move,
        'ai_move': ai_move,
        'result': result,
        'ai_win': ai_win,
        'player_win': player_win,
        'draw': draw,
        'round_num': round_num - 1,
        'next_ai_move': next_ai_move,
        'strategy_log': strategy_log.strip()
    })

@app.route('/reset', methods=['POST'])
def reset():
    global ai_win, player_win, draw, round_num, next_ai_move, player_history, ngram_stats, history_window, previous_pattern, pattern_change_detected

    ai_win = player_win = draw = round_num = 0
    next_ai_move = None
    player_history.clear()
    ngram_stats.clear()
    history_window = deque(maxlen=difficulty_settings[difficulty]['memory_depth'])
    previous_pattern = None
    pattern_change_detected = False

    return jsonify({'message': '게임이 초기화되었습니다.'})

@app.route('/set_difficulty', methods=['POST'])
def set_difficulty():
    global difficulty, history_window
    data = request.json
    difficulty = data.get('difficulty', 'normal')
    history_window = deque(maxlen=difficulty_settings[difficulty]['memory_depth'])
    return jsonify({'message': f'난이도 {difficulty}로 설정되었습니다.'})

@app.route('/set_custom_difficulty', methods=['POST'])
def set_custom_difficulty():
    global difficulty, difficulty_settings, history_window
    data = request.json

    difficulty = 'custom'
    difficulty_settings['custom'] = {
        'random_rate': data.get('random_rate', 0.5),
        'bait_rate': data.get('bait_rate', 0.1),
        'memory_depth': data.get('memory_depth', 2),
        'advanced_strategy': data.get('advanced_strategy', False),
        'adaptive_depth': data.get('adaptive_depth', False)
    }
    history_window = deque(maxlen=difficulty_settings['custom']['memory_depth'])

    return jsonify({'message': '커스텀 난이도 설정 완료'})

@app.route('/get_difficulty', methods=['GET'])
def get_difficulty():
    return jsonify({'difficulty': difficulty})

if __name__ == '__main__':
    app.run(debug=True)