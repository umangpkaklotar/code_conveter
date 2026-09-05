const convertButton = document.getElementById("convertButton");

const sourceLanguage = document.getElementById("sourceLanguage");

const targetLanguage = document.getElementById("targetLanguage");

const inputCode = document.getElementById("inputCode");

const outputCode = document.getElementById("outputCode");

const statusMessage = document.getElementById("statusMessage");


convertButton.addEventListener("click", async function () {

    const code = inputCode.value;

    if (code.trim() === "") {

        statusMessage.textContent = "Please enter some code.";

        return;
    }


    statusMessage.textContent = "Converting code... Please wait.";

    outputCode.value = "";


    try {

        const response = await fetch(
            "http://127.0.0.1:8000/convert",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    source_language: sourceLanguage.value,
                    target_language: targetLanguage.value,
                    code: code
                })
            }
        );


        const data = await response.json();


        if (response.ok) {

            outputCode.value = data.converted_code;

            statusMessage.textContent =
                "Code converted successfully!";

        } else {

            statusMessage.textContent =
                "Error: " + JSON.stringify(data);

        }

    } catch (error) {

        console.error(error);

        statusMessage.textContent =
            "Cannot connect to backend server.";

    }

});