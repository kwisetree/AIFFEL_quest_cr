import requests
import json
import time
import os
from tqdm import tqdm
import logging
import random
import re
from collections import deque # 논문/저자 큐를 명시적으로 사용하지는 않으나, 기존 코드의 import를 유지

# --- 0. 로깅 설정 ---
# 디버깅 및 진행 상황 추적을 위해 파일과 콘솔에 로그를 남깁니다.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sociology_data_collection.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# --- 1. 환경 변수 로드 ---
from dotenv import load_dotenv
load_dotenv()

# Semantic Scholar API 키를 환경 변수에서 로드합니다.
API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY") 
if not API_KEY:
    logging.warning("API 키가 설정되지 않았습니다. API 요청 제한이 더 엄격할 수 있으며, 서비스가 제한될 수 있습니다. .env 파일에 SEMANTIC_SCHOLAR_API_KEY를 설정하세요.")

# --- 2. 설정 ---

# 데이터 저장 디렉토리 및 파일명
DATA_DIR = "semantic_scholar_sociology_data"
os.makedirs(DATA_DIR, exist_ok=True) # 데이터 디렉토리가 없으면 생성

PAPER_NODE_FILE = os.path.join(DATA_DIR, "sociology_papers_core_data.jsonl") # 논문 상세 정보 (노드) 파일
AUTHOR_NODE_FILE = os.path.join(DATA_DIR, "sociology_authors.jsonl")       # 저자 정보 (노드) 파일
EDGE_DATA_FILE = os.path.join(DATA_DIR, "sociology_edges.jsonl")           # 연결 관계 (엣지) 정보 파일

# 진행 상황 저장 파일 (일반 검색, 특정 제목 검색, 그래프 확장 진행 상황을 모두 포함)
# 이 파일은 각 수집 단계의 재시작 지점을 기록합니다.
STATE_FILE = os.path.join(DATA_DIR, "data_collection_state.json")

# 일반 검색을 위한 키워드
GENERAL_QUERY_KEYWORDS = ("social psychology", "sociology", "sociology of emotion")

