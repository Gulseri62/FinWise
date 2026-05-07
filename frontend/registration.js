const API_BASE_URL = 'http://localhost:5000';

// apiRequest fonksiyonu: Tüm API çağrılarını merkezi olarak yönetir
async function apiRequest(endpoint, method, body, resultElementId) {
    const resultElement = document.getElementById(resultElementId);
    if (resultElement) { // Elementin varlığını kontrol et
        resultElement.textContent = 'İstek gönderiliyor...';
        resultElement.className = '';
    }

    const token = localStorage.getItem('authToken');

    const headers = {
        'Content-Type': 'application/json'
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(API_BASE_URL + endpoint, {
            method: method,
            headers: headers,
            body: body ? JSON.stringify(body) : null, // Body null ise gönderme
        });

        const responseData = await response.json().catch(() => ({})); // Her zaman JSON parse etmeye çalış, hata olursa boş obje

        if (!response.ok) {
            // Hata durumunda backend'den gelen mesajı veya genel bir hata mesajını kullan
            throw new Error(responseData.errorMessage || responseData.message || `HTTP error! status: ${response.status}`);
        }

        if (resultElement) {
            resultElement.textContent = response.status === 204 ? "İşlem başarılı (İçerik Yok)." : JSON.stringify(responseData, null, 2); // 204 için özel mesaj
            resultElement.classList.add('success');
        }
        return responseData;
    } catch (error) {
        if (resultElement) {
            resultElement.textContent = `Hata: ${error.message}`;
            resultElement.classList.add('error');
        }
        console.error('API Hatası:', error);
        throw error; // Hata durumunu çağrıldığı yere ilet
    }
}

// validateForm fonksiyonu: Form alanlarının doğruluğunu kontrol eder
function validateForm(form) {
    const errors = [];
    const formElements = form.elements;

    for (let element of formElements) {
        // 'submit' veya 'button' tipindeki elemanları atla
        if (element.type === 'submit' || element.type === 'button') {
            continue;
        }

        // Checkbox veya radio butonları için ayrı kontrol
        if (element.type === 'checkbox' || element.type === 'radio') {
            if (element.required && !form.querySelector(`input[name="${element.name}"]:checked`)) {
                const fieldName = element.labels?.[0]?.textContent || element.name || element.id;
                if (!errors.includes(`${fieldName} seçimi zorunludur.`)) { // Aynı hatayı tekrar eklememek için
                    errors.push(`${fieldName} seçimi zorunludur.`);
                }
            }
            continue; // Bu elemanı zaten kontrol ettik
        }

        if (element.required && !element.value.trim()) {
            const fieldName = element.labels?.[0]?.textContent || element.name || element.id; // Daha iyi bir fieldName alma
            errors.push(`${fieldName} alanı zorunludur.`);
        }
    }

    if (form.id === 'registerForm') {
        if (form.registerPassword.value !== form.confirmPassword.value) {
            errors.push("Şifreler eşleşmiyor.");
        }
    } else if (form.id === 'newPasswordForm') {
        if (form.newPassword.value !== form.confirmNewPassword.value) {
            errors.push("Yeni şifreler eşleşmiyor.");
        }
        if (!form.resetToken.value.trim()) errors.push("Doğrulama Kodu (Token) alanı zorunludur.");
        if (!form.resetEmailConfirm.value.trim()) errors.push("Email alanı zorunludur.");

        // newPasswordForm için de kullanıcı tipi seçimi kontrolü (eğer HTML'de varsa)
        const userTypeInputNewPass = form.querySelector('input[name="userTypeNewPass"]:checked');
        if (!userTypeInputNewPass) {
            errors.push("Lütfen kullanıcı tipini seçiniz (Kullanıcı veya Danışman).");
        }

    } else if (form.id === 'loginForm' || form.id === 'resetForm') {
        const userTypeInput = form.querySelector('input[name="userType"]:checked');
        if (!userTypeInput) {
            errors.push("Kullanıcı tipinizi seçiniz (Kullanıcı veya Danışman).");
        }
    }

    if (errors.length > 0) {
        alert(errors.join("\n"));
        return false;
    }
    return true;
}

// getUserType fonksiyonu: Frontend değerini backend'e uygun formata çevirir
function getUserType(frontendValue) {
    const typeMap = {
        'kullanici': 'user',
        'danisman': 'advisor',
        'user': 'user',
        'advisor': 'advisor'
    };
    // Küçük harfe çevirerek eşleştirme yap, eşleşme yoksa orijinal değeri döndür
    return typeMap[frontendValue.toLowerCase()] || frontendValue;
}

