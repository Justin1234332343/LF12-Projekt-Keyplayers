const year = document.getElementById("year");
if (year) year.textContent = new Date().getFullYear();
const loginBtn = document.getElementById("loginBtn");

const demoLoginBtn = document.getElementById("demoLoginBtn");
const loginModal = document.getElementById("loginModal");
const loginForm = document.getElementById("loginForm");

function openLogin() { loginModal?.showModal(); }
loginBtn?.addEventListener("click", openLogin);
demoLoginBtn?.addEventListener("click", openLogin);

loginForm?.addEventListener("submit", (e) => {
  e.preventDefault();
  alert("Demo: Noch keine echte Anmeldung.\nHier binden wir später die Auth an.");
});
