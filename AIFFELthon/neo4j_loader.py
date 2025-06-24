import os
from dotenv import load_dotenv 
import json
import time
from tqdm.notebook import tqdm
from collections import deque
import logging 

from neo4j import GraphDatabase
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# 환경 변수 로드
load_dotenv()

# Neo4j 접속 정보 및 Google API 키를 환경 변수에서 가져옵니다.
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j") # 기본값 설정
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") # Google API 키도 환경 변수에서 가져옴

# Google Generative AI 임베딩 모델을 초기화합니다.
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)

# Neo4j 드라이버를 초기화합니다.
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# 임베딩이 없는 논문을 가져오는 함수입니다.
def get_papers_without_embeddings(tx):
    # title 속성, abstract 속성, 그리고 abstractEmbedding이 없는 논문을 가져옵니다.
    query = """
    MATCH (p:Paper)
    WHERE p.title IS NOT NULL AND p.abstract IS NOT NULL AND p.abstractEmbedding IS NULL
    RETURN p.paperId AS paperId, p.title AS title, p.abstract AS abstract
    LIMIT 500
    """
    result = tx.run(query)
    # title과 abstract를 모두 포함하여 반환합니다.
    return [{"paperId": record["paperId"], "title": record["title"], "abstract": record["abstract"]} for record in result]

# 생성된 임베딩을 Neo4j에 저장하는 함수입니다.
def store_embeddings(tx, paper_embeddings_data):
    # 임베딩과 함께, 임베딩에 사용된 합쳐진 텍스트도 저장합니다.
    query = """
    UNWIND $data AS row
    MATCH (p:Paper {paperId: row.paperId})
    SET p.abstractEmbedding = row.embedding,
        p.text_for_embedding = row.text
    """
    tx.run(query, data=paper_embeddings_data)

print("임베딩 생성 및 저장을 시작합니다 (제목 + 초록)...")

# 임베딩이 없는 논문이 없을 때까지 반복하여 임베딩을 생성하고 저장합니다.
while True:
    with driver.session(database="neo4j") as session:
        # 임베딩이 없는 논문 목록을 가져옵니다.
        papers = session.execute_read(get_papers_without_embeddings)

        if not papers:
            print("처리할 논문이 없습니다. 작업을 종료합니다.")
            break

        print(f"{len(papers)}개의 논문을 가져왔습니다. 임베딩을 생성합니다...")

        # 제목과 초록을 합쳐서 임베딩할 텍스트 리스트를 만듭니다.
        texts_to_embed = [f"Title: {p['title']}\n\nAbstract: {p['abstract']}" for p in papers]
        
        # 텍스트에 대한 임베딩을 생성합니다.
        paper_vectors = embeddings.embed_documents(texts_to_embed)

        paper_embeddings_to_store = []
        for i, paper in enumerate(papers):
            # 각 논문의 paperId, 생성된 임베딩, 그리고 임베딩에 사용된 텍스트를 저장할 목록에 추가합니다.
            paper_embeddings_to_store.append({
                "paperId": paper['paperId'],
                "embedding": paper_vectors[i],
                "text": texts_to_embed[i] # 임베딩에 사용된 텍스트
            })

        # 생성된 임베딩을 Neo4j에 저장합니다.
        session.execute_write(store_embeddings, paper_embeddings_to_store)
        print(f"{len(papers)}개의 (제목+초록) 임베딩을 성공적으로 저장했습니다.")

# Neo4j 드라이버 연결을 닫습니다.
driver.close()
