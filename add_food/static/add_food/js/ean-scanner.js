import { BrowserMultiFormatReader }
    from "https://cdn.jsdelivr.net/npm/@zxing/library@latest/+esm";

const resultOutput = document.getElementById("scan-result");
const codeInput = document.querySelector('input[name="ean_code"]');
const trigger = document.getElementById("scan-trigger");
const scannerBox = document.getElementById("scanner-box");

let reader = null;

trigger.addEventListener("click", () => {
    // скрываем карточку, показываем видео
    trigger.classList.remove("visible");
    trigger.classList.add("hidden");

    scannerBox.classList.remove("hidden");
    scannerBox.classList.add("visible");

    reader = new BrowserMultiFormatReader();

    reader.decodeFromVideoDevice(null, "preview", (result, err) => {
        if (result) {
            const code = result.text;
            codeInput.value = code;
            resultOutput.textContent = "Распознано: " + code;

            // останавливаем сканер
            reader.reset();

            // возвращаем карточку, прячем видео
            scannerBox.classList.remove("visible");
            scannerBox.classList.add("hidden");

            trigger.classList.remove("hidden");
            trigger.classList.add("visible");
        }
    });
});
