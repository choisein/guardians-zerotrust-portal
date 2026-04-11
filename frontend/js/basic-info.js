// basic-info.js - 학생 기본정보 API 연동

document.addEventListener('DOMContentLoaded', async () => {
    await loadProfile();
});

async function loadProfile() {
    try {
        const response = await fetch('/api/student/profile', {
            method: 'GET',
            credentials: 'include',
        });

        // 세션 만료 시 로그인 페이지로 이동
        if (response.status === 401) {
            window.location.href = '/';
            return;
        }

        if (!response.ok) {
            console.error('프로필 조회 실패:', response.status);
            return;
        }

        const data = await response.json();
        renderProfile(data);

    } catch (error) {
        console.error('프로필 로딩 오류:', error);
    }
}

function renderProfile(p) {
    // 학년 계산 (current_semester → 학년)
    const grade = Math.ceil(p.current_semester / 2);

    // ── 프로필 카드 ──
    // 이름
    const nameEl = document.querySelector('.profile-name');
    if (nameEl) nameEl.textContent = p.name;

    // 전공 + 학년
    const detailEl = document.querySelector('.profile-detail');
    if (detailEl) detailEl.textContent = `보안대학교 ${p.major || ''} | ${grade}학년`;

    // 재학 상태
    const statusEl = document.querySelector('.profile-status');
    if (statusEl) statusEl.textContent = p.status;

    // 연락처
    const contactEl = document.querySelector('.profile-contact');
    if (contactEl) contactEl.textContent = `휴대전화: ${p.phone || '-'}`;

    // 이메일
    const emailEl = document.querySelector('.profile-email');
    if (emailEl) emailEl.textContent = p.email || '-';

    // ── 헤더 사용자 정보 ──
    const headerUserEl = document.getElementById('header-user-info');
    if (headerUserEl) headerUserEl.textContent = `${p.name}(${p.student_id})`;

    // ── 폼 필드 ──
    // 이메일 입력
    const emailInput = document.querySelector('input[type="email"]');
    if (emailInput) emailInput.value = p.email || '';

    // 휴대전화 입력
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    if (phoneInputs[0]) phoneInputs[0].value = p.phone || '';
}
