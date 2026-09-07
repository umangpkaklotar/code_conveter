const $ = (id) => document.getElementById(id);
const token = () => localStorage.getItem("token");
const headers = () => ({ "Content-Type": "application/json", ...(token() ? { Authorization: `Bearer ${token()}` } : {}) });
let outputAnimationTimer = null;
let quotaCountdownTimer = null;

class ApiError extends Error {
    constructor(message, status, retryAfter) {
        super(message);
        this.status = status;
        this.retryAfter = retryAfter;
    }
}

async function responseData(response) {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new ApiError(
            data.detail || "Something went wrong.",
            response.status,
            Number(response.headers.get("Retry-After")) || 0,
        );
    }
    return data;
}

function showQuotaMessage(statusElement, error) {
    if (quotaCountdownTimer) clearInterval(quotaCountdownTimer);
    let remaining = error.retryAfter || 0;
    const baseMessage = error.message || "AI quota reached. Please try again later.";
    const update = () => {
        statusElement.textContent = remaining > 0
            ? `${baseMessage} Retry in ${remaining}s.`
            : baseMessage;
        if (remaining <= 0) {
            clearInterval(quotaCountdownTimer);
            quotaCountdownTimer = null;
        }
        remaining -= 1;
    };
    update();
    if (remaining >= 0) quotaCountdownTimer = setInterval(update, 1000);
}

function logout() {
    localStorage.removeItem("token");
    window.location.href = "/";
}

function addGeneratorLink() {
    const navigation = document.querySelector(".main-nav");
    if (!navigation || navigation.querySelector('a[href="/generate"]')) return;
    const link = document.createElement("a");
    link.className = "nav-link";
    link.href = "/generate";
    link.textContent = "Generate";
    navigation.insertBefore(link, navigation.children[1] || null);
}

addGeneratorLink();

const logoutButton = $("logoutButton");
if (logoutButton) logoutButton.addEventListener("click", logout);

async function loadUser() {
    if (!token()) {
        window.location.href = "/";
        return null;
    }
    const user = await responseData(await fetch("/api/profile", { headers: headers() }));
    const name = $("headerUserName");
    if (name) name.textContent = user.name || "Account";
    const profileName = $("profileName");
    const profileEmail = $("profileEmail");
    if (profileName) profileName.textContent = user.name;
    if (profileEmail) profileEmail.textContent = user.email;
    const profileCreated = $("profileCreated");
    if (profileCreated) profileCreated.textContent = `Member since ${new Date(user.created_at).toLocaleDateString()}`;
    const profileId = $("profileId");
    if (profileId) profileId.textContent = user.id;
    const editName = $("profileEditName");
    const editEmail = $("profileEditEmail");
    if (editName) editName.value = user.name;
    if (editEmail) editEmail.value = user.email;
    return user;
}

async function initProfile() {
    const user = await loadUser();
    if (!user) return;
    $("saveProfileButton").addEventListener("click", async () => {
        const button = $("saveProfileButton");
        const message = $("profileMessage");
        const name = $("profileEditName").value.trim();
        const email = $("profileEditEmail").value.trim().toLowerCase();
        if (!name || !email) {
            message.textContent = "Name and email are required.";
            message.className = "error-message";
            return;
        }
        button.disabled = true;
        button.textContent = "Saving...";
        try {
            const data = await responseData(await fetch("/api/profile", {
                method: "PUT",
                headers: headers(),
                body: JSON.stringify({ name, email })
            }));
            message.textContent = data.message;
            message.className = "success-message";
            await loadUser();
        } catch (error) {
            message.textContent = error.message;
            message.className = "error-message";
        } finally {
            button.disabled = false;
            button.innerHTML = "Save changes <span>→</span>";
        }
    });
}

