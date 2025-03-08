document.addEventListener('DOMContentLoaded', function() {
    const video = document.getElementById('webcam');
    const canvas = document.getElementById('canvas');
    const snapshot = document.getElementById('snapshot');
    const errorMessage = document.getElementById('error-message');

    const constraints = {
        video: true,
        audio: false
    };

    let captureInterval; // Variable to store the interval ID
    const CAPTURE_INTERVAL_MS = 5000; // 5 seconds

    // Get CSRF token from the form with the csrf_token
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Access the webcam
    async function startWebcam() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            video.srcObject = stream;
            errorMessage.textContent = '';

            // Start automatic capture every 5 seconds once webcam is ready
            startAutomaticCapture();
        } catch (err) {
            errorMessage.textContent = `Error accessing the webcam: ${err.message}`;
            console.error('Error accessing the webcam:', err);
        }
    }

    // Start automatic capture
    function startAutomaticCapture() {
        // Take an initial photo immediately
        capturePhoto();

        // Set interval for subsequent photos
        captureInterval = setInterval(capturePhoto, CAPTURE_INTERVAL_MS);

        // Add status message to inform the user
        const statusElement = document.createElement('div');
        statusElement.id = 'auto-capture-status';
        statusElement.className = 'status-message';
        statusElement.textContent = 'Auto-capture active: Taking a photo every 5 seconds';
        document.querySelector('.button-container').appendChild(statusElement);
    }

    // Capture a photo
    function capturePhoto() {
        if (!video.videoWidth) {
            console.log('Video not ready yet');
            return; // Skip if video isn't ready
        }

        const context = canvas.getContext('2d');

        // Set canvas dimensions to match video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        // Draw the current video frame to the canvas
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Convert canvas to data URL and display in img element
        const dataUrl = canvas.toDataURL('image/png');
        snapshot.src = dataUrl;

        // Update timestamp to show when the photo was taken
        const timestamp = updateTimestamp();

        saveImageToServer(dataUrl, timestamp);
    }

    // Save image to server
    function saveImageToServer(dataUrl, timestamp) {
        // Remove the data URL prefix to get just the base64 data
        const base64Data = dataUrl.replace(/^data:image\/png;base64,/, "");

        // Create form data
        const formData = new FormData();
        formData.append('image_data', base64Data);
        formData.append('timestamp', timestamp);

        // Send to server
        fetch('/save_image/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Image saved successfully:', data.filename);
            updateSaveStatus(true, data.filename);
        })
        .catch(error => {
            console.error('Error saving image:', error);
            updateSaveStatus(false, null);
        });
    }

    // Update timestamp when photo was taken
    function updateTimestamp() {
        let timestampElement = document.getElementById('capture-timestamp');

        if (!timestampElement) {
            timestampElement = document.createElement('div');
            timestampElement.id = 'capture-timestamp';
            document.querySelector('.snapshot-container').appendChild(timestampElement);
        }

        const now = new Date();
        const formattedTimestamp = now.toISOString().replace(/[:.]/g, '-');
        timestampElement.textContent = `Photo taken at: ${now.toLocaleTimeString()}`;

        return formattedTimestamp;
    }

    // Function to update save status - This function is referenced but not defined in your original code
    function updateSaveStatus(success, filename) {
        let statusElement = document.getElementById('save-status');

        if (!statusElement) {
            statusElement = document.createElement('div');
            statusElement.id = 'save-status';
            document.querySelector('.snapshot-container').appendChild(statusElement);
        }

        if (success) {
            statusElement.textContent = `Image saved as: ${filename}`;
            statusElement.className = 'status-success';
        } else {
            statusElement.textContent = 'Failed to save image';
            statusElement.className = 'status-error';
        }
    }

    // Clean up resources when leaving the page
    window.addEventListener('beforeunload', function() {
        if (captureInterval) {
            clearInterval(captureInterval);
        }

        // Stop webcam stream
        if (video.srcObject) {
            const tracks = video.srcObject.getTracks();
            tracks.forEach(track => track.stop());
        }
    });

    // Start the webcam when the page loads
    startWebcam();
});