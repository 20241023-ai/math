
import streamlit as st
from google import genai
from PIL import Image
from io import BytesIO

# ==================================================
# 1. 페이지 설정
# ==================================================
st.set_page_config(
    page_title="수학문제 해설",
    page_icon="📐",
    layout="centered"
)

# ==================================================
# 2. 디자인 CSS
# ==================================================
st.markdown("""
<style>
    .stApp {
        max-width: 900px;
        margin: auto;
    }

    h1 {
        text-align: center;
        padding-top: 1rem;
    }

    .subtitle {
        text-align: center;
        color: #888888;
        margin-bottom: 2rem;
    }

    div.stButton > button {
        border-radius: 12px;
        min-height: 45px;
        font-weight: bold;
    }

    [data-testid="stFileUploader"] {
        border-radius: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ==================================================
# 3. Gemini API 클라이언트
# ==================================================
@st.cache_resource
def get_client():
    api_key = st.secrets["GEMINI_API_KEY"]
    return genai.Client(api_key=api_key)

try:
    client = get_client()
except Exception as e:
    st.error(
        "Gemini API 설정을 확인해 주세요. "
        "Streamlit Secrets에 GEMINI_API_KEY가 설정되어 있어야 합니다."
    )
    st.stop()

MODEL_NAME = "gemini-3.1-flash-lite"

# ==================================================
# 4. 제목 및 설명
# ==================================================
st.title("📐 수학문제 해설")

st.markdown(
    '<p class="subtitle">'
    '수학 문제 사진을 올리면 AI가 풀이 과정을 자세히 설명해 줍니다.'
    '</p>',
    unsafe_allow_html=True
)

st.divider()

# ==================================================
# 5. 이미지 업로드
# ==================================================
uploaded_file = st.file_uploader(
    "📷 수학 문제 사진을 업로드하세요",
    type=["png", "jpg", "jpeg"],
    help="수학 문제가 선명하게 보이는 사진을 업로드하세요."
)

# ==================================================
# 6. 이미지 미리보기
# ==================================================
if uploaded_file is not None:
    try:
        image = Image.open(
            BytesIO(uploaded_file.getvalue())
        ).convert("RGB")

        st.image(
            image,
            caption="업로드한 문제",
            use_container_width=True
        )

    except Exception:
        st.error("이미지를 읽을 수 없습니다. 다른 이미지로 시도해 주세요.")
        st.stop()

# ==================================================
# 7. 풀이 프롬프트
# ==================================================
SOLVE_PROMPT = """
너는 학생에게 수학을 가르치는 친절하고 정확한 수학 선생님이다.

첨부된 이미지의 수학 문제를 읽고 문제를 해결해라.

다음 규칙을 지켜라.

[풀이 규칙]

1. 이미지 속 문제를 먼저 읽고 정확히 파악한다.
2. 문제에서 구해야 하는 것을 정리한다.
3. 필요한 수학 개념, 정의 또는 공식을 소개한다.
4. 풀이를 번호가 있는 단계별 과정으로 작성한다.
5. 계산 과정을 가능한 한 생략하지 않는다.
6. 각 식이 어떻게 만들어졌는지 설명한다.
7. 계산 실수를 점검하고 풀이의 논리적 타당성을 확인한다.
8. 여러 풀이 방법이 있다면 기본적인 풀이 방법을 먼저 설명한다.
9. 이미지에서 읽을 수 없는 부분이 있다면 임의로 지어내지 않는다.
10. 마지막에 최종 답을 분명하게 표시한다.

[답변 형식]

### 문제 이해
문제에서 무엇을 구해야 하는지 간단하게 정리한다.

### 핵심 개념
풀이에 필요한 개념과 공식이 있다면 설명한다.

### 단계별 풀이
각 단계를 번호로 나누고 자세히 설명한다.
수식은 LaTeX 형식으로 작성한다.

### 최종 답
최종 답을 명확하게 정리한다.

학생이 답만 외우는 것이 아니라 풀이 원리를 이해할 수 있도록 설명한다.
답변은 한국어로 작성한다.
Markdown을 사용한다.
"""

# ==================================================
# 8. 풀이 결과 저장 초기화
# ==================================================
if "solution" not in st.session_state:
    st.session_state.solution = None

if "followup_history" not in st.session_state:
    st.session_state.followup_history = []

if "image_bytes" not in st.session_state:
    st.session_state.image_bytes = None

# ==================================================
# 9. 문제 풀이 버튼
# ==================================================
if uploaded_file is not None:

    if st.button("✨ 문제 풀이하기", use_container_width=True):

        st.session_state.solution = None
        st.session_state.followup_history = []
        st.session_state.image_bytes = uploaded_file.getvalue()

        with st.spinner("AI 선생님이 문제를 분석하고 있습니다..."):

            try:
                image = Image.open(
                    BytesIO(st.session_state.image_bytes)
                ).convert("RGB")

                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=[
                        image,
                        SOLVE_PROMPT
                    ]
                )

                st.session_state.solution = response.text

            except Exception as e:
                st.error(f"풀이 중 오류가 발생했습니다: {e}")

# ==================================================
# 10. 풀이 결과 표시
# ==================================================
if st.session_state.solution:

    st.divider()

    st.markdown("## 📝 풀이 결과")

    st.markdown(st.session_state.solution)

    st.divider()

    # ==================================================
    # 11. 추가 질문
    # ==================================================
    st.markdown("### 💬 풀이에 대해 추가 질문하기")

    followup = st.text_input(
        "궁금한 부분을 입력하세요",
        placeholder="예: 왜 이 식에서 양변을 나누나요?",
        key="followup_input"
    )

    if st.button("질문하기", use_container_width=True):

        if not followup.strip():
            st.warning("질문을 입력해 주세요.")

        else:
            with st.spinner("추가 질문에 답변하는 중..."):

                try:
                    previous_questions = "\n".join(
                        st.session_state.followup_history
                    )

                    followup_prompt = f"""
                    다음은 원래 수학 문제의 풀이이다.

                    {st.session_state.solution}

                    이전 추가 질문 및 답변:
                    {previous_questions if previous_questions else "없음"}

                    학생의 추가 질문:
                    {followup}

                    기존 문제와 풀이 맥락을 고려하여
                    한국어로 친절하고 자세하게 답변해라.

                    필요한 경우 예시나 수식을 사용하여 설명하라.
                    """

                    image = Image.open(
                        BytesIO(st.session_state.image_bytes)
                    ).convert("RGB")

                    response = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=[
                            image,
                            followup_prompt
                        ]
                    )

                    answer = response.text

                    st.session_state.followup_history.append(
                        f"질문: {followup}\n답변: {answer}"
                    )

                    st.markdown("#### 추가 답변")
                    st.markdown(answer)

                except Exception as e:
                    st.error(f"추가 질문 처리 중 오류가 발생했습니다: {e}")

    # 이전 추가 질문 표시
    if st.session_state.followup_history:

        st.divider()
        st.markdown("### 📚 추가 질문 기록")

        for item in st.session_state.followup_history:
            st.markdown(item)
            st.divider()

# ==================================================
# 12. 초기화 버튼
# ==================================================
if st.session_state.solution:

    if st.button("🔄 새 문제 풀기", use_container_width=True):

        st.session_state.solution = None
        st.session_state.followup_history = []
        st.session_state.image_bytes = None

        st.rerun()

# ==================================================
# 13. 하단 안내
# ==================================================
st.divider()

st.caption(
    "Powered by Gemini API · 수학문제 해설"
)
