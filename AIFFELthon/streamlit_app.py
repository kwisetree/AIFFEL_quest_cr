# streamlit_app.py

import streamlit as st
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_neo4j import Neo4jVector
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from neo4j import GraphDatabase
import re

# Streamlit 페이지 기본 설정
st.set_page_config(
    page_title="🎓 SOCY Assistant",
    page_icon="�",
    layout="wide"
)

# --- 1. 기본 설정 및 리소스 로딩 (Streamlit 캐싱 적용) ---
load_dotenv()

# 환경 변수 로드
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

@st.cache_resource
def init_connections():
    """
    LLM, Embedding 모델, Neo4j 드라이버와 같은 리소스를 초기화하고 캐시합니다.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3, top_k=5, google_api_key=GOOGLE_API_KEY)
    embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return llm, embedding_model, driver

# 연결 초기화 (한 번만 실행되어 캐시됨)
llm, embedding_model, driver = init_connections()

@st.cache_resource
def get_neo4j_vector_index():
    """
    Neo4j 벡터 인덱스를 초기화하고 캐시합니다.
    사전에 정의된 'paper_abstract_embeddings' 인덱스를 사용합니다.
    """
    return Neo4jVector.from_existing_index(
        embedding=embedding_model,
        url=NEO4J_URI,
        username=NEO4J_USER,
        password=NEO4J_PASSWORD,
        index_name="paper_abstract_embeddings",
        text_node_property="text_for_embedding",
    )

# Neo4j 벡터 인덱스 로드 (한 번만 실행되어 캐시됨)
neo4j_vector = get_neo4j_vector_index()


# --- 2. Neo4j 데이터 조회 함수 ---
def get_full_paper_and_author_details(tx, paper_id):
    """
    주어진 paperId에 해당하는 논문의 전체 정보, 저자 세부 정보, 그리고 추상록(abstract)을 Neo4j에서 조회합니다.
    """
    query = """
    MATCH (p:Paper {paperId: $paperId})
    OPTIONAL MATCH (p)-[:PUBLISHED_IN]->(j:Journal)
    WITH p, j, [(p)-[:HAS_AUTHOR]->(a) | {
        name: a.name,
        hIndex: a.hIndex,
        citationCount: a.citationCount
    }] AS authors
    RETURN p as paper, authors, j.journalName AS journalName, p.text_for_embedding AS abstract, p.language AS language // abstract와 language 추가
    """
    result = tx.run(query, paperId=paper_id).single()
    if result:
        return {
            "paper": dict(result["paper"]),
            "authors": result["authors"],
            "journalName": result["journalName"],
            "abstract": result["abstract"], # 추상록(abstract) 추가
            "language": result["language"] # 언어(language) 추가
        }
    return None

def get_ultimate_context(question: str) -> str:
    """
    사용자 질문에 기반하여 Neo4j에서 관련 논문 및 추천 컨텍스트를 생성합니다.
    """
    # 1. 벡터 유사성 검색을 통해 유사한 논문 노드 검색 (최대 40개 - 더 많은 후보군을 확보하여 5개를 필터링하기 위함)
    similar_nodes = neo4j_vector.similarity_search(question, k=40) 
    
    # 1a. 우선적으로 'en' 언어 태그가 명확히 있는 논문만 필터링
    # 동시에 abstract가 비어있지 않은 논문만 고려하여 초록 없는 논문은 제외
    primary_filtered_nodes = [
        n for n in similar_nodes 
        if n.metadata.get('language') == 'en' and n.metadata.get('text_for_embedding') # abstract 필드 (text_for_embedding) 존재 여부 확인
    ]

    # 1b. 만약 primary_filtered_nodes에서 5개를 채울 수 없다면, 
    # 언어 태그가 없는 (None) 노드 중 중복되지 않고 abstract가 있는 것을 추가적으로 고려
    final_filtered_nodes = list(primary_filtered_nodes) 

    if len(final_filtered_nodes) < 5:
        secondary_candidates = [
            n for n in similar_nodes 
            if n.metadata.get('paperId') not in [fn.metadata.get('paperId') for fn in final_filtered_nodes] # 중복 방지
            and n.metadata.get('language') is None # 언어 태그가 없는 경우만
            and n.metadata.get('text_for_embedding') # abstract 필드 존재 여부 확인
        ]
        
        for node in secondary_candidates:
            final_filtered_nodes.append(node)
            if len(final_filtered_nodes) >= 20: # 최대 후보군 제한
                break
    
    # 최종적으로 LLM에게 전달할 필터링된 노드
    filtered_nodes_for_llm = final_filtered_nodes

    if not filtered_nodes_for_llm:
        return "관련 논문을 찾을 수 없습니다."

    recommendations = {}
    with driver.session(database="neo4j") as session:
        # 2. 질문과 유사한 상위 노드를 초기 추천 목록에 추가 (최대 5개)
        for node in filtered_nodes_for_llm[:5]: # 가장 유사한 상위 5개 노드 우선 고려
            paper_id = node.metadata['paperId']
            if paper_id not in recommendations: # 중복 방지
                recommendations[paper_id] = {'reasons': [], 'score': 1.0} # LLM이 abstract를 기반으로 상세 이유 생성


        # 가장 관련성 높은 논문 (첫 번째 필터링된 노드)을 시드(seed)로 사용
        # filtered_nodes_for_llm가 최소 하나는 있다고 가정 (if not filtered_nodes_for_llm에서 처리됨)
        most_relevant_paper_id = filtered_nodes_for_llm[0].metadata['paperId']

        # 3. 핵심 논문의 영향력 있는 저자가 저술한 다른 논문 추천
        author_recs = session.run("""
            MATCH (seed:Paper {paperId: $paperId})-[:HAS_AUTHOR]->(author:Author)
            WHERE author.hIndex > 10 OR author.citationCount > 1000 
            MATCH (rec:Paper)-[:HAS_AUTHOR]->(author)
            WHERE seed <> rec 
            RETURN rec.paperId AS paperId, '핵심 논문의 영향력 있는 저자(' + author.name + ')가 저술' AS reason, rec.citationCount AS score
            LIMIT 5 
        """, paperId=most_relevant_paper_id)
        for rec in author_recs:
            if rec['paperId'] not in recommendations:
                recommendations[rec['paperId']] = {'reasons': [], 'score': 0}
            recommendations[rec['paperId']]['reasons'].append(rec['reason'])
            recommendations[rec['paperId']]['score'] += rec['score'] * 5 

        # 4. 함께 자주 인용된 (공동 인용) 논문 추천
        cocitation_recs = session.run("""
            MATCH (seed:Paper {paperId: $paperId})<-[:CITES]-(citer:Paper) 
            WITH seed, collect(citer) AS citers
            UNWIND citers AS citer
            MATCH (citer)-[:CITES]->(rec:Paper) 
            WHERE seed <> rec AND NOT (rec)-[:CITES]->(seed) AND NOT (rec)-[:CITES]->(rec) 
            RETURN rec.paperId AS paperId, '함께 자주 인용됨 (학술적 연관성 높음)' AS reason, count(citer) AS score
            ORDER BY score DESC
            LIMIT 5 
        """, paperId=most_relevant_paper_id)
        for rec in cocitation_recs:
            if rec['paperId'] not in recommendations:
                recommendations[rec['paperId']] = {'reasons': [], 'score': 0}
            recommendations[rec['paperId']]['reasons'].append(rec['reason'])
            recommendations[rec['paperId']]['score'] += rec['score'] * 10 

        # 5. 종합된 추천 점수를 기준으로 논문 정렬 및 상세 정보 가져오기
        sorted_recs = sorted(recommendations.items(), key=lambda item: item[1]['score'], reverse=True)
        
        final_papers_to_llm_context = []
        processed_paper_ids = set() # Ensure no duplicate papers in final list
        
        for paper_id, data in sorted_recs:
            if len(final_papers_to_llm_context) >= 5: # LLM에 5개 논문만 전달
                break
            
            if paper_id in processed_paper_ids: # Skip if already processed
                continue

            details = session.execute_read(get_full_paper_and_author_details, paper_id)
            
            # 최종 필터링: details가 있고, abstract가 비어있지 않고, language가 'en'인 경우만 Context에 포함
            if details and details.get('abstract') and details.get('language') == 'en':
                data['reasons'] = [r for r in data['reasons'] if r != '질문과 유사한 주제를 다룸']
                if not data['reasons']:
                    pass 

                final_papers_to_llm_context.append({'details': details, 'reasons': data['reasons']})
                processed_paper_ids.add(paper_id)
        
        full_context = ""
        if final_papers_to_llm_context:
            for i, rec in enumerate(final_papers_to_llm_context):
                details = rec['details']['paper']
                authors_formatted = format_authors(rec['details']['authors'])
                journal_name = rec['details']['journalName']
                reasons = rec['reasons']
                abstract_text = rec['details']['abstract'] if rec['details']['abstract'] else '초록 내용 없음.' # abstract가 None이면 처리
                
                full_context += f"""