# 특정 논문 제목 목록 (사용자가 수동으로 지정한 중요 논문)
SPECIFIC_PAPER_TITLES = [
    "Populism Versus Nativism: Socio-Economic, Socio-Cultural, and Emotional Predictors",
    "Two Theoretical Models of Subcultural Anger—Synthesizing Subcultural Theory with the Sociology of Emotions and Exploring Anger in Hip Hop",
    "Evolving Emotion, Situated Context, and Movement Activism: The Case of Bereaved Families in South Korea",
    "What Makes a Relationship Serious? Race, Religion, and Emotions in South Asian Muslim Immigrants’ Romantic Meaning-Making",
    "Do Societies Have Emotions?",
    "Doing Gender, Avoiding Crime: The Gendered Meaning of Criminal Behavior and the Gender Gap in Offending in the United States",
    "The Sociology of Emotions: Feminist, Cultural and Sociological Perspectives",
    "How kindness took a hold: A sociology of emotions, attachment and everyday enchantment",
    "Masculinity Challenged: Emotional Responses to State Support for Women’s Employment in the United Arab Emirates",
    "‘An emotional stalemate’: cold intimacies in heterosexual young people’s dating practices",
    "The tempest within: the origins and outcomes of intense national emotions in times of national division",
    "Research Handbook on the Sociology of Emotion: Institutions and Emotional Rule Regimes",
    "The Managed Response: Digital Emotional Labor in Navigating Intersectional Cyber Aggression",
    "Emotional Benefits of Leader Legitimacy",
    "Emotion Theory: The Routledge Comprehensive Guide: Volume I: History, Contemporary Theories, and Key Elements",
    "Emotion Theory: The Routledge Comprehensive Guide: Volume II: Theories of Specific Emotions and Major Theoretical Challenges",
    "Emotional Pathway to Activism: Emotional Intimacy with Social Minorities and Engagement in Activism in South Korea",
    "Beyond the Feeling Individual: Insights from Sociology on Emotions and Embeddedness",
    "Discrimination in Sentencing: Showing Remorse and the Intersection of Race and Gender",
    "Undocumented Again? DACA Rescission, Emotions, and Incorporation Outcomes among Young Adults",
    "A Network Approach to Assessing the Relationship between Discrimination and Daily Emotion Dynamics",
    "Demonstrating Anticipatory Deflection and a Preemptive Measure to Manage It: An Extension of Affect Control Theory",
    "Emotions in the Perspective of Sociology",
    "(Not) Feeling the Past: Boredom as a Racialized Emotion",
    "Epistemic emotions in prosecutorial decision making",
    "Adolescent Partnership Quality and Emotional Health: Insights from an Intensive Longitudinal Study",
    "To Forgive Is Divine? Morality and the Status Value of Intergroup Revenge and Forgiveness",
    "(Dis)passionate law stories: the emotional processes of encoding narratives in court",
    "Affect, Power, and Institutions",
    "Airing Egypt’s Dirty Laundry: BuSSy’s Storytelling as Feminist Social Change",
    "What happens on the backstage? Emotion work and LGBTQ activism in a collectivist culture",
    "Dystopian emotions: emotional landscapes and dark futures",
    "Fight‐or‐Flight for America: The Affective Conditioning of Christian Nationalist Ideological Views During the Transition to Adulthood",
    "The Social Effects of Emotions",
    "Prosecutors’ Habituation of Emotion Management in Swedish Courts",
    "The Sociology of Emotions in Latin America",
    "The Routledge Companion to Romantic Love",
    "The Emotions in Cultural-Historical Activity Theory: Personality, Emotion and Motivation in Social Relations and Activity",
    "Ressentiment: A Complex Emotion or an Emotional Mechanism of Psychic Defences?",
    "Wanting a “Feminist Abortion Experience”: Emotion Work, Collective Identity, and Pro‐Choice Discourse",
    "Doing Casual Sex: A Sexual Fields Approach to the Emotional Force of Hookup Culture",
    "Grief, Care, and Play: Theorizing the Affective Roots of the Social Self",
    "The Promise of Emotion Practice: At the Bedside and Beyond",
    "The Affective Self: Perseverance of Self-Sentiments in Late-Life Dementia",
    "Emotions and Medical Decision-Making",
    "Critical happiness studies",
    "Unpacking the Parenting Well-Being Gap: The Role of Dynamic Features of Daily Life across Broader Social Contexts",
    "Adolescence, Empathy, and the Gender Gap in Delinquency",
    "Future of our Feelings: Sociological Considerations about Emotional Culture in Pandemic Er",
    "Addressing Emotional Health while Protecting Status: Asian American and White Parents in Suburban America",
    "Feeling Race: Theorizing the Racial Economy of Emotions",
    "Alienation and emotion: social relations and estrangement in contemporary capitalism",
    "Emotions and Loneliness in a Networked Society",
    "Towards an understanding of loneliness among Australian men: Gender cultures, embodied expression and the social bases of belonging",
    "Interactionism and the Sociology of Emotions",
    "The End of Love: a Sociology of Negative Relations",
    "Emotions in Late Modernity",
    "The Formation of Group Ties in Open Interaction Groups",
    "Affect as Methodology: Feminism and the Politics of Emotion1",
    "Empowered: popular feminism and popular misogyny",
    "Villains, Victims, and Heroes in Character Theory and Affect Control Theory",
    "Emotions and empathic imagination: parents relating to norms of work, parenthood and gender equality",
    "Depressive love: a social pathology",
    "Mediating Neoliberal Capitalism: Affect, Subjectivity and Inequality",
    "Emotional Dynamics of Right- and Left-wing Political Populism",
    "Are men getting more emotional? Critical sociological perspectives on men, masculinities and emotions",
    "The affective, cultural and psychic life of postfeminism: A postfeminist sensibility 10 years on",
    "Confidence culture and the remaking of feminism",
    "Emotions as Commodities: Capitalism, Consumption, and Authenticity",
    "The sociology of emotions: A meta-reflexive review of a theoretical tradition in flux",
    "Generalising men’s affective experiences",
    "The Emotional Underpinnings of Populism: How Anger and Fear Affect Populist Attitudes",
    "American Hookup: The New Culture of Sex on Campus",
    "Heinous Crime or Unfortunate Incident: Does Gender Matter?",
    "A Sociological Perspective on Emotions in the Judiciary",
    "The sociology of emotions: Four decades of progress",
    "Genealogies of Emotions, Intimacies, and Desire",
    "Theorizing emotional capital",
    "Correcting Behaviors and Policing Emotions: How Behavioral Infractions Become Feeling‐Rule Violations",
    "What Scientists Who Study Emotion Agree About",
    "Strangers in Their Own Land: Anger and Mourning on the American Right",
    "New Ways of Being a Man: “Positive” Hegemonic Masculinity in Meditation-based Communities of Practice",
    "Why Do People Regulate Their Emotions? A Taxonomy of Motives in Emotion Regulation",
    "Using Identity Processes to Understand Persistent Inequality in Parenting",
    "Learning to “Deal” and “De‐escalate”: How Men in Nursing Manage Self and Patient Emotions",
    "Examining Men’s Status Shield and Status Bonus: How Gender Frames the Emotional Labor and Job Satisfaction of Nurses",
    "The Power of Love: The Role of Emotional Attributions and Standards in Heterosexuals' Attitudes toward Lesbian and Gay Couples",
    "Men’s Emotions: Heteromasculinity, Emotional Reflexivity, and Intimate Relationships",
    "Go with Your Gut: Emotion and Evaluation in Job Interviews",
    "Emotion Management: Sociological Insight into What, How, Why, and to What End?",
    "The Role of Cultural Meanings and Situated Interaction in Shaping Emotion",
    "Sociological Scholarship on Gender Differences in Emotion and Emotional Well-Being in the United States: A Snapshot of the Field",
    "Handbook of the Sociology of Emotions: Volume II",
    "A Social Model of Persistent Mood States",
    "Occupational Status and the Experience of Anger",
    "Future Directions in the Sociology of Emotions",
    "Handbook of the sociology of emotions",
    "The Sociology of Emotions"
]

