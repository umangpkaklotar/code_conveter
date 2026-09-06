const $ = (id) => document.getElementById(id);
const token = () => localStorage.getItem("token");
const headers = () => ({ "Content-Type": "application/json", ...(token() ? { Authorization: `Bearer ${token()}` } : {}) });

async function responseData(response) {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "Something went wrong.");
    return data;
}

function logout() {
    localStorage.removeItem("token");
    window.location.href = "/";
}

const logoutButton = $("logoutButton");
if (logoutButton) logoutButton.addEventListener("click", logout);

async function loadUser() {
    if (!token()) {
        window.location.href = "/";
        return null;
    }
    const user = await responseData(await fetch("/profile", { headers: headers() }));
    const name = $("headerUserName");
    if (name) name.textContent = user.name || "Account";
    const profileName = $("profileName");
    const profileEmail = $("profileEmail");
    if (profileName) profileName.textContent = user.name;
    if (profileEmail) profileEmail.textContent = user.email;
    return user;
}

function initAuthPage() {
    if (token()) {
        window.location.href = "/converter";
        return;
    }
    const loginForm = $("loginForm");
    const registerForm = $("registerForm");
    const message = $("authMessage");
    const showMessage = (text, error = true) => { message.textContent = text; message.className = error ? "error-message" : "success-message"; };
    const showLogin = (text = "") => { loginForm.classList.remove("hidden"); registerForm.classList.add("hidden"); $("loginTab").classList.add("active"); $("registerTab").classList.remove("active"); showMessage(text, false); };
    const showRegister = () => { registerForm.classList.remove("hidden"); loginForm.classList.add("hidden"); $("registerTab").classList.add("active"); $("loginTab").classList.remove("active"); showMessage(""); };
    $("showRegister").addEventListener("click", showRegister);
    $("registerTab").addEventListener("click", showRegister);
    $("showLogin").addEventListener("click", () => showLogin());
    $("loginTab").addEventListener("click", () => showLogin());
    $("registerButton").addEventListener("click", async () => {
        const name = $("registerName").value.trim();
        const email = $("registerEmail").value.trim();
        const password = $("registerPassword").value;
        if (!name || !email || !password) return showMessage("Please complete all fields.");
        if (password.length < 6) return showMessage("Password must be at least 6 characters.");
        const button = $("registerButton"); button.disabled = true; button.textContent = "Creating account...";
        try {
            await responseData(await fetch("/register", { method: "POST", headers: headers(), body: JSON.stringify({ name, email, password }) }));
            $("loginEmail").value = email; $("registerName").value = ""; $("registerEmail").value = ""; $("registerPassword").value = "";
            showLogin("Account created. You can sign in now.");
        } catch (error) { showMessage(error.message); }
        finally { button.disabled = false; button.textContent = "Create account →"; }
    });
    $("loginButton").addEventListener("click", async () => {
        const email = $("loginEmail").value.trim();
        const password = $("loginPassword").value;
        if (!email || !password) return showMessage("Please enter your email and password.");
        const button = $("loginButton"); button.disabled = true; button.textContent = "Signing in...";
        try {
            const data = await responseData(await fetch("/login", { method: "POST", headers: headers(), body: JSON.stringify({ email, password }) }));
            localStorage.setItem("token", data.token); window.location.href = "/converter";
        } catch (error) { showMessage(error.message); }
        finally { button.disabled = false; button.textContent = "Sign in →"; }
    });
}

async function initConverter() {
    await loadUser();
    $("swapButton").addEventListener("click", () => { const source = $("sourceLanguage").value; $("sourceLanguage").value = $("targetLanguage").value; $("targetLanguage").value = source; });
    $("clearButton").addEventListener("click", () => { $("inputCode").value = ""; $("outputCode").value = ""; $("statusMessage").textContent = ""; });
    $("copyButton").addEventListener("click", async () => { if ($("outputCode").value) { await navigator.clipboard.writeText($("outputCode").value); $("statusMessage").textContent = "Code copied to clipboard."; } });
    $("convertButton").addEventListener("click", async () => {
        const source = $("sourceLanguage").value, target = $("targetLanguage").value, code = $("inputCode").value, status = $("statusMessage");
        if (!source || !target || !code.trim()) return (status.textContent = "Select both languages and enter code first.");
        if (source === target) return (status.textContent = "Choose two different languages.");
        const button = $("convertButton"); button.disabled = true; status.textContent = "AI is converting your code...";
        try { const data = await responseData(await fetch("/convert", { method: "POST", headers: headers(), body: JSON.stringify({ source_language: source, target_language: target, code }) })); $("outputCode").value = data.converted_code; status.textContent = "Conversion complete."; }
        catch (error) { status.textContent = error.message; if (error.message.toLowerCase().includes("token")) logout(); }
        finally { button.disabled = false; }
    });
}

async function loadHistory() {
    const list = $("historyList");
    try {
        await loadUser();
        const data = await responseData(await fetch("/history", { headers: headers() }));
        list.innerHTML = "";
        if (!data.data.length) { list.innerHTML = '<p class="empty-history">No conversions yet. Your saved work will appear here.</p>'; return; }
        data.data.forEach((item) => {
            const row = document.createElement("article"); row.className = "history-item";
            row.innerHTML = `<div class="history-info"><strong>${item.source_language} <span>→</span> ${item.target_language}</strong><small>${item.created_at || ""}</small></div><button class="delete-history">Delete</button>`;
            row.querySelector(".delete-history").addEventListener("click", async () => { if (confirm("Delete this conversion?")) { await fetch(`/history/${item._id}`, { method: "DELETE", headers: headers() }); loadHistory(); } });
            list.appendChild(row);
        });
    } catch (error) { list.innerHTML = `<p class="empty-history">${error.message}</p>`; }
}

if ($("authContainer")) initAuthPage();
if ($("convertButton")) initConverter().catch(logout);
if ($("historyList")) {
    $("clearHistoryButton").addEventListener("click", async () => { if (confirm("Clear all conversion history?")) { await fetch("/history", { method: "DELETE", headers: headers() }); loadHistory(); } });
    loadHistory();
}
if ($("profileName")) loadUser().catch(logout);
