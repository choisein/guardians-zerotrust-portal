// ==================== 시간표 검색용 학과 데이터 ====================
const timetableDepartmentData = {
    "농업생명과학대학": [
        { value: "농경제학과", text: "농경제학과" },
        { value: "농학과", text: "농학과" },
        { value: "원예학과", text: "원예학과" },
        { value: "축산학과", text: "축산학과" },
        { value: "산림자원학과", text: "산림자원학과" }
    ],
    "공과대학": [
        { value: "기계공학과", text: "기계공학과" },
        { value: "전기공학과", text: "전기공학과" },
        { value: "토목공학과", text: "토목공학과" },
        { value: "건축학과", text: "건축학과" },
        { value: "화학공학과", text: "화학공학과" },
        { value: "환경공학과", text: "환경공학과" }
    ],
    "인문대학": [
        { value: "국어국문학과", text: "국어국문학과" },
        { value: "영어영문학과", text: "영어영문학과" },
        { value: "중어중문학과", text: "중어중문학과" },
        { value: "역사학과", text: "역사학과" },
        { value: "철학과", text: "철학과" }
    ],
    "사범대학": [
        { value: "교육학과", text: "교육학과" },
        { value: "수학교육과", text: "수학교육과" },
        { value: "과학교육과", text: "과학교육과" },
        { value: "국어교육과", text: "국어교육과" },
        { value: "영어교육과", text: "영어교육과" }
    ],
    "자연과학대학": [
        { value: "수학과", text: "수학과" },
        { value: "물리학과", text: "물리학과" },
        { value: "화학과", text: "화학과" },
        { value: "생물학과", text: "생물학과" },
        { value: "지구과학과", text: "지구과학과" }
    ]
};

// ==================== 시간표 검색용 학과 업데이트 ====================
function updateDepartmentsTimetable() {
    const collegeSelect = document.getElementById("search-college");
    const departmentSelect = document.getElementById("search-department");
    
    const selectedCollege = collegeSelect.value;
    
    // 학과 select 초기화
    departmentSelect.innerHTML = '<option value="">학과 선택</option>';
    
    if (selectedCollege && timetableDepartmentData[selectedCollege]) {
        const departments = timetableDepartmentData[selectedCollege];
        
        departments.forEach(dept => {
            const option = document.createElement("option");
            option.value = dept.value;
            option.textContent = dept.text;
            departmentSelect.appendChild(option);
        });
        
        // 첫 번째 학과 자동 선택 (옵션)
        // departmentSelect.value = departments[0].value;
    }
}

// ==================== 시간표 검색 ====================
function searchSchedule() {
    const year = document.getElementById("search-year").value;
    const semester = document.getElementById("search-semester").value;
    const location = document.getElementById("search-location").value;
    const college = document.getElementById("search-college").value;
    const department = document.getElementById("search-department").value;
    const courseType = document.getElementById("search-coursetype").value;
    const grade = document.getElementById("search-grade").value;
    
    // 검증: 필수 항목 확인
    if (!college) {
        alert("대학을 선택해주세요.");
        return;
    }
    if (!department) {
        alert("학과를 선택해주세요.");
        return;
    }
    
    console.log({
        year,
        semester,
        location,
        college,
        department,
        courseType,
        grade
    });
    
    alert(`검색 조건:\n년도: ${year}\n학기: ${semester}\n위치: ${location}\n대학: ${college}\n학과: ${department}\n교과과정: ${courseType}\n학년: ${grade}`);
}

// ==================== 시간표 검색 초기화 ====================
function resetSearch() {
    document.getElementById("search-year").value = "2026";
    document.getElementById("search-semester").value = "1";
    document.getElementById("search-location").value = "광주";
    document.getElementById("search-college").value = "공과대학";
    document.getElementById("search-coursetype").value = "전공";
    document.getElementById("search-grade").value = "4";
    
    // 학과 업데이트
    updateDepartmentsTimetable();
}

// ==================== 페이지 로드 시 초기화 ====================
document.addEventListener("DOMContentLoaded", function() {
    // 초기 학과 데이터 설정
    updateDepartmentsTimetable();
});
