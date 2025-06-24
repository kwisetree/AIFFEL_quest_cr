import streamlit as st
import os
from dotenv import load_dotenv
from socy_recommender_core import chain  # socy_recommender_core.py에서 chain 임포트
from neo4j import GraphDatabase  # driver close를 위해 필요
import re

# Streamlit 페이지 기본 설정
st.set_page_config(
    page_title="🎓 SOCY Assistant",
    page_icon="🎓",
    layout="wide"
)

# 환경 변수 로드 (Streamlit 앱에서도 필요)
load_dotenv()


# Neo4j 드라이버 연결 (socy_recommender_core에서 초기화되므로 여기서는 접근만)
# 캐싱을 통해 드라이버를 한 번만 초기화하도록 합니다.
@st.cache_resource
def get_driver():
    # socy_recommender_core에서 driver가 초기화되므로 여기서 다시 초기화하지 않고 접근
    # 하지만 Streamlit 환경에서는 스크립트 실행 방식이 달라서 별도 초기화가 더 안전할 수 있음.
    # 여기서는 core 모듈에서 초기화된 driver 객체를 직접 가져오는 대신,
    # Streamlit 앱 시작 시 자체적으로 driver를 관리하는 방식으로 변경 (캐싱 활용)
    NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


driver = get_driver()


# --- 4. 답변 후처리 함수 (streamlit_app.py에 유지) ---
def post_process_response(response: str) -> str:
    """
    LLM 응답을 사용자 친화적인 형식으로 후처리합니다.
    - 불필요한 HTML <br> 태그 제거
    - 마크다운 제목 앞뒤 빈 줄 추가 및 일관된 헤딩 레벨 적용 (모든 ##을 ###으로 변환)
    - 불필요한 구분선 제거
    - 목록 번호와 텍스트 사이 공백 조정
    """
    processed = response.replace("<br><br>", "").replace("<br>", "")

    # 문장 끝에 줄 바꿈을 강제하는 로직을 제거하여 LLM의 자연스러운 흐름을 유지합니다.
    # processed = re.sub(r'(?<=[.?!])\s*([A-Z가-힣])', r'\n\n\1', processed) # 이전 로직 제거

    # 약어 뒤에 불필요하게 생성된 줄 바꿈 제거 로직도 문장 끝 줄 바꿈 로직과 함께 제거합니다.
    # common_abbreviations = [...]
    # for abbr in common_abbreviations:
    #     processed = re.sub(re.escape(abbr) + r'\n\n', abbr + ' ', processed)
    #     processed = re.sub(re.escape(abbr) + r'\n', abbr + ' ', processed)

    # 모든 ## 제목을 ###로 변경하여 일관된 헤딩 레벨을 유지합니다.
    # LLM이 때때로 ##과 ###을 혼용할 수 있으므로, 모든 주요 제목이 동일한 크기로 보이도록 강제합니다.
    # 먼저, ###을 처리하여 기존의 적절한 ###이 훼손되지 않도록 합니다.
    processed = processed.replace("###", "\n\n###")
    # 그 다음, 모든 ##을 ###으로 변환하고, 마찬가지로 앞뒤에 빈 줄을 추가하여 마크다운 렌더링을 돕습니다.
    processed = processed.replace("##", "\n\n###")

    # 문자열 시작이 '\n\n###'으로 시작하면 첫 두 줄 바꿈 제거 (이중 줄 바꿈 방지)
    if processed.startswith('\n\n###'):
        processed = processed[2:]

    # 불필요한 구분선 제거
    processed = processed.replace("------------------------------------", "").replace("------------------------------",
                                                                                      "")
    # 목록 번호와 텍스트 사이의 공백 조정 (예: "1. 텍스트" -> "1. 텍스트")
    processed = re.sub(r'(\d+\.)\s+', r'\1 ', processed)
    return processed


# --- 5. Streamlit 애플리케이션 UI 구성 ---

st.title("🎓 SOCY Assistant: 사회학 논문 추천 챗봇")
st.markdown("""
안녕하세요! 저는 사회학 연구를 위한 AI 어시스턴트, **SOCY Assistant**입니다.

궁금한 사회학 주제나 키워드를 질문하시면, 관련 핵심 논문을 찾아 그 중요성과 학술적 맥락을 깊이 있게 설명해 드립니다.

마치 지도교수님과 대화하듯, 여러분의 연구 여정에 든든한 동반자가 되어 드릴게요.

""")

# 세션 상태에 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 대화 기록 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력 처리
if user_question := st.chat_input("사회학 관련 질문을 입력하세요. (예: 사회학 입문자에게 맞는 논문을 추천해줄래?)"):
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):
        # 응답이 스트리밍될 동안 표시될 빈 플레이스홀더를 생성합니다.
        message_placeholder = st.empty()
        full_response = ""

        with st.spinner("관련 논문을 찾고 답변을 생성하는 중입니다... 잠시만 기다려주세요."):
            try:
                # socy_recommender_core.py에서 임포트된 chain의 stream 메서드 사용
                # 이는 LLM의 응답을 청크(chunk) 단위로 스트리밍합니다.
                for chunk in chain.stream(user_question):
                    # 각 청크의 내용(content)을 full_response에 추가합니다.
                    # chunk가 TextGenerationChunk 객체일 경우 content 속성을 사용합니다.
                    # 그렇지 않은 경우, chunk 자체가 문자열일 수 있습니다.
                    if hasattr(chunk, 'content'):
                        full_response += chunk.content
                    else:
                        full_response += chunk  # Fallback for non-LangChain string chunks

                    # 현재까지의 응답에 깜빡이는 커서 효과를 추가하여 실시간 스트리밍 느낌을 줍니다.
                    # 이 시점에는 최소한의 후처리만 적용하여 LLM의 원본 출력에 가깝게 유지합니다.
                    # 완벽한 서식은 스트리밍 완료 후 'processed_response'에서 적용됩니다.
                    display_response = full_response.replace("##", "###").replace("###", "\n\n###")  # 스트리밍 중 제목 크기만 통일
                    message_placeholder.markdown(display_response + "▌")

                # 스트리밍 완료 후, 최종 응답에 후처리 함수를 적용합니다.
                # 이는 답변의 형식을 일관되게 유지하는 데 도움을 줍니다.
                processed_response = post_process_response(full_response)

                # 최종적으로 후처리된 전체 응답을 커서 없이 표시합니다.
                message_placeholder.markdown(processed_response)

                # 세션 상태에 최종 답변 저장
                st.session_state.messages.append({"role": "assistant", "content": processed_response})

            except Exception as e:
                # 오류 발생 시 사용자에게 메시지 표시
                error_message = f"죄송합니다, 답변을 생성하는 중에 오류가 발생했습니다: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

# Streamlit 앱 종료 시 드라이버 연결 닫기 (선택 사항이지만 권장)
# Streamlit의 라이프사이클 관리와 충돌할 수 있으므로 주의 필요
# 일반적으로 st.cache_resource를 사용하면 Streamlit이 앱 종료 시 자동으로 리소스를 정리하려고 시도합니다.
# 그럼에도 불구하고 명시적으로 닫고 싶다면 다음과 같이 사용할 수 있습니다.
# try:
#     if 'driver' in locals() and driver:
#         driver.close()
#         st.info("Neo4j 드라이버 연결 종료.")
# except Exception as e:
#     st.warning(f"Neo4j 드라이버 종료 중 오류 발생: {e}")
