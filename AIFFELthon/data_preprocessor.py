import requests
import json
import time
import os
from tqdm import tqdm
import logging
import random # `random` 모듈은 현재 코드에서 직접 사용되지 않으므로 제거 가능하지만, 이전 버전과의 일관성을 위해 유지.
import shutil # `shutil` 모듈은 현재 코드에서 직접 사용되지 않으므로 제거 가능.

# --- 0. 로깅 설정 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sociology_data_preprocessor.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# --- 1. 설정 ---

# 데이터 디렉토리 (data_collector.py와 동일하게 설정)
DATA_DIR = "semantic_scholar_sociology_data"

# 원본 데이터 파일 (data_collector.py에서 생성된 Raw Data)
RAW_PAPER_NODE_FILE = os.path.join(DATA_DIR, "sociology_papers_core_data.jsonl")
RAW_AUTHOR_NODE_FILE = os.path.join(DATA_DIR, "sociology_authors.jsonl")
RAW_EDGE_DATA_FILE = os.path.join(DATA_DIR, "sociology_edges.jsonl")

# 전처리된 데이터를 저장할 파일
CLEANED_PAPER_NODE_FILE = os.path.join(DATA_DIR, "sociology_papers_cleaned.jsonl")
CLEANED_AUTHOR_NODE_FILE = os.path.join(DATA_DIR, "sociology_authors_cleaned.jsonl")
CLEANED_EDGE_DATA_FILE = os.path.join(DATA_DIR, "sociology_edges_cleaned.jsonl")

# API 요청 필드 (누락 노드 복구 시 필요)
PAPER_DETAILS_FIELDS = "paperId,title,abstract,authors,language" # 복구 시 필요한 최소 필드
AUTHOR_DETAILS_FIELDS = "authorId,name" # 복구 시 필요한 최소 필드

# 논문 및 저자 식별자 필드
PRIMARY_ID_FIELD = "paperId"

# 필터링 조건 (초록 단어 수)
MIN_ABSTRACT_WORDS = 100

# API 관련 설정 (누락 노드 복구 시 사용)
# Semantic Scholar API 키를 환경 변수에서 로드합니다.
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY") 
if not API_KEY:
    logging.warning("API 키가 설정되지 않았습니다. 누락 노드 복구 기능이 제한될 수 있습니다. .env 파일에 SEMANTIC_SCHOLAR_API_KEY를 설정하세요.")
HEADERS = {"x-api-key": API_KEY} if API_KEY else {}


# --- 2. 보조 함수 ---

def load_ids_from_file(filename, id_key):
    """
    지정된 .jsonl 파일에서 특정 키에 해당하는 ID 목록을 로드합니다.
    파일이 존재하지 않으면 빈 set을 반환합니다.
    """
    ids = set()
    if not os.path.exists(filename):
        logging.info(f"파일 '{os.path.basename(filename)}'이(가) 존재하지 않습니다. 빈 ID 집합을 반환합니다.")
        return ids
    
    logging.info(f"'{os.path.basename(filename)}' 파일에서 '{id_key}' 로드를 시작합니다...")
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                item_id = data.get(id_key)
                if item_id:
                    ids.add(str(item_id))
            except (json.JSONDecodeError, AttributeError) as e:
                logging.warning(f"'{os.path.basename(filename)}'에서 ID 로드 중 파싱 오류: {line.strip()} - {e}. 건너뜁니다.")
                continue
    logging.info(f"ID 로드 완료. 총 {len(ids)}개의 유효한 '{id_key}'를 찾았습니다.")
    return ids

def read_jsonl_file(filename):
    """지정된 .jsonl 파일에서 데이터를 읽어들입니다."""
    data = []
    if not os.path.exists(filename):
        logging.warning(f"파일을 찾을 수 없습니다: {filename}")
        return data
    
    logging.info(f"'{os.path.basename(filename)}' 파일에서 데이터 로드를 시작합니다...")
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError:
                logging.error(f"JSON 파싱 오류 발생: {line.strip()}")
                continue
    logging.info(f"데이터 로드 완료. 총 {len(data)}개의 항목을 읽었습니다.")
    return data

