'use strict';

// ==================== 휴학신청 로직 ====================
function submitLeaveApplication() {
    const leaveType = document.getElementById('leave-type');
    const startSemester = document.getElementById('start-semester');
    const endSemester = document.getElementById('end-semester');
    const reason = document.getElementById('leave-reason');
    
    if (!leaveType || !startSemester || !endSemester || !reason) return;
    
    const leaveTypeVal = leaveType.value;
    const startSemesterVal = startSemester.value;
    const endSemesterVal = endSemester.value;
    const reasonVal = reason.value.trim();

    if (!leaveTypeVal) {
        alert("휴학구분을 선택해 주세요.");
        return;
    }

    if (!startSemesterVal) {
        alert("휴학시작학기를 선택해 주세요.");
        return;
    }

    if (!endSemesterVal) {
        alert("휴학종료학기를 선택해 주세요.");
        return;
    }

    if (!reasonVal) {
        alert("휴학사유를 입력해 주세요.");
        return;
    }

    if (confirm(`${leaveTypeVal}로 ${startSemesterVal}부터 ${endSemesterVal}까지 휴학을 신청하시겠습니까?`)) {
        alert('휴학신청이 정상적으로 접수되었습니다.');
    }
}

// ==================== 대학별 학과 데이터 ====================
const departmentData = {
    "농업생명과학대학": ["농업경제학과", "식물자원과학과", "응용생물학과", "바이오시스템공학부", "산림자원학과"],
    "공과대학": ["소프트웨어공학과", "컴퓨터공학과", "기계공학과", "전자공학과", "건축공학과", "환경공학과"],
    "인문대학": ["영어영문학과", "국어국문학과", "사학과", "철학과", "중어중문학과", "독어독문학과", "프랑스어문학과", "일어일문학과"],
    "사회과학대학": ["경영학과", "경제학부", "정치외교학과", "심리학과"],
    "AI융합대학": ["인공지능학과", "데이터사이언스학과", "지능형로봇학과"],
    "자연과학대학": ["수학과", "물리학과", "화학과", "생명과학과", "지질환경과학과", "통계학과"]
};

// ==================== 전과신청 - 학과 업데이트 ====================
function updateDepartments() {
    const collegeSelect = document.getElementById('college-select');
    const deptSelect = document.getElementById('dept-select');
    
    if (!collegeSelect || !deptSelect) return;
    
    const selectedCollege = collegeSelect.value;

    deptSelect.innerHTML = '<option value="">선택하세요</option>';

    if (selectedCollege && departmentData[selectedCollege]) {
        departmentData[selectedCollege].forEach(dept => {
            const option = document.createElement('option');
            option.value = dept;
            option.textContent = dept;
            deptSelect.appendChild(option);
        });
        deptSelect.disabled = false;
    } else {
        deptSelect.innerHTML = '<option value="">대학을 먼저 선택하세요</option>';
        deptSelect.disabled = true;
    }
}

// ==================== 전과신청 버튼 로직 ====================
function submitMajorChange() {
    const collegeSelect = document.getElementById('college-select');
    const deptSelect = document.getElementById('dept-select');
    
    if (!collegeSelect || !deptSelect) return;
    
    const college = collegeSelect.value;
    const dept = deptSelect.value;

    if (!college || !dept) {
        alert("원하시는 대학과 학과를 모두 선택해 주세요.");
        return;
    }

    if (confirm(`${college} ${dept}로 전과를 신청하시겠습니까?`)) {
        alert('전과신청이 정상적으로 접수되었습니다.');
    }
}

// ==================== 부/복수전공 신청 - 학과 업데이트 ====================
function addDepartments() {
    const collegeSelect = document.getElementById('college-select-double');
    const deptSelect = document.getElementById('dept-select-double');
    
    if (!collegeSelect || !deptSelect) return;
    
    const selectedCollege = collegeSelect.value;

    deptSelect.innerHTML = '<option value="">선택하세요</option>';

    if (selectedCollege && departmentData[selectedCollege]) {
        departmentData[selectedCollege].forEach(dept => {
            const option = document.createElement('option');
            option.value = dept;
            option.textContent = dept;
            deptSelect.appendChild(option);
        });
        deptSelect.disabled = false;
    } else {
        deptSelect.innerHTML = '<option value="">대학을 먼저 선택하세요</option>';
        deptSelect.disabled = true;
    }
}

// ==================== 부/복수전공 신청 버튼 로직 ====================
function submitDoubleMajor() {
    const typeSelect = document.querySelector('#double-major select:first-of-type');
    const collegeSelect = document.getElementById('college-select-double');
    const deptSelect = document.getElementById('dept-select-double');
    
    if (!typeSelect || !collegeSelect || !deptSelect) return;
    
    const type = typeSelect.value;
    const college = collegeSelect.value;
    const dept = deptSelect.value;

    if (!type) {
        alert("신청 구분을 선택해 주세요.");
        return;
    }

    if (!college || !dept) {
        alert("희망 단과대학과 학과를 모두 선택해 주세요.");
        return;
    }

    if (confirm(`${type}으로 ${college} ${dept}를 신청하시겠습니까?`)) {
        alert('부/복수전공 신청이 정상적으로 접수되었습니다.');
    }
}
