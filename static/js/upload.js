/* Upload page functionality */

const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');
const uploadForm = document.getElementById('uploadForm');

// Drop zone
dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        showFileName(e.dataTransfer.files[0]);
        previewFile(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
        showFileName(fileInput.files[0]);
        previewFile(fileInput.files[0]);
    }
});

function showFileName(file) {
    fileName.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
}

function previewFile(file) {
    if (!file.name.endsWith('.csv')) {
        return;
    }
    const reader = new FileReader();
    reader.onload = function(e) {
        const lines = e.target.result.split('\n').slice(0, 6);
        if (lines.length < 2) return;

        const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
        const previewHead = document.getElementById('previewHead');
        const previewBody = document.getElementById('previewBody');

        previewHead.innerHTML = '<tr>' + headers.map(h => `<th>${h}</th>`).join('') + '</tr>';
        previewBody.innerHTML = '';

        for (let i = 1; i < lines.length; i++) {
            if (!lines[i].trim()) continue;
            const cols = lines[i].split(',').map(c => c.trim().replace(/^"|"$/g, ''));
            previewBody.innerHTML += '<tr>' + cols.map(c => `<td>${c.substring(0, 40)}</td>`).join('') + '</tr>';
        }

        document.getElementById('previewSection').classList.remove('d-none');
    };
    reader.readAsText(file.slice(0, 5000));
}

// Upload form submission
uploadForm.addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('project_id', document.getElementById('projectSelect').value);
    formData.append('cycle_name', document.getElementById('cycleName').value);
    formData.append('source_system', document.getElementById('sourceSystem').value);

    const btn = document.getElementById('uploadBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Uploading...';

    try {
        const resp = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
        });
        const result = await resp.json();
        const alertDiv = document.getElementById('resultAlert');
        const resultDiv = document.getElementById('uploadResult');
        resultDiv.classList.remove('d-none');

        if (resp.ok) {
            alertDiv.className = 'alert alert-success';
            let msg = `Uploaded ${result.total_bugs} bugs to cycle. Source: ${result.source_system}.`;
            if (result.classified !== undefined) {
                msg += ` Classified: ${result.classified}. Duplicates: ${result.duplicates_found || 0}. Low confidence: ${result.low_confidence || 0}.`;
            }
            alertDiv.innerHTML = msg + `<br><a href="/cycles/${result.cycle_id}" class="alert-link">View Cycle Details</a>`;
        } else {
            alertDiv.className = 'alert alert-danger';
            alertDiv.textContent = result.detail || 'Upload failed';
        }
    } catch(err) {
        console.error(err);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-cloud-upload"></i> Upload & Analyze';
    }
});

// New project modal
document.getElementById('createProjectBtn').addEventListener('click', async function() {
    const name = document.getElementById('newProjectName').value.trim();
    if (!name) return;

    try {
        const resp = await fetch('/api/projects', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                name: name,
                description: document.getElementById('newProjectDesc').value,
            }),
        });
        const result = await resp.json();
        if (resp.ok) {
            const select = document.getElementById('projectSelect');
            const opt = new Option(result.name, result.id, true, true);
            select.add(opt);
            bootstrap.Modal.getInstance(document.getElementById('newProjectModal')).hide();
            document.getElementById('newProjectName').value = '';
            document.getElementById('newProjectDesc').value = '';
        }
    } catch(err) { console.error(err); }
});
