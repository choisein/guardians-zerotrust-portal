// 비밀번호 보기/숨기기 토글
const togglePasswordBtn = document.getElementById('togglePassword');
const passwordInput = document.getElementById('userPassword');

togglePasswordBtn.addEventListener('click', () => {
    const type = passwordInput.type === 'password' ? 'text' : 'password';
    passwordInput.type = type;
    
    const icon = togglePasswordBtn.querySelector('i');
    icon.classList.toggle('fa-eye');
    icon.classList.toggle('fa-eye-slash');
});

// 로그인 폼 제출
const loginForm = document.getElementById('loginForm');
const errorMessage = document.getElementById('errorMessage');
const successMessage = document.getElementById('successMessage');

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const userId = document.getElementById('userId').value.trim();
    const userPassword = document.getElementById('userPassword').value.trim();
    const rememberMe = document.getElementById('rememberMe').checked;
    
    // 유효성 검사
    if (!userId || !userPassword) {
        showError('아이디와 비밀번호를 모두 입력해주세요.');
        return;
    }
    
    if (userId.length < 4) {
        showError('아이디는 4자 이상이어야 합니다.');
        return;
    }
    
    if (userPassword.length < 6) {
        showError('비밀번호는 6자 이상이어야 합니다.');
        return;
    }
    
    await handleLogin(userId, userPassword, rememberMe);
});

// 로그인 함수 (API 연동)
async function handleLogin(userId, userPassword, rememberMe) {
    const loginBtn = document.querySelector('.login-button');
    try {
        loginBtn.disabled = true;
        loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>로그인 중...</span>';

        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ user_id: userId, password: userPassword }),
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess('로그인 성공! 잠시만 기다려주세요...');

            // 사용자 정보를 세션스토리지에 저장
            sessionStorage.setItem('user', JSON.stringify(data.user));

            // 로그인 정보 저장 (rememberMe 옵션)
            if (rememberMe) {
                localStorage.setItem('savedUserId', userId);
                localStorage.setItem('rememberMe', 'true');
            } else {
                localStorage.removeItem('savedUserId');
                localStorage.removeItem('rememberMe');
            }

            // 2초 후 dashboard.html로 이동
            setTimeout(() => {
                window.location.href = '/templates/dashboard.html';
            }, 2000);
        } else {
            showError(data.error || '아이디 또는 비밀번호가 일치하지 않습니다.');
            loginBtn.disabled = false;
            loginBtn.innerHTML = '<span>로그인</span><i class="fas fa-arrow-right"></i>';
        }

    } catch (error) {
        console.error('Login error:', error);
        showError('서버 연결에 실패했습니다. 잠시 후 다시 시도해주세요.');
        loginBtn.disabled = false;
        loginBtn.innerHTML = '<span>로그인</span><i class="fas fa-arrow-right"></i>';
    }
}

// 에러 메시지 표시
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    successMessage.style.display = 'none';
    
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 5000);
}

// 성공 메시지 표시
function showSuccess(message) {
    successMessage.textContent = message;
    successMessage.style.display = 'block';
    errorMessage.style.display = 'none';
}

// 저장된 정보 불러오기 (페이지 로드 시)
window.addEventListener('load', () => {
    const savedUserId = localStorage.getItem('savedUserId');
    const rememberMe = localStorage.getItem('rememberMe');
    
    if (savedUserId && rememberMe === 'true') {
        document.getElementById('userId').value = savedUserId;
        document.getElementById('rememberMe').checked = true;
        document.getElementById('userPassword').focus();
    }
});

// 엔터 키 처리
document.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && e.target.classList.contains('login-input')) {
        loginForm.dispatchEvent(new Event('submit'));
    }
});
