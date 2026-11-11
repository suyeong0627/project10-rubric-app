# 🎓 Project 10. 학생 자기평가 루브릭 분석 시스템

## 📌 프로젝트 개요
대학 물리/공학 실험 수업용 학생 자가평가 웹 애플리케이션

## 🌐 배포 링크
👉 [앱 바로가기](https://suyeong0627-project10-rubric-app.streamlit.app)

---

## 🛠 사용 기술
| 분류 | 기술 |
|------|------|
| Frontend | Streamlit |
| 시각화 | Plotly |
| 머신러닝 | Scikit-learn (K-Means) |
| 데이터베이스 | SQLite |
| 언어 | Python |

---

## 📂 파일 구조
project10/
├── app.py # 메인 애플리케이션
├── rubrics.db # SQLite 데이터베이스
├── requirements.txt # 패키지 목록
└── README.md # 프로젝트 설명

---

## ⚙️ 주요 기능

### 👨‍🎓 학생 뷰
- 5개 루브릭 영역 1~5점 슬라이더 입력
- 사전/사후 점검 선택 제출
- 레이더 차트(Radar Chart)로 역량 시각화
- 취약 영역 자동 보강 가이드 출력

### 👨‍🏫 교수자 뷰
- K-Means(k=3) 군집화 산점도
- 취약 루브릭 항목 자동 감지 카드
- 전체 데이터 CSV/XLSX 다운로드

---

## 🚀 로컬 실행 방법
```bash
# 패키지 설치
pip install -r requirements.txt

# 앱 실행
streamlit run app.py
📊 알고리즘 설명
Z-score 정규화: 학생 응답 표준화
응답 무결성 검사: 무성의 응답 자동 필터링
K-Means 군집화: 역량별 학생 자동 분류
위상 산점도: 메타인지 2D Quadrant Plot
