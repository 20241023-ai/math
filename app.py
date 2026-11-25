
import streamlit as st
from google import genai
from PIL import Image
from io import BytesIO
import datetime

# =========================================================
# 1. 페이지 설정
# =========================================================
st.set_page_config(
    page_title="수학문제 해설",
    page_icon="📐",
    layout="wide"
)

# =========================================================
# 2. 라이트 테마 디자인
# =========================================================
st.markdown("""
<style>
.stApp {
    background-color: #ffffff !important;
    color: #111827 !important;
}

.block-container {
    max-width: 1100px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

p, li, label, span, div {
    color: #111827;
}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] strong {
    color: #111827 !important;
}

h1, h2, h3, h4, h5, h6 {
    color: #111827 !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #f8fafc !important;
    border-right: 1px solid #e5e7eb;
}

[data-testid="stSidebar"] * {
    color: #111827 !important;
}

/* Captions */
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p {
    color: #4b5563 !important;
}

/* Inputs */
input, textarea {
    color: #111827 !important;
    background-color: #ffffff !important;
}

[data-baseweb="input"] {
    background-color: #ffffff !important;
}

[data-baseweb="select"] * {
    color: #111827 !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background-color: #f9fafb !important;
    border: 1px dashed #94a3b8 !important;
    border-radius: 15px;
    padding: 10px;
}

[data-testid="stFileUploader"] * {
    color: #111827 !important;
}

/* Buttons */
div.stButton > button {
    border-radius: 12px;
    min-height: 45px;
    font-weight: 600;
    background-color: #eef2ff;
    border: 1px solid #c7d2fe;
    color: #3730a3 !important;
}

div.stButton > button p,
div.stButton > button span {
    color: #3730a3 !important;
}

div.stButton > button:hover {
    background-color: #e0e7ff;
    border-color: #818cf8;
}

/* Download button */
[data-testid="stDownloadButton"] button {
    background-color: #eef2ff !important;
    color: #3730a3 !important;
}

[data-testid="stDownloadButton"] button * {
    color: #3730a3 !important;
}

/* Hero */
.hero {
    padding: 30px;
    border-radius: 20px;
    background: linear-gradient(135deg, #eef2ff, #f8fafc);
    border: 1px solid #c7d2fe;
    margin-bottom: 25px;
}

.hero h1 {
    color: #111827 !important;
    margin-bottom: 10px;
    font-size: 2.4rem;
}

.hero p {
    color: #374151 !important;
    font-size: 1.05rem;
}

/* Expander */
[data-testid="stExpander"] {
    background-color: #ffffff !important;
    border: 1px solid #d1d5db !important;
    border-radius: 12px;
}

[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary * {
    color: #111827 !important;
}

/* Radio */
[data-testid="stRadio"] label,
[data-testid="stRadio"] p {
    color: #111827 !important;
}

/* Checkbox */
[data-testid="stCheckbox"] label,
[data-testid="stCheckbox"] p {
    color: #111827 !important;
}

/* Alerts */
[data-testid="stAlert"] * {
    color: #111827 !important;
}

/* Code */
[data-testid="stCode"] pre,
[data-testid="stCode"] code {
    color: #111827 !important;
    background-color: #f3f4f6 !important;
}

/* Divider */
hr {
    border-color: #e5e7eb !important;
}

/* Form */
[data-testid="stForm"] {
    background-color: #ffffff !important;
}

/* Chat */
[data-testid="stChatMessage"] {
    background-color: #f9fafb;
    border-radius: 12px;
}

/* Links */
a {
    color: #4f46e5 !important;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# 3. Gemini 클라이언트
# =========================================================
@st.cache_resource
def initialize_client():
    api_key = st.secrets["GEMINI_API_KEY"]
    return genai.Client(api_key=api_key)

try:
    client = initialize_client()
except Exception as e:
    st.error("Gemini API 키 설정을 확인해 주세요.")
    st.caption(str(e))
    st.stop()

MODEL_NAME = "gemini-3.1-flash-lite"

# =========================================================
# 4. 세션 상태 초기화
# =========================================================
defaults = {
    "solution": "",
    "uploaded_image": None,
    "history": [],
    "chat_history": [],
    "last_mode": "",
    "selected_history": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =========================================================
# 5. Gemini 호출 함수
# =========================================================
def ask_gemini(image, prompt):
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[image, prompt]
    )

    if not response.text:
        raise ValueError("AI가 빈 답변을 반환했습니다.")

    return response.text

# =========================================================
# 6. 프롬프트
# =========================================================
PROMPTS = {

    "상세 풀이": """
너는 친절하고 정확한 수학 전문 선생님이다.

이미지 속 수학 문제를 읽고 해결하라.

## 1. 문제 분석
문제의 조건과 구해야 하는 것을 정리한다.

## 2. 핵심 개념
필요한 개념, 정의, 공식 등을 설명한다.
공식을 사용하는 이유도 설명한다.

## 3. 단계별 풀이
풀이를 번호별로 나눈다.
수식이 만들어지는 이유를 설명한다.
계산 과정은 최대한 생략하지 않는다.

## 4. 검산 및 확인
가능한 경우 답이 맞는지 확인한다.

## 5. 최종 답
최종 답을 명확하게 표시한다.

학생이 원리를 이해할 수 있도록 설명한다.
한국어로 답하고 Markdown과 LaTeX를 사용한다.
""",

    "힌트": """
너는 학생이 스스로 문제를 해결하도록 돕는 수학 튜터이다.

이미지의 수학 문제를 분석하고 다음 형식으로 답변한다.

## 문제에서 알아야 할 것
문제의 조건과 구해야 하는 것을 정리한다.

## 첫 번째 힌트
문제를 시작할 수 있도록 핵심 개념을 알려준다.

## 다음 접근 방법
어떤 공식이나 방법을 생각해야 하는지 알려준다.

주의:
완전한 정답과 전체 풀이를 바로 공개하지 않는다.
학생이 직접 생각할 수 있도록 핵심적인 도움만 준다.

한국어로 답한다.
""",

    "다른 풀이": """
너는 수학 전문 선생님이다.

이미지 속 수학 문제를 해결하되,
가능한 경우 다른 접근 방법을 제시한다.

## 사용되는 아이디어
다른 방법을 사용하기 위해 필요한 개념을 설명한다.

## 다른 풀이 과정
수식과 논리를 단계별로 설명한다.

## 두 방법의 차이
두 풀이의 장점이나 차이를 간단히 설명한다.

## 최종 답
답을 명확하게 표시한다.

문제의 특성상 다른 풀이가 적절하지 않다면
억지로 새로운 방법을 만들지 말고 그 이유를 설명한다.

한국어로 답하고 Markdown과 LaTeX를 사용한다.
""",

    "유사 문제": """
너는 수학 교육 전문가이다.

첨부된 이미지의 문제를 분석하여
비슷한 유형의 연습 문제 3개를 만들어라.

각 문제는 원래 문제와 같은 핵심 개념을 연습하되
숫자, 조건, 표현을 적절히 바꾸어 구성한다.

## 유사 문제 1
문제를 제시한다.

## 유사 문제 2
문제를 제시한다.

## 유사 문제 3
문제를 제시한다.

## 정답
각 문제의 정답을 마지막에 모아서 표시한다.

정답만 제공하고 전체 풀이를 공개하지 않는다.
학생이 먼저 풀어볼 수 있도록 문제와 정답을 분리한다.

한국어로 작성한다.
""",

    "이해 확인 퀴즈": """
너는 수학 교육 전문가이다.

첨부된 수학 문제의 핵심 개념을 기반으로
학생의 이해도를 확인할 수 있는 퀴즈 3개를 만들어라.

문제의 핵심 원리를 확인하는 문제를 만든다.
단순한 숫자 바꾸기뿐 아니라 개념 이해도 확인을 포함한다.

## 퀴즈
3개의 문제를 번호별로 제시한다.

## 정답
정답을 문제와 분리하여 마지막에 제시한다.

## 간단한 설명
각 정답에 대한 간단한 설명을 추가한다.

한국어로 작성한다.
"""
}

# =========================================================
# 7. 사이드바
# =========================================================
with st.sidebar:

    st.markdown("## 📐 수학문제 해설")
    st.caption("Gemini AI 수학 학습 도우미")

    st.divider()

    st.markdown("### 🛠️ 학습 모드")

    mode = st.radio(
        "모드를 선택하세요",
        [
            "상세 풀이",
            "힌트",
            "다른 풀이",
            "유사 문제",
            "이해 확인 퀴즈"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    st.markdown("### 📚 풀이 기록")

    if st.session_state.history:

        for i, item in enumerate(
            reversed(st.session_state.history)
        ):

            if st.button(
                item["title"],
                key=f"history_{i}",
                use_container_width=True
            ):

                st.session_state.solution = item["solution"]
                st.session_state.uploaded_image = item["image"]
                st.session_state.last_mode = item["mode"]
                st.session_state.chat_history = []
                st.rerun()

    else:
        st.caption("아직 풀이 기록이 없습니다.")

    st.divider()

    if st.button("🗑️ 기록 전체 초기화", use_container_width=True):

        st.session_state.history = []
        st.session_state.solution = ""
        st.session_state.chat_history = []
        st.session_state.uploaded_image = None
        st.session_state.last_mode = ""
        st.rerun()

    st.caption("Powered by Gemini")

# =========================================================
# 8. 메인 헤더
# =========================================================
st.markdown("""
<div class="hero">
    <h1>📐 수학문제 해설</h1>
    <p>
        사진 한 장으로 시작하는 수학 학습.<br>
        AI 선생님이 문제를 분석하고 이해하기 쉽게 설명합니다.
    </p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# 9. 이미지 업로드
# =========================================================
st.markdown("### 📷 문제 업로드")

uploaded_file = st.file_uploader(
    "수학 문제 사진을 선택하세요",
    type=["png", "jpg", "jpeg"],
    help="문제가 선명하게 보이는 사진을 권장합니다."
)

# =========================================================
# 10. 이미지 처리
# =========================================================
current_image = None

if uploaded_file is not None:

    try:
        current_image = Image.open(
            BytesIO(uploaded_file.getvalue())
        ).convert("RGB")

        st.session_state.uploaded_image = uploaded_file.getvalue()

    except Exception:
        st.error("이미지를 불러올 수 없습니다.")
        st.stop()

elif st.session_state.uploaded_image is not None:

    current_image = Image.open(
        BytesIO(st.session_state.uploaded_image)
    ).convert("RGB")

# =========================================================
# 11. 이미지 표시 및 풀이 실행
# =========================================================
if current_image is not None:

    st.image(
        current_image,
        caption="업로드한 수학 문제",
        use_container_width=True
    )

    st.markdown(f"**현재 모드:** `{mode}`")

    if st.button("✨ AI 풀이 시작", use_container_width=True):

        with st.spinner("문제를 분석하고 답변을 작성 중입니다..."):

            try:

                prompt = PROMPTS[mode]

                result = ask_gemini(
                    current_image,
                    prompt
                )

                st.session_state.solution = result
                st.session_state.last_mode = mode
                st.session_state.chat_history = []

                history_item = {
                    "title": datetime.datetime.now().strftime(
                        "%m/%d %H:%M"
                    ) + " - " + mode,
                    "solution": result,
                    "image": st.session_state.uploaded_image,
                    "mode": mode
                }

                st.session_state.history.append(history_item)
                st.session_state.history = (
                    st.session_state.history[-20:]
                )

            except Exception as e:
                st.error("AI 요청 중 오류가 발생했습니다.")
                st.exception(e)

# =========================================================
# 12. 풀이 결과
# =========================================================
if st.session_state.solution:

    st.divider()
    st.markdown("## 📝 AI 답변")

    st.markdown(st.session_state.solution)

    st.download_button(
        label="📥 풀이 다운로드",
        data=st.session_state.solution,
        file_name="math_solution.md",
        mime="text/markdown",
        use_container_width=True
    )

    with st.expander("📋 풀이 텍스트 보기 및 복사"):

        st.code(
            st.session_state.solution,
            language="markdown"
        )

    # =====================================================
    # 13. 추가 질문
    # =====================================================
    st.divider()
    st.markdown("## 💬 AI 선생님에게 질문")

    st.caption("풀이에서 이해되지 않는 부분을 질문해 보세요.")

    with st.form("followup_form"):

        question = st.text_area(
            "질문",
            placeholder="예: 이 부분에서 왜 양변에 2를 곱하나요?",
            height=100
        )

        submitted = st.form_submit_button(
            "질문 보내기",
            use_container_width=True
        )

    if submitted:

        if not question.strip():

            st.warning("질문을 입력해 주세요.")

        elif st.session_state.uploaded_image is None:

            st.warning("문제 이미지를 다시 업로드해 주세요.")

        else:

            with st.spinner("답변을 작성 중입니다..."):

                try:

                    original_image = Image.open(
                        BytesIO(st.session_state.uploaded_image)
                    ).convert("RGB")

                    chat_prompt = f"""
                    원래 문제의 풀이:

                    {st.session_state.solution}

                    학생의 질문:

                    {question}

                    원래 문제와 풀이 맥락을 고려해서
                    학생이 이해하기 쉽게 친절하게 설명해라.

                    필요하다면 간단한 예시를 들어 설명한다.
                    한국어로 답하고 Markdown과 LaTeX를 사용한다.
                    """

                    answer = ask_gemini(
                        original_image,
                        chat_prompt
                    )

                    st.session_state.chat_history.append(
                        {
                            "question": question,
                            "answer": answer
                        }
                    )

                except Exception as e:

                    st.error("질문 처리 중 오류가 발생했습니다.")
                    st.exception(e)

    # 추가 질문 기록
    for chat in st.session_state.chat_history:

        with st.chat_message("user"):
            st.markdown(chat["question"])

        with st.chat_message("assistant"):
            st.markdown(chat["answer"])

# =========================================================
# 14. 새 문제 시작
# =========================================================
st.divider()

if st.button("🔄 새 문제 시작", use_container_width=True):

    st.session_state.solution = ""
    st.session_state.uploaded_image = None
    st.session_state.chat_history = []
    st.session_state.last_mode = ""

    st.rerun()

# =========================================================
# 15. 하단
# =========================================================
st.markdown("""
<div style="text-align:center; color:#4b5563; padding:20px;">
    📐 수학문제 해설 · Gemini AI<br>
    <small>AI 풀이를 참고하여 수학 개념을 이해하고 직접 확인해 보세요.</small>
</div>
""", unsafe_allow_html=True)
