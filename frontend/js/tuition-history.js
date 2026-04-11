// tuition-history.js - 등록금 납부 내역 API 연동

document.addEventListener('DOMContentLoaded', async () => {
    await loadTuitionHistory();
});

async function loadTuitionHistory() {
    try {
        // 1. 학생 프로필 로드 (헤더 이름/학번 표시)
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

        // 2. 등록금 납부 내역 로드
        const res = await fetch('/api/student/registrations', {
            credentials: 'include',
        });

        if (!res.ok) {
            showError('납부 내역을 불러오지 못했습니다.');
            return;
        }

        const data = await res.json();
        renderTuitionTable(data.registrations || []);

    } catch (error) {
        console.error('납부 내역 로딩 오류:', error);
        showError('서버 연결에 실패했습니다.');
    }
}

function renderTuitionTable(registrations) {
    const tbody = document.getElementById('tuitionBody');
    if (!tbody) return;

    if (registrations.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" class="empty-row">조회된 납부 내역이 없습니다.</td></tr>`;
        return;
    }

    const statusBadge = (status) => {
        const color = status === '완납' ? '#16a34a' : status === '미납' ? '#dc2626' : '#d97706';
        return `<span style="
            background:${color}20;
            color:${color};
            padding:2px 10px;
            border-radius:12px;
            font-size:0.85em;
            font-weight:600;
        ">${status}</span>`;
    };

    let rows = '';
    registrations.forEach(item => {
        rows += `
        <tr>
            <td>${item.reg_status}</td>
            <td>${statusBadge(item.status)}</td>
            <td class="amount-text">${Number(item.paid_amount).toLocaleString()}원</td>
            <td>${item.reg_date || '-'}</td>
        </tr>`;
    });

    tbody.innerHTML = rows;
}

function showError(msg) {
    const tbody = document.getElementById('tuitionBody');
    if (tbody) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:red;">${msg}</td></tr>`;
    }
}
