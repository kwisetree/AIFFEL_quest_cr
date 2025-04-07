import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:google_fonts/google_fonts.dart';
import 'screens/gallery_screen.dart';
import 'screens/intro/intro_screen.dart';
import 'screens/intro/splash_screen.dart';
import 'utils/preferences_util.dart';

// 해파리 도감에 맞는 핑크 테마 색상 정의
const Color jellyfishPrimaryColor = Color(0xFFE91E63); // 핑크
const Color jellyfishSecondaryColor = Color(0xFFF48FB1); // 연한 핑크
const Color jellyfishBackgroundColor = Color(0xFFFCE4EC); // 매우 연한 핑크

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  try {
    await dotenv.load(fileName: ".env");  // ✅ .env 파일 로드
    
    // 디버깅용 - 설정 초기화 ((필요한 경우 주석 해제)
    // await PreferencesUtil.resetPreferences();
  } catch (e) {
    debugPrint("Failed to load .env file: $e");  // ❗ 에러 출력 개선
  }

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: '해파리 도감',
      theme: ThemeData(
        colorScheme: ColorScheme.light(
          primary: jellyfishPrimaryColor,
          secondary: jellyfishSecondaryColor,
          surface: jellyfishBackgroundColor,
        ),
        scaffoldBackgroundColor: jellyfishBackgroundColor,
        // 고급스러운 앱바 테마
        appBarTheme: AppBarTheme(
          backgroundColor: jellyfishPrimaryColor,
          foregroundColor: Colors.white,
          elevation: 0,
          centerTitle: true,
          shape: const RoundedRectangleBorder(
            borderRadius: BorderRadius.vertical(
              bottom: Radius.circular(20),
            ),
          ),
          titleTextStyle: GoogleFonts.nunito(
            fontSize: 22,
            fontWeight: FontWeight.w700,
            letterSpacing: 0.5,
          ),
        ),
        // 버튼 테마 개선
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: jellyfishPrimaryColor,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(15),
            ),
            elevation: 3,
            shadowColor: jellyfishPrimaryColor.withOpacity(0.5),
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            textStyle: GoogleFonts.nunito(
              fontSize: 16,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        // 기본 텍스트 테마
        textTheme: GoogleFonts.nunitoTextTheme(
          Theme.of(context).textTheme,
        ),
        // 카드 테마
        cardTheme: CardTheme(
          elevation: 6,
          shadowColor: Colors.black26,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
        // 치한 디자인
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: const SplashScreen(),
    );
  }
}