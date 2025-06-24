# 🎓 SOCY Assistant: 사회학 논문 추천 챗봇

## 🚀 프로젝트 개요
SOCY Assistant는 사회학 분야의 연구자, 학생 및 관련 분야에 관심을 지닌 모든 이들을 위하여 개발된 인공지능 기반 논문 추천 챗봇입니다. 본 시스템은 사용자의 질의 및 관심사를 분석하고, Neo4j 그래프 데이터베이스에 구축된 방대한 사회학 논문 데이터셋을 활용하여 관련성이 높고 심층적인 영어 논문을 선별하여 추천합니다. Streamlit을 통해 직관적인 웹 인터페이스를 제공하며, Google Gemini API를 활용하여 우수한 답변 품질과 자연스러운 상호작용을 구현합니다.

## ✨ 주요 기능
- 지능형 논문 추천: 사용자의 사회학적 질의에 최적화된 관련 영어 논문을 최대 5개까지 제안합니다.
- 상세 추천 근거: 각 추천 논문의 중요성, 문제의식, 그리고 사회학적 전통에 대한 기여도를 논문의 초록(Abstract) 내용을 기반으로 상세하고 깊이 있게 설명합니다.
- 저자 및 저널 정보: 논문의 주요 저자 영향력(h-index, 총 인용 수), 게재 저널의 명성, 및 논문 자체의 인용 수를 포함하여 논문의 학술적 신뢰성과 가치 판단에 필요한 정보를 제공합니다.
- 영어 논문 필터링: 시스템은 오직 영어 논문만을 추천하도록 내부적으로 설계되었습니다.
- 전문적 상호작용: 사용자에게 환영의 메시지와 함께 전문적이면서도 친근한 어조로 소통하며, 지도교수와의 대화와 유사한 경험을 제공합니다.
- 모호한 질의 처리: 질문이 모호하여 적절한 논문을 검색하기 어려운 경우, 시스템은 사용자에게 보다 구체적인 질의를 유도하여 향상된 추천 결과를 도출할 수 있도록 안내합니다.

## ⚙️ 기술 스택
본 프로젝트는 다음과 같은 기술 스택을 기반으로 구축되었습니다:

- 프론트엔드/UI: Streamlit
- LLM 통합: LangChain
- 언어 모델: Google Gemini 2.0 Flash API
- 임베딩 모델: GoogleGenerativeAIEmbeddings
- 벡터/그래프 데이터베이스: Neo4j (LangChain Neo4jVector 통합 활용)
- 환경 변수 관리: python-dotenv
- 언어: Python 3.9+

## 🚀 시작하기
본 프로젝트를 로컬 환경에서 실행하기 위한 단계별 지침은 다음과 같습니다.

### 📋 전제 조건
- Python 3.9 이상 버전이 설치되어 있어야 합니다.
- Neo4j Desktop 또는 Neo4j Server가 설치 및 실행 중이어야 합니다.
- Neo4j 데이터베이스에 사회학 논문 데이터가 로드되어 있어야 합니다. (데이터 수집, 전처리, Neo4j 임베딩 등의 코드 제공함).
- paper_abstract_embeddings라는 이름의 벡터 인덱스가 Neo4j에 생성되어 있어야 하며, 해당 인덱스는 text_for_embedding 속성을 기반으로 해야 합니다.

```
CREATE VECTOR INDEX paper_abstract_embeddings IF NOT EXISTS
FOR (p:Paper) ON (p.text_for_embedding)
OPTIONS {nodeProperties: ['paperId', 'language', 'title', 'year', 'citationCount'], embeddingFunction: 'google_embedding', indexSize: 1536};
```
(참고: google_embedding은 Neo4j와 Gemini API 연동 설정 후 생성되는 임베딩 함수명입니다. 실제 Neo4j 설정에 따라 상이할 수 있습니다.)

### ⚙️ 설치 단계
1. 리포지토리 클론:
```
git clone https://github.com/your-username/socy-assistant-chatbot.git
cd socy-assistant-chatbot
```

2. 가상 환경 설정 및 활성화:
```
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

3. 필요 라이브러리 설치:

```
pip install -r requirements.txt
```
(프로젝트 루트에 requirements.txt 파일이 포함되어 있어야 합니다. 포함될 내용 예시: streamlit, python-dotenv, langchain-google-genai, langchain-neo4j, neo4j, pyyaml 등)

4. 환경 변수 설정:
프로젝트 루트 디렉토리에 .env 파일을 생성하고 다음 정보를 추가하십시오.
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
GOOGLE_API_KEY=your_gemini_api_key
```
- NEO4J_URI: Neo4j 데이터베이스 URI (기본값: bolt://localhost:7687)
- NEO4J_USER: Neo4j 사용자명 (기본값: neo4j)
- NEO4J_PASSWORD: Neo4j 데이터베이스 비밀번호
- GOOGLE_API_KEY: Google Cloud Console에서 발급받은 Gemini API 키

5. Streamlit 애플리케이션 실행:
```
streamlit run streamlit_app.py
```
이 명령어를 실행하면 웹 브라우저에서 챗봇 인터페이스가 자동으로 열립니다.

## 💡 사용 지침
챗봇이 실행된 후, 웹 인터페이스의 채팅 입력창에 사회학 관련 질의를 입력하고 Enter 키를 누르십시오.

- 질의 예시:

"감정 사회학 입문자를 위한 논문을 추천해 주십시오."

"페미니즘 사회학의 주요 이론적 관점을 설명해 주십시오."

"사회적 불평등과 감정의 관계를 다룬 논문이 존재합니까?"

"Arlie Hochschild의 논문 중 '감정 노동' 관련 자료가 필요합니다."


챗봇은 질의를 분석하여 관련 논문 목록과 함께 각 논문에 대한 상세 설명, 저자 정보, 저널 정보, 그리고 인용 수를 제공할 것입니다.
