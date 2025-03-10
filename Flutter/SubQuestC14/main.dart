import 'package:flutter/material.dart';

// 앱 시작
void main() {
  runApp(const MyApp());
}

// 앱 루트 위젯
class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false, // 디버그 배너 제거
      title: 'Travel Market App', // 앱 제목
      theme: ThemeData(
        primarySwatch: Colors.blue, // 기본 테마 색상
        primaryColor: Colors.orange, // 주요 색상을 오렌지로 변경
        colorScheme: ColorScheme.fromSwatch().copyWith(
          primary: Colors.orange, // 오렌지를 메인 컬러로 사용
          secondary: Colors.orangeAccent, // 보조 컬러
        ),
      ),
      home: const SplashScreen(), // 시작 화면
    );
  }
}

// 시작 화면 (스플래시)
class SplashScreen extends StatelessWidget {
  const SplashScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        // 중앙 정렬
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center, // 세로 중앙 배치
          children: <Widget>[
            // 로고 이미지 (당근 이미지를 변형해서 여행 테마로 사용할 수 있음)
            Image.asset('images/TMarket.PNG', width: 120, height: 120),
            const SizedBox(height: 20), // 간격
            const Text(
              'Travel Market', // 앱 이름
              style: TextStyle(
                fontSize: 26,
                fontWeight: FontWeight.bold,
                color: Colors.orange,
              ),
            ),
            const SizedBox(height: 10), // 간격
            const Text(
              'Discover travel experiences and shop gear', // 설명
              style: TextStyle(fontSize: 16, color: Colors.grey),
            ),
            const SizedBox(height: 40), // 간격
            // 시작 버튼
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.orange,
                padding: const EdgeInsets.symmetric(
                  horizontal: 100,
                  vertical: 15,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
              onPressed: () {
                // 버튼 클릭 시 메인 화면으로 이동
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const TravelHomeScreen(),
                  ),
                );
              },
              child: const Text(
                'Get Started',
                style: TextStyle(fontSize: 18, color: Colors.white),
              ),
            ),
            const SizedBox(height: 20), // 간격
            // 로그인 텍스트 버튼
            TextButton(
              onPressed: () {
                // 로그인 기능 추후 추가
              },
              child: const Text(
                'Already have an account? Login',
                style: TextStyle(color: Colors.orange, fontSize: 16),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// 샘플 데이터 클래스 (앱 전체에서 사용)
class TravelItem {
  final String id;
  final String title;
  final String location;
  final String price;
  final String status;
  final String description;
  final String seller;
  final bool isLiked;

  TravelItem({
    required this.id,
    required this.title,
    required this.location,
    required this.price,
    required this.status,
    required this.description,
    required this.seller,
    this.isLiked = false,
  });

  TravelItem copyWith({
    String? id,
    String? title,
    String? location,
    String? price,
    String? status,
    String? description,
    String? seller,
    bool? isLiked,
  }) {
    return TravelItem(
      id: id ?? this.id,
      title: title ?? this.title,
      location: location ?? this.location,
      price: price ?? this.price,
      status: status ?? this.status,
      description: description ?? this.description,
      seller: seller ?? this.seller,
      isLiked: isLiked ?? this.isLiked,
    );
  }
}

// 메인 홈 화면
class TravelHomeScreen extends StatefulWidget {
  const TravelHomeScreen({Key? key}) : super(key: key);

  @override
  State<TravelHomeScreen> createState() => _TravelHomeScreenState();
}

class _TravelHomeScreenState extends State<TravelHomeScreen> {
  // 샘플 아이템 목록
  List<TravelItem> items = [
    TravelItem(
      id: '1',
      title: '여행 티켓 팝니다',
      location: '서울',
      price: '11,000원',
      status: '예약중',
      description: '제주도 왕복 항공권입니다. 3월 10일~15일 예약했으나 일정이 변경되어 판매합니다. 직거래 가능합니다.',
      seller: '여행자123',
    ),
    TravelItem(
      id: '2',
      title: '해외 유심 팝니다',
      location: '인천',
      price: '5,000원',
      status: '판매중',
      description: '일본 10일 사용 유심카드입니다. 데이터 무제한이고 개봉만 했습니다. 직거래 우선입니다.',
      seller: '인천사람',
    ),
    TravelItem(
      id: '3',
      title: '캐리어 중고',
      location: '부산',
      price: '20,000원',
      status: '예약중',
      description: '2번 사용한 24인치 캐리어입니다. 상태 좋고 바퀴도 이상 없습니다. 부산 서면에서 거래 가능합니다.',
      seller: '부산여행러',
    ),
    TravelItem(
      id: '4',
      title: '트래블백 팝니다',
      location: '대구',
      price: '8,000원',
      status: '판매중',
      description: '접이식 트래블백입니다. 여행갈 때 추가 짐 가방으로 좋아요. 한 번 사용했습니다.',
      seller: '대구엄마',
    ),
    TravelItem(
      id: '5',
      title: '비행기 모델 굿즈',
      location: '제주',
      price: '15,000원',
      status: '판매중',
      description: '비행기 모형 컬렉션입니다. 대한항공, 아시아나, 제주항공 모델 3개 일괄 판매합니다.',
      seller: '제주귤농장',
    ),
  ];

  int _selectedIndex = 0; // 하단 네비게이션 인덱스

  // 좋아요 토글 함수
  void _toggleLike(String itemId) {
    setState(() {
      final index = items.indexWhere((item) => item.id == itemId);
      if (index != -1) {
        items[index] = items[index].copyWith(isLiked: !items[index].isLiked);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // 상단바: 위치를 제목으로 표시
      appBar: AppBar(
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0.5,
        title: const Row(
          children: [
            Text('서울', style: TextStyle(fontWeight: FontWeight.bold)),
            Icon(Icons.keyboard_arrow_down_rounded, size: 20),
          ],
        ),
        actions: [
          IconButton(icon: const Icon(Icons.search), onPressed: () {}),
          IconButton(
            icon: const Icon(Icons.notifications_none),
            onPressed: () {},
          ),
        ],
      ),

      // 목록 영역
      body: ListView.separated(
        itemCount: items.length,
        separatorBuilder: (context, index) => const Divider(height: 1),
        itemBuilder: (context, index) {
          final item = items[index];
          return ListTile(
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 16,
              vertical: 8,
            ),
            // 왼쪽 아이콘(여행 로고 등) - 임시 이미지 사용
            leading: Container(
              width: 50,
              height: 50,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(8),
                color: Colors.orange.shade100,
              ),
              child: const Icon(Icons.luggage, color: Colors.orange),
            ),
            // 제목 + 위치
            title: Text(
              item.title,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            subtitle: Text('${item.location} • 방금 올림'),
            // 우측 가격 + 상태
            trailing: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  item.price,
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                // 상태(예약중/판매중 등)
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    color:
                        (item.status == '예약중')
                            ? Colors.orange.shade100
                            : Colors.blue.shade100,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    item.status,
                    style: TextStyle(
                      fontSize: 12,
                      color:
                          (item.status == '예약중')
                              ? Colors.orange.shade800
                              : Colors.blue.shade800,
                    ),
                  ),
                ),
              ],
            ),
            onTap: () {
              // 상품 상세 페이지로 이동
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder:
                      (context) => ItemDetailScreen(
                        item: item,
                        onLikeToggle: () => _toggleLike(item.id),
                      ),
                ),
              );
            },
          );
        },
      ),

      // 화면 우측 하단 FloatingActionButton
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // 새 상품 등록 화면으로 이동
        },
        backgroundColor: Colors.orange,
        child: const Icon(Icons.add),
      ),

      // 하단 네비게이션 바
      bottomNavigationBar: BottomNavigationBar(
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined),
            label: 'HOME',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.favorite_border),
            label: '관심목록',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.chat_bubble_outline),
            label: '채팅',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person_outline),
            label: 'MY',
          ),
        ],
        currentIndex: _selectedIndex,
        selectedItemColor: Colors.orange,
        unselectedItemColor: Colors.grey,
        showUnselectedLabels: true,
        type: BottomNavigationBarType.fixed,
        onTap: (index) {
          setState(() {
            _selectedIndex = index;
          });

          // 채팅 탭을 선택했을 때 채팅 목록 화면으로 이동
          if (index == 2) {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (context) => const ChatListScreen()),
            );
          }
        },
      ),
    );
  }
}

