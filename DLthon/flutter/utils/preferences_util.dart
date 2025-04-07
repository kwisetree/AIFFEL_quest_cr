import 'package:shared_preferences/shared_preferences.dart';

class PreferencesUtil {
  static const String _keyIntroSeen = 'intro_seen';

  // 인트로 화면 본 적 있는지 확인
  static Future<bool> isIntroSeen() async {
    try {
      final SharedPreferences prefs = await SharedPreferences.getInstance();
      return prefs.getBool(_keyIntroSeen) ?? false;
    } catch (e) {
      print('설정 로드 오류: $e');
      return false; // 오류 발생시 기본값 false
    }
  }

  // 인트로 화면 본 것으로 표시
  static Future<void> setIntroSeen() async {
    try {
      final SharedPreferences prefs = await SharedPreferences.getInstance();
      await prefs.setBool(_keyIntroSeen, true);
    } catch (e) {
      print('설정 저장 오류: $e');
    }
  }
  
  // 설정 초기화 - 디버깅용
  static Future<void> resetPreferences() async {
    try {
      final SharedPreferences prefs = await SharedPreferences.getInstance();
      await prefs.clear();
      print('모든 설정이 초기화되었습니다.');
    } catch (e) {
      print('설정 초기화 오류: $e');
    }
  }
}
