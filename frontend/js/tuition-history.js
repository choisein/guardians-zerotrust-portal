/**
 * ---------------------------------------------------------------
 * 1️⃣ 학번 추출 & 초기 설정
 * ---------------------------------------------------------------
 */
const urlParams = new URLSearchParams(window.location.search);
// 마찬가지로 저장소(localStorage)를 확인하도록 변경
const currentStudentId = urlParams.get('studentId') || localStorage.getItem('studentId') || '213804';

if (urlParams.get('studentId')) {
    localStorage.setItem('studentId', currentStudentId);
}

/* ------------------- 2️⃣ 임의 데이터 생성 함수 (Fallback) ------------------- */
function generateMockTuition(studentId, count = 4) {
    const semesters = ['2024-1', '2024-2', '2023-1', '2023-2', '2022-1', '2022-2'];
    const types = ['재학', '휴학', '전과', '신입'];
    const result = [];

    for (let i = 0; i < count; i++) {
        const yearSem = semesters[i % semesters.length]; // 순차적 학기 배정
        const type = types[Math.floor(Math.random() * types.length)];
        const targetAmt = 3620000; // 기준 등록금
        const paidAmt = targetAmt; // 전액 납부 가정
        
        result.push({
            student_id: studentId,
            year_sem: yearSem,
            type: type,
            target_amt: targetAmt,
            paid_amt: paidAmt,
            pay_date: '2024-03-02'
        });
    }
    return result.sort((a, b) => b.year_sem.localeCompare(a.year_sem));
}

/* ------------------- 3️⃣ 데이터 렌더링 함수 (UI 출력) ------------------- */
function renderTuitionTable(data) {
    const tbody = document.getElementById('tuitionBody');
    if (!tbody) return;

    if (!data || data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="empty-row">조회된 내역이 없습니다.</td></tr>`;
        return;
    }

    let rows = '';
    data.forEach(item => {
        rows += `
        <tr>
            <td>${item.year_sem}</td>
            <td>${item.type}</td>
            <td class="amount-text">${Number(item.target_amt).toLocaleString()}원</td>
            <td class="amount-text">${Number(item.paid_amt).toLocaleString()}원</td>
            <td>${item.pay_date}</td>
        </tr>`;
    });
    tbody.innerHTML = rows;
}

/* ------------------- 4️⃣ 통합 데이터 로드 로직 ------------------- */
document.addEventListener('DOMContentLoaded', async () => {
    console.log(`조회 시작: 학번 ${currentStudentId}`);

    try {
        /* [핵심] 실제 DB/API 연동 시도 부분 */
        // 나중에 실제 API 주소가 생기면 아래 주소를 수정하고 주석을 해제하세요.
        /*
        const response = await fetch(`https://api.your-univ.ac.kr/tuition?studentId=${currentStudentId}`);
        if (!response.ok) throw new Error('Network response was not ok');
        const realData = await response.json();
        renderTuitionTable(realData);
        console.log("실제 데이터 로드 완료");
        */

        // --- API 연결 전까지는 아래 코드가 작동합니다 ---
        console.warn("현재는 API가 없어 가짜 데이터를 사용합니다.");
        const mockData = generateMockTuition(currentStudentId, 4);
        renderTuitionTable(mockData);

    } catch (error) {
        console.error("데이터 로드 중 오류 발생:", error);
        // 에러 발생 시에도 사용자에게 가짜 데이터를 보여주어 화면이 깨지지 않게 함
        const fallbackData = generateMockTuition(currentStudentId, 4);
        renderTuitionTable(fallbackData);
    }
});