const requestEl = document.getElementById("request");
const remainingEl = document.getElementById("remaining");
const button = document.getElementById("submit-button");
const emojiEl = document.getElementById("emoji");
const messageEl = document.getElementById("message");
const timerEl = document.getElementById("timer");

const API_URL = "http://127.0.0.1:8000/api/check";
const LIMIT = 5;

const emojis = ["🙂", "😀", "😎", "🚀", "🤩", "🥳", "🤡"];

let countdown = null;

function startCountdown(seconds) {
    if (countdown) {
        clearInterval(countdown);
        countdown = null;
    }

    let timeLeft = seconds;
    timerEl.textContent = timeLeft;

    countdown = setInterval(function () {
        timeLeft--;
        if (timeLeft < 0) {
            timeLeft = 0;
        }
        timerEl.textContent = timeLeft;

        if (timeLeft <= 0) {
            clearInterval(countdown);
            countdown = null;

            requestEl.textContent = 0;
            remainingEl.textContent = LIMIT;
            timerEl.textContent = 60;
            emojiEl.textContent = emojis[0];
            messageEl.textContent =
                "New window started! Click Request to send a request.";
            button.disabled = false;
        }
    }, 1000);
}

function pickEmoji(data) {
    if (!data.allowed) {
        return "🤡";
    }
    const count = data.count;
    if (count >= 1 && count <= 5) {
        return emojis[count];
    }
    return emojis[0];
}

button.addEventListener("click", function () {
    fetch(API_URL)
        .then(async function (response) {
            const data = await response.json();

            if (response.ok) {
                requestEl.textContent = data.count;
                remainingEl.textContent = data.remaining;
                messageEl.textContent = data.message;
                emojiEl.textContent = pickEmoji(data);
                button.disabled = false;
                startCountdown(data.reset_in);
            } else {
                requestEl.textContent = data.count;
                remainingEl.textContent = data.remaining;
                messageEl.textContent = data.message;
                emojiEl.textContent = "🤡";
                button.disabled = true;
                startCountdown(data.reset_in);
            }
        })
        .catch(function (error) {
            console.error("Error:", error);
            messageEl.textContent =
                "Could not reach the backend. Is the FastAPI server running?";
            emojiEl.textContent = "🙂";
        });
});
