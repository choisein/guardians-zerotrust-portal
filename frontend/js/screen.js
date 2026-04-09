// 페이지 로드 시 로그인 확인
window.addEventListener('load', () => {
    // 세션스토리지에서 사용자 정보 가져오기
    const userInfo = sessionStorage.getItem('user');
    
    if (!userInfo) {
        // 로그인 정보가 없으면 로그인 페이지로 이동
        alert('로그인이 필요합니다.');
        window.location.href = 'login.html';
        return;
    }
    
    // 사용자 정보 파싱
    const user = JSON.parse(userInfo);
    
    // 사용자 이름 표시
    document.getElementById('userName').textContent = user.name || user.id;
    
    // 웰컴 메시지
    document.getElementById('welcomeMessage').textContent = 
        `${user.name || user.id}님, 환영합니다!`;
});

// 로그아웃
function logout() {
    if (confirm('정말 로그아웃하시겠습니까?')) {
        // 세션스토리지 삭제
        sessionStorage.removeItem('user');
        
        // 로그인 페이지로 이동
        window.location.href = 'index.html';
    }
}

// 사이드바 메뉴 활성화
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        document.querySelectorAll('.nav-item').forEach(el => {
            el.classList.remove('active');
        });
        
        item.classList.add('active');
    });
});
