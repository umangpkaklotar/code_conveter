/* =========================
AUTH ELEMENTS
========================= */

const authContainer =
document.getElementById("authContainer");

const appContainer =
document.getElementById("appContainer");

const loginForm =
document.getElementById("loginForm");

const registerForm =
document.getElementById("registerForm");

const showRegister =
document.getElementById("showRegister");

const showLogin =
document.getElementById("showLogin");

const authMessage =
document.getElementById("authMessage");

const loginEmail =
document.getElementById("loginEmail");

const loginPassword =
document.getElementById("loginPassword");

const loginButton =
document.getElementById("loginButton");

const registerName =
document.getElementById("registerName");

const registerEmail =
document.getElementById("registerEmail");

const registerPassword =
document.getElementById("registerPassword");

const registerButton =
document.getElementById("registerButton");

/* =========================
PROFILE ELEMENTS
========================= */

const profileName =
document.getElementById("profileName");

const profileEmail =
document.getElementById("profileEmail");

const logoutButton =
document.getElementById("logoutButton");

/* =========================
CODE CONVERTER ELEMENTS
========================= */

const convertButton =
document.getElementById("convertButton");

const sourceLanguage =
document.getElementById("sourceLanguage");

const targetLanguage =
document.getElementById("targetLanguage");

const inputCode =
document.getElementById("inputCode");

const outputCode =
document.getElementById("outputCode");

const statusMessage =
document.getElementById("statusMessage");

const swapButton =
document.getElementById("swapButton");

const clearButton =
document.getElementById("clearButton");

const copyButton =
document.getElementById("copyButton");

/* =========================
HISTORY ELEMENTS
========================= */

const historyList =
document.getElementById("historyList");

const clearHistoryButton =
document.getElementById(
"clearHistoryButton"
);

/* =========================
GET TOKEN
========================= */

function getToken() {

```
return localStorage.getItem(
    "token"
);
```

}

/* =========================
AUTH HEADERS
========================= */

function authHeaders() {

```
return {

    "Content-Type":
        "application/json",

    "Authorization":
        "Bearer " + getToken()

};
```

}

/* =========================
SHOW REGISTER FORM
========================= */

