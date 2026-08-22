// read API base from the body tag so we dont hardcode localhost everywhere
const API_BASE = document.body.dataset.api || 'http://localhost:8000/api';


// helper to clean any stray checkbox markdown [-] from text
function cleanMarkdownCheckboxes(text) {
    if (!text) return '';
    return text.replace(/-\s*\[\s*\]\s*/g, '- ');
}


// ============ shared functions ============

async function deleteMeeting(event, meetingId, redirectHome) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    if (!confirm('Delete this meeting? The audio file will also be removed.')) return;

    try {
        let res = await fetch(API_BASE + '/meetings/' + meetingId, { method: 'DELETE' });
        if (res.ok) {
            if (redirectHome) {
                window.location.href = '/';
            } else {
                let card = document.getElementById('meeting-card-' + meetingId);
                if (card) {
                    card.remove();
                    let list = document.getElementById('meetings-list');
                    if (list && list.children.length === 0) location.reload();
                } else {
                    location.reload();
                }
            }
        } else {
            alert('Failed to delete meeting');
        }
    } catch (e) {
        alert('Could not reach backend');
    }
}


// ============ upload page (index.html) ============

document.addEventListener('DOMContentLoaded', function () {
    // initialize lucide icons
    if (window.lucide) {
        lucide.createIcons();
    }

    // --- upload form setup ---
    var dropZone = document.getElementById('drop-zone');
    var fileInput = document.getElementById('audio-file');
    var uploadForm = document.getElementById('upload-form');

    if (dropZone && fileInput && uploadForm) {
        var fileInfo = document.getElementById('file-info');
        var fileName = document.getElementById('file-name');
        var fileSize = document.getElementById('file-size');
        var uploadBtn = document.getElementById('upload-btn');
        var progressContainer = document.getElementById('progress-container');
        var progressBar = document.getElementById('progress-bar');
        var progressText = document.getElementById('progress-text');
        var languageSelect = document.getElementById('language-select');

        dropZone.addEventListener('click', function () { fileInput.click(); });

        dropZone.addEventListener('dragover', function (e) {
            e.preventDefault();
            dropZone.classList.add('border-ef-green', 'bg-ef-bg1');
        });

        dropZone.addEventListener('dragleave', function () {
            dropZone.classList.remove('border-ef-green', 'bg-ef-bg1');
        });

        dropZone.addEventListener('drop', function (e) {
            e.preventDefault();
            dropZone.classList.remove('border-ef-green', 'bg-ef-bg1');
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                showFile(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', function () {
            if (fileInput.files.length) showFile(fileInput.files[0]);
        });

        function showFile(file) {
            var sizeMB = (file.size / 1024 / 1024).toFixed(1);
            fileName.textContent = file.name;
            fileSize.textContent = '(' + sizeMB + ' MB)';
            fileInfo.classList.remove('hidden');
            uploadBtn.disabled = false;
        }

        uploadForm.addEventListener('submit', function (e) {
            e.preventDefault();
            if (!fileInput.files.length) return;

            uploadBtn.disabled = true;
            uploadBtn.textContent = 'Uploading...';
            progressContainer.classList.remove('hidden');

            var formData = new FormData();
            formData.append('file', fileInput.files[0]);
            if (languageSelect) formData.append('language', languageSelect.value);

            var xhr = new XMLHttpRequest();
            xhr.open('POST', API_BASE + '/meetings/upload');

            xhr.upload.onprogress = function (e) {
                if (e.lengthComputable) {
                    var pct = Math.round(e.loaded / e.total * 100);
                    progressBar.style.width = pct + '%';
                    progressText.textContent = 'Uploading... ' + pct + '%';
                }
            };

            xhr.onload = function () {
                if (xhr.status >= 200 && xhr.status < 300) {
                    var data = JSON.parse(xhr.responseText);
                    progressText.textContent = 'Done! Redirecting...';
                    progressBar.style.width = '100%';
                    setTimeout(function () { window.location.href = '/meeting/' + data.id; }, 500);
                } else {
                    var err = JSON.parse(xhr.responseText);
                    alert('Upload failed: ' + (err.detail || 'Unknown error'));
                    resetForm();
                }
            };

            xhr.onerror = function () {
                alert('Upload failed — is the backend running?');
                resetForm();
            };

            xhr.send(formData);
        });

        function resetForm() {
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Upload & Process';
            progressContainer.classList.add('hidden');
            progressBar.style.width = '0%';
        }
    }

    // --- meeting detail page stuff ---

    // render markdown in summary and action items (with checkbox syntax stripped)
    var summaryDiv = document.getElementById('summary-content');
    if (summaryDiv && summaryDiv.dataset.raw) {
        var cleanSummary = cleanMarkdownCheckboxes(summaryDiv.dataset.raw);
        summaryDiv.innerHTML = marked.parse(cleanSummary);
    }

    var actionsDiv = document.getElementById('actions-content');
    if (actionsDiv && actionsDiv.dataset.raw) {
        var cleanActions = cleanMarkdownCheckboxes(actionsDiv.dataset.raw);
        actionsDiv.innerHTML = marked.parse(cleanActions);
    }

    // set up audio player source
    var audioEl = document.querySelector('audio[data-meeting-id]');
    if (audioEl) {
        var mid = audioEl.dataset.meetingId;
        var sourceEl = audioEl.querySelector('source');
        if (sourceEl) {
            sourceEl.src = API_BASE + '/meetings/' + mid + '/audio';
            audioEl.load();
        }
    }

    // poll status if meeting is still processing
    var processingBox = document.getElementById('processing-box');
    if (processingBox) {
        var meetingId = processingBox.dataset.id;
        var pollTimer = setInterval(function () {
            fetch(API_BASE + '/meetings/' + meetingId + '/status')
                .then(function (res) { return res.json(); })
                .then(function (data) {
                    var statusEl = document.getElementById('current-status');
                    if (statusEl) {
                        statusEl.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
                    }
                    if (data.status === 'completed' || data.status === 'failed') {
                        clearInterval(pollTimer);
                        location.reload();
                    }
                })
                .catch(function () { /* backend might be busy */ });
        }, 2000);
    }
});


// ============ meeting detail actions ============

function toggleTranscript() {
    var body = document.getElementById('transcript-body');
    var icon = document.getElementById('toggle-icon');
    if (!body) return;
    body.classList.toggle('hidden');
    if (icon) {
        icon.style.transform = body.classList.contains('hidden') ? 'rotate(0deg)' : 'rotate(180deg)';
    }
}

function downloadContent(type) {
    var name = document.querySelector('h1');
    var baseName = name ? name.textContent.replace(/\.[^/.]+$/, '') : 'meeting';
    var content, ext;

    if (type === 'summary') {
        var el = document.getElementById('summary-content');
        content = el ? (el.dataset.raw || el.textContent) : '';
        ext = '.md';
    } else {
        var el = document.getElementById('transcript-content');
        content = el ? el.textContent : '';
        ext = '.txt';
    }

    var blob = new Blob([content], { type: 'text/plain' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = baseName + '_' + type + ext;
    a.click();
    URL.revokeObjectURL(a.href);
}

async function resummarize(meetingId) {
    var btn = document.getElementById('resummarize-btn');
    if (btn) btn.disabled = true;

    try {
        var res = await fetch(API_BASE + '/meetings/' + meetingId + '/resummarize', { method: 'POST' });
        if (res.ok) {
            location.reload();
        } else {
            alert('Failed to re-summarize');
            if (btn) btn.disabled = false;
        }
    } catch (e) {
        alert('Could not reach backend');
        if (btn) btn.disabled = false;
    }
}

async function retranscribe(meetingId) {
    var lang = prompt('Language code (en, es, fr, de, hi...) or leave empty for auto:', 'en');
    if (lang === null) return;

    var btn = document.getElementById('retranscribe-btn');
    if (btn) btn.disabled = true;

    try {
        var formData = new FormData();
        formData.append('language', lang.trim() || 'auto');

        var res = await fetch(API_BASE + '/meetings/' + meetingId + '/retranscribe', {
            method: 'POST',
            body: formData,
        });

        if (res.ok) {
            location.reload();
        } else {
            var err = await res.json();
            alert('Re-transcribe failed: ' + (err.detail || 'Unknown error'));
            if (btn) btn.disabled = false;
        }
    } catch (e) {
        alert('Could not reach backend');
        if (btn) btn.disabled = false;
    }
}
