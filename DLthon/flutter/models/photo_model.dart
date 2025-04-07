import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';
import '../constants/const.dart'; // ✅ API 키 가져오기

class Photo {
  final int id;
  final String url;
  final String title;
  final File? localFile; // ✅ 로컬 파일 추가 (갤러리 & 카메라 지원)

  Photo({
    required this.id,
    required this.url,
    required this.title,
    this.localFile,
  });

  // ✅ Unsplash API 응답(JSON)을 Photo 객체로 변환하는 팩토리 메서드
  factory Photo.fromJson(Map<String, dynamic> json, int id) {
    return Photo(
      id: id,
      url: json['urls']['regular'], // Unsplash에서 제공하는 이미지 URL
      title: json['description'] ?? "Animal Photo #$id", // 설명이 없으면 기본 제목 사용
    );
  }
}

// ✅ Unsplash API에서 랜덤 동물 사진 가져오는 함수 - 최적화
Future<List<Photo>> getRandomAnimalPhotos(int count) async {
  if (unsplashAccessKey.isEmpty) {
    throw Exception("❗ Unsplash API Key가 없습니다. `const.dart` 파일을 확인하세요.");
  }

  final String url =
      "https://api.unsplash.com/photos/random?query=jellyfish&count=$count&client_id=$unsplashAccessKey";

  try {
    final response = await http.get(
      Uri.parse(url),
      headers: {'Accept-Version': 'v1'}, // API 버전 명시
    ).timeout(const Duration(seconds: 15), onTimeout: () {
      debugPrint("타임아웃: Unsplash API 응답이 너무 오래 걸립니다.");
      throw Exception("타임아웃: 서버 응답이 너무 오래 걸립니다.");
    }); // 타임아웃 추가

    if (response.statusCode == 200) {
      // compute를 사용한 백그라운드 처리로 성능 향상
      return await compute(_parsePhotos, response.body);
    } else {
      throw Exception("❗ Unsplash API 오류: ${response.statusCode}");
    }
  } catch (e) {
    debugPrint("API 호출 오류: $e");
    throw Exception("❗ 이미지를 불러오는 중 오류가 발생했습니다. 네트워크를 확인해주세요.");
  }
}

// 백그라운드 스레드에서 JSON 파싱
List<Photo> _parsePhotos(String responseBody) {
  final List<dynamic> jsonData = json.decode(responseBody);
  return jsonData.asMap().entries.map((entry) {
    return Photo.fromJson(entry.value, entry.key);
  }).toList();
}