# API 요청 시 한 번에 처리할 논문 개수 (일괄 조회 시 사용)
BATCH_SIZE = 50 

# API 요청 시 한 번에 가져올 논문 개수 (API 최대 100개)
LIMIT_PER_REQUEST = 100

# 최종적으로 수집할 최대 논문 수 (일반 검색용)
MAX_TOTAL_PAPERS_GENERAL_SEARCH = 10000000 

# 초기 시드 논문 검색을 위한 목표 논문 수 (PAPER_NODE_FILE이 비어있을 경우)
INITIAL_SEED_LIMIT = 1000

# 몇 개의 프론티어 논문을 처리한 후, 신규 노드 수집 및 저장을 할지 결정 (그래프 확장 시)
SAVE_INTERVAL_EXPANSION = 50

# 일반 검색 시 필터링을 위한 최소 초록 단어 수
MIN_ABSTRACT_WORDS = 50

# 검색할 연도 범위 설정
START_YEAR = 2025
END_YEAR = 1950 # 1950년까지 포함

# API 요청 필드 (논문 상세 정보)
PAPER_DETAILS_FIELDS = (
    "paperId,corpusId,externalIds,url,title,abstract,authors,year,journal,venue,fieldsOfStudy,"
    "publicationTypes,publicationDate,citationCount,referenceCount,language" # language 필드 포함
)

# 엣지 및 저자 정보를 가져올 필드 목록
CONNECTION_FIELDS = "references.paperId,citations.paperId,authors.authorId,authors.name"

# 모든 논문에 대해 주 식별자로 사용할 필드
PRIMARY_ID_FIELD = "paperId"

# 일반 검색 시 필터링을 위한 타겟 저널 목록 (소문자로 통일)
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


# --- 3. 보조 함수 ---

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

