import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../utils/preferences_util.dart';
import '../gallery_screen.dart';
import 'intro_screen.dart';
import 'dart:math' as math;

// 핑크 테마 색상 정의
const Color pinkPrimary = Color(0xFFE91E63);
const Color pinkLight = Color(0xFFF48FB1);
const Color pinkDark = Color(0xFFAD1457);
const Color pinkBackground = Color(0xFFFCE4EC);

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  _SplashScreenState createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> with TickerProviderStateMixin {
  // 스케일 애니메이션
  late AnimationController _scaleController;
  late Animation<double> _scaleAnimation;
  
  // 페이드 애니메이션
  late AnimationController _fadeController;
  late Animation<double> _fadeAnimation;
  
  // 회전 애니메이션
  late AnimationController _rotateController;
  late Animation<double> _rotateAnimation;
  
  // 파티클 애니메이션
  late AnimationController _particleController;
  late Animation<double> _particleAnimation;
  
  // 배경 그라데이션 애니메이션
  late AnimationController _backgroundController;
  late Animation<Color?> _backgroundAnimation;
  
  final List<Particle> _particles = List.generate(
    15, 
    (index) => Particle(
      position: Offset(
        math.Random().nextDouble() * 300, 
        math.Random().nextDouble() * 300
      ),
      size: math.Random().nextDouble() * 10 + 5,
      color: Color.fromRGBO(
        255, 
        math.Random().nextInt(100) + 155, 
        math.Random().nextInt(155) + 100, 
        math.Random().nextDouble() * 0.5 + 0.5
      ),
      speed: math.Random().nextDouble() * 2 + 1,
    )
  );

  @override
  void initState() {
    super.initState();
    
    // 스케일 애니메이션
    _scaleController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    );
    _scaleAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _scaleController, curve: Curves.elasticOut)
    );
    
    // 페이드 애니메이션
    _fadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _fadeController, curve: Curves.easeIn)
    );
    
    // 회전 애니메이션
    _rotateController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 10000),
    )..repeat();
    _rotateAnimation = Tween<double>(begin: 0, end: 2 * math.pi).animate(
      CurvedAnimation(parent: _rotateController, curve: Curves.linear)
    );
    
    // 파티클 애니메이션
    _particleController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 5000),
    )..repeat();
    _particleAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _particleController, curve: Curves.linear)
    );
    
    // 배경 그라데이션 애니메이션
    _backgroundController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 3000),
    )..repeat(reverse: true);
    _backgroundAnimation = ColorTween(
      begin: pinkBackground,
      end: Color(0xFFF8BBD0),
    ).animate(_backgroundController);
    
    // 애니메이션 시작
    _scaleController.forward();
    _fadeController.forward();
    
    // 갤러리 화면으로 기본적으로 이동 (인트로 건너뛰기)
    Future.delayed(const Duration(seconds: 3), () {
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (context) => const GalleryScreen()),
      );
    });
  }

  @override
  void dispose() {
    _scaleController.dispose();
    _fadeController.dispose();
    _rotateController.dispose();
    _particleController.dispose();
    _backgroundController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;
    
    return AnimatedBuilder(
      animation: _backgroundController,
      builder: (context, child) {
        return Scaffold(
          body: Container(
            width: double.infinity,
            height: double.infinity,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  _backgroundAnimation.value ?? pinkBackground,
                  pinkBackground,
                ],
              ),
            ),
            child: Stack(
              children: [
                // 파티클 애니메이션
                ...(_particles.map((particle) {
                  return AnimatedBuilder(
                    animation: _particleAnimation,
                    builder: (context, child) {
                      final value = _particleAnimation.value;
                      final dx = (particle.position.dx + particle.speed * 100 * value) % size.width;
                      final dy = (particle.position.dy - particle.speed * 80 * value) % size.height;
                      
                      return Positioned(
                        left: dx,
                        top: dy,
                        child: Opacity(
                          opacity: 0.7,
                          child: Container(
                            width: particle.size,
                            height: particle.size,
                            decoration: BoxDecoration(
                              color: particle.color,
                              shape: BoxShape.circle,
                              boxShadow: [
                                BoxShadow(
                                  color: particle.color.withOpacity(0.3),
                                  blurRadius: 10,
                                  spreadRadius: 1,
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  );
                }).toList()),
                
                // 메인 콘텐츠
                Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // 해파리 이미지
                      AnimatedBuilder(
                        animation: Listenable.merge([_scaleAnimation, _rotateAnimation]),
                        builder: (context, child) {
                          return Transform.scale(
                            scale: _scaleAnimation.value,
                            child: Transform.rotate(
                              angle: _rotateAnimation.value * 0.1,
                              child: Container(
                                width: 250,
                                height: 250,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  boxShadow: [
                                    BoxShadow(
                                      color: pinkPrimary.withOpacity(0.3),
                                      blurRadius: 25,
                                      spreadRadius: 10,
                                    ),
                                  ],
                                ),
                                child: Image.asset(
                                  'assets/images/jellyfish.png',
                                  width: 220,
                                  height: 220,
                                ),
                              ),
                            ),
                          );
                        },
                      ),
                      
                      const SizedBox(height: 30),
                      
                      // 메인 타이틀
                      AnimatedBuilder(
                        animation: _fadeAnimation,
                        builder: (context, child) {
                          return FadeTransition(
                            opacity: _fadeAnimation,
                            child: Transform.translate(
                              offset: Offset(0, 20 * (1 - _fadeAnimation.value)),
                              child: Text(
                                "Jellyfish 해파리 도감",
                                style: GoogleFonts.cabin(
                                  fontSize: 36,
                                  fontWeight: FontWeight.bold,
                                  color: pinkDark,
                                  letterSpacing: 1.2,
                                  shadows: [
                                    Shadow(
                                      color: Colors.black12,
                                      offset: Offset(2, 2),
                                      blurRadius: 5,
                                    ),
                                  ],
                                ),
                                textAlign: TextAlign.center,
                              ),
                            ),
                          );
                        },
                      ),
                      
                      const SizedBox(height: 16),
                      
                      // 부제목
                      AnimatedBuilder(
                        animation: _fadeAnimation,
                        builder: (context, child) {
                          return FadeTransition(
                            opacity: _fadeAnimation,
                            child: Transform.translate(
                              offset: Offset(0, 30 * (1 - _fadeAnimation.value)),
                              child: Text(
                                "인공지능 해파리 도감",
                                style: GoogleFonts.nunitoSans(
                                  fontSize: 20,
                                  color: pinkDark.withOpacity(0.8),
                                  height: 1.3,
                                  letterSpacing: 1.0,
                                  fontWeight: FontWeight.w600,
                                ),
                                textAlign: TextAlign.center,
                              ),
                            ),
                          );
                        },
                      ),
                      
                      const SizedBox(height: 40),
                      
                      // 로딩 인디케이터
                      FadeTransition(
                        opacity: _fadeAnimation,
                        child: SizedBox(
                          width: 60,
                          height: 60,
                          child: CircularProgressIndicator(
                            valueColor: AlwaysStoppedAnimation<Color>(pinkPrimary),
                            strokeWidth: 4,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class Particle {
  final Offset position;
  final double size;
  final Color color;
  final double speed;
  
  Particle({
    required this.position,
    required this.size,
    required this.color,
    required this.speed,
  });
}
