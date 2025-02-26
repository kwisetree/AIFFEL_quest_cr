import 'dart:async';
import 'package:flutter/material.dart';

void main() {
  runApp(PomodoroApp());
}

// 앱의 기본 구조 설정
class PomodoroApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: PomodoroTimerScreen(),
    );
  }
}

// 타이머 화면을 담당하는 StatefulWidget
class PomodoroTimerScreen extends StatefulWidget {
  @override
  _PomodoroTimerScreenState createState() => _PomodoroTimerScreenState();
}

class _PomodoroTimerScreenState extends State<PomodoroTimerScreen> {
  // 기본 시간 설정 (초 단위)
  static const int workTime = 25;      // 25초 (작업 시간)  -> 60을 곱해 주면 분 단위로 변경 가능
  static const int shortBreakTime = 5; // 5초 (짧은 휴식) -> 60을 곱해 주면 분 단위로 변경 가능
  static const int longBreakTime = 15; // 15초 (긴 휴식) -> 60을 곱해 주면 분 단위로 변경 가능
  static const int tickInterval = 1;  // 1초마다 업데이트

  int cycle = 0;             // 현재 작업/휴식 사이클 (4회마다 긴 휴식)
  int remainingTime = workTime;  // 현재 남은 시간 (초 단위)
  int totalElapsedTime = 0;   // 누적 시간 (초 단위)
  bool isWorking = true;     // 현재 작업 중인지 여부
  Timer? timer;              // 타이머 객체
  bool isRunning = false;    // 타이머 실행 여부 확인 (중복 실행 방지)

  // 타이머 시작 함수
  void startTimer() {
    if (isRunning) return; // 중복 실행 방지
    isRunning = true;

    timer = Timer.periodic(Duration(seconds: tickInterval), (t) {
      if (remainingTime > tickInterval) {
        setState(() {
          remainingTime -= tickInterval; // 지정한 간격(1초)마다 시간 감소
          totalElapsedTime += tickInterval; // 누적 시간 추가
        });
      } else {
        t.cancel(); // 타이머 종료
        isRunning = false;
        remainingTime = 0;
        onSessionEnd(); // 세션 종료 처리
      }
    });
  }

  // 타이머 일시정지 함수
  void pauseTimer() {
    if (timer != null && timer!.isActive) {
      timer!.cancel(); // 타이머 일시정지
      setState(() {
        isRunning = false;
      });
    }
  }

  // 타이머 재개 함수
  void resumeTimer() {
    if (!isRunning) {
      startTimer(); // 타이머 재개
      setState(() {
        isRunning = true;
      });
    }
  }

  // 현재 세션(작업/휴식)이 끝났을 때 실행되는 함수
  void onSessionEnd() {
    if (isWorking) {
      print("작업 시간이 종료되었습니다. 휴식 시간을 시작합니다.");
    } else {
      print("휴식 시간이 종료되었습니다. 작업 시간을 시작합니다.");
    }
    nextSession(); // 다음 세션(작업 or 휴식)으로 전환
  }

  // 다음 세션(작업 or 휴식)으로 전환하는 함수
  void nextSession() {
    setState(() {
      isWorking = !isWorking; // 작업 ↔ 휴식 전환

      // 작업 시간이 끝났을 때만 사이클 증가
      if (!isWorking) {
        cycle++; // 회차 증가
        // 사이클이 4의 배수일 때만 긴 휴식(15초), 그 외에는 짧은 휴식(5초)
        remainingTime = (cycle % 4 == 0) ? longBreakTime : shortBreakTime;
      } else {
        remainingTime = workTime; // 휴식이 끝났다면 다시 작업 시간 설정
      }
    });
    startTimer(); // 다음 세션 타이머 시작
  }

  */
  // 타이머를 초기 상태로 리셋하는 함수
  void resetTimer() {
    setState(() {
      cycle = 0; // 사이클 초기화
      totalElapsedTime = 0; // 누적 시간 초기화
      isWorking = true; // 작업 모드로 초기화
      remainingTime = workTime; // 25초로 설정
      isRunning = false;
    });
    timer?.cancel(); // 타이머 종료
  }

  // 초 단위를 "MM:SS" 형식으로 변환하는 함수
  String formatTime(int seconds) {
    int minutes = seconds ~/ 60;
    int secs = seconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
  }

