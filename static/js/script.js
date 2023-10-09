const startStopBtn = document.getElementById("start-stop-btn");
const microphoneIcon = document.getElementById("microphone-icon");
const conversation = document.getElementById("conversation");

const dots = Array.from(document.querySelectorAll('.dot'));
// Pause the animation
dots.forEach(dot => {
    dot.style.animationPlayState = 'paused';
});

let isRecording = false;
let hasAccess = false;
let stream;
let mediaRecorder;

if (!hasAccess) {
    navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then((s) => {
            hasAccess = true;
            stream = s;

            mediaRecorder = new MediaRecorder(stream);

            startStopBtn.addEventListener("click", () => {
                if (!isRecording) {
                    startStopBtn.innerHTML = "Stop Recording";
                    isRecording = true;
                    microphoneIcon.className = "microphone icon";
                    microphoneIcon.style.animation = "wave 2s infinite";
                    // Resume the animation
                    dots.forEach(dot => {
                        dot.style.animationPlayState = 'running';
                    });
                    mediaRecorder.start();
                } else {
                    startStopBtn.innerHTML = "Start Recording";
                    isRecording = false;
                    microphoneIcon.className = "microphone slash icon";
                    microphoneIcon.style.animation = "";
                    // Pause the animation
                    dots.forEach(dot => {
                        dot.style.animationPlayState = 'paused';
                    });
                    mediaRecorder.stop();
                }
            });
            mediaRecorder.addEventListener("dataavailable", (e) => {
                const audioBlob = new Blob([e.data], { type: "audio/wav" });

                const audioUrl = URL.createObjectURL(audioBlob);

                const audioElement = document.createElement("audio");
                audioElement.src = audioUrl;
                audioElement.controls = true;
                audioElement.style.margin = "10px";

                conversation.appendChild(audioElement);

                // create a File object from the Blob of the recorded audio
                const file = new File([e.data], "audio.wav", {
                    type: "audio/wav",
                });

                // create a new FormData object
                const formData = new FormData();
                formData.append("audio", file);

                // send a POST request to the /upload route
                fetch("/upload", {
                    method: "POST",
                    body: formData,
                }).then((response) => {
                    window.location = response.url;
                });
            });
        })
        .catch((e) => {
            console.log(e);
        });
}

conversation.scrollTop = conversation.scrollHeight;
const clearConversationBtn = document.getElementById(
    "clear-conversation-btn"
);
clearConversationBtn.addEventListener("click", () => {
    conversation.innerHTML = "";
});