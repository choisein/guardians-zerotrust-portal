// 정보를 유지하며 페이지를 이동시키는 역할
document.addEventListener('DOMContentLoaded', () => {
    const studentId = "213804"; // 현재 로그인한 학번 고정

    document.querySelectorAll('.mega-menu a').forEach(link => {
        link.addEventListener('click', (e) => {
            const target = link.getAttribute('href');
            if (target && target !== '#') {
                e.preventDefault();
                // 모든 이동에 학번을 강제로 붙임
                location.href = `${target}?studentId=${studentId}`;
            }
        });
    });
});

/* navigation.js  – 페이지 로드 시 한 번 실행 */
document.addEventListener('DOMContentLoaded', () => {
    // 현재 URL에 포함된 studentId 파라미터를 읽어온다
    const urlParams = new URLSearchParams(window.location.search);
    const studentId = urlParams.get('studentId');   // 예: 213804

    // <h1> 안의 <a id="univLink"> 를 찾아 href 를 동적으로 만들기
    const univLink = document.getElementById('univLink');
    if (univLink && studentId) {
        // 기존 href (dashboard.html) 에 쿼리스트링을 붙인다
        const baseHref = univLink.getAttribute('href');   // "dashboard.html"
        const newHref  = `${baseHref}?studentId=${encodeURIComponent(studentId)}`;
        univLink.setAttribute('href', newHref);
    }

    // --------------------------------------------------------------
    // ★ 기존에 mega‑menu 등 다른 링크에서도 studentId 가 유지되도록
    //   기존 로직이 있으면 그대로 두고, 아래와 같이 추가해도 OK
    // --------------------------------------------------------------
    // 예시: 모든 .nav-link에 studentId 자동 추가
    document.querySelectorAll('.nav-link').forEach(link => {
        const dest = link.getAttribute('href');
        if (dest && studentId) {
            link.setAttribute('href', `${dest}?studentId=${encodeURIComponent(studentId)}`);
        }
    });
});