async function initForgotPassword() {
    const user = await loadUser();
    if (user) $("resetEmail").value = user.email;
    $("resetPasswordButton").addEventListener("click", async () => {
        const email = $("resetEmail").value.trim().toLowerCase();
        const password = $("resetPassword").value;
        const confirmation = $("resetPasswordConfirm").value;
        const message = $("resetMessage");
        if (!email || !password || !confirmation) {
            message.textContent = "Complete all password reset fields.";
            message.className = "error-message";
            return;
        }
        if (password.length < 6) {
            message.textContent = "New password must be at least 6 characters.";
            message.className = "error-message";
            return;
        }
        if (password !== confirmation) {
            message.textContent = "The passwords do not match.";
            message.className = "error-message";
            return;
        }
        const button = $("resetPasswordButton");
        button.disabled = true;
        button.textContent = "Changing password...";
        try {
            const data = await responseData(await fetch("/api/forgot-password", {
                method: "POST",
                headers: headers(),
                body: JSON.stringify({ email, new_password: password })
            }));
            message.textContent = data.message;
            message.className = "success-message";
            $("resetPassword").value = "";
            $("resetPasswordConfirm").value = "";
        } catch (error) {
            message.textContent = error.message;
            message.className = "error-message";
        } finally {
            button.disabled = false;
            button.innerHTML = "Change password <span>→</span>";
        }
    });
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
    $("clearButton").addEventListener("click", () => {
        stopOutputAnimation();
        $("inputCode").value = "";
        $("outputCode").value = "";
        $("outputCode").dataset.fullCode = "";
        if ($("explanationText")) $("explanationText").textContent = "The explanation will appear after conversion.";
        updateOutputProgress(0, 0);
        $("statusMessage").textContent = "";
    });
    $("copyButton").addEventListener("click", async () => {
        const completeCode = $("outputCode").dataset.fullCode || $("outputCode").value;
        if (completeCode) {
            await navigator.clipboard.writeText(completeCode);
            $("statusMessage").textContent = "Complete converted code copied.";
        }
    });
    $("convertButton").addEventListener("click", async () => {
        const source = $("sourceLanguage").value, target = $("targetLanguage").value, code = $("inputCode").value, status = $("statusMessage");
        if (!source || !target || !code.trim()) return (status.textContent = "Select both languages and enter code first.");
        if (source === target) return (status.textContent = "Choose two different languages.");
        const button = $("convertButton"); button.disabled = true; status.textContent = "AI is converting your code...";
        try {
            const data = await responseData(await fetch("/convert", { method: "POST", headers: headers(), body: JSON.stringify({ source_language: source, target_language: target, code }) }));
            animateOutputCode(data.converted_code);
            if ($("explanationText")) $("explanationText").textContent = data.explanation || "No explanation was returned.";
            status.textContent = "Conversion complete. Writing the result line by line...";
        }
        catch (error) {
            if (error.status === 429) showQuotaMessage(status, error);
            else status.textContent = error.message;
            if (error.message.toLowerCase().includes("token")) logout();
        }
        finally { button.disabled = false; }
    });
}

async function initGenerator() {
    await loadUser();
    const prompt = $("generationPrompt");
    const button = $("generateButton");
    const status = $("generationStatus");
    const output = $("generatedCode");
    const explanation = $("generatedExplanation");
    const copyButton = $("copyGeneratedButton");

    copyButton.addEventListener("click", async () => {
        const code = output.dataset.fullCode || "";
        if (!code) return;
        await navigator.clipboard.writeText(code);
        copyButton.textContent = "Copied";
        setTimeout(() => { copyButton.textContent = "Copy code"; }, 1200);
    });
    button.addEventListener("click", async () => {
        if (!prompt.value.trim()) return (status.textContent = "Describe the code you want to build first.");
        button.disabled = true;
        status.textContent = "AI is turning your idea into code...";
        output.textContent = "";
        explanation.innerHTML = '<p class="loading-copy">Thinking through the best implementation...</p>';
        try {
            const data = await responseData(await fetch("/generate", {
                method: "POST",
                headers: headers(),
                body: JSON.stringify({ prompt: prompt.value })
            }));
            output.dataset.fullCode = data.converted_code || "";
            output.textContent = data.converted_code || "No code was returned.";
            explanation.innerHTML = formatExplanation(data.explanation);
            $("generationLanguageLabel").textContent = data.detected_language || "Language detected";
            $("generationProgress").textContent = "Complete";
            status.textContent = "Done — this generation is saved in your history.";
        } catch (error) {
            if (error.status === 429) showQuotaMessage(status, error);
            else status.textContent = error.message;
            if (error.message.toLowerCase().includes("token")) logout();
        } finally { button.disabled = false; }
    });
}