// 상품 상세 화면
class ItemDetailScreen extends StatefulWidget {
  final TravelItem item;
  final VoidCallback onLikeToggle;

  const ItemDetailScreen({
    Key? key,
    required this.item,
    required this.onLikeToggle,
  }) : super(key: key);

  @override
  State<ItemDetailScreen> createState() => _ItemDetailScreenState();
}

class _ItemDetailScreenState extends State<ItemDetailScreen> {
  late bool isLiked;

  @override
  void initState() {
    super.initState();
    isLiked = widget.item.isLiked;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0.5,
        title: const Text('상품 상세'),
        actions: [
          IconButton(icon: const Icon(Icons.share), onPressed: () {}),
          IconButton(icon: const Icon(Icons.more_vert), onPressed: () {}),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 상품 이미지
                  Container(
                    width: double.infinity,
                    height: 250,
                    color: Colors.orange.shade100,
                    child: const Icon(
                      Icons.luggage,
                      size: 100,
                      color: Colors.orange,
                    ),
                  ),

                  // 판매자 정보
                  ListTile(
                    leading: const CircleAvatar(
                      backgroundColor: Colors.grey,
                      child: Icon(Icons.person, color: Colors.white),
                    ),
                    title: Text(widget.item.seller),
                    subtitle: Text(widget.item.location),
                    trailing: OutlinedButton(
                      onPressed: () {},
                      style: OutlinedButton.styleFrom(
                        side: const BorderSide(color: Colors.grey),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(20),
                        ),
                      ),
                      child: const Text('프로필'),
                    ),
                  ),

                  const Divider(height: 1),

                  // 상품 정보
                  Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          widget.item.title,
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          '${widget.item.location} • 방금 올림',
                          style: TextStyle(color: Colors.grey.shade600),
                        ),
                        const SizedBox(height: 16),
                        Text(
                          widget.item.description,
                          style: const TextStyle(fontSize: 16, height: 1.5),
                        ),
                        const SizedBox(height: 24),
                        const Row(
                          children: [
                            Icon(
                              Icons.remove_red_eye_outlined,
                              size: 16,
                              color: Colors.grey,
                            ),
                            SizedBox(width: 4),
                            Text('조회 32', style: TextStyle(color: Colors.grey)),
                            SizedBox(width: 8),
                            Icon(
                              Icons.favorite_border,
                              size: 16,
                              color: Colors.grey,
                            ),
                            SizedBox(width: 4),
                            Text('관심 2', style: TextStyle(color: Colors.grey)),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),

          // 하단 액션 버튼들
          Container(
            padding: const EdgeInsets.all(16.0),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.grey.withOpacity(0.3),
                  spreadRadius: 1,
                  blurRadius: 5,
                  offset: const Offset(0, -1),
                ),
              ],
            ),
            child: Row(
              children: [
                // 좋아요 버튼
                IconButton(
                  icon: Icon(
                    isLiked ? Icons.favorite : Icons.favorite_border,
                    color: isLiked ? Colors.red : Colors.grey,
                  ),
                  onPressed: () {
                    setState(() {
                      isLiked = !isLiked;
                    });
                    widget.onLikeToggle();
                  },
                ),
                const SizedBox(width: 8),
                // 가격
                Expanded(
                  child: Text(
                    widget.item.price,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                // 채팅하기 버튼
                ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.orange,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 12,
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  onPressed: () {
                    // 채팅 화면으로 이동
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => ChatScreen(item: widget.item),
                      ),
                    );
                  },
                  child: const Text('채팅하기'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// 채팅 목록 화면
class ChatListScreen extends StatelessWidget {
  const ChatListScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // 샘플 채팅 리스트
    final List<Map<String, dynamic>> chatList = [
      {
        'title': '여행 티켓 팝니다',
        'seller': '김안정',
        'lastMessage': '안녕하세요',
        'time': '5:02 PM',
        'price': '3,000원',
        'isUnread': true,
      },
      {
        'title': '해외 유심 팝니다',
        'seller': '박여행',
        'lastMessage': '네고 가능할까요?',
        'time': '4:30 PM',
        'price': '5,000원',
        'isUnread': false,
      },
      {
        'title': '캐리어 중고',
        'seller': '이캐리',
        'lastMessage': '직거래 가능하신가요?',
        'time': '어제',
        'price': '20,000원',
        'isUnread': false,
      },
    ];

    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0.5,
        title: const Text('채팅', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: ListView.separated(
        itemCount: chatList.length,
        separatorBuilder: (context, index) => const Divider(height: 1),
        itemBuilder: (context, index) {
          final chat = chatList[index];
          return ListTile(
            contentPadding: const EdgeInsets.all(16),
            leading: const CircleAvatar(
              backgroundColor: Colors.orange,
              child: Icon(Icons.person, color: Colors.white),
            ),
            title: Row(
              children: [
                Text(
                  chat['seller'],
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(width: 8),
                if (chat['isUnread'])
                  Container(
                    width: 6,
                    height: 6,
                    decoration: const BoxDecoration(
                      color: Colors.orange,
                      shape: BoxShape.circle,
                    ),
                  ),
              ],
            ),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 4),
                Text(chat['lastMessage']),
                const SizedBox(height: 4),
                Text(
                  chat['title'],
                  style: TextStyle(color: Colors.grey[600], fontSize: 12),
                ),
              ],
            ),
            trailing: Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  chat['time'],
                  style: TextStyle(color: Colors.grey[600], fontSize: 12),
                ),
                const SizedBox(height: 8),
                Text(
                  chat['price'],
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                    color: Colors.grey[800],
                  ),
                ),
              ],
            ),
            onTap: () {
              // 채팅 상세 화면으로 이동
              final TravelItem mockItem = TravelItem(
                id: '${index + 1}',
                title: chat['title'],
                location: '서울',
                price: chat['price'],
                status: '판매중',
                description: '상세 설명',
                seller: chat['seller'],
              );

              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => ChatScreen(item: mockItem),
                ),
              );
            },
          );
        },
      ),
    );
  }
}