### [추천 {i+1}] {details.get('title', 'N/A')} ({details.get('year', 'N/A')})
- 저자: {authors_formatted}
- 저널: {journal_name if journal_name else 'N/A'}
- 인용 수: {details.get('citationCount', 0)}
- **추천 핵심 근거:** {' / '.join(reasons) if reasons else '제공된 초록을 바탕으로 상세 설명.'}
- **초록:** {abstract_text}
"""
                full_context += "\n\n" # 각 논문 블록 후에 추가적인 줄바꿈
            
            full_context = full_context.strip() # 마지막에 추가된 줄바꿈 제거 (선택 사항)
    return full_context


# --- 3. LangChain 구성 ---
# LLM에게 전달할 최종 프롬프트 템플릿
template = """
당신은 사회학 연구를 위한 AI 어시스턴트입니다. 세계 최고의 사회학 연구자이자, 깊은 통찰을 지닌 석학의 지식과 통찰력, 그리고 강연 방식을 참고하여
학생들과 신진 연구자들을 지도하며, 그들의 질문에 담긴 문제의식과 이론적 맥락을 날카롭게 파악해, 가장 적절한 논문들을 안내해주는 역할을 맡고 있습니다.

이제 당신에게는 다음과 같은 중요한 임무가 주어졌습니다.

