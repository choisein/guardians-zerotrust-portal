// ==================== 현재 페이지에 맞는 사이드바 메뉴 활성화 ====================
window.addEventListener('DOMContentLoaded', function() {
    const currentFile = window.location.pathname.split('/').pop() || 'basic-info.html';
    
    if (!currentFile) return;
    
    // 먼저 모든 menu-item에서 active 클래스 제거
    document.querySelectorAll('.menu-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 현재 페이지의 메뉴에만 active 추가
    document.querySelectorAll('.menu-item').forEach(item => {
        const link = item.querySelector('a');
        if (link) {
            let href = link.getAttribute('href');
            if (!href) return;
            
            // href에서 쿼리와 해시 제거 후 파일명만 추출
            href = href.split('?')[0].split('#')[0];
            
            // 현재 파일명과 링크 파일명 비교
            if (href === currentFile) {
                item.classList.add('active');
            }
        }
    });
});

// ==================== 사이드바 섹션 토글 ====================

function toggleSection(element) {
    // 1. 클릭된 타이틀(element)이 속한 가장 가까운 부모 컨테이너(.sidebar-section)를 찾음
    const section = element.closest('.sidebar-section');
    
    // 2. 그 부모 컨테이너 '내부'에서만 메뉴 리스트와 아이콘을 찾음 (중요!)
    const menuList = section.querySelector('.menu-list');
    const icon = section.querySelector('.fa-chevron-right');

    // 3. 현재 상태를 체크 (인라인 스타일이 없으면 계산된 스타일을 읽음)
    const isHidden = window.getComputedStyle(menuList).display === 'none';

    if (isHidden) {
        // 닫혀있으면 연다
        menuList.style.display = 'block';
        if (icon) icon.style.transform = 'rotate(90deg)';
    } else {
        // 열려있으면 닫는다
        menuList.style.display = 'none';
        if (icon) icon.style.transform = 'rotate(0deg)';
    }
}
