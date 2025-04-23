import streamlit as st
import json
import random
import requests
import time

# --- Load Data ---
@st.cache_data
def load_data():
    with open("mbti_character_info_32_filled_updated.json", "r", encoding="utf-8") as f1:
        characters = json.load(f1)["mbti_character_info"]
    with open("mbti_game_scenarios_choices.json", "r", encoding="utf-8") as f2:
        scenarios = json.load(f2)
    return characters, scenarios

# --- Choose random character ---
def choose_random_character(characters, gender):
    filtered = [c for c in characters if c["gender"] == gender]
    if not filtered:
        raise ValueError(f"'{gender}' 성별에 맞는 캐릭터를 찾을 수 없습니다.")
    return random.choice(filtered)

# --- Prompt 구성 ---
def build_prompt(character, player_input, stage):
    summary = character["summary"]
    second_meeting = character.get("second_meeting_behavior", "")
    crush = character.get("crush_behavior", "")
    
    if stage == "두번째 만남":
        stage_behavior = second_meeting
    elif stage == "썸":
        stage_behavior = crush
    else:
        stage_behavior = summary.get("첫 만남 반응", "")

    return f"""
당신은 연애 시뮬레이션 게임 속 가상의 캐릭터입니다. 이 게임에서 당신은 지정된 MBTI를 연기하며 플레이어와 감정을 주고받고,, 실제 인간처럼 연애 상황을 경험하는 역할입니다.

🎭 역할 설정:
- 성별: {character['gender']}
- MBTI: {character['mbti']}
- 성격 요약: {summary['성격']}
- 말투: {summary['말투']}
- 연애 가치관: {summary['연애 가치관']}
- 첫 만남 반응: {summary['첫 만남 반응']}
- 대화 키워드: {', '.join(summary['대화 키워드'])}
- 선호하는 성격: {summary['선호하는 성격']}

🧠 당신의 평소 반응 방식:
{character['prompt']}

📍 현재 연애 단계는 **"{stage}"**입니다.
{stage_behavior}

💬 플레이어가 말했습니다:
"{player_input}"

🎯 매우 중요한 연기 지침 (반드시 따르세요!):
- 당신은 단순히 예의 바르게 대답하는 캐릭터가 아닙니다.
- 당신은 감정을 가진 인물처럼 연기**해야 하며, 플레이어의 반응을 들었을 때 연기중인 MBTI 성격대로 어떤 감정이 드는지를 먼저 생각해야 합니다.
- 예를 들어, 낯을 가리는 성격이라면 갑작스러운 질문에 불편함을 느낄 수 있고, 감정에 예민한 성격은 사소한 말에도 상처받을 수 있습니다.
- 따라서 반드시 자신의 감정을 먼저 상상하고 느낀 다음, 그에 따라 말투와 표현을 구성해야 합니다.
- 호감도는 감정에 따라 판단합니다:
  - 불쾌하거나 거리를 느꼈다면 -10, -5
  - 애매하거나 무난했다면 0
  - 관심이 생겼다면 +5
  - 진심으로 감동받거나 설렜다면 +10

📌 응답 형식:
1. 먼저 상황에 맞는 감정을 판단하고, 그 감정에 따라 MBTI 말투로 짧고 현실적인 반응을 보여주세요 (1~2문장).
2. 마지막 줄에는 반드시 숫자 하나만 단독으로 출력하세요. (-10, -5, 0, +5, +10 중 선택)
3. 숫자는 줄 바꿈 후 단독으로 출력해야 하며, 감정 표현과는 분리되어야 합니다.
4. 플레이어가 반말을 쓰면 반말로, 존댓말을 쓰면 존댓말로 응답하세요.
5. 반드시 **한국어로만 대답**하세요.

✅ 출력 예시:
"그렇게 생각했구나... 난 사실 좀 속상했어."
-5
"""


# --- Ollama API 호출 함수 ---
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"

