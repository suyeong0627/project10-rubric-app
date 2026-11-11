import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import sqlite3
import time
import datetime
import io

# ───────────────────────────────────────
# 페이지 기본 설정
# ───────────────────────────────────────
st.set_page_config(
    page_title="🎓 실험 역량 자가진단 시스템",
    page_icon="🎓",
    layout="wide"
)

# ───────────────────────────────────────
# DB 초기화 및 함수
# ───────────────────────────────────────
def init_db():
    conn = sqlite3.connect('rubrics.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rubrics
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  student_id TEXT, name TEXT, section TEXT,
                  session TEXT, eval_type TEXT,
                  theory INTEGER, equipment INTEGER,
                  data_precision INTEGER, error_analysis INTEGER,
                  conclusion INTEGER, timestamp TEXT,
                  response_time REAL, actual_error_rate REAL)''')
    conn.commit()
    conn.close()

def save_to_db(data):
    conn = sqlite3.connect('rubrics.db')
    c = conn.cursor()
    c.execute('''INSERT INTO rubrics
                 (student_id, name, section, session, eval_type,
                  theory, equipment, data_precision, error_analysis,
                  conclusion, timestamp, response_time, actual_error_rate)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
              (data['student_id'], data['name'], data['section'],
               data['session'], data['eval_type'], data['theory'],
               data['equipment'], data['data_precision'],
               data['error_analysis'], data['conclusion'],
               data['timestamp'], data['response_time'],
               data['actual_error_rate']))
    conn.commit()
    conn.close()

def load_from_db():
    conn = sqlite3.connect('rubrics.db')
    df = pd.read_sql_query("SELECT * FROM rubrics", conn)
    conn.close()
    return df