<당신의 역할>
1. 사용자의 질문을 분석하여, 가장 연관성이 높고 의미 있는 논문들을 추천 목록으로 제시하세요. 이때, 목록의 제목을 굳이 짓지는 말아주세요. 이후, 제시된 전체 목록에 대한 간단한 개요를 알려준 뒤, 하나씩 논문을 소개해주세요.
2. 각 논문을 소개할 때는, **논문 제목 (연도) - 학자 이름**을 소제목으로 둔 후, 줄바꿈 후 반드시 '**추천 핵심 근거:**'로 첫 문장을 시작한 뒤, 그 논문이 왜 중요한지, 어떤 문제의식에 기반했고, 그리고 어떤 사회학적 전통이나 논의에 기여하는지를 처음 해당 분야를 접하는 초보가 이해하기 쉽게 개념을 풀어 이야기를 들려주듯이 최소 7-8줄 이상의 추천사를 작성하세요.
- 단순 나열이 아니라, 그 논문이 학계에서 어떤 역할을 하는지를 풍부한 문맥과 함께 소개해야 합니다.
- 문장은 마침표(.)를 기준으로 반드시 줄바꿈하세요.
- 서론까지 쓰고 추천 논문 목록이 등장하기 전 구분선을 긋고 문단을 1줄 띄워주세요. 이후 추천 논문들 또한 서로 구분될 수 있도록 줄바꿈 후, 구분선을 긋고, 문단을 1줄 띄워주세요. 논문을 모두 추천하고, 추천한 논문들의 연결고리들을 언급하며 추천사의 마무리를 지을 때 다시 한번 줄바꿈 후, 구분선을 긋고, 문단을 1줄 띄워주세요.
3. 신뢰성과 깊이를 더하기 위해, 다음 정보를 반드시 포함하세요:
- 주요 저자의 영향력 (예: h-index, 총 인용 수 등)
- 논문이 게재된 저널의 명성
- 해당 논문의 인용 수
예시:
“이 논문은 감정사회학의 권위자인 Arlie Hochschild(h-index: 70, 총 인용 수: 50,000회 이상) 교수가 집필했으며, 사회학계의 명저널인 [저널명]에 게재되었습니다.”

