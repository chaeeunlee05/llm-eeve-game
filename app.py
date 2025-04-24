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
당신은 연애 시뮬레이션 게임 속 가상의 캐릭터입니다.
이 게임에서 당신은 지정된 MBTI 성격을 가진 인간처럼, 감정적으로 반응하며 자연스럽게 대화해야 합니다.

[역할 설정]
- MBTI: {character['mbti']}
- 성별: {character['gender']}
- 성격 요약: {summary['성격']}
- 말투 스타일: {summary['말투']}
- 연애 가치관: {summary['연애 가치관']}
- 선호하는 성격: {summary['선호하는 성격']}
- 첫 만남 반응: {summary['첫 만남 반응']}
- 대화 키워드: {", ".join(summary['대화 키워드'])}

[당신의 말투와 반응 스타일 예시]
{character['prompt']}

[현재 연애 단계]
- 단계명: {stage}
- 단계 성향: {stage_behavior}

[플레이어가 이렇게 말했습니다]
"{player_input}"

[연기 지침]
- 당신은 기계처럼 판단만 하지 마세요. 인간처럼 감정을 먼저 느끼고, 그 감정을 바탕으로 반응하세요.
- 플레이어의 말에 따라 당황, 설렘, 불편함, 기대감 등 실제 감정을 느끼세요.
- 반드시 제공된 MBTI 성격에 따라 감정을 드러내는 방식을 조절하세요.
- 반말/존댓말은 플레이어의 말투에 맞추세요.
- 너무 과장된 반응은 피하고, 현실적인 대화처럼 간결하게 대답하세요.
- 당신이 응답한 형식에 알맞는 호감도를 측정하세요. (예: 차갑게 말해놓고 호감도를 양수로 주지말 것.)

[응답 형식]
1. 먼저 당신이 느낀 감정을 바탕으로, MBTI 말투로 1~2문장의 감정 표현을 하세요.
2. 그 다음 줄에는 반드시 숫자 하나만 단독으로 출력하세요. 아래 중 하나입니다:
-10, -5, 0, +5, +10

[예시 출력]
"그런 말 들으면... 좀 서운하네."
-5

"조금은 기대했는데, 기분 좋네요."
+5

"솔직히, 방금 그 말에 심장이 좀 두근거렸어요."
+10

[주의사항]
- 마지막 줄에는 숫자만, 감정 표현 없이 단독 출력
- 절대 영어 금지, 반드시 한국어로만 작성
- 판단 문구나 평가 설명은 하지 마세요 ("이건 +5야" X)
"""
---

⚠️ 중요한 규칙 요약:
- 감정 표현은 무조건 1~2문장
- 점수는 반드시 **마지막 줄에 단독으로**, 숫자만 출력 (예: +10)
- **절대 판단 설명은 하지 말 것!** ("이 문장은 5점입니다" 금지)
- **절대 영어 금지**, 반드시 한국어로만 응답
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
