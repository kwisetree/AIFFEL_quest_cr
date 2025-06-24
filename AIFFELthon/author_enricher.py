import os
import requests
import time
from dotenv import load_dotenv
from neo4j import GraphDatabase
import logging

# --- 0. 로깅 설정 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("author_enricher.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# --- 1. 환경 변수 로드 ---
load_dotenv()

# Neo4j 접속 정보
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD") # .env 파일에서 불러옵니다.

# Semantic Scholar API 키
S2_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
AUTHOR_API_URL = "https://api.semanticscholar.org/graph/v1/author/"
AUTHOR_FIELDS = "hIndex,paperCount,citationCount,affiliations" # 가져올 저자 필드

# API 요청 헤더 설정
headers = {}
if S2_API_KEY:
    headers['x-api-key'] = S2_API_KEY
    logging.info("Semantic Scholar API 키를 사용하여 인증된 요청을 보냅니다.")
else:
    logging.warning("경고: Semantic Scholar API 키가 없습니다. 속도 제한 모드로 작동합니다. .env 파일에 SEMANTIC_SCHOLAR_API_KEY를 설정하세요.")

# Neo4j 드라이버 초기화
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# --- 2. Neo4j 데이터 조회 및 업데이트 함수 ---

def get_authors_to_enrich(tx):
    """
    Neo4j에서 hIndex가 없는 저자 ID 목록을 가져옵니다.
    """
    query = """
    MATCH (a:Author)
    WHERE a.authorId IS NOT NULL AND (a.hIndex IS NULL OR a.hIndex = 0)
    RETURN a.authorId AS authorId
    LIMIT 100
    """
    result = tx.run(query)
    return [record["authorId"] for record in result]

def update_author_details(tx, author_data_list):
    """
    Neo4j의 저자 노드에 상세 정보를 업데이트합니다.
    """
    query = """
    UNWIND $data AS author
    MATCH (a:Author {authorId: author.authorId})
    SET a += author.details
    """
    tx.run(query, data=author_data_list)

# --- 3. 보조 함수 ---

def format_time(seconds):
    """초를 시:분:초 형태의 문자열로 변환합니다."""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

# --- 4. 메인 실행 로직 ---

