import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../utils/preferences_util.dart';
import '../gallery_screen.dart';
import 'dart:math' as math;

class IntroScreen extends StatefulWidget {
  const IntroScreen({super.key});

  @override
  _IntroScreenState createState() => _IntroScreenState();
}

class _IntroScreenState extends State<IntroScreen> with TickerProviderStateMixin {
  late PageController _pageController;
  int _currentPage = 0;
  
  // 페이드 애니메이션
  late AnimationController _fadeController;
  late Animation<double> _fadeAnimation;
  
  // 부유 애니메이션 (해파리 움직임 효과)
  late AnimationController _floatController;
  late Animation<double> _floatAnimation;
  
  // 회전 애니메이션
  late AnimationController _rotateController;
  late Animation<double> _rotateAnimation;
  
  // 스케일 애니메이션
  late AnimationController _scaleController;
  late Animation<double> _scaleAnimation;

  final List<IntroPage> _pages = [
    IntroPage(
      title: "해파리 도감 어플",
      description: "다양한 해파리 종류를 식별하고 상세 정보를 제공하는 해파리 도감입니다.",
      image: Icons.auto_awesome,
      color: Color(0xFFFF4081),
    ),
    IntroPage(
      title: "인공지능 종 식별",
      description: "해파리 사진을 촬영하거나 불러와서 AI가 자동으로 해파리 종을 식별합니다.",
      image: Icons.science,
      color: Color(0xFFF06292),
    ),
    IntroPage(
      title: "해파리 사진 카메라",
      description: "카메라로 직접 해파리를 촬영하거나, 갤러리에서 해파리 사진을 불러와 종을 확인해보세요.",
      image: Icons.camera_alt,
      color: Color(0xFFEC407A),
    ),
    IntroPage(
      title: "시작하기",
      description: "지금 바로 해파리 도감을 시작하세요!",
      image: Icons.rocket_launch,
      color: Color(0xFFE91E63),
    ),
  ];