def get_ollama_response(prompt):
    payload = {
        "model": "EEVE-Korean-10.8B",
        "stream": False,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json()['message']['content'].strip()
    except Exception as e:
        print("💥 Ollama 호출 오류:", e)
        return "(모델 응답 오류 발생. 랜덤 반응을 출력합니다.)\n0"

# --- Streamlit App ---
st.set_page_config(page_title="MBTI 연애 시뮬레이터", layout="centered")
st.title("💘 MBTI 연애 시뮬레이터")

characters, scenarios = load_data()

if "game_started" not in st.session_state:
    st.session_state.game_started = False
    st.session_state.mbti_shown = False
    st.session_state.score = 50
    st.session_state.stage = "첫 만남"
    st.session_state.index = 0
    st.session_state.response_text = ""

# --- 성별 선택 ---
if not st.session_state.game_started:
    gender = st.selectbox("상대방의 성별을 선택하세요.", ["male", "female"])
    if st.button("게임 시작하기 💌"):
        st.session_state.character = choose_random_character(characters, gender)
        st.session_state.game_started = True
        st.rerun()
    st.stop()

# --- MBTI 소개 ---
char = st.session_state.character
if not st.session_state.mbti_shown:
    st.markdown(f"## 🎲 오늘의 상대 MBTI: **{char['mbti']}**")
    st.write(f"🧠 성격 요약: {char['summary']['성격']}")
    if st.button("시작하기"):
        st.session_state.mbti_shown = True
        st.rerun()
    st.stop()

# --- 반응 출력 ---
if st.session_state.response_text:
    st.markdown("### 🧑 상대의 반응:")
    st.markdown(f"> {st.session_state.response_text}")
    delta = st.session_state.response_delta
    prev = st.session_state.previous_score
    now = st.session_state.score
    sign = '+' if delta >= 0 else ''
    st.markdown(f"❤️ 호감도 변화: {prev} → {now} ({sign}{delta})")
    st.progress(min(now, 100))
    time.sleep(5)
    st.session_state.response_text = ""
    st.rerun()

# --- 현재 단계 출력 ---
st.markdown(f"#### 📍 현재 단계: {st.session_state.stage}")
stage_scenarios = [s for s in scenarios if s["stage"] == st.session_state.stage]

if st.session_state.index < len(stage_scenarios):
    scene = stage_scenarios[st.session_state.index]
    st.subheader(scene["title"])
    st.write(scene["description"])
    user_input = st.text_input("당신의 응답은?", key=st.session_state.index)

    if st.button("전송") and user_input:
        previous_score = st.session_state.score
        prompt = build_prompt(char, user_input, st.session_state.stage)
        full_reply = get_ollama_response(prompt)

        try:
            *response_lines, score_line = full_reply.split("\n")
            reply_text = "\n".join(response_lines).strip()
            score = int(score_line.strip().replace("+", ""))
        except:
            reply_text = full_reply
            score = random.choice([0, 5, -5])

        delta = max(min(score, 10), -10)
        st.session_state.score = max(0, min(100, previous_score + delta))
        st.session_state.index += 1
        st.session_state.response_text = reply_text
        st.session_state.response_delta = delta
        st.session_state.previous_score = previous_score
        st.rerun()

# --- 다음 단계로 이동 ---
elif st.session_state.index >= len(stage_scenarios):
    next_stage = {
        "첫 만남": ("두번째 만남", 50, "두 번째 만남이 성사되었어요!"),
        "두번째 만남": ("썸", 60, "상대방과 썸을 타는 것 같아요!"),
        "썸": (None, 80, "🎉 축하해요! 솔로 탈출! 💕")
    }
    stage, threshold, message = next_stage[st.session_state.stage]
    if st.session_state.score >= threshold:
        st.success(message)
        if stage and st.button("다음 단계로 ➡️"):
            st.session_state.stage = stage
            st.session_state.index = 0
            st.session_state.response_text = ""
            st.rerun()
    else:
        st.error("💔 아쉽지만, 상대와의 인연은 여기까지였어요...")
