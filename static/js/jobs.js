// Modal Logic for Job Applications
function openAnalysisModal(btn) {
    const url = btn.getAttribute('data-url');
    const applyUrl = btn.getAttribute('data-apply-url');
    
    document.getElementById('currentAnalysisUrl').value = url;
    document.getElementById('modalApplyBtn').href = applyUrl;
    
    document.getElementById('analysisModal').classList.remove('hidden');
    resetModal();
}

function closeAnalysisModal() {
    const modal = document.getElementById('analysisModal');
    if(modal) modal.classList.add('hidden');
}

function showFileName(input) {
    const display = document.getElementById('fileNameDisplay');
    if (input.files && input.files[0]) {
        display.textContent = input.files[0].name;
        display.classList.remove('hidden');
    }
}

function resetModal() {
    document.getElementById('analysisStep1').classList.remove('hidden');
    document.getElementById('analysisStep2').classList.add('hidden');
    document.getElementById('fileNameDisplay').classList.add('hidden');
    const form = document.getElementById('analysisForm');
    if(form) form.reset();
    
    document.getElementById('modalApplyBtn').classList.add('hidden');
    document.getElementById('modalSourceBtn').classList.add('hidden');
}

// Single Advert Page Analysis Logic
function analyzeResumeSingle(url, csrfToken) {
    const fileInput = document.getElementById('resume-scan-input');
    const file = fileInput.files[0];
    if (!file) { alert("Please select a resume file first."); return; }

    // UI Updates
    document.getElementById('ai-result').classList.remove('hidden');
    document.getElementById('loading-scan').classList.remove('hidden');
    document.getElementById('scan-content').classList.add('hidden');

    const formData = new FormData();
    formData.append('resume', file);
    formData.append('csrfmiddlewaretoken', csrfToken);

    fetch(url, { method: 'POST', body: formData })
    .then(response => response.json())
    .then(data => {
        document.getElementById('loading-scan').classList.add('hidden');
        document.getElementById('scan-content').classList.remove('hidden');
        
        if(data.status === 'success' || data.status === 'fail') {
            const scoreMatch = data.message.match(/\((\d+)%\)/);
            const score = scoreMatch ? scoreMatch[1] : '--';
            const scoreDisplay = document.getElementById('score-display');
            scoreDisplay.innerText = score + '%';
            
            if(parseInt(score) > 70) scoreDisplay.classList.replace('text-yellow-400', 'text-green-400');
            else if(parseInt(score) < 40) scoreDisplay.classList.replace('text-yellow-400', 'text-red-400');

            document.getElementById('feedback-display').innerText = data.message;
        } else {
            document.getElementById('feedback-display').innerText = "Error analyzing file.";
        }
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('loading-scan').classList.add('hidden');
        alert("Something went wrong with the AI analysis.");
    });
}

function autoFillApp() {
    const scanInput = document.getElementById('resume-scan-input');
    const appInput = document.querySelector('input[type="file"][name="cv"]');
    
    if(scanInput.files.length > 0 && appInput) {
        const dt = new DataTransfer();
        dt.items.add(scanInput.files[0]);
        appInput.files = dt.files;
        document.getElementById('application-form').scrollIntoView({behavior: 'smooth'});
    }
}