  @override
  void initState() {
    super.initState();
    _pageController = PageController();
    
    // 페이드 애니메이션
    _fadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _fadeController, curve: Curves.easeIn)
    );
    
    // 부유 애니메이션 (위아래로 떠다니는 효과)
    _floatController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 3000),
    )..repeat(reverse: true);
    _floatAnimation = Tween<double>(begin: -15.0, end: 15.0).animate(
      CurvedAnimation(parent: _floatController, curve: Curves.easeInOut)
    );
    
    // 회전 애니메이션
    _rotateController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 10000),
    )..repeat();
    _rotateAnimation = Tween<double>(begin: 0, end: 2 * math.pi).animate(
      CurvedAnimation(parent: _rotateController, curve: Curves.linear)
    );
    
    // 스케일 애니메이션
    _scaleController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat(reverse: true);
    _scaleAnimation = Tween<double>(begin: 0.95, end: 1.05).animate(
      CurvedAnimation(parent: _scaleController, curve: Curves.easeInOut)
    );
    
    _fadeController.forward();
  }

  @override
  void dispose() {
    _pageController.dispose();
    _fadeController.dispose();
    _floatController.dispose();
    _rotateController.dispose();
    _scaleController.dispose();
    super.dispose();
  }

  void _onPageChanged(int page) {
    setState(() {
      _currentPage = page;
    });
    _fadeController.reset();
    _fadeController.forward();
  }

  void _navigateToApp() async {
    // 인트로 화면을 본 것으로 표시
    await PreferencesUtil.setIntroSeen();
    
    // 화면 전환 애니메이션
    await _scaleController.reverse();
    
    // ignore: use_build_context_synchronously
    if (!mounted) return; // 위젯이 소멸되었는지 확인
    
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (context) => const GalleryScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              Color(0xFFFCE4EC), // 매우 연한 핑크
              Color(0xFFF8BBD0), // 연한 핑크
            ],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              Expanded(
                child: PageView.builder(
                  controller: _pageController,
                  onPageChanged: _onPageChanged,
                  itemCount: _pages.length,
                  itemBuilder: (context, index) {
                    return FadeTransition(
                      opacity: _fadeAnimation,
                      child: _buildIntroPage(_pages[index]),
                    );
                  },
                ),
              ),
              _buildBottomActions(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildIntroPage(IntroPage page) {
    return Padding(
      padding: const EdgeInsets.all(32.0),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // 애니메이션 효과가 적용된 이미지
          AnimatedBuilder(
            animation: Listenable.merge([_floatAnimation, _rotateAnimation, _scaleAnimation]),
            builder: (context, child) {
              return Transform.translate(
                offset: Offset(0, _floatAnimation.value),
                child: Transform.rotate(
                  angle: _rotateAnimation.value * 0.05, // 작은 각도로만 회전
                  child: Transform.scale(
                    scale: _scaleAnimation.value,
                    child: Container(
                      height: 220,
                      width: 220,
                      decoration: BoxDecoration(
                        boxShadow: [
                          BoxShadow(
                            color: page.color.withOpacity(0.3),
                            blurRadius: 20,
                            spreadRadius: 5,
                          ),
                        ],
                        shape: BoxShape.circle,
                      ),
                      child: Image.asset(
                        'assets/images/jellyfish.png',
                        height: 200,
                        width: 200,
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
          
          SizedBox(height: 40),
          AnimatedBuilder(
            animation: _fadeController,
            builder: (context, child) {
              return Transform.translate(
                offset: Offset(0, 20 * (1 - _fadeAnimation.value)),
                child: Opacity(
                  opacity: _fadeAnimation.value,
                  child: Text(
                    page.title,
                    style: GoogleFonts.nunito(
                      fontSize: 30,
                      fontWeight: FontWeight.bold,
                      color: const Color(0xFFAD1457),
                      shadows: [
                        Shadow(
                          color: Colors.black12,
                          offset: Offset(1, 1),
                          blurRadius: 3,
                        ),
                      ],
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
              );
            }
          ),
          SizedBox(height: 20),
          AnimatedBuilder(
            animation: _fadeController,
            builder: (context, child) {
              return Transform.translate(
                offset: Offset(0, 30 * (1 - _fadeAnimation.value)),
                child: Opacity(
                  opacity: _fadeAnimation.value,
                  child: Text(
                    page.description,
                    style: GoogleFonts.nunitoSans(
                      fontSize: 18,
                      color: const Color(0xFFAD1457),
                      height: 1.5,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
              );
            }
          ),
        ],
      ),
    );
  }

  Widget _buildBottomActions() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.8),
        borderRadius: BorderRadius.vertical(top: Radius.circular(30)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            spreadRadius: 0,
            offset: Offset(0, -2),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(
              _pages.length,
              (index) => _buildDotIndicator(index),
            ),
          ),
          const SizedBox(height: 24),
          _currentPage == _pages.length - 1
              ? AnimatedBuilder(
                  animation: _scaleController,
                  builder: (context, child) {
                    return Transform.scale(
                      scale: 1 + (_scaleAnimation.value - 1) * 0.1,
                      child: ElevatedButton(
                        onPressed: _navigateToApp,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFFE91E63),
                          foregroundColor: Colors.white,
                          minimumSize: const Size(double.infinity, 56),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                          elevation: 5,
                          shadowColor: const Color(0xFFE91E63).withOpacity(0.5),
                        ),
                        child: Text(
                          "시작하기",
                          style: GoogleFonts.nunito(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1.2,
                          ),
                        ),
                      ),
                    );
                  }
                )
              : Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    TextButton(
                      onPressed: _navigateToApp,
                      child: Text(
                        "건너뛰기",
                        style: GoogleFonts.nunito(
                          color: const Color(0xFF9E9E9E),
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                    ElevatedButton(
                      onPressed: () {
                        _pageController.nextPage(
                          duration: const Duration(milliseconds: 400),
                          curve: Curves.easeInOut,
                        );
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFE91E63),
                        foregroundColor: Colors.white,
                        minimumSize: const Size(120, 48),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        elevation: 3,
                        shadowColor: const Color(0xFFE91E63).withOpacity(0.3),
                      ),
                      child: Row(
                        children: [
                          Text(
                            "다음",
                            style: GoogleFonts.nunito(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          SizedBox(width: 5),
                          Icon(Icons.arrow_forward, size: 16),
                        ],
                      ),
                    ),
                  ],
                ),
        ],
      ),
    );
  }

  Widget _buildDotIndicator(int index) {
    bool isActive = _currentPage == index;
    
    return AnimatedContainer(
      duration: Duration(milliseconds: 300),
      margin: const EdgeInsets.symmetric(horizontal: 4),
      height: 8,
      width: isActive ? 24 : 8,
      decoration: BoxDecoration(
        color: isActive
            ? const Color(0xFFE91E63)
            : const Color(0xFFCBD5E1),
        borderRadius: BorderRadius.circular(4),
        boxShadow: isActive ? [
          BoxShadow(
            color: const Color(0xFFE91E63).withOpacity(0.3),
            blurRadius: 3,
            spreadRadius: 1,
          )
        ] : null,
      ),
    );
  }
}

class IntroPage {
  final String title;
  final String description;
  final IconData image;
  final Color color;

  IntroPage({
    required this.title,
    required this.description,
    required this.image,
    required this.color,
  });
}