function formatExplanation(text) {
    const wrapper = document.createElement("div");
    String(text || "No explanation was returned.").split(/\n+/).forEach((line) => {
        const clean = line.trim();
        if (!clean) return;
        if (clean.endsWith(":")) {
            const heading = document.createElement("h4");
            heading.textContent = clean.slice(0, -1);
            wrapper.appendChild(heading);
        } else {
            const item = document.createElement(clean.startsWith("-") ? "li" : "p");
            item.textContent = clean.replace(/^-\s*/, "");
            if (item.tagName === "LI") {
                let list = wrapper.lastElementChild;
                if (!list || list.tagName !== "UL") { list = document.createElement("ul"); wrapper.appendChild(list); }
                list.appendChild(item);
            } else wrapper.appendChild(item);
        }
    });
    return wrapper.innerHTML;
}

function stopOutputAnimation() {
    if (outputAnimationTimer) {
        clearInterval(outputAnimationTimer);
        outputAnimationTimer = null;
    }
}

function updateOutputProgress(current, total) {
    const progress = $("outputProgress");
    if (progress) progress.textContent = total ? `Lines ${current}/${total}` : "Ready for output";
}

function animateOutputCode(code) {
    stopOutputAnimation();
    const output = $("outputCode");
    const normalizedCode = String(code || "").replace(/\r\n?/g, "\n");
    const lines = normalizedCode.split("\n");
    let lineNumber = 0;
    output.value = "";
    output.dataset.fullCode = normalizedCode;
    updateOutputProgress(0, lines.length);
    outputAnimationTimer = setInterval(() => {
        output.value += (lineNumber ? "\n" : "") + lines[lineNumber];
        lineNumber += 1;
        output.scrollTop = output.scrollHeight;
        updateOutputProgress(lineNumber, lines.length);
        if (lineNumber >= lines.length) stopOutputAnimation();
    }, 85);
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
            row.innerHTML = `<div class="history-info"><strong>${item.source_language} <span>→</span> ${item.target_language}</strong><small>${item.created_at || ""}</small></div><div class="history-actions"><button class="view-history">View code</button><button class="delete-history">Delete</button></div><div class="history-details hidden"><div><div class="detail-heading"><span>Input code</span><button class="copy-detail" data-copy="input">Copy</button></div><pre class="history-code input-detail">${escapeHtml(item.input_code || "")}</pre></div><div><div class="detail-heading"><span>Converted code</span><button class="copy-detail" data-copy="converted">Copy</button></div><pre class="history-code converted-detail">${escapeHtml(item.converted_code || "")}</pre></div><div><span>Full explanation</span><p class="history-explanation">${escapeHtml(item.explanation || "No explanation saved for this conversion.")}</p></div></div>`;
            row.querySelector(".view-history").addEventListener("click", () => {
                const details = row.querySelector(".history-details");
                details.classList.toggle("hidden");
                row.querySelector(".view-history").textContent = details.classList.contains("hidden") ? "View code" : "Hide code";
            });
            row.querySelectorAll(".copy-detail").forEach((button) => {
                button.addEventListener("click", async () => {
                    const selector = button.dataset.copy === "input" ? ".input-detail" : ".converted-detail";
                    await navigator.clipboard.writeText(row.querySelector(selector).textContent);
                    button.textContent = "Copied";
                    setTimeout(() => { button.textContent = "Copy"; }, 1200);
                });
            });
            row.querySelector(".delete-history").addEventListener("click", async () => { if (confirm("Delete this conversion?")) { await fetch(`/history/${item._id}`, { method: "DELETE", headers: headers() }); loadHistory(); } });
            list.appendChild(row);
        });
    } catch (error) { list.innerHTML = `<p class="empty-history">${error.message}</p>`; }
}

function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character]));
}

if ($("authContainer")) initAuthPage();
if ($("convertButton")) initConverter().catch(logout);
if ($("generateButton")) initGenerator().catch(logout);
if ($("historyList")) {
    $("clearHistoryButton").addEventListener("click", async () => { if (confirm("Clear all conversion history?")) { await fetch("/history", { method: "DELETE", headers: headers() }); loadHistory(); } });
    loadHistory();
}
if ($("profileName")) initProfile().catch(logout);
if ($("resetPasswordButton")) initForgotPassword().catch(logout);
