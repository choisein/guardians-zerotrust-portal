// dashboard.js - 대시보드 프로필 API 연동

document.addEventListener('DOMContentLoaded', async () => {
    await loadDashboardProfile();
});

async function loadDashboardProfile() {
    try {
        const res = await fetch('/api/student/profile', {
            credentials: 'include',
        });

        // 세션 만료 시 로그인 페이지로 이동
        if (res.status === 401) {
            window.location.href = '/';
            return;
        }

        if (!res.ok) {
            console.error('프로필 조회 실패:', res.status);
            return;
        }

        const p = await res.json();
        renderDashboard(p);

    } catch (error) {
        console.error('대시보드 로딩 오류:', error);
    }
}

function renderDashboard(p) {
    const grade = Math.ceil(p.current_semester / 2);

    // 헤더 + 프로필 카드 이름 (두 곳 동시 업데이트)
    document.querySelectorAll('#name').forEach(el => {
        el.textContent = p.name;
    });

    // 헤더 + 프로필 카드 학번 (두 곳 동시 업데이트)
    document.querySelectorAll('#student_id').forEach(el => {
        // 헤더는 "(학번: 123456)" 형식, 프로필 카드는 숫자만
        if (el.classList.contains('ml-2')) {
            el.textContent = `(학번: ${p.student_id})`;
        } else {
            el.textContent = p.student_id;
        }
    });

    // 학년
    const semesterEl = document.getElementById('current_semester');
    if (semesterEl) semesterEl.textContent = `${grade}학년`;

    // 재학 상태
    const statusEl = document.getElementById('status');
    if (statusEl) statusEl.textContent = p.status;

    // 전공
    const majorEl = document.getElementById('major');
    if (majorEl) majorEl.textContent = p.major || '-';
}