def write_jsonl_file(data_list, filename):
    """데이터 목록을 .jsonl 파일에 저장합니다."""
    logging.info(f"'{os.path.basename(filename)}' 파일에 데이터 쓰기를 시작합니다...")
    with open(filename, 'w', encoding='utf-8') as f:
        for item in data_list:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    logging.info(f"데이터 쓰기 완료. 총 {len(data_list)}개의 항목을 저장했습니다.")

def append_to_jsonl(data_list, filename):
    """
    데이터 목록을 .jsonl 파일에 추가합니다.
    """
    if not data_list:
        return
    with open(filename, 'a', encoding='utf-8') as f:
        for item in data_list:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

def make_api_request(url, headers, timeout=60, retries=5, initial_wait=15, is_post=False, json_data=None):
    """
    API 요청을 수행하고 오류 발생 시 재시도합니다. POST 요청도 지원합니다.
    """
    for i in range(retries):
        try:
            if is_post:
                response = requests.post(url, headers=headers, json=json_data, timeout=timeout)
            else:
                response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP 오류 발생 (시도 {i+1}/{retries}): {e} for URL: {url}")
            if e.response.status_code == 400:
                logging.warning(f"잘못된 요청 오류 (400). 이 요청은 스킵합니다.")
                return None
            wait_time = initial_wait * (2 ** i)
            if e.response.status_code == 429:
                wait_time = max(wait_time, 60)
                logging.warning(f"API 속도 제한(429) 발생. {wait_time}초간 대기합니다.")
            elif e.response.status_code >= 500:
                wait_time = max(wait_time, 30)
                logging.warning(f"API 서버 오류({e.response.status_code}) 발생. {wait_time}초 후 재시도합니다.")
            else:
                logging.warning(f"기타 HTTP 오류. {wait_time}초 후 재시도합니다.")
            time.sleep(wait_time)
        except requests.exceptions.RequestException as e:
            logging.error(f"네트워크 연결 오류 발생 (시도 {i+1}/{retries}): {e}. {initial_wait}초 후 재시도합니다.")
            time.sleep(initial_wait)
    logging.error(f"최대 재시도 횟수 초과. 요청 실패: {url}")
    return None

