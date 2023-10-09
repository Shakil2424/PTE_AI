const startStopBtn = document.getElementById("start-button");
const dots = Array.from(document.querySelectorAll('.dot'));
// Pause the animation
dots.forEach(dot => {
    dot.style.animationPlayState = 'paused';
});

let isRecording = false;
let hasAccess = false;
let stream;
let mediaRecorder;

function handleSuccess(s) {
    hasAccess = true;
    stream = s;

    mediaRecorder = new MediaRecorder(stream);
    startStopBtn.addEventListener("click", () => {
        if (!isRecording) {
            startStopBtn.innerHTML = "Stop Listening";
            isRecording = true;
            mediaRecorder.start();
            // Resume the animation
            dots.forEach(dot => {
                dot.style.animationPlayState = 'running';
            });
        } else {
            startStopBtn.innerHTML = "Start Listening";
            isRecording = false;
            mediaRecorder.stop();
            dots.forEach(dot => {
                dot.style.animationPlayState = 'paused';
            });
            // Start recording again
            setTimeout(() => {
                mediaRecorder.start();
                // Resume the animation
                dots.forEach(dot => {
                    dot.style.animationPlayState = 'running';
                });
            }, 500);
        }
    });
    mediaRecorder.addEventListener("dataavailable", (e) => {
        const audioBlob = new Blob([e.data], { type: "audio/wav" });
        const audioUrl = URL.createObjectURL(audioBlob);
        const file = new File([e.data], "audio.wav", {
            type: "audio/wav",
        });

        // Get the reference text
        const referenceText = document.getElementById("random-sentence").innerText;

        const formData = new FormData();
        formData.append("audio", file);
        formData.append("reference", referenceText); // Add the reference text to the form data

        fetch("/Read_Aloud", {
            method: "POST",
            body: formData,
        }).then((response) => {
            window.location = response.url;
        });
    });
}

function handleError(e) {
    console.log(e);
}

if (!hasAccess) {
    navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then(handleSuccess)
        .catch(handleError);
}
