/* -------------------------------------------------
   ① 포스터 이미지 목록 – 실제 이미지 URL 로 교체
------------------------------------------------- */
const posters = [
    "https://portal.jnu.ac.kr/cms/Upload/banner/59625b15-316a-4ff3-bb86-fe7010ee0c7d.jpg",
    "https://portal.jnu.ac.kr/cms/Upload/banner/1eb306da-fd62-4aff-ab55-b9c5a5cbb158.jpg",
    "https://portal.jnu.ac.kr/cms/Upload/banner/0b6ea7e1-8eea-4786-8b12-f36302200e77.jpg",
    "https://portal.jnu.ac.kr/cms/Upload/banner/0eae2ca8-b19c-488d-a240-3c2fcd5992e6.jpg"
];

/* -------------------------------------------------
   ② 요소 선택
------------------------------------------------- */
let curIdx = 0;
const posterEl = document.getElementById('hero-poster');
const dotEls   = document.querySelectorAll('.dot');

/* -------------------------------------------------
   ③ 슬라이드 전환 함수
------------------------------------------------- */
function setPoster(idx) {
    curIdx = idx;
    posterEl.style.backgroundImage = `url("${posters[curIdx]}")`;

    // dot 상태 업데이트
    dotEls.forEach((d, i) => d.classList.toggle('active', i === curIdx));
}

/* -------------------------------------------------
   ④ 자동 전환 (5초 간격)
------------------------------------------------- */
let autoTimer = setInterval(() => {
    const next = (curIdx + 1) % posters.length;
    setPoster(next);
}, 5000);

/* -------------------------------------------------
  ⑤ 점 클릭 시 즉시 전환 + 타이머 재시작
------------------------------------------------- */
dotEls.forEach(dot => {
    dot.addEventListener('click', () => {
        clearInterval(autoTimer);
        setPoster(parseInt(dot.dataset.index));
        // 클릭 후 바로 자동 전환 재개
        autoTimer = setInterval(() => {
            const next = (curIdx + 1) % posters.length;
            setPoster(next);
        }, 5000);
    });
});

/* 최초 로드 시 첫 번째 포스터 표시 */
setPoster(0);
