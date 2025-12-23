import json
import os
from datetime import datetime, date

DATA_FILE = "exams.json"

# 시험 일정들을 저장할 리스트
# 예: {"subject": "수학", "date": "2025-03-15", "desc": "중간고사", "note": "공식 꼭 외우기"}
exams = []

def load_exams_from_file():
    """프로그램 시작할 때 파일에서 시험 일정 불러오기"""
    global exams
    if not os.path.exists(DATA_FILE):
        exams = []
        return

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            exams = json.load(f)
    except Exception:
        exams = []

def save_exams_to_file():
    """시험 일정이 바뀔 때 파일에 저장하기"""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(exams, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f("저장 중 오류가 발생했습니다: {e}"))

def add_exam():
    print("\n[시험 일정 추가]")
    subject = input("과목 입력: ")
    date_str = input("날짜 입력(YYYY-MM-DD): ")
    desc = input("내용 입력(예: 중간고사, 단원평가 등): ")
    note = input("간단 메모(엔터만 치면 없음): ")

    exam = {
        "subject": subject,
        "date": date_str,
        "desc": desc,
        "note": note
    }
    exams.append(exam)
    save_exams_to_file()
    print("시험 일정이 추가되었습니다!\n")

def parse_exam_date(exam):
    """문자열 날짜를 datetime.date로 변환 (실패 시 None)"""
    try:
        return datetime.strptime(exam["date"], "%Y-%m-%d").date()
    except Exception:
        return None

def get_sorted_exams():
    """날짜 기준으로 정렬된 시험 일정 리스트 반환"""
    def sort_key(exam):
        d = parse_exam_date(exam)
        return d if d is not None else date.max

    return sorted(exams, key=sort_key)

def format_d_day(exam_date):
    """오늘 기준 D-day 문자열 반환"""
    if exam_date is None:
        return "날짜 형식 오류"

    today = date.today()
    delta = (exam_date - today).days  # 양수: 남은 날, 0: 오늘, 음수: 지난 시험[web:168][web:171]

    if delta > 0:
        return f"D-{delta}"
    elif delta == 0:
        return "D-day"
    else:
        return f"D+{abs(delta)}"

def show_exams():
    print("\n[시험 일정 목록 (날짜 순 + D-day)]")
    if not exams:
        print("등록된 시험 일정이 없습니다.\n")
        return

    sorted_exams = get_sorted_exams()

    for i, exam in enumerate(sorted_exams, start=1):
        exam_date = parse_exam_date(exam)
        d_day = format_d_day(exam_date)
        print(f"{i}) {exam['subject']} - {exam['date']} - {exam['desc']} - {d_day}")
        if exam.get("note"):
            print(f"    메모: {exam['note']}")
    print(f"(총 {len(sorted_exams)}개)\n")

def delete_exam():
    print("\n[시험 일정 삭제]")
    if not exams:
        print("삭제할 시험 일정이 없습니다.\n")
        return

    sorted_exams = get_sorted_exams()
    for i, exam in enumerate(sorted_exams, start=1):
        exam_date = parse_exam_date(exam)
        d_day = format_d_day(exam_date)
        print(f"{i}) {exam['subject']} - {exam['date']} - {exam['desc']} - {d_day}")
        if exam.get("note"):
            print(f"    메모: {exam['note']}")

    try:
        choice = int(input("삭제할 번호를 입력하세요 (취소: 0): "))
    except ValueError:
        print("숫자를 입력해 주세요.\n")
        return

    if choice == 0:
        print("삭제를 취소했습니다.\n")
        return

    if 1 <= choice <= len(sorted_exams):
        exam_to_delete = sorted_exams[choice - 1]
        exams.remove(exam_to_delete)
        save_exams_to_file()
        print("선택한 시험 일정이 삭제되었습니다.\n")
    else:
        print("잘못된 번호입니다.\n")

def main():
    load_exams_from_file()

    while True:
        print("========================")
        print("  시험 일정 관리 프로그램")
        print("========================")
        print("1. 시험 일정 추가")
        print("2. 시험 일정 보기 (날짜 순 + D-day)")
        print("3. 시험 일정 삭제")
        print("4. 종료")
        choice = input("메뉴 선택: ")

        if choice == "1":
            add_exam()
        elif choice == "2":
            show_exams()
        elif choice == "3":
            delete_exam()
        elif choice == "4":
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 입력입니다. 다시 선택하세요.\n")

if __name__ == "__main__":
    main()