def load_priority_ids_from_file(filename, id_key, num_lines):
    """
    지정된 .jsonl 파일의 첫 N개 줄에서 ID 목록을 순서대로 로드합니다.
    파일이 존재하지 않으면 빈 리스트를 반환합니다.
    """
    priority_ids = []
    if not os.path.exists(filename):
        logging.info(f"우선순위 ID 파일 '{os.path.basename(filename)}'이(가) 존재하지 않습니다. 빈 리스트를 반환합니다.")
        return priority_ids
    
    logging.info(f"'{os.path.basename(filename)}' 파일에서 우선순위 ID 로드를 시작합니다 (첫 {num_lines}개).")
    with open(filename, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= num_lines:
                break
            try:
                data = json.loads(line)
                item_id = data.get(id_key)
                if item_id:
                    priority_ids.append(str(item_id))
            except (json.JSONDecodeError, AttributeError) as e:
                logging.warning(f"우선순위 ID 로드 중 {i+1}번째 줄 파싱 오류: {line.strip()} - {e}. 건너뜁니다.")
                continue
    logging.info(f"우선순위 ID 로드 완료. 총 {len(priority_ids)}개의 유효한 우선순위 ID를 찾았습니다.")
    return priority_ids

def load_state(filename):
    """
    이전 수집/확장 진행 상황을 단일 파일에서 로드합니다.
    파일이 존재하지 않으면 기본값을 반환합니다.
    """
    if not os.path.exists(filename):
        logging.info(f"상태 파일 '{os.path.basename(filename)}'이(가) 존재하지 않습니다. 초기 상태로 시작합니다.")
        return {
            "general_search_offset": 0,
            "general_search_current_year": START_YEAR,
            "processed_specific_titles": [],
            "processed_expansion_ids": [],
            "last_api_call_counter": 0
        }
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            state = json.load(f)
            logging.info(f"상태 파일 로드 완료: {state}")
            return state
    except (json.JSONDecodeError, IOError) as e:
        logging.warning(f"상태 파일 로드 실패: {e}. 초기 상태로 시작합니다.")
        return {
            "general_search_offset": 0,
            "general_search_current_year": START_YEAR,
            "processed_specific_titles": [],
            "processed_expansion_ids": [],
            "last_api_call_counter": 0
        }


def save_state(state, filename):
    """
    현재 수집/확장 진행 상황을 단일 파일에 저장합니다.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=4)
    logging.info(f"상태 파일 저장 완료. (일반 검색 Year: {state.get('general_search_current_year')}, Offset: {state.get('general_search_offset')}, 처리된 확장 ID: {len(state.get('processed_expansion_ids'))})")


def append_to_jsonl(data_list, filename):
    """
    데이터 목록을 .jsonl 파일에 추가합니다.
    """
    if not data_list:
        return
    with open(filename, 'a', encoding='utf-8') as f:
        for item in data_list:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def is_valid_and_relevant(paper_data):
    """
    논문이 모든 품질 조건을 만족하는지 확인합니다.
    이 함수는 주로 초기 시드 논문 수집에 사용됩니다.
    Args:
        paper_data (dict): 논문 데이터 딕셔너리.
    Returns:
        bool: 논문이 유효하고 관련성이 있으면 True, 그렇지 않으면 False.
    """
    # 1. 초록 단어 수 필터링
    abstract = paper_data.get('abstract')
    if not abstract or len(str(abstract).split()) < MIN_ABSTRACT_WORDS: # abstract가 None이거나 비어있을 경우 str() 변환
        return False
    
    # 2. 언어 필터링 (영어 논문만 허용)
    paper_language = paper_data.get('language')
    if not paper_language or paper_language.lower() != 'en':
        return False

    # 3. 연구 분야 필터링
    fields_of_study = paper_data.get("fieldsOfStudy", [])
    if fields_of_study and any(TARGET_FIELD_OF_STUDY in str(field).lower() for field in fields_of_study):
        return True
    
    # 4. 저널/발행처 이름 필터링
    journal_name = ""
    journal_info = paper_data.get("journal")
    if journal_info and journal_info.get("name"):
        journal_name = journal_info.get("name", "").lower()
    elif paper_data.get("venue"):
        journal_name = paper_data.get("venue", "").lower()

    if journal_name in TARGET_SOCIOLOGY_JOURNALS:
        return True
        
    return False

def make_api_request(url, headers, timeout=60, retries=5, initial_wait=15, is_post=False, json_data=None):
    """
    API 요청을 수행하고 오류 발생 시 재시도합니다. POST 요청도 지원합니다.
    Args:
        url (str): 요청할 API URL.
        headers (dict): 요청 헤더.
        timeout (int): 요청 시간 초과 (초).
        retries (int): 재시도 횟수.
        initial_wait (int): 첫 재시도 전 대기 시간 (초).
        is_post (bool): POST 요청인 경우 True.
        json_data (dict): POST 요청 시 전송할 JSON 데이터.
    Returns:
        dict or None: 성공 시 JSON 응답, 실패 시 None.
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
                return None # 400 Bad Request는 재시도해도 소용없음
            wait_time = initial_wait * (2 ** i) # 지수 백오프
            if e.response.status_code == 429: # Too Many Requests
                wait_time = max(wait_time, 60) # 최소 60초 대기
                logging.warning(f"API 속도 제한(429) 발생. {wait_time}초간 대기합니다.")
            elif e.response.status_code >= 500: # Server Error
                wait_time = max(wait_time, 30) # 최소 30초 대기
                logging.warning(f"API 서버 오류({e.response.status_code}) 발생. {wait_time}초 후 재시도합니다.")
            else:
                logging.warning(f"기타 HTTP 오류. {wait_time}초 후 재시도합니다.")
            time.sleep(wait_time)
        except requests.exceptions.RequestException as e:
            logging.error(f"네트워크 연결 오류 발생 (시도 {i+1}/{retries}): {e}. {initial_wait}초 후 재시도합니다.")
            time.sleep(initial_wait)
    logging.error(f"최대 재시도 횟수 초과. 요청 실패: {url}")
    return None

def search_paper_by_title(title, headers, fields):
    """
    특정 논문 제목으로 Semantic Scholar API를 검색합니다.
    Args:
        title (str): 검색할 논문 제목.
        headers (dict): API 요청 헤더.
        fields (str): 가져올 논문 필드.
    Returns:
        dict or None: 첫 번째 일치하는 논문 데이터 딕셔너리, 없으면 None.
    """
    # 정확도를 높이기 위해 제목을 인용 부호로 묶습니다.
    search_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query=\"{requests.utils.quote(title)}\"&limit=1&fields={fields}"
    logging.info(f"특정 제목 검색 API 요청: {title}")
    data = make_api_request(search_url, headers)
    if data and data.get("data"):
        return data["data"][0] # 첫 번째 결과를 반환
    return None

def fetch_related_papers_and_authors(paper_id, headers, paper_details_fields, connection_fields):
    """
    주어진 논문의 참조, 인용 논문 및 저자 정보를 가져옵니다.
    """
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields={connection_fields}"
    logging.info(f"관계 및 저자 정보 API 요청: {paper_id}")
    paper_data = make_api_request(url, headers)
    
    if not paper_data or not paper_data.get(PRIMARY_ID_FIELD):
        return None, [], [], [] # paper_data, references, citations, authors

    # 1. References
    references = []
    for ref_entry in paper_data.get('references', []):
        ref_id = ref_entry.get(PRIMARY_ID_FIELD)
        if ref_id and ref_entry.get('paperId'): # Ensure paperId is present in ref_entry
            references.append(ref_entry['paperId'])

    # 2. Citations
    citations = []
    for cit_entry in paper_data.get('citations', []):
        cit_id = cit_entry.get(PRIMARY_ID_FIELD)
        if cit_id and cit_entry.get('paperId'): # Ensure paperId is present in cit_entry
            citations.append(cit_entry['paperId'])

    # 3. Authors
    authors_info = []
    for author_entry in paper_data.get('authors', []):
        author_id = author_entry.get('authorId')
        author_name = author_entry.get('name')
        if author_id and author_name:
            authors_info.append({"authorId": author_id, "name": author_name})

    return paper_data, references, citations, authors_info


# --- 4. 통합된 데이터 수집 및 확장 메인 로직 ---

def run_full_data_collection():
    """
    Semantic Scholar API를 통해 사회학 논문 데이터를 초기 수집하고, 
    수집된 논문들을 기반으로 그래프를 확장하는 통합 메인 함수입니다.
    """
    logging.info("="*30 + " SOCY Assistant 데이터 수집 및 확장 시작 " + "="*30)
    
    headers = {"x-api-key": API_KEY} if API_KEY else {}

    # 상태 로드: 일반 검색, 특정 제목 검색, 그래프 확장 진행 상황
    state = load_state(STATE_FILE)

    # 현재까지 수집된 모든 논문 ID (파일에서 로드)
    all_collected_paper_ids = load_ids_from_file(PAPER_NODE_FILE, PRIMARY_ID_FIELD)
    # 현재까지 수집된 모든 저자 ID (파일에서 로드)
    all_existing_author_ids = load_ids_from_file(AUTHOR_NODE_FILE, "authorId")

    # tqdm 프로그레스 바 초기화 (총 논문 수는 유동적이므로, 현재 수집된 논문 수로 초기화)
    pbar = tqdm(initial=len(all_collected_paper_ids), total=MAX_TOTAL_PAPERS_GENERAL_SEARCH, desc="총 수집 논문")
    
    # --- 단계 1: 초기 논문 상세 정보 수집 (GENERAL_QUERY_KEYWORDS 및 SPECIFIC_PAPER_TITLES 기반) ---
    logging.info("--- 1단계: 초기 논문 상세 정보 수집 시작 ---")

    # 1-1. PAPER_NODE_FILE이 비어있으면 초기 일반 검색을 통해 시드 논문 수집
    if not all_collected_paper_ids:
        logging.info(f"논문 노드 파일 '{PAPER_NODE_FILE}'이 비어있습니다. 초기 일반 검색을 수행합니다.")
        current_offset = state['general_search_offset']
        papers_added_in_seed = 0
        
        # tqdm을 사용하여 초기 검색 진행 상황 표시
        initial_search_pbar = tqdm(total=INITIAL_SEED_LIMIT, desc="초기 시드 논문 수집 중", leave=False)

        while papers_added_in_seed < INITIAL_SEED_LIMIT:
            query_param = " OR ".join(GENERAL_QUERY_KEYWORDS)
            search_url = (
                f"https://api.semanticscholar.org/graph/v1/paper/search?"
                f"query={requests.utils.quote(query_param)}&offset={current_offset}&limit={LIMIT_PER_REQUEST}&fields={PAPER_DETAILS_FIELDS}"
            )
            logging.info(f"초기 검색 API 요청: offset={current_offset}")
            
            data = make_api_request(search_url, headers)
            state['last_api_call_counter'] += 1
            if data is None or not data.get("data"):
                logging.info("초기 검색에서 더 이상 논문이 없습니다. 시드 수집을 종료합니다.")
                break
            
            newly_found_papers_in_batch = []
            for paper in data.get("data", []):
                paper_id = paper.get(PRIMARY_ID_FIELD)
                if paper_id and paper_id not in all_collected_paper_ids and is_valid_and_relevant(paper):
                    newly_found_papers_in_batch.append(paper)
                    all_collected_paper_ids.add(paper_id)
                    papers_added_in_seed += 1
            
            if newly_found_papers_in_batch:
                append_to_jsonl(newly_found_papers_in_batch, PAPER_NODE_FILE)
                pbar.update(len(newly_found_papers_in_batch))
                initial_search_pbar.update(len(newly_found_papers_in_batch))
                logging.info(f"-> 초기 검색에서 {len(newly_found_papers_in_batch)}개 논문 추가. 현재 총 {len(all_collected_paper_ids)}개 논문.")
            
            if 'next' in data and data['next'] is not None:
                current_offset = data['next']
            else:
                logging.info("초기 검색 마지막 페이지에 도달했습니다. 시드 수집을 종료합니다.")
                break
            
            time.sleep(1.2) # API 지연
        
        initial_search_pbar.close()
        state['general_search_offset'] = current_offset # 일반 검색 offset 업데이트
        save_state(state, STATE_FILE) # 초기 검색 진행 상황 저장

        if not all_collected_paper_ids:
            logging.error("초기 검색 후에도 논문 노드 파일이 비어있습니다. 작업을 종료합니다.")
            return

    # 1-2. 특정 논문 제목 검색 및 관련 논문 수집
    logging.info("--- 특정 논문 제목 및 관련 논문 수집 시작 ---")
    processed_specific_titles = set(state['processed_specific_titles'])
    
    for title in SPECIFIC_PAPER_TITLES:
        if pbar.n >= MAX_TOTAL_PAPERS_GENERAL_SEARCH:
            logging.info("최대 수집 목표에 도달했습니다. 작업을 종료합니다.")
            break

        if title in processed_specific_titles:
            logging.info(f"이미 처리된 특정 논문 제목: '{title}'. 건너뜁니다.")
            continue

        logging.info(f"논문 제목 검색 중: '{title}'")
        found_paper = search_paper_by_title(title, headers, PAPER_DETAILS_FIELDS) # PAPER_DETAILS_FIELDS 사용
        state['last_api_call_counter'] += 1
        time.sleep(1.2) # API 속도 제한 방지

        papers_to_process = []
        if found_paper:
            logging.info(f"제목 '{title}'에 해당하는 논문 ID '{found_paper.get(PRIMARY_ID_FIELD)}' 발견.")
            papers_to_process.append(found_paper)

            # 참조 및 인용 논문 검색 (CONNECTION_FIELDS 사용)
            _, references_ids, citations_ids, _ = fetch_related_papers_and_authors(
                found_paper[PRIMARY_ID_FIELD], headers, PAPER_DETAILS_FIELDS, CONNECTION_FIELDS
            )
            state['last_api_call_counter'] += 1
            time.sleep(1.2)

            # 새로 발견된 참조/인용 논문의 상세 정보 일괄 수집
            related_paper_ids_to_fetch = list(set(references_ids + citations_ids) - all_collected_paper_ids)
            if related_paper_ids_to_fetch:
                logging.info(f"-> '{title}' 관련 신규 참조/인용 논문 {len(related_paper_ids_to_fetch)}개 상세 정보 수집.")
                batch_details_data = make_api_request(
                    "https://api.semanticscholar.org/graph/v1/paper/batch",
                    headers, is_post=True, json_data={"ids": related_paper_ids_to_fetch, "fields": PAPER_DETAILS_FIELDS}
                )
                state['last_api_call_counter'] += 1
                time.sleep(1.2)
                if batch_details_data:
                    valid_batch_papers = [p for p in batch_details_data if p and p.get(PRIMARY_ID_FIELD)]
                    papers_to_process.extend(valid_batch_papers)
                    for p in valid_batch_papers:
                        all_collected_paper_ids.add(p[PRIMARY_ID_FIELD])
            
            logging.info(f"'{title}'에 대해 총 {len(papers_to_process)}개의 논문 상세 정보 준비 완료 (중복 포함).")
        else:
            logging.warning(f"제목 '{title}'에 해당하는 논문을 찾을 수 없습니다.")

        newly_added_for_specific_title = []
        for paper in papers_to_process:
            paper_id = paper.get(PRIMARY_ID_FIELD)
            if paper_id and paper_id not in all_collected_paper_ids: # 이미 수집된 paper_id는 제외
                if is_valid_and_relevant(paper):
                    newly_added_for_specific_title.append(paper)
                    all_collected_paper_ids.add(paper_id) # 전체 ID 집합에 추가
        
        if newly_added_for_specific_title:
            append_to_jsonl(newly_added_for_specific_title, PAPER_NODE_FILE)
            pbar.update(len(newly_added_for_specific_title))
            logging.info(f"->> 특정 제목/관련 검색에서 {len(newly_added_for_specific_title)}개의 새 논문 추가. (총: {pbar.n}개)")
        else:
            logging.info("->> 이번 특정 제목/관련 검색에서 필터링을 통과한 새 논문이 없습니다.")
        
        state['processed_specific_titles'].append(title) # 처리된 제목 기록
        save_state(state, STATE_FILE) # 진행 상황 저장

    logging.info("--- 1단계: 초기 논문 상세 정보 수집 완료 ---")


    # --- 단계 2: 그래프 확장 (인용/참고 관계 및 저자 정보 수집) ---
    logging.info("--- 2단계: 그래프 확장 시작 (인용/참고/저자 관계) ---")

    # 2-1. 처리할 대상(프론티어) 선정 (우선순위 + 나머지)
    processed_expansion_ids = set(state['processed_expansion_ids']) # 이미 확장 처리 완료된 논문 ID
    
    # 2-1-1. 우선 처리할 논문 (파일의 첫 N개)
    priority_ids_from_file = load_priority_ids_from_file(PAPER_NODE_FILE, PRIMARY_ID_FIELD, 76)
    priority_frontier = deque([pid for pid in priority_ids_from_file if pid not in processed_expansion_ids])
    if priority_frontier:
        logging.info(f"파일의 첫 76개 논문 중, 아직 확장 처리되지 않은 {len(priority_frontier)}개를 우선적으로 처리합니다.")

    # 2-1-2. 나머지 처리 대상 (모든 수집된 논문 중 아직 확장 안 된 것)
    other_unprocessed_ids = (all_collected_paper_ids - processed_expansion_ids) - set(priority_frontier)
    other_frontier = deque(list(other_unprocessed_ids))
    random.shuffle(other_frontier) # 나머지 목록은 무작위로 섞음
    
    # 2-1-3. 최종 프론티어 목록 결합 (deque 사용)
    # priority_frontier가 먼저 비워지고, 그 다음 other_frontier가 처리됩니다.
    
    logging.info(f"총 {len(all_collected_paper_ids)}개 논문 보유. 이 중 {len(processed_expansion_ids)}개 확장 완료.")
    logging.info(f"최종 확장 프론티어 논문: {len(priority_frontier) + len(other_frontier)}개 (우선 {len(priority_frontier)}개 + 나머지 {len(other_frontier)}개)")

    if not priority_frontier and not other_frontier:
        logging.info("모든 논문의 그래프 확장이 완료되었습니다. 작업을 종료합니다.")
        pbar.close()
        save_state(state, STATE_FILE)
        return
    
    # 배치 저장을 위한 임시 리스트
    temp_new_paper_ids_to_fetch_details = set()
    temp_new_authors_to_save = []
    temp_edges_to_save = []
    
    # 전체 프론티어를 처리하는 루프
    # priority_frontier를 먼저 처리하고, 그 다음 other_frontier를 처리합니다.
    current_frontier_queue = priority_frontier
    while current_frontier_queue or other_frontier:
        if not current_frontier_queue and other_frontier:
            current_frontier_queue = other_frontier # 우선순위 큐가 비면, 나머지 큐를 현재 큐로 설정

        if not current_frontier_queue: # 두 큐 모두 비면 종료
            break

        paper_id_to_process = current_frontier_queue.popleft() # 큐에서 논문 ID 가져오기

        if paper_id_to_process in processed_expansion_ids: # 이미 처리된 논문일 경우 건너뛰기
            pbar.update(1) # 프로그레스 바는 계속 업데이트
            continue

        try:
            logging.info(f"프론티어 논문 확장 처리 중: {paper_id_to_process} (남은 프론티어: {len(priority_frontier) + len(other_frontier)})")
            
            # 2-2. [관계 및 저자 수집] 프론티어 논문의 연결 관계 및 저자 정보를 조회
            paper_data_with_connections, references_ids, citations_ids, authors_info = \
                fetch_related_papers_and_authors(paper_id_to_process, headers, PAPER_DETAILS_FIELDS, CONNECTION_FIELDS)
            state['last_api_call_counter'] += 1
            time.sleep(1.2) # API 지연

            if not paper_data_with_connections:
                logging.warning(f"프론티어 논문 ID {paper_id_to_process}의 관계 정보 조회 실패. 건너뜁니다.")
                processed_expansion_ids.add(paper_id_to_process)
                pbar.update(1)
                continue

            source_paper_id = paper_data_with_connections[PRIMARY_ID_FIELD]
            
            # 2-3. 인용/참고 관계 엣지 생성 및 신규 논문 ID 확보
            for ref_id in references_ids:
                temp_edges_to_save.append({"source": source_paper_id, "target": ref_id, "relation": "REFERENCES"})
                if ref_id not in all_collected_paper_ids: # 아직 수집되지 않은 논문이라면
                    temp_new_paper_ids_to_fetch_details.add(ref_id)
            for cit_id in citations_ids:
                temp_edges_to_save.append({"source": cit_id, "target": source_paper_id, "relation": "CITES"})
                if cit_id not in all_collected_paper_ids: # 아직 수집되지 않은 논문이라면
                    temp_new_paper_ids_to_fetch_details.add(cit_id)

            # 2-4. 저자-논문(WROTE) 엣지 생성 및 신규 저자 노드 확보
            for author in authors_info:
                author_id = author.get("authorId")
                if not author_id: continue
                
                temp_edges_to_save.append({"source": author_id, "target": source_paper_id, "relation": "WROTE"})
                
                if author_id not in all_existing_author_ids: # 아직 수집되지 않은 저자라면
                    temp_new_authors_to_save.append({"authorId": author_id, "name": author.get("name")})
                    all_existing_author_ids.add(author_id) # 전체 저자 ID 집합에 추가

            # 현재 논문 ID를 확장 처리 완료 목록에 추가
            processed_expansion_ids.add(paper_id_to_process)
            pbar.update(1) # 메인 프로그레스 바 업데이트

            # 2-5. [저장 주기] 일정 주기마다, 임시 저장된 데이터를 파일에 쓰고, 신규 논문 상세 정보를 조회하여 저장
            if (pbar.n - len(state['processed_expansion_ids'])) % SAVE_INTERVAL_EXPANSION == 0 or len(current_frontier_queue) + len(other_frontier) == 0:
                logging.info(f"\n--- 확장 프론티어 배치 처리 완료. ({SAVE_INTERVAL_EXPANSION}개 논문) ---")
                
                # 임시 저장된 엣지 및 저자 노드 파일에 추가
                if temp_edges_to_save:
                    append_to_jsonl(temp_edges_to_save, EDGE_DATA_FILE)
                    logging.info(f" -> {len(temp_edges_to_save)}개 엣지 파일에 저장.")
                    temp_edges_to_save.clear()
                if temp_new_authors_to_save:
                    append_to_jsonl(temp_new_authors_to_save, AUTHOR_NODE_FILE)
                    logging.info(f" -> {len(temp_new_authors_to_save)}개 저자 노드 파일에 저장.")
                    temp_new_authors_to_save.clear()
                
                logging.info(f" -> {len(temp_new_paper_ids_to_fetch_details)}개의 새로운 연결 논문 상세 정보 조회 대기 중.")

                # 신규 논문 상세 정보를 일괄 조회하여 저장 (Batch API 호출)
                if temp_new_paper_ids_to_fetch_details:
                    new_ids_list_for_details = list(temp_new_paper_ids_to_fetch_details)
                    newly_fetched_details = []
                    
                    details_pbar = tqdm(total=len(new_ids_list_for_details), desc=" -> 신규 논문 상세 정보 수집 중", leave=False)
                    for j in range(0, len(new_ids_list_for_details), BATCH_SIZE):
                        batch_ids = new_ids_list_for_details[j:j+BATCH_SIZE]
                        batch_data = make_api_request(
                            "https://api.semanticscholar.org/graph/v1/paper/batch",
                            headers, is_post=True, json_data={"ids": batch_ids, "fields": PAPER_DETAILS_FIELDS}
                        )
                        state['last_api_call_counter'] += 1
                        time.sleep(1.2) # API 지연 (배치 호출 간)

                        if batch_data:
                            valid_batch_papers = [p for p in batch_data if p and p.get(PRIMARY_ID_FIELD)]
                            newly_fetched_details.extend(valid_batch_papers)
                            for p in valid_batch_papers:
                                all_collected_paper_ids.add(p[PRIMARY_ID_FIELD]) # 전체 논문 ID 집합에 추가
                        details_pbar.update(len(batch_ids)) # 배치 크기만큼 업데이트
                    details_pbar.close()

                    if newly_fetched_details:
                        append_to_jsonl(newly_fetched_details, PAPER_NODE_FILE)
                        logging.info(f"->> 성공적으로 {len(newly_fetched_details)}개의 신규 논문 상세 정보 저장 완료.")
                    
                    temp_new_paper_ids_to_fetch_details.clear() # 상세 정보를 가져온 후 집합 비우기

                state['processed_expansion_ids'] = list(processed_expansion_ids) # set을 list로 변환하여 저장 가능하게
                save_state(state, STATE_FILE) # 진행 상황 저장
                logging.info("-" * 20)
                time.sleep(2) # 배치 처리 후 추가 지연

        except Exception as e:
            logging.error(f"논문 ID {paper_id_to_process} 처리 중 오류: {e}")
            processed_expansion_ids.add(paper_id_to_process) # 오류 발생 논문도 처리 완료로 간주하여 재시도 방지
            pbar.update(1)
            time.sleep(5) # 오류 발생 시 잠시 대기

    pbar.close()
    logging.info("="*30 + " 모든 데이터 수집 및 확장 작업 완료 " + "="*30)
    state['processed_expansion_ids'] = list(processed_expansion_ids) # 최종 저장
    save_state(state, STATE_FILE)
    logging.info(f"최종 수집 논문 수: {len(all_collected_paper_ids)}개. 최종 저자 수: {len(all_existing_author_ids)}개.")
    logging.info("다음 실행 시, 오늘 새로 추가되거나 이전에 처리되지 않은 논문들을 기반으로 확장을 계속합니다.")


# --- 5. 스크립트 실행 ---
if __name__ == '__main__':
    # 만약 진행 상황 파일이 꼬여서 계속 같은 오류가 발생하면,
    # 'semantic_scholar_sociology_data/data_collection_state.json' 파일을 수동으로 삭제하고 다시 실행해보세요.
    run_full_data_collection()
