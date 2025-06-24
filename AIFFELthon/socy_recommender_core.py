import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_neo4j import Neo4jVector
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from neo4j import GraphDatabase
import re 
import random 

# --- 1. 기본 설정 및 초기화 ---
load_dotenv() # 환경 변수 로드

# Neo4j 접속 정보 및 Google API 키를 환경 변수에서 가져옵니다.
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# 언어 모델 및 임베딩 모델 초기화
llm = ChatGoogleGenerativeAI(model="models/gemini-2.0-flash", temperature=0.3, top_k=5)
embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Neo4j 드라이버 및 벡터 인덱스 연결
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
neo4j_vector = Neo4jVector.from_existing_index(
    embedding=embedding_model,
    url=NEO4J_URI,
    username=NEO4J_USER,
    password=NEO4J_PASSWORD,
    index_name="paper_abstract_embeddings",
    text_node_property="text_for_embedding",
)

# --- 2. Neo4j 데이터 조회 함수 ---
def get_full_paper_and_author_details(tx, paper_id):
    query = """
    MATCH (p:Paper {paperId: $paperId})
    OPTIONAL MATCH (p)-[:PUBLISHED_IN]->(j:Journal)
    WITH p, j, [(p)-[:HAS_AUTHOR]->(a) | {
        name: a.name,
        hIndex: a.hIndex,
        citationCount: a.citationCount
    }] AS authors
    RETURN p as paper, authors, j.journalName AS journalName
    """
    result = tx.run(query, paperId=paper_id).single()
    if result:
        return {
            "paper": dict(result["paper"]),
            "authors": result["authors"],
            "journalName": result["journalName"]
        }
    return None

def get_ultimate_context(question: str) -> str:
    def is_latin(text):
        return all(ord(c) < 128 or c.isspace() for c in text)

    # 벡터 유사도 검색 (많이 뽑고 나중에 필터링)
    similar_nodes = neo4j_vector.similarity_search(question, k=20)
    filtered_nodes = [n for n in similar_nodes if 'language' not in n.metadata or n.metadata['language'] in ['en', 'ko']]

    if not filtered_nodes:
        return "관련 논문을 찾을 수 없습니다."

    recommendations = {}
    with driver.session(database="neo4j") as session:
        for node in filtered_nodes[:5]:
            paper_id = node.metadata['paperId']
            recommendations[paper_id] = {'reasons': ['질문과 유사한 주제를 다룸'], 'score': 1.0}

        most_relevant_paper_id = filtered_nodes[0].metadata['paperId']

        author_recs = session.run("""
            MATCH (seed:Paper {paperId: $paperId})-[:HAS_AUTHOR]->(author:Author)
            WHERE author.hIndex > 10 OR author.citationCount > 1000
            MATCH (rec:Paper)-[:HAS_AUTHOR]->(author)
            WHERE seed <> rec
            RETURN rec.paperId AS paperId, '핵심 논문의 영향력 있는 저자(' + author.name + ')가 저술' AS reason, rec.citationCount AS score
            LIMIT 2
        """, paperId=most_relevant_paper_id)
        for rec in author_recs:
            if rec['paperId'] not in recommendations:
                recommendations[rec['paperId']] = {'reasons': [], 'score': 0}
            recommendations[rec['paperId']]['reasons'].append(rec['reason'])
            recommendations[rec['paperId']]['score'] += rec['score'] * 5

        cocitation_recs = session.run("""
            MATCH (seed:Paper {paperId: $paperId})<-[:CITES]-(citer:Paper)
            WITH seed, collect(citer) AS citers
            UNWIND citers AS citer
            MATCH (citer)-[:CITES]->(rec:Paper)
            WHERE seed <> rec AND NOT (rec)-[:CITES]->(seed) AND NOT (seed)-[:CITES]->(rec)
            RETURN rec.paperId AS paperId, '함께 자주 인용됨 (학술적 연관성 높음)' AS reason, count(citer) AS score
            ORDER BY score DESC
            LIMIT 2
        """, paperId=most_relevant_paper_id)
        for rec in cocitation_recs:
            if rec['paperId'] not in recommendations:
                recommendations[rec['paperId']] = {'reasons': [], 'score': 0}
            recommendations[rec['paperId']]['reasons'].append(rec['reason'])
            recommendations[rec['paperId']]['score'] += rec['score'] * 10

        sorted_recs = sorted(recommendations.items(), key=lambda item: item[1]['score'], reverse=True)
        top_recs_info = []
        for paper_id, data in sorted_recs[:5]:
            details = session.execute_read(get_full_paper_and_author_details, paper_id)
            if details and is_latin(details['paper'].get('title', '')):
                top_recs_info.append({'details': details, 'reasons': data['reasons']})

        def format_authors(authors_list):
            if not authors_list:
                return 'N/A'
            return ', '.join([
                f"{a.get('name', 'N/A')} (h-index: {a.get('hIndex', 0)}, 총 인용: {a.get('citationCount', 0)})"
                for a in authors_list
            ])

        full_context = ""
        if top_recs_info:
            full_context += "### 추천 논문 목록 ###\n"
            for i, rec in enumerate(top_recs_info):
                details = rec['details']['paper']
                authors_formatted = format_authors(rec['details']['authors'])
                journal_name = rec['details']['journalName']
                reasons = rec['reasons']
                full_context += f"""
[추천 {i+1}] {details.get('title', 'N/A')} ({details.get('year', 'N/A')})
- 저자: {authors_formatted}
- 저널: {journal_name if journal_name else 'N/A'}
- 인용 수: {details.get('citationCount', 0)}
- **추천 핵심 근거:** {' / '.join(reasons)}
"""
        return full_context