// Kayıt formu için event listener
document.getElementById('registerForm')?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.target;

    if (!validateForm(form)) return;


    const data = {
        email: form.registerEmail.value,
        password: form.registerPassword.value,
        firstName: form.firstName.value,
        lastName: form.lastName.value,
        confirmPassword: form.confirmPassword.value,
    };

    try {
        await apiRequest('/auth/signup', 'POST', data, 'signupResult');
        alert("Kayıt başarılı! Lütfen giriş yapınız.");
        document.querySelector(".form-register").style.display = "none";
        document.querySelector(".form-login").style.display = "block";
        document.querySelector(".wrapper").classList.remove("active");
    } catch (error) {
        // Hata apiRequest içinde gösteriliyor
    }
});

// Giriş formu için event listener
document.getElementById('loginForm')?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.target;

    if (!validateForm(form)) return;

    const userTypeInput = form.querySelector('input[name="userType"]:checked');
    const userTypeValue = getUserType(userTypeInput.value);

    const data = {
        email: form.loginEmail.value,
        password: form.loginPassword.value,
        userType: userTypeValue
    };

    try {
        const response = await apiRequest('/auth/signin', 'POST', data, 'signinResult');

        if (response && response.token) {
            localStorage.setItem('authToken', response.token);
            // Refresh token da backend'den dönüyorsa sakla
            if (response.refreshToken) {
                localStorage.setItem('refreshToken', response.refreshToken);
            }

            // Backend'den dönen response objesindeki alan isimlerine göre userRole, userFirstName ve userId'ı kaydet
            if (response.user_type) { // Tercih edilen isimlendirme
                localStorage.setItem('userRole', response.user_type);
            } else if (response.userType) { // Alternatif isimlendirme (şu anki backend'e göre)
                localStorage.setItem('userRole', response.userType);
            }

            if (response.first_name) { // Tercih edilen isimlendirme
                localStorage.setItem('userFirstName', response.first_name);
            } else if (response.firstName) { // Alternatif isimlendirme
                localStorage.setItem('userFirstName', response.firstName);
            }

            if (response.user_id) { // Tercih edilen isimlendirme
                localStorage.setItem('userId', response.user_id);
            } else if (response.userId) { // Alternatif isimlendirme
                localStorage.setItem('userId', response.userId);
            }

            // Kullanıcı tipine göre yönlendirme
            const storedUserRole = localStorage.getItem('userRole'); // localStorage'a kaydedilen rolü kullan
            if (storedUserRole === 'advisor') {
                window.location.href = 'advisor_giris.html'; // Danışman paneli sayfasına yönlendir
            } else {
                window.location.href = 'giris.html'; // Normal kullanıcı ana sayfasına yönlendir
            }
        }
    } catch (error) {
        // Hata apiRequest içinde gösteriliyor
    }
});

// ŞİFRE SIFIRLAMA AKIŞI
let newPassUserTypeFromURL = null; // Şifre sıfırlama linkinden gelen kullanıcı tipi için

// Sayfa yüklendiğinde URL'den şifre sıfırlama parametrelerini kontrol et
window.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const action = urlParams.get('action');
    const token = urlParams.get('token');
    const email = urlParams.get('email');
    const userTypeParam = urlParams.get('type');

    if (action === 'reset' && token && email && userTypeParam) {
        // Diğer formları gizle, Yeni Şifre formunu göster
        document.querySelector(".form-login").style.display = "none";
        document.querySelector(".form-register").style.display = "none";
        document.querySelector(".form-reset").style.display = "none";
        const newPasswordFormElement = document.querySelector(".form-new-password");
        if (newPasswordFormElement) {
            newPasswordFormElement.style.display = "block";
            document.querySelector(".wrapper")?.classList.add("active");

            // Değerleri Yeni Şifre formundaki inputlara ata
            const newPassForm = document.getElementById('newPasswordForm');
            if (newPassForm) {
                newPassForm.resetToken.value = token;
                newPassForm.resetEmailConfirm.value = email;
                newPassUserTypeFromURL = getUserType(userTypeParam);
                // HTML'e eklenmiş gizli bir input varsa userTypeNewPass'e de değeri set edebiliriz
                const hiddenUserTypeInput = newPassForm.querySelector('input[name="userTypeNewPass"]');
                if (hiddenUserTypeInput) {
                    hiddenUserTypeInput.value = newPassUserTypeFromURL;
                }
            }
        }
    }
});