showRegister.addEventListener(
"click",
function () {

```
    loginForm.classList.add(
        "hidden"
    );

    registerForm.classList.remove(
        "hidden"
    );

    authMessage.textContent =
        "";

}
```

);

/* =========================
SHOW LOGIN FORM
========================= */

showLogin.addEventListener(
"click",
function () {

```
    registerForm.classList.add(
        "hidden"
    );

    loginForm.classList.remove(
        "hidden"
    );

    authMessage.textContent =
        "";

}
```

);

/* =========================
REGISTER USER
========================= */

registerButton.addEventListener(
"click",
async function () {

```
    const name =
        registerName.value.trim();

    const email =
        registerEmail.value.trim();

    const password =
        registerPassword.value;


    if (
        !name ||
        !email ||
        !password
    ) {

        authMessage.textContent =
            "Please fill all fields.";

        return;

    }


    registerButton.disabled =
        true;

    registerButton.textContent =
        "Creating Account...";


    try {

        const response =
            await fetch(
                "/register",
                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            name:
                                name,

                            email:
                                email,

                            password:
                                password

                        })

                }
            );


        const data =
            await response.json();


        if (response.ok) {

            authMessage.textContent =
                "Registration successful! Please login.";


            registerForm.classList.add(
                "hidden"
            );

            loginForm.classList.remove(
                "hidden"
            );


            loginEmail.value =
                email;


            registerName.value =
                "";

            registerEmail.value =
                "";

            registerPassword.value =
                "";

        } else {

            authMessage.textContent =
                data.detail ||
                "Registration failed.";

        }

    } catch (error) {

        console.error(error);

        authMessage.textContent =
            "Cannot connect to server.";

    }


    registerButton.disabled =
        false;

    registerButton.textContent =
        "Register";

}
```

);

/* =========================
LOGIN USER
========================= */

loginButton.addEventListener(
"click",
async function () {

```
    const email =
        loginEmail.value.trim();

    const password =
        loginPassword.value;


    if (
        !email ||
        !password
    ) {

        authMessage.textContent =
            "Please enter email and password.";

        return;

    }


    loginButton.disabled =
        true;

    loginButton.textContent =
        "Logging in...";


    try {

        const response =
            await fetch(
                "/login",
                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            email:
                                email,

                            password:
                                password

                        })

                }
            );


        const data =
            await response.json();


        if (response.ok) {

            /* Save JWT Token */

            localStorage.setItem(
                "token",
                data.token
            );


            /* Show Application */

            authContainer.classList.add(
                "hidden"
            );

            appContainer.classList.remove(
                "hidden"
            );


            /* Show User Profile */

            profileName.textContent =
                data.user.name;

            profileEmail.textContent =
                data.user.email;


            /* Clear Password */

            loginPassword.value =
                "";


            /* Load User History */

            loadHistory();

        } else {

            authMessage.textContent =
                data.detail ||
                "Invalid email or password.";

        }

    } catch (error) {

        console.error(error);

        authMessage.textContent =
            "Cannot connect to server.";

    }


    loginButton.disabled =
        false;

    loginButton.textContent =
        "Login";

}
```

);

/* =========================
LOGOUT FUNCTION
========================= */

function logout() {

```
/* Remove Token */

localStorage.removeItem(
    "token"
);


/* Hide Application */

appContainer.classList.add(
    "hidden"
);


/* Show Login */

authContainer.classList.remove(
    "hidden"
);


/* Clear Fields */

loginPassword.value =
    "";

inputCode.value =
    "";

outputCode.value =
    "";

statusMessage.textContent =
    "";


authMessage.textContent =
    "Logged out successfully.";
```

}

/* =========================
LOGOUT BUTTON
========================= */

logoutButton.addEventListener(
"click",
function () {

```
    logout();

}
```

);

/* =========================
CONVERT CODE
========================= */

convertButton.addEventListener(
"click",
async function () {

```
    const code =
        inputCode.value;


    /* Check Languages */

    if (
        !sourceLanguage.value ||
        !targetLanguage.value
    ) {

        statusMessage.textContent =
            "Please select both source and target languages.";

        return;

    }


    /* Check Code */

    if (
        code.trim() === ""
    ) {

        statusMessage.textContent =
            "Please enter some code.";

        return;

    }


    /* Check Same Language */

    if (
        sourceLanguage.value ===
        targetLanguage.value
    ) {

        statusMessage.textContent =
            "Source and target languages cannot be the same.";

        return;

    }


    statusMessage.textContent =
        "🤖 AI is converting your code...";


    outputCode.value =
        "";


    /* Disable Button */

    convertButton.disabled =
        true;

    convertButton.textContent =
        "Converting...";


    try {

        const response =
            await fetch(
                "/convert",
                {

                    method:
                        "POST",

                    headers:
                        authHeaders(),

                    body:
                        JSON.stringify({

                            source_language:
                                sourceLanguage.value,

                            target_language:
                                targetLanguage.value,

                            code:
                                code

                        })

                }
            );


        const data =
            await response.json();


        if (
            response.ok &&
            data.converted_code
        ) {

            outputCode.value =
                data.converted_code;


            statusMessage.textContent =
                "✅ Code converted successfully!";


            /* Refresh History */

            loadHistory();

        } else {

            statusMessage.textContent =
                "❌ " +
                (
                    data.detail ||
                    data.error ||
                    data.message ||
                    "Conversion failed."
                );

        }

    } catch (error) {

        console.error(error);

        statusMessage.textContent =
            "❌ Cannot connect to server.";

    }


    /* Enable Button Again */

    convertButton.disabled =
        false;

    convertButton.textContent =
        "✨ Convert Code";

}
```

);

/* =========================
SWAP LANGUAGES
========================= */

swapButton.addEventListener(
"click",
function () {

```
    const source =
        sourceLanguage.value;


    sourceLanguage.value =
        targetLanguage.value;


    targetLanguage.value =
        source;

}
```

);

/* =========================
CLEAR CODE
========================= */

clearButton.addEventListener(
"click",
function () {

```
    inputCode.value =
        "";

    outputCode.value =
        "";

    statusMessage.textContent =
        "";

}
```

);

/* =========================
COPY OUTPUT CODE
========================= */

copyButton.addEventListener(
"click",
async function () {

```
    if (
        outputCode.value.trim() === ""
    ) {

        statusMessage.textContent =
            "No converted code to copy.";

        return;

    }


    try {

        await navigator.clipboard.writeText(
            outputCode.value
        );


        statusMessage.textContent =
            "📋 Converted code copied!";

    } catch (error) {

        console.error(error);

        statusMessage.textContent =
            "Failed to copy code.";

    }

}
```

);

/* =========================
LOAD HISTORY
========================= */

async function loadHistory() {

```
try {

    const response =
        await fetch(
            "/history",
            {

                headers:
                    authHeaders()

            }
        );


    const data =
        await response.json();


    /* Token Expired */

    if (!response.ok) {

        if (
            response.status === 401
        ) {

            logout();

        }

        return;

    }


    displayHistory(
        data.data
    );

} catch (error) {

    console.error(
        "History Error:",
        error
    );

}
```

}

/* =========================
DISPLAY HISTORY
========================= */

function displayHistory(history) {

```
historyList.innerHTML =
    "";


/* No History */

if (
    !history ||
    history.length === 0
) {

    historyList.innerHTML =
        `
        <div class="empty-history">
            No conversion history yet.
        </div>
        `;

    return;

}


history.forEach(
    function (item) {

        const historyItem =
            document.createElement(
                "div"
            );


        historyItem.className =
            "history-item";


        historyItem.innerHTML =
            `

            <div class="history-info">

                <strong>

                    ${item.source_language}
                    →
                    ${item.target_language}

                </strong>


                <small>

                    ${item.created_at}

                </small>

            </div>


            <div class="history-actions">

                <button
                    class="view-history"
                >

                    View

                </button>


                <button
                    class="delete-history"
                >

                    Delete

                </button>

            </div>

            `;


        /* VIEW BUTTON */

        const viewButton =
            historyItem.querySelector(
                ".view-history"
            );


        viewButton.addEventListener(
            "click",
            function () {

                sourceLanguage.value =
                    item.source_language;

                targetLanguage.value =
                    item.target_language;

                inputCode.value =
                    item.input_code;

                outputCode.value =
                    item.converted_code;


                window.scrollTo({

                    top:
                        0,

                    behavior:
                        "smooth"

                });

            }
        );


        /* DELETE BUTTON */

        const deleteButton =
            historyItem.querySelector(
                ".delete-history"
            );


        deleteButton.addEventListener(
            "click",
            function () {

                deleteHistory(
                    item._id
                );

            }
        );


        historyList.appendChild(
            historyItem
        );

    }
);
```

}

/* =========================
DELETE ONE HISTORY
========================= */

async function deleteHistory(
conversionId
) {

```
const confirmDelete =
    confirm(
        "Delete this conversion?"
    );


if (!confirmDelete) {

    return;

}


try {

    const response =
        await fetch(

            "/history/" +
            conversionId,

            {

                method:
                    "DELETE",

                headers:
                    authHeaders()

            }

        );


    if (response.ok) {

        statusMessage.textContent =
            "Conversion deleted.";

        loadHistory();

    } else {

        const data =
            await response.json();

        alert(

            data.detail ||
            "Failed to delete conversion."

        );

    }

} catch (error) {

    console.error(error);

    alert(
        "Cannot connect to server."
    );

}
```

}

/* =========================
CLEAR ALL HISTORY
========================= */

clearHistoryButton.addEventListener(
"click",
async function () {

```
    const confirmClear =
        confirm(
            "Are you sure you want to delete all conversion history?"
        );


    if (!confirmClear) {

        return;

    }


    try {

        const response =
            await fetch(
                "/history",
                {

                    method:
                        "DELETE",

                    headers:
                        authHeaders()

                }
            );


        if (response.ok) {

            statusMessage.textContent =
                "All history deleted.";

            loadHistory();

        } else {

            alert(
                "Failed to clear history."
            );

        }

    } catch (error) {

        console.error(error);

        alert(
            "Cannot connect to server."
        );

    }

}
```

);

/* =========================
CHECK LOGIN ON PAGE LOAD
========================= */

async function checkLogin() {

```
const token =
    getToken();


/* User Not Logged In */

if (!token) {

    return;

}


try {

    const response =
        await fetch(
            "/profile",
            {

                headers:
                    authHeaders()

            }
        );


    const data =
        await response.json();


    /* Valid Token */

    if (response.ok) {

        authContainer.classList.add(
            "hidden"
        );

        appContainer.classList.remove(
            "hidden"
        );


        profileName.textContent =
            data.name;

        profileEmail.textContent =
            data.email;


        loadHistory();

    } else {

        /* Invalid Token */

        localStorage.removeItem(
            "token"
        );

    }

} catch (error) {

    console.error(
        "Login Check Error:",
        error
    );

}
```

}

/* =========================
RUN ON PAGE LOAD
========================= */

checkLogin();
