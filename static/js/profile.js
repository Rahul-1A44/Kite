/* static/js/profile.js */

document.addEventListener('DOMContentLoaded', function() {
    // 1. Auto-Hide Toast Notifications
    const notifications = document.querySelectorAll('.toast-notification');
    if (notifications.length > 0) {
        setTimeout(() => {
            notifications.forEach(toast => {
                toast.classList.add('hiding');
                toast.addEventListener('animationend', () => toast.remove());
            });
        }, 3000);
    }
});

// 2. Modal Logic
function openModal(id) {
    const modal = document.getElementById(id);
    if(modal) {
        modal.classList.remove('hidden');
        // Small delay to allow display:block to apply before opacity transition
        setTimeout(() => modal.classList.remove('opacity-0'), 10);
    }
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if(modal) {
        modal.classList.add('opacity-0');
        setTimeout(() => modal.classList.add('hidden'), 300);
    }
}

// 3. Image Preview
function previewImage(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('modalProfilePreview').src = e.target.result;
        }
        reader.readAsDataURL(input.files[0]);
    }
}

// 4. Webcam Logic
let videoStream = null;

async function openCameraModal() {
    const modal = document.getElementById('webcamModal');
    const video = document.getElementById('cameraFeed');
    modal.classList.remove('hidden');

    try {
        videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = videoStream;
    } catch (err) {
        alert("Could not access camera. Please check permissions.");
        closeCameraModal();
    }
}

function closeCameraModal() {
    const modal = document.getElementById('webcamModal');
    modal.classList.add('hidden');
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
}

function takeSnapshot() {
    const video = document.getElementById('cameraFeed');
    const canvas = document.getElementById('cameraCanvas');
    const fileInput = document.getElementById('id_profile_picture');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    canvas.toBlob((blob) => {
        const file = new File([blob], "webcam-photo.jpg", { type: "image/jpeg" });
        
        // Create a DataTransfer to simulate a file upload event
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;
        
        // Trigger preview
        previewImage(fileInput);
        closeCameraModal();
    }, 'image/jpeg');
}

// Close modals on outside click
window.onclick = function(event) {
    if (event.target.classList.contains('modal') && event.target.id !== 'webcamModal') {
        closeModal(event.target.id);
    }
}