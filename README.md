# 🎓 Project 10. 학생 자기평가 루브릭 분석 시스템

## 📌 프로젝트 개요
대학 물리/공학 실험 수업용 학생 자가평가 웹 애플리케이션

## 🛠️ 사용 기술
- Python 3.11
- Streamlit
- Plotly
- Scikit-learn (K-Means 군집화)
- SQLite

## ✨ 주요 기능
- 5개 역량 영역 슬라이더 자가평가 (이론/장비/데이터/오차/결론)
- 사전·사후 레이더 차트 비교
- 무성의 응답 자동 감지 필터
- K-Means(k=3) 군집화 → 학습 그룹 자동 분류
- 메타인지 Quadrant Plot (자가점수 vs 실제 오차율)
- CSV / Excel 데이터 다운로드

## 🚀 실행 방법
```bash
pip install streamlit pandas numpy plotly scikit-learn openpyxl
streamlit run app.py
