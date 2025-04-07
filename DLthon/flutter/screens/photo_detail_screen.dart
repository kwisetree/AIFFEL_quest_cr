import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import 'package:cached_network_image/cached_network_image.dart';
import 'dart:convert';
import '../models/photo_model.dart';
import 'dart:math' as math;

class PhotoDetailScreen extends StatefulWidget {
  final Photo photo;

  const PhotoDetailScreen({super.key, required this.photo});

  @override
  _PhotoDetailScreenState createState() => _PhotoDetailScreenState();
}

class _PhotoDetailScreenState extends State<PhotoDetailScreen> with TickerProviderStateMixin {
  String? prediction;
  String? animalInfo;
  bool isLoading = true;
  final TextEditingController _promptController = TextEditingController();
  bool _isCustomPromptEnabled = false;
  
  // 애니메이션 컨트롤러
  late AnimationController _floatController;
  late Animation<double> _floatAnimation;
  
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;
  
  late AnimationController _contentFadeController;
  late Animation<double> _contentFadeAnimation;
  
  late AnimationController _rippleController;
  late Animation<double> _rippleAnimation;

  @override
  void initState() {
    super.initState();
    
    // 플로팅 애니메이션 (위아래로 움직임)
    _floatController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 3000),
    )..repeat(reverse: true);
    _floatAnimation = Tween<double>(begin: -10.0, end: 10.0).animate(
      CurvedAnimation(parent: _floatController, curve: Curves.easeInOut)
    );
    
    // 맥박 애니메이션 (크기 변화)
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat(reverse: true);
    _pulseAnimation = Tween<double>(begin: 0.95, end: 1.05).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut)
    );
    
    // 콘텐츠 페이드 애니메이션
    _contentFadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _contentFadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _contentFadeController, curve: Curves.easeOut)
    );
    
    // 물결 애니메이션
    _rippleController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 4000),
    )..repeat();
    _rippleAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _rippleController, curve: Curves.linear)
    );
    
    _analyzeImage();
  }
  
  @override
  void dispose() {
    _promptController.dispose();
    _floatController.dispose();
    _pulseController.dispose();
    _contentFadeController.dispose();
    _rippleController.dispose();
    super.dispose();
  }

  // 해파리 분석 API 호출
  Future<void> _analyzeImage({String? customPrompt}) async {
    setState(() {
      isLoading = true;
    });
    
    print("API 호출 시작 - URL: ${widget.photo.url}");
    
    try {
      var response = await http.post(
        Uri.parse('https://779e-34-145-20-93.ngrok-free.app/predict'),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "image_url": widget.photo.url,
          if (customPrompt != null && customPrompt.isNotEmpty)
            "prompt": customPrompt
        }),
      ).timeout(const Duration(seconds: 10), onTimeout: () {
        print("API 호출 타임아웃 발생");
        throw Exception("타임아웃: 서버 응답이 너무 오래 걸립니다");
      });

      print("API 응답 코드: ${response.statusCode}");
      
      if (response.statusCode == 200) {
        var jsonResponse = utf8.decode(response.bodyBytes);
        print("API 응답 내용 일부: ${jsonResponse.substring(0, math.min(100, jsonResponse.length))}...");
        var decodedResponse = json.decode(jsonResponse);

        setState(() {
          prediction = decodedResponse['prediction'] ?? "예측 불가";

          if (decodedResponse['info'] is Map<String, dynamic>) {
            animalInfo = decodedResponse['info']['summary'] ?? "정보 없음";
          } else if (decodedResponse['info'] is String) {
            animalInfo = decodedResponse['info'];
          } else {
            animalInfo = "정보 없음";
          }

          isLoading = false;
        });
        
        // 콘텐츠 페이드인 애니메이션 시작
        _contentFadeController.reset();
        _contentFadeController.forward();
      } else {
        print("API 오류 응답: ${response.body}");
        setState(() {
          prediction = "분석 실패: 서버 응답 오류";
          animalInfo = "정보 없음";
          isLoading = false;
        });
        
        _contentFadeController.reset();
        _contentFadeController.forward();
      }
    } catch (e) {
      print("API 호출 예외 발생: $e");
      setState(() {
        prediction = "분석 실패: $e";
        animalInfo = "정보 없음";
        isLoading = false;
      });
      
      _contentFadeController.reset();
      _contentFadeController.forward();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: IconThemeData(color: Colors.white),
        title: Text(
          "🔎 해파리 도감 정보", 
          style: GoogleFonts.cabin(
            fontWeight: FontWeight.bold,
            color: Colors.white,
            shadows: [
              Shadow(
                color: Colors.black38,
                offset: Offset(1, 1),
                blurRadius: 2,
              ),
            ],
          ),
        ),
        flexibleSpace: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Color(0xFFE91E63).withOpacity(0.8),
                Color(0xFFEC407A).withOpacity(0.6),
              ],
            ),
          ),
        ),
      ),
      body: Stack(
        children: [
          // 배경 그라데이션
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Color(0xFFFCE4EC),
                  Colors.white,
                ],
              ),
            ),
          ),
          
          // 물결 효과
          AnimatedBuilder(
            animation: _rippleAnimation,
            builder: (context, child) {
              return Positioned(
                top: MediaQuery.of(context).size.height * 0.25,
                left: 0,
                right: 0,
                child: CustomPaint(
                  painter: RipplePainter(
                    color: Color(0xFFF8BBD0).withOpacity(0.5),
                    animationValue: _rippleAnimation.value,
                  ),
                  child: SizedBox(
                    height: 100,
                    width: double.infinity,
                  ),
                ),
              );
            },
          ),
          
          // 메인 콘텐츠
          SingleChildScrollView(
            physics: BouncingScrollPhysics(),
            child: Padding(
              padding: EdgeInsets.only(top: AppBar().preferredSize.height + MediaQuery.of(context).padding.top),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  // 해파리 이미지
                  Hero(
                    tag: 'photo_${widget.photo.id}',
                    child: Card(
                      elevation: 8,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(24),
                      ),
                      margin: const EdgeInsets.all(24),
                      child: AnimatedBuilder(
                        animation: Listenable.merge([_floatAnimation, _pulseAnimation]),
                        builder: (context, child) {
                          return Transform.translate(
                            offset: Offset(0, _floatAnimation.value),
                            child: Transform.scale(
                              scale: _pulseAnimation.value,
                              child: ClipRRect(
                                borderRadius: BorderRadius.circular(24),
                                child: Container(
                                  height: 300,
                                  width: double.infinity,
                                  decoration: BoxDecoration(
                                    boxShadow: [
                                      BoxShadow(
                                        color: Colors.black.withOpacity(0.2),
                                        blurRadius: 15,
                                        offset: Offset(0, 5),
                                      ),
                                    ],
                                  ),
                                  child: widget.photo.localFile != null
                                      ? Image.file(
                                          widget.photo.localFile!,
                                          fit: BoxFit.cover,
                                        )
                                      : CachedNetworkImage(
                                          imageUrl: widget.photo.url,
                                          fit: BoxFit.cover,
                                          placeholder: (context, url) => Container(
                                            color: Colors.grey[200],
                                            child: Center(
                                              child: CircularProgressIndicator(
                                                valueColor: AlwaysStoppedAnimation<Color>(Color(0xFFE91E63)),
                                                strokeWidth: 2,
                                              ),
                                            ),
                                          ),
                                          errorWidget: (context, url, error) => Container(
                                            color: Colors.grey[200],
                                            child: Center(
                                              child: Column(
                                                mainAxisAlignment: MainAxisAlignment.center,
                                                children: [
                                                  Icon(
                                                    Icons.broken_image,
                                                    color: Colors.red[300],
                                                    size: 40,
                                                  ),
                                                  SizedBox(height: 8),
                                                  Text(
                                                    "이미지를 불러올 수 없습니다",
                                                    style: TextStyle(color: Colors.red[700]),
                                                  ),
                                                ],
                                              ),
                                            ),
                                          ),
                                        ),
                                ),
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                  ),
                  
                  // 커스텀 질문 토글
                  Container(
                    margin: EdgeInsets.symmetric(horizontal: 24),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(30),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.grey.withOpacity(0.2),
                          blurRadius: 8,
                          spreadRadius: 1,
                          offset: Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Material(
                      color: Colors.transparent,
                      child: InkWell(
                        borderRadius: BorderRadius.circular(30),
                        onTap: () {
                          setState(() {
                            _isCustomPromptEnabled = !_isCustomPromptEnabled;
                          });
                        },
                        child: Padding(
                          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
                          child: Row(
                            children: [
                              Switch(
                                value: _isCustomPromptEnabled,
                                activeColor: Color(0xFFE91E63),
                                onChanged: (value) {
                                  setState(() {
                                    _isCustomPromptEnabled = value;
                                  });
                                },
                              ),
                              SizedBox(width: 8),
                              Text(
                                '해파리에 대해 질문하기',
                                style: GoogleFonts.nunitoSans(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w600,
                                  color: Color(0xFFAD1457),
                                ),
                              ),
                              Spacer(),
                              Icon(
                                _isCustomPromptEnabled ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                                color: Color(0xFFAD1457),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                  
                  // 커스텀 질문 입력
                  if (_isCustomPromptEnabled)
                    AnimatedContainer(
                      duration: Duration(milliseconds: 300),
                      margin: EdgeInsets.fromLTRB(24, 16, 24, 0),
                      padding: EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(20),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.grey.withOpacity(0.1),
                            blurRadius: 10,
                            spreadRadius: 1,
                            offset: Offset(0, 2),
                          ),
                        ],
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          TextField(
                            controller: _promptController,
                            decoration: InputDecoration(
                              hintText: '해파리에 대한 추가 질문을 입력하세요',
                              hintStyle: GoogleFonts.nunitoSans(color: Colors.grey.shade400),
                              filled: true,
                              fillColor: Color(0xFFFCE4EC),
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(15),
                                borderSide: BorderSide.none,
                              ),
                              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                              suffixIcon: Icon(Icons.help_outline, color: Color(0xFFE91E63)),
                            ),
                            style: GoogleFonts.nunitoSans(
                              fontSize: 16,
                              color: Colors.black87,
                            ),
                            maxLines: 2,
                          ),
                          SizedBox(height: 16),
                          ElevatedButton.icon(
                            onPressed: () {
                              setState(() {
                                isLoading = true;
                              });
                              _analyzeImage(customPrompt: _promptController.text);
                              FocusScope.of(context).unfocus();
                            },
                            icon: Icon(Icons.search, size: 20),
                            label: Text(
                              '분석 실행',
                              style: GoogleFonts.nunitoSans(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Color(0xFFE91E63),
                              padding: EdgeInsets.symmetric(vertical: 12),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                              elevation: 3,
                            ),
                          ),
                        ],
                      ),
                    ),
                  
                  // 로딩 인디케이터 또는 결과
                  Padding(
                    padding: EdgeInsets.all(24),
                    child: isLoading
                        ? Column(
                            children: [
                              SizedBox(
                                width: 60,
                                height: 60,
                                child: CircularProgressIndicator(
                                  valueColor: AlwaysStoppedAnimation<Color>(Color(0xFFE91E63)),
                                  strokeWidth: 4,
                                ),
                              ),
                              SizedBox(height: 16),
                              Text(
                                '해파리 분석 중...',
                                style: GoogleFonts.nunitoSans(
                                  fontSize: 16,
                                  color: Color(0xFFAD1457),
                                ),
                              ),
                              SizedBox(height: 24),
                              ElevatedButton.icon(
                                onPressed: () {
                                  setState(() {
                                    isLoading = false;
                                  });
                                  _analyzeImage(customPrompt: _promptController.text);
                                },
                                icon: Icon(Icons.refresh),
                                label: Text('다시 시도'),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Color(0xFFE91E63),
                                  padding: EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                                ),
                              ),
                            ],
                          )
                        : FadeTransition(
                            opacity: _contentFadeAnimation,
                            child: Column(
                              children: [
                                // 종류 헤더
                                Container(
                                  padding: EdgeInsets.symmetric(vertical: 16, horizontal: 24),
                                  decoration: BoxDecoration(
                                    gradient: LinearGradient(
                                      colors: [
                                        Color(0xFFE91E63),
                                        Color(0xFFEC407A),
                                      ],
                                      begin: Alignment.topLeft,
                                      end: Alignment.bottomRight,
                                    ),
                                    borderRadius: BorderRadius.circular(16),
                                    boxShadow: [
                                      BoxShadow(
                                        color: Color(0xFFE91E63).withOpacity(0.3),
                                        blurRadius: 10,
                                        spreadRadius: 1,
                                        offset: Offset(0, 4),
                                      ),
                                    ],
                                  ),
                                  child: Row(
                                    children: [
                                      Container(
                                        width: 50,
                                        height: 50,
                                        decoration: BoxDecoration(
                                          color: Colors.white,
                                          shape: BoxShape.circle,
                                        ),
                                        child: Center(
                                          child: Text(
                                            '🐋',
                                            style: TextStyle(
                                              fontSize: 24,
                                            ),
                                          ),
                                        ),
                                      ),
                                      SizedBox(width: 16),
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              '해파리 종류',
                                              style: GoogleFonts.nunitoSans(
                                                fontSize: 14,
                                                color: Colors.white.withOpacity(0.8),
                                              ),
                                            ),
                                            SizedBox(height: 4),
                                            Text(
                                              prediction ?? "결과 없음",
                                              style: GoogleFonts.cabin(
                                                fontSize: 22,
                                                fontWeight: FontWeight.bold,
                                                color: Colors.white,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                
                                SizedBox(height: 24),
                                
                                // 상세 정보 카드
                                Container(
                                  padding: EdgeInsets.all(24),
                                  decoration: BoxDecoration(
                                    color: Colors.white,
                                    borderRadius: BorderRadius.circular(20),
                                    boxShadow: [
                                      BoxShadow(
                                        color: Colors.grey.withOpacity(0.2),
                                        blurRadius: 10,
                                        spreadRadius: 1,
                                        offset: Offset(0, 4),
                                      ),
                                    ],
                                  ),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        '해파리 정보',
                                        style: GoogleFonts.cabin(
                                          fontSize: 18,
                                          fontWeight: FontWeight.bold,
                                          color: Color(0xFFAD1457),
                                        ),
                                      ),
                                      Divider(
                                        color: Color(0xFFF8BBD0),
                                        thickness: 2,
                                        height: 24,
                                      ),
                                      Text(
                                        animalInfo ?? "정보 없음",
                                        style: GoogleFonts.nunitoSans(
                                          fontSize: 16,
                                          height: 1.6,
                                          color: Colors.black87,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                
                                // 공유 버튼
                                SizedBox(height: 32),
                                ElevatedButton.icon(
                                  onPressed: () {
                                    // 공유 기능 (실제로는 추가 구현 필요)
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      SnackBar(
                                        content: Text('결과를 공유할 수 있습니다!'),
                                        backgroundColor: Color(0xFFE91E63),
                                      ),
                                    );
                                  },
                                  icon: Icon(Icons.share, size: 20),
                                  label: Text(
                                    '결과 공유하기',
                                    style: GoogleFonts.nunitoSans(
                                      fontSize: 16,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: Color(0xFF9C27B0),
                                    foregroundColor: Colors.white,
                                    padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(30),
                                    ),
                                    elevation: 3,
                                  ),
                                ),
                                
                                SizedBox(height: 40),
                              ],
                            ),
                          ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// 물결 효과 페인터
class RipplePainter extends CustomPainter {
  final Color color;
  final double animationValue;
  
  RipplePainter({required this.color, required this.animationValue});
  
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.fill
      ..strokeWidth = 2;
    
    final path = Path();
    
    // 시작점
    path.moveTo(0, size.height * 0.5);
    
    // 물결 곡선
    for (var i = 0; i < size.width; i++) {
      // 사인파 계산
      final y = math.sin((animationValue * 2 * math.pi) + (i / size.width * 4 * math.pi)) * 20;
      path.lineTo(i.toDouble(), size.height * 0.5 + y);
    }
    
    // 화면 하단까지 채우기
    path.lineTo(size.width, size.height);
    path.lineTo(0, size.height);
    path.close();
    
    canvas.drawPath(path, paint);
  }
  
  @override
  bool shouldRepaint(RipplePainter oldDelegate) {
    return oldDelegate.animationValue != animationValue || oldDelegate.color != color;
  }
}