def is_valid_paper_for_preprocessing(paper_data, min_abstract_words):
    """
    논문이 전처리 단계의 품질 조건을 만족하는지 확인합니다.
    Args:
        paper_data (dict): 논문 데이터 딕셔너리.
        min_abstract_words (int): 초록의 최소 단어 수.
    Returns:
        bool: 논문이 유효하고 관련성이 있으면 True, 그렇지 않으면 False.
    """
    # 1. paperId, title, abstract 존재 여부 확인
    if not paper_data.get('paperId') or not paper_data.get('title') or not paper_data.get('abstract'):
        return False

    # 2. 초록(abstract)이 존재하고, 최소 단어 수 이상인가?
    abstract = paper_data.get('abstract')
    if not abstract or len(str(abstract).split()) < min_abstract_words:
        return False
    
    # 3. 참고문헌(references)과 피인용(citations) 정보가 모두 존재하는가?
    # 이 필터는 연결 정보가 없는 논문을 제외하는 데 사용될 수 있습니다.
    # Semantic Scholar API 응답 구조를 고려하여, references/citations 키는 있을 수 있으나,
    # 그 안에 paperId 필드가 실제 논문을 가리키는 유효한 데이터가 없을 수 있습니다.
    # 여기서는 단순히 키의 존재 여부만 확인합니다.
    if 'references' not in paper_data or 'citations' not in paper_data:
        return False
    
    # 4. 언어 필터링 (영어 논문만 허용)
    paper_language = paper_data.get('language')
    if not paper_language or paper_language.lower() != 'en':
        return False

    # (이 부분은 data_collector에서 필터링을 수행하므로,
    # 전처리 단계에서는 다시 엄격하게 저널/연구 분야를 필터링할 필요는 없을 수 있습니다.
    # 하지만 데이터 무결성 검증 차원에서 유지하는 것은 좋습니다.)
    # 5. 연구 분야 또는 저널/발행처 이름 필터링 (data_collector.py의 논리 재사용)
    TARGET_SOCIOLOGY_JOURNALS = { 
        "young - nordic journal of youth research", "american journal of sociology", "social forces",
        "demography", "sociological symposium", "sociological science",
        "sociological methodology", "social science research", "sociological analysis",
        "sociological bulletin", "sociological abstracts", "sociological jurisprudence journal",
        "sociological forum (randolph, n.j.)", "sociological theory",
        "sociological methods & research", "sociological perspectives", "sociological research",
        "sociological studies of children and youth", "sociological practice",
        "british journal of sociology", "sociological inquiry", "sociological journal",
        "sociological spectrum", "american sociological review", "journal of health and social behavior",
        "sociologia da educação", "gender & society", "sociology of health and illness",
        "sociological research online", "the sociological quarterly", "theory and society",
        "sociology of race and ethnicity", "men and masculinities", "sexualities",
        "politics & society", "cultural sociology", "current sociology", "social networks",
        "qualitative sociology", "european sociological review", "contexts",
        "social indicators research", "ethnic and racial studies", "advances in group processes",
        "socius", "social psychology quarterly", "social science & medicine (1967)",
        "social science & medicine medical psychology and medical sociology", "sociology compass",
        "journal of marriage and family", "city & society", "city & community",
        "work and occupations", "social problems", "the annual review of sociology"
    }
    TARGET_FIELD_OF_STUDY = "sociology"

    fields_of_study = paper_data.get("fieldsOfStudy", [])
    journal_name = ""
    journal_info = paper_data.get("journal")
    if journal_info and journal_info.get("name"):
        journal_name = journal_info.get("name", "").lower()
    elif paper_data.get("venue"):
        journal_name = paper_data.get("venue", "").lower()

    is_relevant_field = fields_of_study and any(TARGET_FIELD_OF_STUDY in str(field).lower() for field in fields_of_study)
    is_relevant_journal = journal_name in TARGET_SOCIOLOGY_JOURNALS

    if not (is_relevant_field or is_relevant_journal):
        return False
        
    return True


# --- 3. 핵심 전처리 로직 ---