def add_sample_data():
    """교수자 뷰 시뮬레이션용 샘플 데이터"""
    conn = sqlite3.connect('rubrics.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM rubrics")
    count = c.fetchone()[0]

    if count == 0:
        samples = [
            ("2024001","김민준","1반","1차시 등가속도 운동","사후",4,3,5,2,4,3.2),
            ("2024002","이서연","1반","1차시 등가속도 운동","사후",5,5,5,5,5,1.1),
            ("2024003","박지호","2반","1차시 등가속도 운동","사후",2,2,3,2,2,8.7),
            ("2024004","최예린","1반","1차시 등가속도 운동","사후",3,4,4,3,4,4.2),
            ("2024005","정우진","2반","1차시 등가속도 운동","사후",1,2,2,1,2,12.3),
            ("2024006","한소희","1반","1차시 등가속도 운동","사후",5,4,5,4,5,2.1),
            ("2024007","오준서","2반","1차시 등가속도 운동","사후",3,3,3,3,3,5.5),
            ("2024008","윤채원","3반","1차시 등가속도 운동","사후",4,5,4,5,4,1.8),
            ("2024009","임도현","3반","1차시 등가속도 운동","사후",2,3,2,2,3,9.1),
            ("2024010","강지우","3반","1차시 등가속도 운동","사후",5,5,4,5,5,1.5),
        ]
        for s in samples:
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rt = float(np.random.uniform(40, 180))
            c.execute('''INSERT INTO rubrics
                         (student_id,name,section,session,eval_type,
                          theory,equipment,data_precision,error_analysis,
                          conclusion,timestamp,response_time,actual_error_rate)
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                      (s[0],s[1],s[2],s[3],s[4],s[5],s[6],s[7],s[8],s[9],ts,rt,s[10]))
    conn.commit()
    conn.close()

# ───────────────────────────────────────
# 무결성 검사
# ───────────────────────────────────────
def check_integrity(scores, response_time):
    issues = []
    if response_time < 30:
        issues.append("⚠️ 응답 시간이 너무 짧습니다 (무성의 응답 의심)")
    if np.var(scores) == 0:
        issues.append("⚠️ 모든 항목 점수가 동일합니다 (무성의 응답 의심)")
    if all(s == 5 for s in scores) or all(s == 1 for s in scores):
        issues.append("⚠️ 극단적 응답 패턴이 감지되었습니다")
    return issues

# ───────────────────────────────────────
# 레이더 차트 (사전/사후 비교)
# ───────────────────────────────────────
CATEGORIES = ['이론 이해','장비 조작','데이터 정밀도','오차 분석','공학적 결론']

def radar_comparison(pre, post):
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=pre + [pre[0]], theta=CATEGORIES + [CATEGORIES[0]],
        fill='toself', name='🔵 사전 점수',
        line_color='royalblue', fillcolor='rgba(65,105,225,0.2)'))
    fig.add_trace(go.Scatterpolar(
        r=post + [post[0]], theta=CATEGORIES + [CATEGORIES[0]],
        fill='toself', name='🟠 사후 점수',
        line_color='orange', fillcolor='rgba(255,165,0,0.2)'))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0,5])),
        height=420, title="📊 사전/사후 역량 비교 레이더 차트")
    return fig

# ───────────────────────────────────────
# 학생 뷰
# ───────────────────────────────────────
def student_view():
    st.header("🧑‍🎓 학생 자가평가")

    with st.sidebar:
        st.markdown("### 📝 학생 정보")
        student_id = st.text_input("학번", placeholder="예: 2024001")
        name       = st.text_input("이름", placeholder="예: 홍길동")
        section    = st.selectbox("분반", [f"{i}반" for i in range(1,8)])
        session    = st.selectbox("실험 차시", [
            "1차시 등가속도 운동","2차시 운동량 보존",
            "3차시 에너지 보존","4차시 단진동","5차시 전기회로"])
        eval_type  = st.radio("평가 시점", ["사전 점검","사후 점검"])

    if 'start_time' not in st.session_state:
        st.session_state.start_time = time.time()

    tab1, tab2 = st.tabs(["📋 평가 입력", "📊 내 결과 보기"])

    # ── 탭 1: 평가 입력 ──
    with tab1:
        st.subheader(f"🔬 {session} — {eval_type}")
        st.info("💡 솔직한 자가평가가 가장 도움이 됩니다!")

        with st.form("eval_form"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 루브릭 항목 (1~5점)")
                theory         = st.slider("1️⃣ 이론 이해도",       1, 5, 3)
                equipment      = st.slider("2️⃣ 장비 조작 능력",    1, 5, 3)
                data_precision = st.slider("3️⃣ 데이터 정밀도",     1, 5, 3)
                error_analysis = st.slider("4️⃣ 오차 분석 능력",    1, 5, 3)
                conclusion     = st.slider("5️⃣ 공학적 결론 도출",  1, 5, 3)

            with col2:
                st.markdown("#### 실시간 미리보기")
                scores_now = [theory, equipment, data_precision,
                              error_analysis, conclusion]
                fig_prev = go.Figure(go.Scatterpolar(
                    r=scores_now + [scores_now[0]],
                    theta=CATEGORIES + [CATEGORIES[0]],
                    fill='toself', line_color='royalblue',
                    fillcolor='rgba(65,105,225,0.3)'))
                fig_prev.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0,5])),
                    showlegend=False, height=320,
                    margin=dict(l=40,r=40,t=30,b=30))
                st.plotly_chart(fig_prev, use_container_width=True)

            submitted = st.form_submit_button("✅ 제출하기",
                                              use_container_width=True)

            if submitted:
                if not student_id or not name:
                    st.error("❌ 학번과 이름을 입력해주세요!")
                else:
                    rt     = time.time() - st.session_state.start_time
                    s_list = [theory, equipment, data_precision,
                              error_analysis, conclusion]
                    issues = check_integrity(s_list, rt)

                    # 가상 실험 오차율 (시뮬레이션)
                    actual_err = round(float(np.random.uniform(1, 15)), 2)

                    save_to_db({
                        'student_id': student_id, 'name': name,
                        'section': section, 'session': session,
                        'eval_type': eval_type,
                        'theory': theory, 'equipment': equipment,
                        'data_precision': data_precision,
                        'error_analysis': error_analysis,
                        'conclusion': conclusion,
                        'timestamp': datetime.datetime.now()
                                       .strftime("%Y-%m-%d %H:%M:%S"),
                        'response_time': rt,
                        'actual_error_rate': actual_err
                    })

                    for iss in issues:
                        st.warning(iss)

                    st.success(f"✅ 제출 완료!  응답 시간: {rt:.1f}초")
                    st.session_state.start_time  = time.time()
                    st.session_state.last_scores = s_list
                    st.session_state.student_id  = student_id

    # ── 탭 2: 결과 보기 ──
    with tab2:
        st.subheader("📊 나의 사전/사후 비교")

        if 'student_id' not in st.session_state:
            st.info("👆 먼저 평가를 제출해주세요! (데모 차트를 미리 표시합니다)")
            demo_pre  = [3, 2, 4, 2, 3]
            demo_post = [4, 4, 5, 3, 4]
            st.plotly_chart(radar_comparison(demo_pre, demo_post),
                            use_container_width=True)
            show_guide(demo_pre, demo_post)
        else:
            df  = load_from_db()
            my  = df[df['student_id'] == st.session_state.student_id]
            pre_rows  = my[my['eval_type'] == '사전 점검']
            post_rows = my[my['eval_type'] == '사후 점검']

            if pre_rows.empty or post_rows.empty:
                st.warning("사전/사후를 모두 제출하면 비교 차트가 나타납니다!")
                if not my.empty:
                    r = my.iloc[-1]
                    s = [r['theory'],r['equipment'],r['data_precision'],
                         r['error_analysis'],r['conclusion']]
                    st.plotly_chart(radar_comparison(s, s),
                                    use_container_width=True)
            else:
                r_pre  = pre_rows.iloc[-1]
                r_post = post_rows.iloc[-1]
                pre_s  = [r_pre['theory'],  r_pre['equipment'],
                           r_pre['data_precision'], r_pre['error_analysis'],
                           r_pre['conclusion']]
                post_s = [r_post['theory'], r_post['equipment'],
                           r_post['data_precision'],r_post['error_analysis'],
                           r_post['conclusion']]
                st.plotly_chart(radar_comparison(pre_s, post_s),
                                use_container_width=True)
                show_guide(pre_s, post_s)

def show_guide(pre, post):
    guides = {
        '이론 이해':     "📚 교재 Chapter 복습 및 개념 정리 필요",
        '장비 조작':     "🔧 실습실 추가 실습 시간 신청 권장",
        '데이터 정밀도': "📐 측정 반복 횟수 증가 및 유효숫자 복습",
        '오차 분석':     "📊 오차 전파 공식 학습 및 연습 문제 풀이",
        '공학적 결론':   "✍️ 보고서 작성 가이드라인 재검토 권장"
    }
    st.markdown("### 📌 보강 가이드")
    for i, cat in enumerate(CATEGORIES):
        diff = post[i] - pre[i]
        if   diff < 0: st.error(  f"⬇️ **{cat}** 하락 ({pre[i]}→{post[i]}점): {guides[cat]}")
        elif diff == 0: st.warning(f"➡️ **{cat}**: 변화 없음 — 꾸준한 복습 필요")
        else:           st.success(f"⬆️ **{cat}**: +{diff}점 향상! 👏")

# ───────────────────────────────────────
# 교수자 뷰
# ───────────────────────────────────────
def professor_view():
    st.header("👨‍🏫 교수자 관리자 대시보드")
    df = load_from_db()

    if df.empty:
        st.error("데이터가 없습니다.")
        return

    # 상단 지표 카드
    score_cols = ['theory','equipment','data_precision','error_analysis','conclusion']
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("👥 총 응답 수",       len(df))
    c2.metric("⏱️ 평균 응답 시간",  f"{df['response_time'].mean():.0f}초")
    c3.metric("⚠️ 무성의 응답 의심", len(df[df['response_time'] < 30]))
    c4.metric("📊 평균 종합 점수",
              f"{df[score_cols].mean().mean():.2f} / 5.0")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["🤖 군집 분석", "📍 메타인지 위상도", "📋 데이터 관리"])

    # ── 탭 1: K-Means 군집 ──
    with tab1:
        st.subheader("K-Means 군집 분석 (k=3)")

        X        = df[score_cols].values
        X_scaled = StandardScaler().fit_transform(X)
        km       = KMeans(n_clusters=3, random_state=42, n_init=10)
        df['cluster'] = km.fit_predict(X_scaled)

        means   = df.groupby('cluster')[score_cols].mean().mean(axis=1).sort_values()
        idx     = means.index.tolist()
        c_label = {idx[0]:"🔴 이론 보강 필요군",
                   idx[1]:"🟡 장비 실습 필요군",
                   idx[2]:"🟢 우수 자기주도군"}
        df['cluster_label'] = df['cluster'].map(c_label)

        col_a, col_b = st.columns([2,1])
        with col_a:
            fig_km = px.scatter(
                df, x='theory', y='error_analysis',
                color='cluster_label',
                hover_data=['name','section'],
                title="역량 군집 산점도 (이론 이해 vs 오차 분석)",
                color_discrete_map={
                    "🔴 이론 보강 필요군":"#ef4444",
                    "🟡 장비 실습 필요군":"#f59e0b",
                    "🟢 우수 자기주도군":"#10b981"},
                labels={'theory':'이론 이해도','error_analysis':'오차 분석'})
            fig_km.update_layout(height=420)
            st.plotly_chart(fig_km, use_container_width=True)

        with col_b:
            for lbl in ["🟢 우수 자기주도군","🟡 장비 실습 필요군","🔴 이론 보강 필요군"]:
                grp = df[df['cluster_label'] == lbl]
                with st.expander(f"{lbl} ({len(grp)}명)"):
                    st.dataframe(grp[['name','section']].reset_index(drop=True),
                                 use_container_width=True)

        # 금주 중점 지도 포인트
        st.markdown("---")
        avg_s   = df[score_cols].mean()
        weakest = avg_s.idxmin()
        w_names = {'theory':'이론 이해','equipment':'장비 조작',
                   'data_precision':'데이터 정밀도',
                   'error_analysis':'오차 분석','conclusion':'공학적 결론'}
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#667eea,#764ba2);
                    padding:20px;border-radius:15px;color:white;text-align:center;">
            <h3>🎯 금주 중점 지도 포인트</h3>
            <h2>⚠️ {w_names[weakest]}</h2>
            <p>분반 평균 <strong>{avg_s[weakest]:.2f} / 5.0</strong></p>
            <p>이 영역에 대한 집중 지도가 필요합니다!</p>
        </div>""", unsafe_allow_html=True)

    # ── 탭 2: 메타인지 위상도 ──
    with tab2:
        st.subheader("메타인지 Quadrant Plot")
        st.info("X: 오차 분석 자가점수  |  Y: 실제 실험 오차율 (↓낮을수록 우수)")

        mx = df['error_analysis'].mean()
        my = df['actual_error_rate'].mean()

        fig_q = go.Figure()
        # 사분면 배경
        for x0,x1,y0,y1,clr in [
            (0.5,mx,my,16,'rgba(255,80,80,0.07)'),
            (mx, 5.5,my,16,'rgba(255,200,0,0.07)'),
            (0.5,mx,0, my,'rgba(0,100,255,0.07)'),
            (mx, 5.5,0, my,'rgba(0,200,80,0.07)')]:
            fig_q.add_shape(type="rect",x0=x0,x1=x1,y0=y0,y1=y1,
                            fillcolor=clr,line=dict(width=0))

        fig_q.add_hline(y=my, line_dash="dash", line_color="gray",
                        annotation_text="평균 오차율")
        fig_q.add_vline(x=mx, line_dash="dash", line_color="gray",
                        annotation_text="평균 자가점수")

        fig_q.add_trace(go.Scatter(
            x=df['error_analysis'], y=df['actual_error_rate'],
            mode='markers+text', text=df['name'],
            textposition='top center',
            marker=dict(size=14, color=df['error_analysis'],
                        colorscale='RdYlGn', showscale=True,
                        colorbar=dict(title="자가평가")),
            hovertemplate='<b>%{text}</b><br>자가점수:%{x}<br>오차율:%{y:.1f}%<extra></extra>'))

        for tx,ty,txt in [
            (1.2,14,"⚠️ 과신형"),(4.5,1.5,"✅ 정확한 자기인식"),
            (1.2,1.5,"📚 겸손형"),(4.5,14,"🤔 과소평가형")]:
            fig_q.add_annotation(x=tx,y=ty,text=txt,showarrow=False,
                                 font=dict(size=11))

        fig_q.update_layout(
            title="메타인지 위상 산점도",
            xaxis_title="오차 분석 자가점수 (1~5)",
            yaxis_title="실제 실험 오차율 (%)",
            xaxis=dict(range=[0.5,5.5]),
            yaxis=dict(range=[0,16]), height=520)
        st.plotly_chart(fig_q, use_container_width=True)

    # ── 탭 3: 데이터 관리 ──
    with tab3:
        st.subheader("전체 데이터 관리")

        c1,c2 = st.columns(2)
        with c1:
            sec_f = st.multiselect("분반", df['section'].unique(),
                                   default=list(df['section'].unique()))
        with c2:
            typ_f = st.multiselect("평가 유형", df['eval_type'].unique(),
                                   default=list(df['eval_type'].unique()))

        fdf  = df[df['section'].isin(sec_f) & df['eval_type'].isin(typ_f)]
        dcol = ['student_id','name','section','session','eval_type',
                'theory','equipment','data_precision','error_analysis',
                'conclusion','timestamp']
        st.dataframe(fdf[dcol], use_container_width=True, height=300)

        b1,b2 = st.columns(2)
        with b1:
            csv_data = fdf[dcol].to_csv(index=False, encoding='utf-8-sig')
            st.download_button("📥 CSV 다운로드", csv_data,
                               file_name=f"rubric_{datetime.date.today()}.csv",
                               mime="text/csv", use_container_width=True)
        with b2:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine='openpyxl') as w:
                fdf[dcol].to_excel(w, index=False, sheet_name='루브릭데이터')
            st.download_button("📥 Excel 다운로드", buf.getvalue(),
                               file_name=f"rubric_{datetime.date.today()}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)

# ───────────────────────────────────────
# 메인
# ───────────────────────────────────────
def main():
    init_db()
    add_sample_data()

    st.title("🎓 실험 역량 자가진단 시스템")
    st.markdown("---")

    with st.sidebar:
        st.markdown("## 👤 뷰 선택")
        view = st.radio("", ["🧑‍🎓 학생 뷰", "👨‍🏫 교수자 뷰"])

    if view == "🧑‍🎓 학생 뷰":
        student_view()
    else:
        professor_view()

if __name__ == "__main__":
    main()