// Şifremi Unuttum formu için event listener
document.getElementById('resetForm')?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.target;

    const emailValue = form.resetEmail.value.trim();
    if (!emailValue) {
        alert("Email alanı zorunludur.");
        return;
    }

    const userTypeInput = form.querySelector('input[name="userType"]:checked');
    if (!userTypeInput) {
        alert("Lütfen kullanıcı tipini seçiniz (Kullanıcı veya Danışman).");
        return;
    }
    const userTypeValue = getUserType(userTypeInput.value);

    const data = {
        email: emailValue,
        userType: userTypeValue
    };

    try {
        await apiRequest('/auth/forgot-password', 'POST', data, 'forgotPasswordResult');

        const forgotPasswordResultElement = document.getElementById('forgotPasswordResult');
        if (forgotPasswordResultElement) {
            forgotPasswordResultElement.textContent = "E-posta adresinize bir doğrulama kodu gönderildi. Lütfen kodu ve e-postanızı kullanarak yeni şifrenizi belirleyin.";
            forgotPasswordResultElement.className = 'success';
        }

        const newPassForm = document.getElementById('newPasswordForm');
        if (newPassForm && newPassForm.resetEmailConfirm) {
            newPassForm.resetEmailConfirm.value = emailValue;
        }

        document.querySelector(".form-reset").style.display = "none";
        document.querySelector(".form-new-password").style.display = "block";

    } catch (error) {
        // Hata apiRequest içinde gösteriliyor
    }
});

// Yeni Şifre Belirleme formu için event listener
document.getElementById('newPasswordForm')?.addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.target;

    if (!validateForm(form)) return; // validateForm çağrısı eklendi

    const newPasswordValue = form.newPassword.value;
    const confirmNewPasswordValue = form.confirmNewPassword.value;
    const emailValue = form.resetEmailConfirm.value.trim();
    const tokenValue = form.resetToken.value.trim();

    // Kullanıcı tipini formdaki radio butonlardan veya URL'den gelenden al
    let userTypeValueForNewPass = null;
    const userTypeInputNewPass = form.querySelector('input[name="userTypeNewPass"]:checked');
    if (userTypeInputNewPass) {
        userTypeValueForNewPass = getUserType(userTypeInputNewPass.value);
    } else if (newPassUserTypeFromURL) { // Eğer URL'den geliyorsa (tercihen gizli inputa atılmalıydı)
        userTypeValueForNewPass = newPassUserTypeFromURL;
    } else {
        alert("Kullanıcı tipi belirlenemedi. Lütfen tekrar deneyin.");
        return;
    }

    const data = {
        email: emailValue,
        resetToken: tokenValue,
        newPassword: newPasswordValue,
        confirmNewPassword: confirmNewPasswordValue,
        userType: userTypeValueForNewPass
    };

    try {
        await apiRequest('/auth/reset-password', 'POST', data, 'resetPasswordResult');
        const resetPasswordResultElement = document.getElementById('resetPasswordResult');
        if (resetPasswordResultElement) {
            resetPasswordResultElement.textContent = "Şifreniz başarıyla güncellendi. Lütfen yeni şifrenizle giriş yapınız.";
            resetPasswordResultElement.className = 'success';
        }

        document.querySelector(".form-new-password").style.display = "none";
        document.querySelector(".form-login").style.display = "block";
        document.querySelector(".wrapper")?.classList.remove("active");
        form.reset();

    } catch (error) {
        // Hata apiRequest içinde gösteriliyor
    }
});

// Form görünürlüğü geçişleri için genel fonksiyonlar (HTML'den çağrılabilir)
function showLoginForm() {
    document.querySelector(".form-login").style.display = "block";
    document.querySelector(".form-register").style.display = "none";
    document.querySelector(".form-reset").style.display = "none";
    document.querySelector(".form-new-password").style.display = "none";
    document.querySelector(".wrapper").classList.remove("active");
}

function showRegisterForm() {
    document.querySelector(".form-login").style.display = "none";
    document.querySelector(".form-register").style.display = "block";
    document.querySelector(".form-reset").style.display = "none";
    document.querySelector(".form-new-password").style.display = "none";
    document.querySelector(".wrapper").classList.add("active");
}

function showResetForm() {
    document.querySelector(".form-login").style.display = "none";
    document.querySelector(".form-register").style.display = "none";
    document.querySelector(".form-reset").style.display = "block";
    document.querySelector(".form-new-password").style.display = "none";
    document.querySelector(".wrapper").classList.remove("active"); // Reset formu da geniş form değilse
}

// Event Listener'lara ? (optional chaining) eklendi
// Çünkü bu script farklı HTML sayfalarında da kullanılıyor olabilir ve o sayfada ilgili element olmayabilir.
// Bu, "Cannot read properties of null (reading 'addEventListener')" hatasını önler.