def recover_missing_nodes_from_edges():
    """
    엣지 파일 기준으로 누락된 논문/저자 노드가 있는지 확인하고 API로 정보를 복구하여 해당 노드 파일에 추가합니다.
    """
    logging.info("\n" + "="*30 + " 누락 노드 복구 단계 시작 " + "="*30)
    
    if not os.path.exists(RAW_EDGE_DATA_FILE):
        logging.info(f"엣지 파일 '{RAW_EDGE_DATA_FILE}'이(가) 없어 노드 복구 단계를 건너뜁니다.")
        return

    # 1. 현재 모든 논문 및 저자 ID 로드
    existing_paper_ids = load_ids_from_file(RAW_PAPER_NODE_FILE, PRIMARY_ID_FIELD)
    existing_author_ids = load_ids_from_file(RAW_AUTHOR_NODE_FILE, 'authorId')

    # 2. 엣지 파일을 순회하며 누락된 노드 ID 수집
    missing_paper_ids = set()
    missing_author_ids = set()
    logging.info(f"'{os.path.basename(RAW_EDGE_DATA_FILE)}' 파일을 확인하여 누락된 노드를 찾습니다...")
    with open(RAW_EDGE_DATA_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                edge = json.loads(line)
                source_id, target_id, relation = edge.get('source'), edge.get('target'), edge.get('relation')

                if not (source_id and target_id and relation):
                    continue # 유효하지 않은 엣지 건너뛰기

                # WROTE 관계: source=author, target=paper
                if relation == 'WROTE':
                    if source_id not in existing_author_ids: missing_author_ids.add(source_id)
                    if target_id not in existing_paper_ids: missing_paper_ids.add(target_id)
                # CITES/REFERENCES 관계: source=paper, target=paper
                else: # CITES, REFERENCES
                    if source_id not in existing_paper_ids: missing_paper_ids.add(source_id)
                    if target_id not in existing_paper_ids: missing_paper_ids.add(target_id)
            except (json.JSONDecodeError, KeyError) as e:
                logging.warning(f"엣지 파싱 중 오류: {line.strip()} - {e}. 건너뜁니다.")
                continue
    
    # 3. 누락된 논문 정보 복구 (API 호출)
    if missing_paper_ids:
        logging.info(f"{len(missing_paper_ids)}개의 누락된 논문 노드를 발견했습니다. API로 정보를 복구합니다.")
        recovered_papers = []
        for paper_id in tqdm(list(missing_paper_ids), desc="누락 논문 복구 중"):
            url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields={PAPER_DETAILS_FIELDS}"
            paper_data = make_api_request(url, HEADERS)
            if paper_data and paper_data.get(PRIMARY_ID_FIELD):
                recovered_papers.append(paper_data)
            time.sleep(1.2) # API 호출 간 지연
        
        if recovered_papers:
            append_to_jsonl(recovered_papers, RAW_PAPER_NODE_FILE)
            logging.info(f"-> {len(recovered_papers)}개의 논문 노드 복구 완료. '{os.path.basename(RAW_PAPER_NODE_FILE)}'에 추가됨.")
        else:
            logging.info("-> 복구할 유효한 논문 노드가 없었습니다.")

    # 4. 누락된 저자 정보 복구 (API 호출)
    if missing_author_ids:
        logging.info(f"{len(missing_author_ids)}개의 누락된 저자 노드를 발견했습니다. API로 정보를 복구합니다.")
        recovered_authors = []
        for author_id in tqdm(list(missing_author_ids), desc="누락 저자 복구 중"):
            url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}?fields={AUTHOR_DETAILS_FIELDS}"
            author_data = make_api_request(url, HEADERS)
            if author_data and author_data.get('authorId'):
                recovered_authors.append(author_data)
            time.sleep(1.2) # API 호출 간 지연
        
        if recovered_authors:
            append_to_jsonl(recovered_authors, RAW_AUTHOR_NODE_FILE)
            logging.info(f"-> {len(recovered_authors)}개의 저자 노드 복구 완료. '{os.path.basename(RAW_AUTHOR_NODE_FILE)}'에 추가됨.")
        else:
            logging.info("-> 복구할 유효한 저자 노드가 없었습니다.")

    if not missing_paper_ids and not missing_author_ids:
        logging.info("누락된 노드가 없어 복구 작업을 건너뛰었습니다.")
        
    logging.info("="*32 + " 노드 복구 완료 " + "="*32 + "\n")


