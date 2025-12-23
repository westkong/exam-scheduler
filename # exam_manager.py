import streamlit as st
import json
import os
from datetime import datetime, date

DATA_FILE = "exams.json"

# 데이터 로드/저장 함수
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(exams):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(exams, f, ensure_ascii=False, indent=2)

# 페이지 설정
st.set_page_config(page_title="시험 일정 관리", page_icon="📅")
st.title("📅 시험 일정 관리 프로그램")

# 세션 상태 초기화 (데이터 유지)
if 'exams' not in st.session_state:
    st.session_state.exams = load_data()

# 사이드바: 시험 추가
with st.sidebar:
    st.header("➕ 새 일정 추가")
    with st.form("add_form", clear_on_submit=True):
        subject = st.text_input("과목")
        exam_date = st.date_input("시험 날짜", min_value=date.today())
        desc = st.text_input("내용 (예: 중간고사)")
        note = st.text_area("메모")
        submit = st.form_submit_button("추가하기")

        if submit and subject:
            new_exam = {
                "subject": subject,
                "date": exam_date.strftime("%Y-%m-%d"),
                "desc": desc,
                "note": note
            }
            st.session_state.exams.append(new_exam)
            save_data(st.session_state.exams)
            st.success(f"{subject} 일정이 추가되었습니다!")

# 메인 화면: 일정 목록
st.subheader("📋 전체 시험 일정")

if not st.session_state.exams:
    st.info("등록된 시험 일정이 없습니다.")
else:
    # 날짜 정렬
    sorted_exams = sorted(st.session_state.exams, 
                          key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d").date())

    for idx, exam in enumerate(sorted_exams):
        exam_date_obj = datetime.strptime(exam['date'], "%Y-%m-%d").date()
        today = date.today()
        diff = (exam_date_obj - today).days
        
        # D-day 계산 및 색상 지정
        if diff > 0: d_text = f"D-{diff}"
        elif diff == 0: d_text = "D-day"; d_text = f":red[{d_text}]"
        else: d_text = f"D+{abs(diff)}"

        with st.expander(f"{d_text} | {exam['subject']} ({exam['date']})"):
            st.write(f"**내용:** {exam['desc']}")
            st.write(f"**메모:** {exam['note']}")
            if st.button(f"삭제", key=f"del_{idx}"):
                st.session_state.exams.remove(exam)
                save_data(st.session_state.exams)
                st.rerun()
