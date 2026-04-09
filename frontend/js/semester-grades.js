document.addEventListener('DOMContentLoaded', () => {
    // 1. 학번 가져오기 (URL 파라미터 혹은 기본값)
    const urlParams = new URLSearchParams(window.location.search);
    // URL -> localStorage -> 기본값 순서로 학번을 찾습니다.
    const studentId = urlParams.get('studentId') || localStorage.getItem('studentId') || '213804';

    // 만약 URL로 들어왔다면 나중을 위해 localStorage에 업데이트해줍니다.
    if (urlParams.get('studentId')) {
        localStorage.setItem('studentId', studentId);
    }

    // 2. 화면 요소 잡기
    const gradeListContainer = document.getElementById('grade-list');
    const avgGradeElement = document.getElementById('avg_grade');

    // 3. 임시 데이터 (실제 DB 연결 전까지 보여줄 데이터)
    const mockGrades = [
        { semester: "2024-1", course_name: "네트워크 보안", course_grade: "A+", semester_grade: "4.5" },
        { semester: "2024-1", course_name: "운영체제론", course_grade: "A0", semester_grade: "4.0" },
        { semester: "2024-1", course_name: "알고리즘 분석", course_grade: "B+", semester_grade: "3.5" },
        { semester: "2024-1", course_name: "데이터베이스 응용", course_grade: "A+", semester_grade: "4.5" }
    ];

    // [중요] 실제 데이터 렌더링 함수
    function renderGrades(data) {
        if (!gradeListContainer) return;

        let htmlContent = '';
        let totalSum = 0;

        data.forEach(item => {
            htmlContent += `
                <tr>
                    <td>${item.semester}</td>
                    <td style="text-align: left; padding-left: 20px;">${item.course_name}</td>
                    <td>${item.course_grade}</td>
                    <td style="font-weight:bold;">${item.semester_grade}</td>
                </tr>
            `;
            totalSum += parseFloat(item.semester_grade);
        });

        gradeListContainer.innerHTML = htmlContent;
        
        // 평균 계산 후 출력
        const average = (totalSum / data.length).toFixed(2);
        avgGradeElement.innerText = average;
    }

    /* 
       4. 데이터 연동 로직
       지금은 DB가 없으므로 바로 renderGrades(mockGrades)를 실행합니다.
       나중에 DB가 생기면 아래 주석 처리된 fetch 부분을 사용하세요.
    */

    // --- 실제 DB 연결 시 사용할 코드 (주석 해제 후 사용) ---
    /*
    fetch(`https://api.university.com/grades?studentId=${studentId}`)
        .then(res => res.json())
        .then(realData => {
            renderGrades(realData);
        })
        .catch(err => {
            console.error("데이터 로드 실패, 목데이터를 표시합니다.");
            renderGrades(mockGrades); 
        });
    */

    // 
    renderGrades(mockGrades);
});