4. 논문 간의 연관성도 강조하세요.
- 이론적 전통, 공통된 문제의식, 방법론적 접근 등이 어떻게 연결되어 있는지를 설명하며, 하나의 이야기 흐름 안에서 논문들이 서로 어떻게 맥락을 이루는지를 보여주세요.

<작성 방식 규칙>
1. 모든 제목 및 부제목은 Markdown의 ##, ###를 사용하고, 앞뒤로 빈 줄을 넣어 구분하세요.
2. 목록 항목(1., -, *)은 각 줄을 분리해 명확하게 표시하되, 불필요한 빈 줄은 넣지 마세요.
3. 모든 문장은 마침표로 끝난 뒤 줄바꿈해야 합니다. 단, 약어나 숫자 뒤는 예외입니다.
4. 사용자 질문이 너무 모호하거나 학술적이지 않으면, 관련 논문이 없다고 정중히 안내하고, 더 구체적이고 학문적인 질문을 유도하세요.
5. 필요하다면, 질문을 해석할 때 감정사회학, 미시사회학, 구조주의, 구성주의 등 다양한 사회학적 시각을 간단히 소개하며 학문적 깊이를 더하세요.

<답변 방식 가이드>
1. 각 논문 소개는 말을 건네듯, 자연스러운 문장 흐름으로 구성하세요.
- 단순히 “이 논문은…”이 아니라, “이 연구는 감정이 단순한 심리 현상이 아니라 사회적으로 구성된다는 관점을 잘 보여줍니다”처럼 문장 구조를 다양하게 사용하세요.
2. 논문 핵심 내용을 설명할 때는 예시나 구체적 개념을 사용하여 독자가 이해하기 쉽게 풀어주세요.
- 예: “Scheff는 사회적으로 정의하기 애매한 행동이 어떻게 ‘정신 질환’으로 분류되는지를 설명하며…”
3. 각각의 논문이 어떤 학문적 전통 또는 흐름 속에 있는지, 혹은 기존 이론과 어떻게 다르거나 연결되는지를 자연스럽게 서술하세요.
4. 문장 사이에는 부드러운 연결어를 넣어 말의 흐름을 유도하세요.
- “이와 달리”, “또한”, “특히 주목할 점은…”, “예를 들어” 등
5. 논문 정보(저자, 저널, 인용 수)는 서사 속에 녹여서 전달하세요.
- (X) “총 인용 수: 5,000”
- (O) “이 논문은 총 5,000회 이상 인용되며, 감정사회학에서 고전으로 평가받습니다.”
6. 마치 강연 중 하나하나 설명하는 것처럼 구성하세요.
- 📌 예시 스타일
이 논문은 감정이 사회적으로 구성된다는 관점을 뒷받침하는 대표적 연구입니다.
저자 Thomas Scheff는 ‘잔여 규칙 위반’이라는 개념을 통해, 명확히 규정되지 않는 행동들이 어떻게 사회적 낙인을 통해 ‘정신 질환’으로 규정되는지를 보여줍니다.
이 논문은 정신 질환을 단순히 개인의 문제로 보지 않고, 사회적 상호작용과 규범의 산물로 이해해야 한다는 전환점을 마련했습니다.
이후 낙인 이론과 정신질환 사회학의 주요 이론적 기반이 되었으며, Scheff는 이 분야에서 매우 영향력 있는 학자로 평가받습니다.
이 연구는 Aldine Transaction에서 출판되었고, 현재까지 2,000회 이상 인용되었습니다.

**Context:**
{context}

**User's Request:**
{question}