def clean_and_filter_data():
    """
    수집된 원시 데이터를 전처리하여 필터링 조건을 만족하는 데이터만 저장합니다.
    - 논문: 초록 유무, 초록 길이, 언어(영어), 주요 필드/저널 관련성 필터링.
    - 저자: 중복 제거 및 유효한 authorId 확인.
    - 엣지: 연결된 노드가 모두 유효한 노드(논문/저자) ID 집합에 포함되는지 확인.
    """
    logging.info("\n" + "="*30 + " 데이터 정제 및 필터링 단계 시작 " + "="*30)

    # 1. 논문 데이터 클리닝 및 필터링
    logging.info(f"'{os.path.basename(RAW_PAPER_NODE_FILE)}' 파일에서 유효하지 않은 논문을 제거합니다...")
    raw_papers = read_jsonl_file(RAW_PAPER_NODE_FILE)
    
    valid_papers = []
    valid_paper_ids = set() # 유효한 논문 ID만 저장하여 엣지 필터링에 사용
    
    for paper in tqdm(raw_papers, desc="논문 필터링 중"):
        if is_valid_paper_for_preprocessing(paper, MIN_ABSTRACT_WORDS):
            valid_papers.append(paper)
            valid_paper_ids.add(paper[PRIMARY_ID_FIELD])
    
    write_jsonl_file(valid_papers, CLEANED_PAPER_NODE_FILE)
    logging.info(f"논문 노드 정제 완료. {len(raw_papers)}개 중 {len(valid_papers)}개 유지. '{os.path.basename(CLEANED_PAPER_NODE_FILE)}'에 저장됨.")

    # 2. 저자 데이터 중복 제거 및 유효성 확인
    logging.info(f"'{os.path.basename(RAW_AUTHOR_NODE_FILE)}' 파일에서 저자 데이터를 정제합니다...")
    raw_authors = read_jsonl_file(RAW_AUTHOR_NODE_FILE)
    unique_authors = {} # authorId 기준으로 중복 제거
    
    for author in raw_authors:
        author_id = author.get('authorId')
        if author_id and author.get('name'): # ID와 이름이 모두 있는 유효한 저자만
            unique_authors[author_id] = author
    
    cleaned_authors = list(unique_authors.values())
    valid_author_ids = set(author['authorId'] for author in cleaned_authors) # 유효한 저자 ID만 저장
    
    write_jsonl_file(cleaned_authors, CLEANED_AUTHOR_NODE_FILE)
    logging.info(f"저자 노드 정제 완료. {len(raw_authors)}개 중 {len(cleaned_authors)}개 유지. '{os.path.basename(CLEANED_AUTHOR_NODE_FILE)}'에 저장됨.")

    # 3. 엣지 데이터 필터링 (유효한 노드에 연결된 엣지만 유지)
    logging.info(f"'{os.path.basename(RAW_EDGE_DATA_FILE)}' 파일에서 유효하지 않은 노드에 연결된 엣지를 제거합니다...")
    raw_edges = read_jsonl_file(RAW_EDGE_DATA_FILE)
    
    # 논문 및 저자의 모든 유효한 ID를 통합
    all_valid_node_ids = valid_paper_ids.union(valid_author_ids)

    cleaned_edges = []
    for edge in tqdm(raw_edges, desc="엣지 필터링 중"):
        source_id = edge.get('source')
        target_id = edge.get('target')
        relation = edge.get('relation')

        # source, target, relation 필드가 모두 존재하고, 양쪽 노드가 유효한 ID 집합에 속해야 함
        if source_id and target_id and relation and \
           source_id in all_valid_node_ids and target_id in all_valid_node_ids:
            cleaned_edges.append(edge)
    
    write_jsonl_file(cleaned_edges, CLEANED_EDGE_DATA_FILE)
    logging.info(f"엣지 정제 완료. {len(raw_edges)}개 중 {len(cleaned_edges)}개 유지. '{os.path.basename(CLEANED_EDGE_DATA_FILE)}'에 저장됨.")
    
    logging.info("="*32 + " 데이터 정제 및 필터링 완료 " + "="*32 + "\n")


# --- 4. 메인 전처리 실행 함수 ---

def run_data_preprocessor():
    """
    데이터 전처리 스크립트의 메인 실행 함수입니다.
    이 함수는 누락 노드를 복구한 후 데이터를 정제합니다.
    """
    print_step_header("데이터 전처리 파이프라인 시작")
    
    # 1. 엣지 파일 기준으로 누락된 논문/저자 노드 정보 복구 (필요시 API 호출)
    recover_missing_nodes_from_edges()

    # 2. 수집된 모든 Raw 데이터를 필터링하고 정제하여 Cleaned 파일 생성
    clean_and_filter_data()

    print_step_footer("데이터 전처리 파이프라인 완료")

# --- 5. 스크립트 실행 ---
if __name__ == '__main__':
    run_data_preprocessor()
