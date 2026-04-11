// course-registration.js -- 학생 수강내역 API 연동

document.addEventListener('DOMContentLoaded', async () => {
    await loadHeaderUserInfo();   // 헤더 사용자 정보
    await loadCourses();          // 수강 내역 테이블
});


// ─────────────────────────────────────────────
// 1. 헤더 사용자 정보 (프로필 API에서 가져옴)
// ─────────────────────────────────────────────
async function loadHeaderUserInfo() {
    const headerUserEl = document.getElementById('header-user-info');
    if (!headerUserEl) return;

    try {
        const res = await fetch('/api/student/profile', {
            credentials: 'include',
        });

        if (!res.ok) {
            if (res.status === 401) {
                window.location.href = '/';
                return;
            }
            headerUserEl.textContent = '사용자 정보 없음';
            return;
        }

        const profile = await res.json();
        headerUserEl.textContent = `${profile.name}(${profile.student_id})`;

    } catch (err) {
        console.error('헤더 사용자 정보 로딩 실패:', err);
        headerUserEl.textContent = '사용자 정보 없음';
    }
}


// ─────────────────────────────────────────────
// 2. 수강 내역 로드
// ─────────────────────────────────────────────
async function loadCourses() {
    const tbody = document.getElementById("course-list-body");

    try {
        const response = await fetch("/api/student/enrollments", {
            credentials: "include",
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => null);
            const msg = errData?.error || `서버 오류 (${response.status})`;
            tbody.innerHTML = `<tr><td colspan="3" style="color:red;">${msg}</td></tr>`;
            return;
        }

        const data = await response.json();
        const courses = data.enrollments;

        if (!Array.isArray(courses) || courses.length === 0) {
            tbody.innerHTML = `<tr><td colspan="3">수강 중인 과목이 없습니다.</td></tr>`;
            return;
        }

        renderCourses(courses);

    } catch (err) {
        console.error("수강 내역 로딩 실패:", err);
        tbody.innerHTML = `<tr><td colspan="3" style="color:red;">데이터를 불러올 수 없습니다.</td></tr>`;
    }
}


// ─────────────────────────────────────────────
// 3. 테이블 렌더링
// ─────────────────────────────────────────────
function renderCourses(courses) {
    const tbody = document.getElementById("course-list-body");
    tbody.innerHTML = "";

    courses.forEach(course => {
        const tr = document.createElement("tr");

        const tdName = document.createElement("td");
        tdName.textContent = course.course_name;

        const tdProf = document.createElement("td");
        tdProf.textContent = course.professor;

        const tdGrade = document.createElement("td");
        tdGrade.textContent = course.grade ?? "수강중";

        tr.appendChild(tdName);
        tr.appendChild(tdProf);
        tr.appendChild(tdGrade);
        tbody.appendChild(tr);
    });
}