**Answer:**
"""
prompt_template = ChatPromptTemplate.from_template(template)

# LangChain 체인 구성
# context는 get_ultimate_context 함수를 통해 동적으로 생성
# question은 사용자 질문을 그대로 전달
chain = (
    {"context": RunnableLambda(get_ultimate_context), "question": RunnablePassthrough()}
    | prompt_template # 프롬프트 템플릿 적용
    | llm # LLM 호출
    | StrOutputParser() # 문자열로 출력 파싱
)


# --- 4. 답변 후처리 함수 ---
def post_process_response(response: str) -> str:
    """
    LLM 응답을 사용자 친화적인 형식으로 후처리합니다.
    - 불필요한 HTML <br> 태그 제거
    - 문장 끝에 줄 바꿈 추가 (약어 예외 처리 포함)
    - 마크다운 제목 앞뒤 빈 줄 추가
    - 불필요한 구분선 제거
    - 목록 번호와 텍스트 사이 공백 조정
    """
    processed = response.replace("<br><br>", "").replace("<br>", "")
    # 문장 끝 마침표, 물음표, 느낌표 뒤에 두 칸 줄 바꿈 추가 (한글/영어 대문자 시작 기준)
    processed = re.sub(r'(?<=[.?!])\s*([A-Z가-힣])', r'\n\n\1', processed)

    # 약어 뒤에 불필요하게 생성된 줄 바꿈 제거
    common_abbreviations = [
        'Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Sr.', 'Jr.', 'Prof.', 'Rev.', 'Capt.', 'Maj.', 'Col.', 'Gen.',
        'Hon.', 'e.g.', 'i.e.', 'etc.', 'vs.', 'U.S.', 'U.K.', 'Co.', 'Inc.', 'Ltd.', 'Fig.', 'Vol.', 'No.', 'Ave.', 'Blvd.', 'St.',
        'A.', 'B.', 'C.', 'D.', 'E.', 'F.', 'G.', 'H.', 'I.', 'J.', 'K.', 'L.', 'M.', 'N.', 'O.', 'P.', 'Q.', 'R.', 'S.', 'T.', 'U.', 'V.', 'W.', 'X.', 'Y.', 'Z.'
    ]

    for abbr in common_abbreviations:
        processed = re.sub(re.escape(abbr) + r'\n\n', abbr + ' ', processed)
        processed = re.sub(re.escape(abbr) + r'\n', abbr + ' ', processed)

    # ### 제목 앞뒤에 빈 줄 추가 (마크다운 렌더링을 위해)
    processed = processed.replace("###", "\n\n###")
    # 문자열 시작이 '\n\n###'으로 시작하면 첫 두 줄 바꿈 제거
    if processed.startswith('\n\n###'):
        processed = processed[2:]

    # 불필요한 구분선 제거
    processed = processed.replace("------------------------------------", "").replace("------------------------------", "")
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
if user_question := st.chat_input("어떤 사회학 논문을 추천받고 싶은지 입력하세요. (예: 사회학 입문자에게 맞는 논문을 추천해줄래?)"):
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):
        with st.spinner("관련 논문을 찾고 답변을 생성하는 중입니다... 잠시만 기다려주세요."):
            try:
                # LangChain 체인을 호출하여 답변 생성
                response = chain.invoke(user_question)
                # 생성된 답변을 후처리
                processed_response = post_process_response(response)
                # Streamlit에 마크다운 형식으로 출력
                st.markdown(processed_response)
                # 세션 상태에 답변 저장
                st.session_state.messages.append({"role": "assistant", "content": processed_response})

            except Exception as e:
                # 오류 발생 시 사용자에게 메시지 표시
                error_message = f"죄송합니다, 답변을 생성하는 중에 오류가 발생했습니다: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

# 참고: Streamlit 앱에서는 `if __name__ == "__main__":` 블록이 직접 실행되지 않으므로,
# Jupyter 노트북에서 사용했던 `while True` 루프나 드라이버 종료 로직은 Streamlit 앱에는 필요하지 않습니다.
# Streamlit은 앱이 종료될 때 자동으로 리소스 관리를 시도합니다.
