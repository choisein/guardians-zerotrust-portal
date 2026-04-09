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

// 로그인 함수
async function handleLogin(userId, userPassword, rememberMe) {
    try {
        const loginBtn = document.querySelector('.login-button');
        loginBtn.disabled = true;
        loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>로그인 중...</span>';
        
        // 데이터베이스 연동 API 호출
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                userId: userId,
                password: userPassword,
                rememberMe: rememberMe
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showSuccess('로그인 성공! 잠시만 기다려주세요...');
            
            // 토큰 저장 (필요시)
            if (data.token) {
                localStorage.setItem('authToken', data.token);
            }
            
            setTimeout(() => {
                window.location.href = data.redirectUrl || '/dashboard';
            }, 2000);
        } else {
            showError(data.message || '로그인에 실패했습니다.');
            loginBtn.disabled = false;
            loginBtn.innerHTML = '<span>로그인</span><i class="fas fa-arrow-right"></i>';
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('서버와의 연결에 실패했습니다.');
        const loginBtn = document.querySelector('.login-button');
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

// 로그인 정보 저장
window.addEventListener('beforeunload', () => {
    const userId = document.getElementById('userId').value;
    const rememberMe = document.getElementById('rememberMe').checked;
    
    if (rememberMe) {
        localStorage.setItem('savedUserId', userId);
        localStorage.setItem('rememberMe', 'true');
    } else {
        localStorage.removeItem('savedUserId');
        localStorage.removeItem('rememberMe');
    }
});

// 저장된 정보 불러오기
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
// 로그인 함수
async function handleLogin(userId, userPassword, rememberMe) {
    try {
        const loginBtn = document.querySelector('.login-button');
        loginBtn.disabled = true;
        loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>로그인 중...</span>';
        
        // 테스트용 더미 데이터 (실제로는 서버의 API와 연동)
        const dummyUserId = 'admin';
        const dummyPassword = '123456';
        
        // 아이디와 비밀번호 검증
        if (userId === dummyUserId && userPassword === dummyPassword) {
            showSuccess('로그인 성공! 잠시만 기다려주세요...');
            
            // 사용자 정보를 세션스토리지에 저장
            sessionStorage.setItem('user', JSON.stringify({
                id: userId,
                name: '한국대학교 학생',
                email: userId + '@hankuk.ac.kr'
            }));
            
            // 로그인 정보 저장 (rememberMe 옵션)
            if (rememberMe) {
                localStorage.setItem('savedUserId', userId);
                localStorage.setItem('rememberMe', 'true');
            } else {
                localStorage.removeItem('savedUserId');
                localStorage.removeItem('rememberMe');
            }
            
            // 2초 후 screen.html로 이동 ⭐
            setTimeout(() => {
                window.location.href = 'screen.html';
            }, 2000);
        } else {
            showError('아이디 또는 비밀번호가 일치하지 않습니다.');
            loginBtn.disabled = false;
            loginBtn.innerHTML = '<span>로그인</span><i class="fas fa-arrow-right"></i>';
        }
        
    } catch (error) {
        console.error('Login error:', error);
        showError('로그인 중 오류가 발생했습니다.');
        const loginBtn = document.querySelector('.login-button');
        loginBtn.disabled = false;
        loginBtn.innerHTML = '<span>로그인</span><i class="fas fa-arrow-right"></i>';
    }
}