// 채팅 상세 화면
class ChatScreen extends StatefulWidget {
  final TravelItem item;

  const ChatScreen({Key? key, required this.item}) : super(key: key);

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final List<Map<String, dynamic>> _messages = [];

  @override
  void initState() {
    super.initState();
    // 초기 메시지 설정 (예시로)
    if (widget.item.title == '여행 티켓 팝니다') {
      _messages.addAll([
        {'sender': 'other', 'text': '안녕하세요', 'time': '5:02 PM'},
        {'sender': 'me', 'text': '안녕하세요.', 'time': '5:06 PM'},
        {'sender': 'me', 'text': '네고 가능한가요?', 'time': '5:06 PM'},
        {'sender': 'other', 'text': '안됩니다.', 'time': '5:10 PM'},
      ]);
    }
  }

  void _sendMessage() {
    if (_messageController.text.trim().isNotEmpty) {
      setState(() {
        _messages.add({
          'sender': 'me',
          'text': _messageController.text,
          'time': '${DateTime.now().hour}:${DateTime.now().minute} PM',
        });
      });
      _messageController.clear();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0.5,
        title: Text(widget.item.seller),
        actions: [
          IconButton(icon: const Icon(Icons.call), onPressed: () {}),
          IconButton(icon: const Icon(Icons.menu), onPressed: () {}),
        ],
      ),
      body: Column(
        children: [
          // 상품 정보 영역
          Container(
            padding: const EdgeInsets.all(16.0),
            decoration: BoxDecoration(
              color: Colors.grey[100],
              border: Border(bottom: BorderSide(color: Colors.grey[300]!)),
            ),
            child: Row(
              children: [
                // 상품 썸네일
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: Colors.orange[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.luggage, color: Colors.orange),
                ),
                const SizedBox(width: 12),
                // 상품 정보
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        widget.item.title,
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        widget.item.price,
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                ),
                // 예약하기 버튼
                OutlinedButton(
                  onPressed: () {},
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Colors.orange,
                    side: const BorderSide(color: Colors.orange),
                  ),
                  child: const Text('예약하기'),
                ),
              ],
            ),
          ),

