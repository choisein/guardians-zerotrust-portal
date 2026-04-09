// 1. HOT NEWS 데이터 배열
const newsData = [
    "2026학년도 1학기 행정업무보조 국가근로장학생 희망근로기관 신청 안내",
    "2026년도 1학기 수강취소 안내 (취소기간 준수)",
    "2026년 와플대학교 라오스 단기 봉사단 모집 공고",
    "2026년 어학연수(교환학생) 추가모집 및 설명회 안내"
];

let currentNewsIndex = 0;
const newsTextEl = document.getElementById('hot-news-text');
const newsContainerEl = document.getElementById('hot-news-container');

// 2. 뉴스 변경 함수
function updateNews() {
    // 애니메이션 효과를 위해 클래스 잠시 제거 후 추가 (CSS 애니메이션 적용 시)
    newsTextEl.style.opacity = 0;
    newsTextEl.style.transform = "translateY(10px)";

    setTimeout(() => {
        // 다음 뉴스로 인덱스 변경
        currentNewsIndex = (currentNewsIndex + 1) % newsData.length;
        
        // 텍스트 교체
        newsTextEl.innerText = newsData[currentNewsIndex];
        
        // 다시 나타나게 설정
        newsTextEl.style.opacity = 1;
        newsTextEl.style.transform = "translateY(0)";
    }, 400); // 0.4초 후 텍스트 교체
}

// 3. 3초마다 뉴스 자동 전환
setInterval(updateNews, 3000);

// 초기 스타일 설정 (부드러운 전환을 위해 JS에서 직접 주거나 CSS에 추가)
newsTextEl.style.transition = "all 0.5s ease-in-out";
newsTextEl.style.display = "block";
