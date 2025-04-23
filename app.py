import streamlit as st
import json
import random
import requests
import os
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
def build_prompt(character_prompt, player_input, stage):
    return f"""당신은 연애 시뮬레이션 게임에 등장하는 가상의 캐릭터입니다. 
게임은 플레이어와의 감정 교류를 중심으로 진행되며, 당신은 플레이어의 연애 상대 역할을 수행합니다.

🧠 당신은 다음과 같은 MBTI 성격을 가진 캐릭터로 연기해야 합니다:
{character_prompt}

📍 현재 연애 단계는 **"{stage}"**입니다:
- 첫 만남: 아직 어색하고 조심스러운 분위기. 첫인상이 중요합니다.
- 두 번째 만남: 어느 정도 친밀감이 형성되어 있고, 더 자연스러운 감정 표현이 가능합니다.
- 썸 단계: 서로 감정이 무르익고 있으며, 관계에 대한 진지한 대화도 가능합니다.

💬 플레이어가 당신에게 다음과 같은 말을 했습니다:
\"{player_input}\"

📝 당신의 응답은 다음의 형식을 따라야 합니다:

1. 먼저 MBTI 성격을 기반으로, **해당 상황에 어울리는 자연스럽고 감정이 담긴 말투로 대답**하세요.  
말투는 너무 딱딱하지 않고, 실제 연애 상황에서 나올 법한 말처럼 구성하세요.

2. 그 다음 줄에, 플레이어의 발언을 듣고 **당신이 느낀 감정에 따라 호감도 변화를 숫자로 표현**하세요.  
가능한 숫자: -10, -5, 0, +5, +10  
(기분이 상했거나 거리감을 느꼈다면 -10/-5, 별 감흥이 없었다면 0, 긍정적인 감정이라면 +5/+10)

3. 반드시 마지막 줄에는 아무 말 없이 **숫자 하나만 출력**해야 합니다.  
숫자는 따로 줄 바꿈해서 출력하세요.

4. 상대방이 반말을 하면 반말로, 존댓말을 하면 존댓말로 대답하세요. (한국어로만 대화하세요)

출력 예시:
\"좋은 질문이네. 그런 생각을 하다니 너 정말 섬세한 것 같아. 나 이런 이야기 좋아해 :)\"\n+5
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
        print("Ollama 호출 오류:", e)
        return "(모델 응답 오류 발생. 랜덤 반응을 출력합니다.)\n0"

# --- Streamlit App ---
st.set_page_config(page_title="MBTI 연애 시뮬레이터", layout="centered")
st.title("💘 MBTI 연애 시뮬레이터 두근두근 마음을 여는 대화")

characters, scenarios = load_data()

if "game_started" not in st.session_state:
    st.session_state.game_started = False
    st.session_state.mbti_shown = False
    st.session_state.score = 50
    st.session_state.stage = "첫 만남"
    st.session_state.index = 0
    st.session_state.response_text = ""
    st.session_state.ready_for_next = False

# --- 게임 시작 전: 성별 선택 ---
if not st.session_state.game_started:
    gender = st.selectbox("상대방의 성별을 선택하세요. MBTI는 랜덤입니다.", ["male", "female"])
    if st.button("게임 시작하기 💌"):
        st.session_state.character = choose_random_character(characters, gender)
        st.session_state.game_started = True
        st.session_state.selected_gender = gender
        st.rerun()
    st.stop()

# --- MBTI 소개 후 시작 버튼 ---
char = st.session_state.character
if not st.session_state.mbti_shown:
    st.markdown(f"## 🎲 오늘의 상대 MBTI: **{char['mbti']}**")
    st.write(f"🧠 성격 요약: {char['summary']['성격']}")
    if st.button("시작하기"):
        st.session_state.mbti_shown = True
        st.rerun()
    st.stop()

# --- 반응 출력이 있는 경우 ---
if st.session_state.response_text:
    st.markdown("### 🧑 상대의 반응:")
    st.markdown(f"> {st.session_state.response_text}")
    delta = st.session_state.response_delta
    prev = st.session_state.previous_score
    now = st.session_state.score
    sign = '+' if delta >= 0 else ''
    st.markdown(f"❤️ 호감도 변화: {prev} → {now} ({sign}{delta})")
    st.progress(min(now, 100))
    time.sleep(3)
    st.session_state.response_text = ""
    st.rerun()

# --- 현재 단계 상황 출력 ---
st.markdown(f"#### 📍 현재 단계: {st.session_state.stage}")
stage_scenarios = [s for s in scenarios if s["stage"] == st.session_state.stage]

if st.session_state.index < len(stage_scenarios):
    scene = stage_scenarios[st.session_state.index]
    st.subheader(f"{scene['title']}")
    st.write(scene["description"])

    user_input = st.text_input("당신의 응답은?", key=st.session_state.index)

    if st.button("전송") and user_input:
        previous_score = st.session_state.score
        prompt = build_prompt(char["prompt"], user_input, st.session_state.stage)

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

# --- 다음 단계로 넘어갈지 판단
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