def enrich_authors():
    """
    Semantic Scholar API를 통해 Neo4j의 저자 노드 정보를 강화하는 메인 함수입니다.
    """
    logging.info("="*30 + " 저자 정보 강화 시작 " + "="*30)

    try:
        with driver.session(database="neo4j") as session:
            # 강화할 전체 저자 수를 미리 가져옵니다.
            total_authors_to_process = session.run("""
                MATCH (a:Author)
                WHERE a.authorId IS NOT NULL AND (a.hIndex IS NULL OR a.hIndex = 0)
                RETURN count(a) AS total
            """).single()['total']
        
        if total_authors_to_process == 0:
            logging.info("모든 저자 정보가 이미 최신입니다 (hIndex가 없는 저자가 없습니다). 작업을 종료합니다.")
            return
            
        logging.info(f"총 {total_authors_to_process}명의 저자 정보 강화를 시작합니다...")

    except Exception as e:
        logging.error(f"오류: 전체 저자 수를 가져오는 데 실패했습니다. Neo4j DB 연결을 확인하세요. - {e}")
        return

    processed_count = 0
    start_time = time.time() # 작업 시작 시간 기록

    while True:
        try:
            with driver.session(database="neo4j") as session:
                # hIndex가 없는 저자 ID 목록을 가져옵니다.
                author_ids = session.execute_read(get_authors_to_enrich)
            
            if not author_ids:
                logging.info("\n처리할 저자가 더 이상 없습니다. 모든 저자 정보 강화 작업이 완료되었습니다.")
                break
                
            logging.info(f"\n{len(author_ids)}명의 저자 정보를 Semantic Scholar API로부터 가져옵니다...")
            
            authors_to_update_batch = []
            for author_id in author_ids:
                try:
                    response = requests.get(
                        f"{AUTHOR_API_URL}{author_id}?fields={AUTHOR_FIELDS}",
                        headers=headers,
                        timeout=30 # API 호출 타임아웃 설정
                    )
                    response.raise_for_status() # HTTP 오류 발생 시 예외 발생
                    data = response.json()
                    
                    details = {
                        'hIndex': data.get('hIndex'),
                        'paperCount': data.get('paperCount'),
                        'citationCount': data.get('citationCount'),
                    }
                    
                    # 소속 정보 처리 (리스트 중 첫 번째 소속의 이름만 저장)
                    affiliations_list = data.get('affiliations')
                    if affiliations_list and isinstance(affiliations_list, list) and len(affiliations_list) > 0:
                        first_affiliation = affiliations_list[0]
                        if first_affiliation and 'name' in first_affiliation:
                            details['affiliation'] = first_affiliation['name']
                    
                    authors_to_update_batch.append({'authorId': author_id, 'details': details})

                except requests.exceptions.HTTPError as e:
                    logging.warning(f"경고: Author ID '{author_id}' 정보를 가져오는 데 실패했습니다. (HTTP 에러: {e.response.status_code} - {e.response.text})")
                    if e.response.status_code == 429: # Too Many Requests
                        logging.warning("API 속도 제한(429) 발생. 60초간 대기합니다.")
                        time.sleep(60)
                    elif e.response.status_code == 404: # Not Found (해당 저자 ID 없음)
                        logging.info(f"정보를 찾을 수 없는 저자 ID: {author_id}. 스킵합니다.")
                        # 해당 저자에 hIndex=0을 설정하여 다시 조회되지 않도록 처리 (선택 사항)
                        # session.execute_write("MATCH (a:Author {authorId: $authorId}) SET a.hIndex = 0", authorId=author_id)
                        pass
                    else:
                        logging.warning(f"기타 HTTP 오류. 15초 후 다음 저자로 넘어갑니다.")
                        time.sleep(15) # 일반적인 HTTP 오류
                except requests.exceptions.RequestException as e:
                    logging.error(f"네트워크/연결 오류 발생: {author_id} - {e}. 15초 후 재시도합니다.")
                    time.sleep(15)
                except Exception as e:
                    logging.error(f"알 수 없는 에러 발생: {author_id} - {e}")
                    time.sleep(5) # 알 수 없는 오류 발생 시 잠시 대기

                # API 호출 간 지연
                time.sleep(1.5 if S2_API_KEY else 3.1) # 키가 있으면 1.5초, 없으면 3.1초 지연

            if authors_to_update_batch:
                with driver.session(database="neo4j") as session:
                    session.execute_write(update_author_details, authors_to_update_batch)
                processed_count += len(authors_to_update_batch)
                
                percentage = (processed_count / total_authors_to_process) * 100
                elapsed_time = time.time() - start_time
                
                # 남은 예상 시간 계산
                etr_formatted = "계산 중..."
                if processed_count > 0:
                    time_per_item = elapsed_time / processed_count
                    remaining_items = total_authors_to_process - processed_count
                    etr_seconds = remaining_items * time_per_item
                    etr_formatted = format_time(etr_seconds)

                progress_string = (
                    f"업데이트 완료: {len(authors_to_update_batch)}명. "
                    f"총 진행: {processed_count}/{total_authors_to_process} ({percentage:.2f}%) - "
                    f"남은 예상 시간: {etr_formatted}"
                )
                logging.info(progress_string)
            else:
                logging.info("이번 배치에서 업데이트할 저자 정보가 없었습니다.")

        except Exception as e:
            logging.error(f"메인 루프 실행 중 오류 발생: {e}")
            time.sleep(10) # 치명적인 오류 발생 시 대기

    logging.info("="*30 + " 저자 정보 강화 작업 완료 " + "="*30)
    # 모든 작업 완료 후 Neo4j 드라이버 연결 종료
    driver.close()

# --- 5. 스크립트 실행 ---
if __name__ == '__main__':
    enrich_authors()