  // UI 빌드 (Flutter 화면 구성)
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Pomodoro Timer"), centerTitle: true),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // 현재 상태 표시 (작업 / 짧은 휴식 / 긴 휴식)
            Text(
              isWorking ? "🔴 작업 시간" : (cycle % 4 == 0 ? "💤 긴 휴식" : "🟢 짧은 휴식"),
              style: TextStyle(fontSize: 30, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 20),

            // 남은 시간 표시
            Text(
              formatTime(remainingTime), // ex) "00:25"
              style: TextStyle(fontSize: 50, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 20),

            // 누적 시간 표시
            Text(
              "누적 시간: ${formatTime(totalElapsedTime)}", // ex) "00:25"
              style: TextStyle(fontSize: 20),
            ),
            SizedBox(height: 20),

            // 사이클 번호 표시
            Text(
              "사이클: $cycle",
              style: TextStyle(fontSize: 20),
            ),
            SizedBox(height: 30),

            // 시작 / 일시정지 / 리셋 버튼 UI
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ElevatedButton(
                  onPressed: () {
                    if (isRunning) {
                      pauseTimer();
                    } else {
                      resumeTimer();
                    }
                  },
                  child: Icon(
                    isRunning ? Icons.pause : Icons.play_arrow,
                    size: 40,
                  ),
                ),
                SizedBox(width: 20),
                ElevatedButton(
                  onPressed: resetTimer,
                  child: Icon(
                    Icons.refresh,
                    size: 40,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}


///*Pomodoro 앱 개발 과정: 오류 해결 및 개선 회고
// 1. 초기 버전
// 기능: 타이머 기능 (작업 시간, 휴식 시간) 구현현
// 문제: 4회차에 한번씩 긴 휴식 추가 하였으나 두배수로 횟수가 증가됨
// 해결 및 개선사항:
// 1. 원래 코드에서는 'isWorking = !isWorking' 직후에 바로 'cycle++'를 실행
//    이는 작업 시간이 끝났을 때뿐만 아니라 휴식 시간이 끝났을 때도 사이클이 증가하는 오류가 발생했습니다.
//
// 2. 포모도로 타이머의 원리는 '작업 → 휴식 → 작업 → 휴식...'의 순환인데,
//    사이클은 작업 시간이 끝날 때만 증가해야 합니다. 즉, 작업 1회 + 휴식 1회를 완료했을 때
//    하나의 사이클로 간주해야 합니다.
//
// 3. 수정된 코드에서는 'if (!isWorking)' 조건문 안에 'cycle++'를 넣어
//    작업 시간이 끝나고 휴식 시간으로 전환될 때만 사이클이 증가하도록 수정했습니다.
//    이렇게 하면 정확히 작업 시간이 끝날 때만 사이클이 증가합니다.

// 1-1. 초기버전 개선 (목표)
// 기능: 타이머 기능 (작업 시간, 휴식 시간), 타이머 시작/일시정지/리셋 버튼, 기본 UI 구성

// 2. 오류 디버깅 및 해결 과정

// 2-1. 타이머 실행 중 UI 업데이트 문제:
// 초기 코드에서는 startTimer 함수가 타이머를 주기적으로 업데이트하는데, setState가 제대로 호출되지 않아 UI가 실시간으로 갱신되지 않는 문제가 발생했습니다.
// 해결: setState가 타이머 내부의 시간 업데이트 후 호출되도록 하여 UI가 제대로 갱신되게 했습니다. 또한, Timer 객체를 제대로 관리하여 중복 실행을 방지했습니다.

// 2-2. 일시정지와 재개 문제:
// pauseTimer와 resumeTimer 함수에서 타이머 상태가 제대로 반영되지 않아, 일시정지와 재개 시 UI가 늦게 반영되거나, 예상치 못한 동작이 발생했습니다.
// 해결: isRunning 상태를 setState 내부에서 업데이트하여 UI가 즉시 반영되도록 개선했습니다. 또한, 일시정지 시 타이머가 취소되고, 재개 시 타이머가 다시 시작되도록 했습니다.

// 2-3. 사이클 및 누적 시간 추가:
// 처음에는 단순히 작업 시간만 처리되었고, 누적 시간과 사이클 개념이 없었습니다.
// 해결:
// 누적 시간(totalElapsedTime)을 추가하여 사용자가 지금까지 진행한 시간을 추적할 수 있게 했습니다.
// 사이클(cycle)을 추가하여 작업/휴식 사이클이 끝날 때마다 카운트를 올리고, 매 4번째 사이클에서 긴 휴식이 오도록 로직을 수정했습니다.
// UI에 누적 시간과 사이클을 표시하는 섹션을 추가하여, 타이머의 진행 상황을 직관적으로 알 수 있도록 했습니다.

// 3. UI 개선
// 기존 UI: 텍스트 기반으로 작업/휴식 상태, 타이머, 누적 시간을 표시했습니다.
// 문제A: UI가 다소 정적이고, 직관적인 피드백을 주지 못하는 점이 있었습니다.
// 해결:ElevatedButton에 텍스트 대신 아이콘을 사용하여, 타이머 진행 상태를 아이콘(Icons.pause, Icons.play_arrow, Icons.refresh)으로 표시하도록 개선했습니다.
// 각 버튼의 기능에 맞는 아이콘을 추가하여 사용자 경험을 개선했습니다. 예를 들어, 시작/일시정지 버튼을 Icons.pause와 Icons.play_arrow로 표시하여, 현재 타이머 상태에 따라 동적으로 아이콘이 변경되도록 했습니다.
// 리셋 버튼에 Icons.refresh 아이콘을 추가하여 사용자가 쉽게 인식할 수 있도록 했습니다.
// 문제B: 타이머가 일시정지되었을 때 UI가 즉시 반영되지 않아 버튼 상태가 딜레이로 반영되는 문제.
// 해결: setState 내에서 isRunning 값을 즉시 업데이트하여 UI가 빠르게 반영되도록 했습니다.

// 4. 버퍼링 문제 해결
// 문제: 타이머 실행 중에 setState를 계속 호출하여 UI가 렉이 걸리는 문제 발생. 타이머의 상태가 계속 변경되며 매번 setState가 호출되어 UI가 지연되는 문제가 있었습니다.
// 해결: Timer.periodic 내부에서 remainingTime과 totalElapsedTime 값을 주기적으로 갱신하면서 setState 호출을 최소화하고, UI 업데이트가 원활하게 이루어지도록 최적화했습니다.
// 불필요한 setState 호출을 줄여서, 화면 갱신이 최소화되도록 개선했습니다.

// 5. 종합적인 결과
// 타이머 기능을 성공적으로 구현하고, 일시정지 및 재개 버튼 기능을 원활하게 처리할 수 있게 되었습니다.
// 누적 시간과 사이클을 추가하여, 사용자가 현재까지 진행된 작업과 휴식 시간을 추적할 수 있도록 했습니다.
// UI를 아이콘 기반으로 직관적으로 변경하여 사용자 경험을 개선하였습니다.
// 타이머의 성능을 최적화하여, 버퍼링 없이 원활하게 동작할 수 있도록 했습니다.

// 6. 향후 개선 사항
// 추가적인 기능 개선: 타이머 종료 시 알림을 추가하거나, 사용자 맞춤형 설정(작업 시간, 휴식 시간 설정)을 추가하여 사용자 경험을 더욱 향상시킬 수 있을 것 같습니다.
// UI/UX 향상: 다양한 테마나 애니메이션 효과를 추가하여 시각적으로 더욱 매력적인 앱이 되지 않을까 합니다!

// 7. 개인 회고(곽현정)
// 이 프로젝트를 통해 타이머 관리, UI 디자인, 상태 업데이트 등의 핵심 개념을 실제로 다루어 보면서 Flutter와 Dart의 동작 방식에 대한 이해를 깊게 할 수 있었습니다.
// 버퍼링 문제와 UI 반영 지연 등 초기 개발 단계에서 발생했던 문제들을 해결하면서 코드를 최적화하고 효율적으로 앱 상태를 관리하고 업데이트하는 과정을 익힐 수 있어서 즐거웠어요.
// 승아님과 함께한 덕분에 서로 한 줄 한 줄 정리하고, 앱의 어떤 부분을 개선할 수 있을지에 대해 상의해보는 과정이 마치 앱 개발자가 된 기분을 ㅋㅋ 느끼게 해주었습니다.
// 나중에는 더 개선 사항까지 해서 정말 앱을 제대로 만들어 보는데까지 한발자국 나아간 갈 것 같아서 기대가 됩니다!

// 개인 회고(전승아)
// 퀘스트보단 짧은 프로젝트를 해낸 느낌입니다!
// 기본적으로 4번에 한번 긴휴식으로 전환하는 타이머가 제대로 전환되지 않고 계속 반복되어, 작업시간 이후에만 1 카운트를 증가하고, 이를 바탕으로 4배수마다 고치는 타이머를 개선했고,
// 이후에 타이머 초기화 버튼을 누르면 초기화되도록 구현했습니다. 이후에도 잔버그가 계속 있어 현정님과 토론하며 문제를 개선했습니다.
// 작성과 실행을 통해 문제를 발견하고 해결하고 시각화 하는 짧은 프로젝트를 해보는 것이 보람찼습니다. 조금 더 UI나 서비스를 개선하고 싶은 욕심이 들었습니다.
