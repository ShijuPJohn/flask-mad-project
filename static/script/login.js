const email_field = document.getElementById("email")
const password_field = document.getElementById("password")
const login_btn = document.getElementById("login-btn")
const snackbar = document.getElementById("snackbar")
login_btn.addEventListener("click", loginHandler)

function loginHandler(e) {
    e.preventDefault()
    if (!emailValidate(email_field.value) || !passwordValidate(password_field.value)) {
        snackbar.innerText = "Invalid email or password. Password must be at least 8 characters long"
    } else {
        snackbar.innerText = "Email and Password valid"
    }
    setTimeout(() => {
        snackbar.innerText = ""
    }, 2000)
}

function emailValidate(email) {
    let valid = true
    if (email.length <= 5) {
        valid = false
    }
    if (!email.includes("@") || !email.includes(".")) {
        valid = false
    }
    return valid
}

function passwordValidate(password) {
    let valid = true
    if (password.length <= 7) {
        valid = false
    }
    return valid
}