# --- 3. 최종 프롬프트 템플릿 ---
template = """
당신은 세계 최고의 사회학 연구자이자, 깊은 통찰을 지닌 석학입니다.
학생들과 신진 연구자들을 지도하며, 그들의 질문에 담긴 문제의식과 이론적 맥락을 날카롭게 파악해, 가장 적절한 논문들을 안내해주는 역할을 맡고 있습니다.

이제 당신에게는 다음과 같은 중요한 임무가 주어졌습니다.

<당신의 역할>
1. 사용자의 질문을 분석하여, 가장 연관성이 높고 의미 있는 논문들을 추천 목록으로 제시하세요. 먼저 전체 목록에 대한 간단한 개요를 알려준 뒤, 하나씩 논문을 소개해주세요.
2. 각 논문을 소개할 때는, 반드시 '추천 핵심 근거'로 문장을 시작한 뒤, 그 논문이 왜 중요한지, 어떤 문제의식에 기반했는지, 그리고 어떤 사회학적 전통이나 논의에 기여하는지를 이야기하듯 서술하세요.
- 단순 나열이 아니라, 그 논문이 학계에서 어떤 역할을 하는지를 풍부한 문맥과 함께 소개해야 합니다.
- 문장은 마침표(.)를 기준으로 반드시 줄바꿈하세요.
3. 신뢰성과 깊이를 더하기 위해, 다음 정보를 반드시 포함하세요:
- 주요 저자의 영향력 (예: h-index, 총 인용 수 등)
- 논문이 게재된 저널의 명성
- 해당 논문의 인용 수
예시:
“이 논문은 감정사회학의 권위자인 Arlie Hochschild(h-index: 70, 총 인용 수: 50,000회 이상) 교수가 집필했으며, 사회학계의 명저널인 [저널명]에 게재되었습니다.”

4. 논문 간의 연관성도 강조하세요.=
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

prompt = ChatPromptTemplate.from_template(template)

chain = (
    {"context": RunnableLambda(get_ultimate_context), "question": RunnableLambda(lambda x: x)}
    | prompt
    | llm
    | StrOutputParser()
)

# --- 애플리케이션 실행 ---
if __name__ == "__main__":
    print("안녕하세요, 반갑습니다. 저는 🎓SOCY Assistant🎓입니다.")
    print("사회학 연구 분야를 깊이 있게 탐색하고 싶으신가요?")
    print("저는 사회학 전문 지식을 바탕으로,")
    print("질문하신 주제와 관련된 핵심 논문을 찾아내고,")
    print("그 이해를 넓혀줄 연관 연구들을 추천해 드립니다.")
    print("마치 지도교수님과의 심도 깊은 학문적 대화를 경험하는 것처럼,")
    print("추천 논문들의 연결 고리와 학문적 의의를 명확하게 파악할 수 있도록 안내합니다.")
    print("학술적인 질문을 던져주세요. (종료하려면 'exit' 입력)")
    
    while True:
        question = input(">> ") # 사용자의 입력을 먼저 받음

        if question.lower() == 'exit':
            break
        
        # --- 사용자 질문 출력 추가 ---
        print(f"\n[사용자 질문]: {question}")
        print("-" * 30) # 시각적인 구분선
        # --- 사용자 질문 출력 끝 ---

        # 사용자의 질문을 받은 후에 chain.invoke 호출
        try:
            response = chain.invoke(question) 
        except NameError:
            print("오류: 'chain' 객체가 정의되지 않았습니다. LangChain 셋업 코드를 확인해주세요.")
            break
        except Exception as e:
            print(f"AI 답변 생성 중 오류 발생: {e}")
            continue
        
        # --- AI 답변 후처리 (Post-processing) 시작 ---
        processed_response = response

        # 1. AI가 생성한 불필요한 <br> 태그 제거
        processed_response = processed_response.replace("<br><br>", "")
        processed_response = processed_response.replace("<br>", "")

        # 2. 문장 끝 마침표(.) 뒤에 줄 바꿈 추가 (두 단계 접근 방식)
        # 2-1단계: 문장 끝으로 보이는 '. ', '? ', '! ' 뒤에 줄바꿈 두 개를 추가합니다.
        # 이 과정에서 약어 뒤에도 임시적으로 줄바꿈이 생길 수 있습니다.
        # '(?<=[.?!])'는 문장 부호 뒤를 의미하고, '\s*'는 0개 이상의 공백, '([A-Z가-힣])'는 대문자/한글 시작을 의미합니다.
        processed_response = re.sub(r'(?<=[.?!])\s*([A-Z가-힣])', r'\n\n\1', processed_response)
        
        # 2-2단계: 특정 약어 뒤에 불필요하게 생성된 줄바꿈 제거 (고정 길이 패턴으로만 가능한 약어들)
        # 자주 사용되는 약어 리스트입니다. 필요에 따라 추가하거나 수정할 수 있습니다.
        # 주의: 이니셜(예: J. K. Rowling의 'J.')과 같이 단일 대문자로 된 약어는 완벽하게 처리하기 어렵습니다.
        # 여기서는 비교적 고정된 형태의 약어들만 포함합니다.
        common_abbreviations = [
            'Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Sr.', 'Jr.', 'Prof.', 'Rev.', 'Capt.', 'Maj.', 'Col.', 'Gen.',
            'Hon.', 'e.g.', 'i.e.', 'etc.', 'vs.', 'U.S.', 'U.K.', 'Co.', 'Inc.', 'Ltd.', 'Fig.', 'Vol.', 'No.', 'Ave.', 'Blvd.', 'St.',
            # 추가적으로 발생할 수 있는 이니셜 형태 예외 (목록이 길어질 수 있음)
            'A.', 'B.', 'C.', 'D.', 'E.', 'F.', 'G.', 'H.', 'I.', 'J.', 'K.', 'L.', 'M.', 'N.', 'O.', 'P.', 'Q.', 'R.', 'S.', 'T.', 'U.', 'V.', 'W.', 'X.', 'Y.', 'Z.'
        ]
        
        # 약어 뒤의 \n\n을 다시 공백으로 대체합니다.
        for abbr in common_abbreviations:
            # re.escape를 사용하여 약어 내의 특수 문자(예: .)를 이스케이프 처리합니다.
            processed_response = re.sub(re.escape(abbr) + r'\n\n', abbr + ' ', processed_response)
            # 혹시 \n만 있는 경우도 처리 (덜 일반적이지만, 안전하게)
            processed_response = re.sub(re.escape(abbr) + r'\n', abbr + ' ', processed_response)

        # 3. ### 제목 앞뒤에 빈 줄 추가 (Markdown 포맷 유지)
        processed_response = processed_response.replace("###", "\n\n###")
        if processed_response.startswith('\n\n###'):
            processed_response = processed_response[2:]
            
        # '분석 대상 핵심 논문' 제거로 인해 이 구분선도 제거
        processed_response = processed_response.replace("------------------------------------", "") 
        processed_response = processed_response.replace("------------------------------", "") 

        # 4. 목록 번호와 다음 텍스트 사이에 불필요한 공백 제거
        processed_response = re.sub(r'(\d+\.)\s+', r'\1 ', processed_response)


        # --- AI 답변 후처리 끝 ---

        print("\n🎓SOCY Assistant🎓:\n")
        print(processed_response) # 처리된 답변을 출력
        print("-" * 30)

    # driver 객체는 이 코드 블록 외부에 정의되어 있어야 합니다.
    try:
        if 'driver' in locals() and driver: # driver가 로컬 스코프에 정의되어 있고 유효한지 확인
            driver.close()
            print("Neo4j 드라이버 연결 종료.")
    except NameError:
        print("오류: 'driver' 객체가 정의되지 않았습니다. Neo4j 연결 코드를 확인해주세요.")
    except Exception as e:
        print(f"Neo4j 드라이버 종료 중 오류 발생: {e}")