          // 채팅 메시지 영역
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                final bool isMe = message['sender'] == 'me';

                return Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: Row(
                    mainAxisAlignment:
                        isMe ? MainAxisAlignment.end : MainAxisAlignment.start,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (!isMe) ...[
                        const CircleAvatar(
                          radius: 16,
                          backgroundColor: Colors.grey,
                          child: Icon(
                            Icons.person,
                            color: Colors.white,
                            size: 16,
                          ),
                        ),
                        const SizedBox(width: 8),
                      ],
                      Column(
                        crossAxisAlignment:
                            isMe
                                ? CrossAxisAlignment.end
                                : CrossAxisAlignment.start,
                        children: [
                          if (!isMe)
                            Padding(
                              padding: const EdgeInsets.only(bottom: 4),
                              child: Text(widget.item.seller),
                            ),
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              if (isMe) ...[
                                Text(
                                  message['time'],
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: Colors.grey[600],
                                  ),
                                ),
                                const SizedBox(width: 8),
                              ],
                              Container(
                                padding: const EdgeInsets.all(12),
                                constraints: BoxConstraints(
                                  maxWidth:
                                      MediaQuery.of(context).size.width * 0.6,
                                ),
                                decoration: BoxDecoration(
                                  color:
                                      isMe ? Colors.orange : Colors.grey[200],
                                  borderRadius: BorderRadius.circular(16),
                                ),
                                child: Text(
                                  message['text'],
                                  style: TextStyle(
                                    color: isMe ? Colors.white : Colors.black,
                                  ),
                                ),
                              ),
                              if (!isMe) ...[
                                const SizedBox(width: 8),
                                Text(
                                  message['time'],
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: Colors.grey[600],
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ],
                      ),
                    ],
                  ),
                );
              },
            ),
          ),

          // 메시지 입력 영역
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
            color: Colors.white,
            child: Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.add_circle_outline),
                  onPressed: () {},
                ),
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    decoration: BoxDecoration(
                      color: Colors.grey[200],
                      borderRadius: BorderRadius.circular(24),
                    ),
                    child: TextField(
                      controller: _messageController,
                      decoration: const InputDecoration(
                        hintText: '메시지 입력',
                        border: InputBorder.none,
                      ),
                    ),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.send, color: Colors.orange),
                  onPressed: _sendMessage,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
