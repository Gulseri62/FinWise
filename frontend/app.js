const wrapper = document.querySelector('.wrapper');
const loginlink = document.querySelector('.login-link');
const registerlink = document.querySelector('.register-link');


const buttons = document.querySelectorAll('.student-teacher button');

const menuIcon = document.getElementById('menu-icon');
const navLinks = document.getElementById('nav-links');

menuIcon.addEventListener('click', () => {
    navLinks.classList.toggle('active');
});

registerlink.addEventListener('click', () => {
    wrapper.classList.add('active');
});

loginlink.addEventListener('click', () => {
    wrapper.classList.remove('active');
});


buttons.forEach(button => {
    button.addEventListener('click', () => {
        // Önce hepsinden 'active' classını kaldır
        buttons.forEach(btn => btn.classList.remove('active'));

        // Sadece tıklanan butona 'active' classı ekle
        button.classList.add('active');
    });
});