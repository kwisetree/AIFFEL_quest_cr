import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:camera/camera.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../models/photo_model.dart';
import 'photo_detail_screen.dart';
import 'dart:math';

class GalleryScreen extends StatefulWidget {
  const GalleryScreen({super.key});

  @override
  _GalleryScreenState createState() => _GalleryScreenState();
}

class _GalleryScreenState extends State<GalleryScreen> with TickerProviderStateMixin {
  late Future<List<Photo>> _photoFuture;
  final List<Photo> _localPhotos = [];
  final ImagePicker _picker = ImagePicker();
  List<CameraDescription> _cameras = [];

  // 애니메이션 컨트롤러
  late AnimationController _gridAnimationController;
  late AnimationController _fabAnimationController;
  late Animation<double> _fabScaleAnimation;
  late Animation<double> _fabRotateAnimation;

  // 검색 컨트롤러
  final TextEditingController _searchController = TextEditingController();
  bool _isSearching = false;
  String _searchQuery = "";

  // 스크롤 컨트롤러
  late ScrollController _scrollController;
  bool _showToTopButton = false;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
    _loadPhotos();

    // 시스템 UI 최적화
    SystemChrome.setSystemUIOverlayStyle(SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
    ));

    // 그리드 애니메이션 컨트롤러
    _gridAnimationController = AnimationController(
      duration: const Duration(milliseconds: 1200), // 약간 빠르게
      vsync: this,
    );

    // FAB 애니메이션 컨트롤러
    _fabAnimationController = AnimationController(
      duration: const Duration(milliseconds: 2000),
      vsync: this,
    );

    _fabScaleAnimation = Tween<double>(begin: 1.0, end: 1.1).animate(
      CurvedAnimation(
        parent: _fabAnimationController,
        curve: Curves.easeInOut,
      ),
    );

    _fabRotateAnimation = Tween<double>(begin: 0.0, end: 0.1).animate(
      CurvedAnimation(
        parent: _fabAnimationController,
        curve: Curves.easeInOut,
      ),
    );

    // 스크롤 컨트롤러 - 메모리 누수 방지를 위한 dispose 추가
    _scrollController = ScrollController();
    _scrollController.addListener(_handleScroll);

    // 애니메이션 시작
    _gridAnimationController.forward();
    _fabAnimationController.repeat(reverse: true);
  }
  
  // 스크롤 이벤트 처리 - 성능 최적화
  void _handleScroll() {
    final showButton = _scrollController.offset > 200;
    if (showButton != _showToTopButton) {
      setState(() {
        _showToTopButton = showButton;
      });
    }
  }
  
  // 사진 로딩 함수
  Future<void> _loadPhotos() async {
    _photoFuture = getRandomAnimalPhotos(30);
  }

  @override
  void dispose() {
    // 모든 컨트롤러 정리 - 메모리 누수 방지
    _gridAnimationController.dispose();
    _fabAnimationController.dispose();
    _searchController.dispose();
    _scrollController.removeListener(_handleScroll); // 리스너 제거
    _scrollController.dispose();
    super.dispose();
  }

  // 카메라 초기화 및 권한 요청
  Future<void> _initializeCamera() async {
    await requestCameraPermission();
    _cameras = await availableCameras();
    if (_cameras.isEmpty) {
      print("No available cameras");
    }
  }

  // 카메라 권한 요청 함수
  Future<void> requestCameraPermission() async {
    var status = await Permission.camera.request();
    if (status.isDenied || status.isPermanentlyDenied) {
      print("Camera permission denied");
    }
  }

  // 새로고침 시 새로운 사진을 불러오는 함수 - 최적화
  Future<void> _refreshPhotos() async {
    try {
      // 상태 보존 방식으로 동시성 이슈 해결
      final newPhotosFuture = getRandomAnimalPhotos(30);
      
      setState(() {
        _photoFuture = newPhotosFuture;
      });
      
      // 새로고침 애니메이션 - 최적화
      _gridAnimationController.reset();
      await Future.delayed(const Duration(milliseconds: 50)); // 작은 지연을 주어 애니메이션 알고리즘 개선
      _gridAnimationController.forward();
    } catch (e) {
      // 오류 처리
      debugPrint('새로고침 오류: $e');
      // 오류 가 발생해도 애니메이션은 계속 진행
      _gridAnimationController.reset();
      _gridAnimationController.forward();
    }
  }

  // 카메라 또는 갤러리에서 사진 가져오기
  Future<void> _pickImage(ImageSource source) async {
    final XFile? pickedFile = await _picker.pickImage(source: source);

    if (pickedFile != null) {
      setState(() {
        _localPhotos.add(
          Photo(
            id: 1000 + _localPhotos.length,
            url: "", // 로컬 파일이라 URL 없음
            title: "내 해파리 사진",
            localFile: File(pickedFile.path),
          ),
        );
      });
    }
  }

  // 네비게이션: 사진 클릭하면 상세 페이지로 이동
  void _navigateToDetail(Photo photo) {
    Navigator.push(
      context,
      PageRouteBuilder(
        transitionDuration: Duration(milliseconds: 500),
        pageBuilder: (context, animation, secondaryAnimation) => PhotoDetailScreen(photo: photo),
        transitionsBuilder: (context, animation, secondaryAnimation, child) {
          var begin = Offset(0.0, 0.1);
          var end = Offset.zero;
          var curve = Curves.easeOutQuint;
          var tween = Tween(begin: begin, end: end).chain(CurveTween(curve: curve));
          return SlideTransition(
            position: animation.drive(tween),
            child: FadeTransition(
              opacity: animation,
              child: child,
            ),
          );
        },
      ),
    );
  }

  // FloatingActionButton (카메라 및 갤러리 추가 버튼)
  Widget _buildFloatingActionButton() {
    return AnimatedBuilder(
      animation: _fabAnimationController,
      builder: (context, child) {
        return Transform.scale(
          scale: _fabScaleAnimation.value,
          child: Transform.rotate(
            angle: _fabRotateAnimation.value,
            child: FloatingActionButton(
              backgroundColor: Theme.of(context).colorScheme.primary,
              foregroundColor: Colors.white,
              elevation: 8,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              onPressed: () {
                _showImagePickerOptions();
              },
              child: const Icon(Icons.add_a_photo, size: 26),
            ),
          ),
        );
      },
    );
  }

  // 이미지 피커 옵션 바텀시트
  void _showImagePickerOptions() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) {
        return Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
            boxShadow: [
              BoxShadow(
                color: Colors.black12,
                blurRadius: 10,
                spreadRadius: 2,
              )
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 40,
                height: 4,
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: Colors.grey.shade300,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              Text(
                '해파리 사진 추가하기',
                style: GoogleFonts.nunito(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: const Color(0xFFAD1457),
                ),
              ),
              const SizedBox(height: 16),
              ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF8BBD0),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(Icons.camera_alt, color: Color(0xFFAD1457)),
                ),
                title: Text(
                  "카메라로 촬영",
                  style: GoogleFonts.nunitoSans(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                subtitle: Text(
                  "지금 해파리를 촬영하세요",
                  style: GoogleFonts.nunitoSans(
                    fontSize: 14,
                    color: Colors.grey.shade600,
                  ),
                ),
                onTap: () {
                  Navigator.pop(context);
                  _pickImage(ImageSource.camera);
                },
              ),
              const SizedBox(height: 8),
              ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF8BBD0),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(Icons.photo_library, color: Color(0xFFAD1457)),
                ),
                title: Text(
                  "갤러리에서 선택",
                  style: GoogleFonts.nunitoSans(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                subtitle: Text(
                  "저장된 해파리 사진을 선택하세요",
                  style: GoogleFonts.nunitoSans(
                    fontSize: 14,
                    color: Colors.grey.shade600,
                  ),
                ),
                onTap: () {
                  Navigator.pop(context);
                  _pickImage(ImageSource.gallery);
                },
              ),
              const SizedBox(height: 16),
            ],
          ),
        );
      },
    );
  }

  // 앱바 검색 아이콘 토글
  void _toggleSearch() {
    setState(() {
      _isSearching = !_isSearching;
      if (!_isSearching) {
        _searchController.clear();
        _searchQuery = "";
      }
    });
  }

  // 맨 위로 스크롤
  void _scrollToTop() {
    _scrollController.animateTo(
      0,
      duration: Duration(milliseconds: 500),
      curve: Curves.easeOutCubic,
    );
  }

  // 검색 결과 필터링
  List<Photo> _filterPhotos(List<Photo> photos) {
    if (_searchQuery.isEmpty) {
      return photos;
    }

    return photos.where((photo) =>
        photo.title.toLowerCase().contains(_searchQuery.toLowerCase())
    ).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: NestedScrollView(
        controller: _scrollController,
        headerSliverBuilder: (context, innerBoxIsScrolled) => [
          SliverAppBar(
            expandedHeight: 120.0,
            floating: true,
            pinned: true,
            elevation: 0,
            backgroundColor: Theme.of(context).colorScheme.primary,
            shape: const RoundedRectangleBorder(
              borderRadius: BorderRadius.vertical(
                bottom: Radius.circular(20),
              ),
            ),
            flexibleSpace: FlexibleSpaceBar(
              title: _isSearching
                  ? Container(
                width: double.infinity,
                height: 40,
                margin: EdgeInsets.only(left: 48.0, right: 16.0),
                child: TextField(
                  controller: _searchController,
                  onChanged: (value) {
                    setState(() {
                      _searchQuery = value;
                    });
                  },
                  style: GoogleFonts.nunito(
                    color: Colors.white,
                    fontSize: 16,
                  ),
                  decoration: InputDecoration(
                    hintText: '해파리 검색...',
                    hintStyle: GoogleFonts.nunito(
                      color: Colors.white70,
                      fontSize: 16,
                    ),
                    border: InputBorder.none,
                    contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  ),
                ),
              )
                  : Text(
                "해파리 도감",
                style: GoogleFonts.cabin(
                  fontWeight: FontWeight.bold,
                  fontSize: 22,
                ),
              ),
              centerTitle: true,
              background: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Color(0xFFEC407A),
                      Color(0xFFE91E63),
                    ],
                  ),
                ),
                child: Center(
                  child: Opacity(
                    opacity: 0.2,
                    child: Image.asset(
                      'assets/images/jellyfish.png',
                      width: 100,
                      height: 100,
                      fit: BoxFit.contain,
                    ),
                  ),
                ),
              ),
            ),
            actions: [
              IconButton(
                icon: Icon(_isSearching ? Icons.close : Icons.search, size: 26),
                onPressed: _toggleSearch,
                tooltip: _isSearching ? '검색 닫기' : '검색',
              ),
              IconButton(
                icon: const Icon(Icons.refresh, size: 26),
                onPressed: _refreshPhotos,
                tooltip: '새로고침',
              ),
            ],
          ),
        ],
        body: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Colors.white,
                Color(0xFFFCE4EC),
              ],
            ),
          ),
          child: RefreshIndicator(
            onRefresh: _refreshPhotos,
            color: Theme.of(context).colorScheme.primary,
            child: FutureBuilder<List<Photo>>(
              future: _photoFuture,
              builder: (context, snapshot) {
                // ✅ 디버깅용 로그
                print("📸 connectionState: ${snapshot.connectionState}");
                print("📦 hasData: ${snapshot.hasData}");
                print("❗ error: ${snapshot.error}");

                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(
                    child: CircularProgressIndicator(),
                  );
                } else if (snapshot.hasError) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.error_outline,
                          size: 60,
                          color: Colors.red.shade300,
                        ),
                        SizedBox(height: 16),
                        Text(
                          "오류 발생: ${snapshot.error}",
                          style: GoogleFonts.nunitoSans(
                            fontSize: 16,
                            color: Colors.red.shade800,
                          ),
                        ),
                        SizedBox(height: 24),
                        ElevatedButton.icon(
                          onPressed: _refreshPhotos,
                          icon: Icon(Icons.refresh),
                          label: Text("다시 시도"),
                          style: ElevatedButton.styleFrom(
                            padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                          ),
                        ),
                      ],
                    ),
                  );
                } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          Icons.photo_album_outlined,
                          size: 60,
                          color: Colors.grey.shade400,
                        ),
                        SizedBox(height: 16),
                        Text(
                          "사진을 불러올 수 없습니다.",
                          style: GoogleFonts.nunitoSans(
                            fontSize: 16,
                            color: Colors.grey.shade700,
                          ),
                        ),
                      ],
                    ),
                  );
                }

                // 📸 정상적으로 데이터가 있을 때 이후 코드는 기존 그대로!    // 나머지 그리드 표시 코드는 그대로
                return GridView.builder(
                  padding: const EdgeInsets.all(10),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2, // ✅ 2열로 변경 (사진 더 크게)
                    crossAxisSpacing: 10,
                    mainAxisSpacing: 10,
                  ),
                  itemCount: _filterPhotos([...snapshot.data!, ..._localPhotos]).length,
                  itemBuilder: (context, index) {
                    final photos = _filterPhotos([...snapshot.data!, ..._localPhotos]);
                    final photo = photos[index];
                    final isLocal = photo.localFile != null; // 로컬 파일 여부 확인

                    return GestureDetector(
                      onTap: () => _navigateToDetail(photo),
                      child: ScaleTransition(
                        scale: Tween<double>(begin: 0.0, end: 1.0).animate(
                          CurvedAnimation(
                            parent: _gridAnimationController,
                            curve: Curves.easeInOut,
                          ),
                        ),
                        child: FadeTransition(
                          opacity: Tween<double>(begin: 0.0, end: 1.0).animate(
                            CurvedAnimation(
                              parent: _gridAnimationController,
                              curve: Curves.easeInOut,
                            ),
                          ),
                          child: Hero(
                            tag: 'photo_${photo.id}',
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(12),
                              child: isLocal
                                  ? Image.file(
                                File(photo.localFile!.path),
                                fit: BoxFit.cover,
                              )
                                  : CachedNetworkImage(
                                imageUrl: photo.url,
                                fit: BoxFit.cover,
                                placeholder: (context, url) => Container(
                                  color: Colors.grey[200],
                                  child: Center(
                                    child: CircularProgressIndicator(
                                      valueColor: AlwaysStoppedAnimation<Color>(Theme.of(context).colorScheme.primary),
                                      strokeWidth: 2,
                                    ),
                                  ),
                                ),
                                errorWidget: (context, url, error) => Container(
                                  color: Colors.grey[200],
                                  child: Icon(Icons.error, color: Colors.red[300]),
                                ),
                                // 성능 최적화 옵션
                                memCacheWidth: MediaQuery.of(context).size.width ~/ 2 * 2, // 해상도에 맞게 계산
                                fadeOutDuration: const Duration(milliseconds: 300),
                                fadeInDuration: const Duration(milliseconds: 300),
                              ),
                            ),
                          ),
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ),
      ),
      floatingActionButton: _showToTopButton
          ? Column(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          FloatingActionButton(
            onPressed: _scrollToTop,
            mini: true,
            backgroundColor: Theme.of(context).colorScheme.secondary,
            foregroundColor: Colors.white,
            elevation: 6,
            child: Icon(Icons.arrow_upward, size: 20),
            heroTag: "toTopButton",
          ),
          SizedBox(height: 16),
          _buildFloatingActionButton(),
        ],
      )
          : _buildFloatingActionButton(),
    );
  }
}