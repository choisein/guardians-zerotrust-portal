// semester-grades.js - 학기별 성적 API 연동

document.addEventListener('DOMContentLoaded', async () => {
    await loadGrades();
});

async function loadGrades() {
    try {
        const profileRes = await fetch('/api/student/profile', {
            credentials: 'include',
        });

        if (profileRes.status === 401) {
            window.location.href = '/';
            return;
        }

        if (profileRes.ok) {
            const profile = await profileRes.json();
            const nameEl = document.getElementById('name');
            const studentIdEl = document.getElementById('student_id');
            if (nameEl) nameEl.textContent = profile.name;
            if (studentIdEl) studentIdEl.textContent = `(학번: ${profile.student_id})`;
        }

        const gradesRes = await fetch('/api/student/grades', {
            credentials: 'include',
        });

        if (!gradesRes.ok) {
            showError('성적 데이터를 불러오지 못했습니다.');
            return;
        }

        const data = await gradesRes.json();
        renderGrades(data);

    } catch (error) {
        console.error('성적 로딩 오류:', error);
        showError('서버 연결에 실패했습니다.');
    }
}

function renderGrades(data) {
    const tbody = document.getElementById('grade-list');
    const avgGradeEl = document.getElementById('avg_grade');

    if (!tbody) return;

    const semesters = data.semesters || {};
    const semesterKeys = Object.keys(semesters).sort((a, b) => Number(a) - Number(b));

    if (semesterKeys.length === 0) {
        tbody.innerHTML = '<tr><td colspan="2" style="text-align:center;">성적 데이터가 없습니다.</td></tr>';
        return;
    }

    let html = '';

    semesterKeys.forEach(sem => {
        const semData = semesters[sem];
        const courses = semData.courses || [];
        const semGrade = semData.semester_grade ? Number(semData.semester_grade).toFixed(2) : '-';

        // 학기 헤더 행 ✅ colspan="2"
        html += `
            <tr style="background:#f0f4ff;">
                <td colspan="2" style="font-weight:bold; padding-left:12px;">
                    ${sem}학기
                </td>
            </tr>
        `;

        // 과목별 행 ✅ td 2개만 (과목명 + 평점)
        courses.forEach(course => {
            const grade = course.course_grade !== null ? Number(course.course_grade).toFixed(1) : '-';
            html += `
                <tr>
                    <td style="text-align:left; padding-left:20px;">${course.course_name}</td>
                    <td>${grade}</td>
                </tr>
            `;
        });

        // 학기 평균 행 ✅ td 2개만
        html += `
            <tr style="background:#fafafa; border-top: 1px solid #ddd;">
                <td style="text-align:right; padding-right:20px; color:#555; font-size:0.9em;">
                    ${sem}학기 평균 평점
                </td>
                <td style="font-weight:bold; color:#2563eb;">${semGrade}</td>
            </tr>
        `;
    });

    tbody.innerHTML = html;

    if (avgGradeEl) {
        avgGradeEl.textContent = data.avg_grade ? Number(data.avg_grade).toFixed(2) : '-';
    }
}

function showError(msg) {
    const tbody = document.getElementById('grade-list');
    if (tbody) {
        tbody.innerHTML = `<tr><td colspan="2" style="text-align:center; color:red;">${msg}</td></tr>`;
    }
}
