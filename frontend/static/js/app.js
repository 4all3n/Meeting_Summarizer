const API_BASE = 'http://localhost:8000/api';

// global delete meeting function
async function deleteMeeting(event, meetingId, redirectHome = false) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    if (!confirm('Are you sure you want to delete this meeting? This will also delete the audio file.')) {
        return;
    }

    try {
        let res = await fetch(`${API_BASE}/meetings/${meetingId}`, {
            method: 'DELETE',
        });

        if (res.ok) {
            if (redirectHome) {
                window.location.href = '/';
            } else {
                let card = document.getElementById(`meeting-card-${meetingId}`);
                if (card) {
                    card.remove();
                    let list = document.getElementById('meetings-list');
                    if (list && list.children.length === 0) {
                        location.reload();
                    }
                } else {
                    location.reload();
                }
            }
        } else {
            alert('Failed to delete meeting');
        }
    } catch (e) {
        alert('Could not reach backend server');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('audio-file');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const fileSize = document.getElementById('file-size');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadForm = document.getElementById('upload-form');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const languageSelect = document.getElementById('language-select');

    if (!dropZone) return; // not on the upload page

    // clicking the drop zone opens file picker
    dropZone.addEventListener('click', () => fileInput.click());

    // drag and drop handlers
    dropZone.addEventListener('dragover', e => {
        e.preventDefault();
        dropZone.classList.add('border-indigo-400', 'bg-indigo-50');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('border-indigo-400', 'bg-indigo-50');
    });

    dropZone.addEventListener('drop', e => {
        e.preventDefault();
        dropZone.classList.remove('border-indigo-400', 'bg-indigo-50');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            showFileInfo(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) showFileInfo(fileInput.files[0]);
    });

    function showFileInfo(file) {
        let sizeMB = (file.size / 1024 / 1024).toFixed(1);
        fileName.textContent = file.name;
        fileSize.textContent = `(${sizeMB} MB)`;
        fileInfo.classList.remove('hidden');
        uploadBtn.disabled = false;
    }

    // handle upload
    uploadForm.addEventListener('submit', e => {
        e.preventDefault();
        if (!fileInput.files.length) return;

        uploadBtn.disabled = true;
        uploadBtn.textContent = 'Uploading...';
        progressContainer.classList.remove('hidden');

        let formData = new FormData();
        formData.append('file', fileInput.files[0]);
        if (languageSelect) {
            formData.append('language', languageSelect.value);
        }

        let xhr = new XMLHttpRequest();
        xhr.open('POST', `${API_BASE}/meetings/upload`);

        // show upload progress
        xhr.upload.onprogress = e => {
            if (e.lengthComputable) {
                let pct = Math.round(e.loaded / e.total * 100);
                progressBar.style.width = pct + '%';
                progressText.textContent = `Uploading... ${pct}%`;
            }
        };

        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                let data = JSON.parse(xhr.responseText);
                progressText.textContent = 'Done! Redirecting...';
                progressBar.style.width = '100%';
                setTimeout(() => window.location.href = `/meeting/${data.id}`, 500);
            } else {
                let err = JSON.parse(xhr.responseText);
                alert('Upload failed: ' + (err.detail || 'Unknown error'));
                resetUpload();
            }
        };

        xhr.onerror = () => {
            alert('Upload failed — is the backend server running?');
            resetUpload();
        };

        xhr.send(formData);
    });

    function resetUpload() {
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Upload & Process';
        progressContainer.classList.add('hidden');
        progressBar.style.width = '0%';
    }
});
