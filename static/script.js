document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('control-form');
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const videoFeed = document.getElementById('video-feed');
    const videoPlaceholder = document.getElementById('video-placeholder');
    const statusDot = document.getElementById('status-dot');
    const statusText = document.getElementById('status-text');
    const sampleSelect = document.getElementById('sample_video');
    const uploadInput = document.getElementById('video-upload');
    const fileNameDisplay = document.getElementById('file-name');
    const confSlider = document.getElementById('conf');
    const confValDisplay = document.getElementById('conf-val');

    // UI elements for stats
    const statCount = document.getElementById('stat-count');
    const statFrames = document.getElementById('stat-frames');
    const statFps = document.getElementById('stat-fps');

    let currentStreamId = null;
    let statsInterval = null;
    let chartInstance = null;

    // Initialize Chart
    const ctx = document.getElementById('countChart').getContext('2d');
    
    // Gradient for chart area
    let gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(14, 165, 233, 0.5)');
    gradient.addColorStop(1, 'rgba(14, 165, 233, 0.0)');

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Fish Count',
                data: [],
                borderColor: '#0ea5e9',
                backgroundColor: gradient,
                borderWidth: 2,
                pointRadius: 0,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 0 // Disable animation for real-time updates to reduce CPU
            },
            scales: {
                x: {
                    display: false // Hide x-axis labels to look cleaner
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#94a3b8',
                        precision: 0
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });

    // Fetch models
    fetch('/models')
        .then(res => res.json())
        .then(models => {
            const modelSelect = document.getElementById('model_type');
            modelSelect.innerHTML = ''; // clear options
            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                modelSelect.appendChild(option);
            });
        });

    // Fetch sample videos
    fetch('/samples')
        .then(res => res.json())
        .then(samples => {
            samples.forEach(sample => {
                const option = document.createElement('option');
                option.value = sample;
                option.textContent = sample;
                sampleSelect.appendChild(option);
            });
            if(samples.length > 0) {
                sampleSelect.value = samples[0];
            }
        });

    // Update confidence display
    confSlider.addEventListener('input', (e) => {
        confValDisplay.textContent = e.target.value;
    });

    // Handle file selection
    uploadInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            fileNameDisplay.textContent = e.target.files[0].name;
            sampleSelect.value = ''; // Clear sample selection
        } else {
            fileNameDisplay.textContent = 'No file chosen';
        }
    });

    sampleSelect.addEventListener('change', () => {
        if (sampleSelect.value) {
            uploadInput.value = '';
            fileNameDisplay.textContent = 'No file chosen';
        }
    });

    // Start Analysis
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(form);
        
        // Ensure either file or sample is provided
        if (!formData.get('file').name && !formData.get('sample_video')) {
            alert('Please select a sample video or upload a file.');
            return;
        }

        startBtn.disabled = true;
        startBtn.textContent = 'Starting...';

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Upload failed');
            }

            const data = await response.json();
            currentStreamId = data.stream_id;

            // Update UI
            startBtn.classList.add('hidden');
            stopBtn.classList.remove('hidden');
            videoPlaceholder.classList.add('hidden');
            videoFeed.classList.remove('hidden');
            statusDot.classList.add('active');
            statusText.textContent = 'Processing Live Stream...';
            statusText.style.color = '#10b981';

            // Reset Chart
            chartInstance.data.labels = [];
            chartInstance.data.datasets[0].data = [];
            chartInstance.update();

            // Start video feed
            videoFeed.src = `/video_feed/${currentStreamId}`;

            // Start polling stats
            if (statsInterval) clearInterval(statsInterval);
            statsInterval = setInterval(fetchStats, 1000);

        } catch (error) {
            console.error(error);
            alert('Error starting analysis.');
            startBtn.disabled = false;
            startBtn.textContent = 'Start Analysis';
        }
    });

    // Stop Analysis
    stopBtn.addEventListener('click', async () => {
        if (!currentStreamId) return;

        await fetch(`/stop/${currentStreamId}`, { method: 'POST' });
        
        stopStreamUI();
    });

    function stopStreamUI() {
        if (statsInterval) clearInterval(statsInterval);
        
        videoFeed.src = '';
        videoFeed.classList.add('hidden');
        videoPlaceholder.classList.remove('hidden');
        
        startBtn.classList.remove('hidden');
        startBtn.disabled = false;
        startBtn.textContent = 'Start Analysis';
        
        stopBtn.classList.add('hidden');
        
        statusDot.classList.remove('active');
        statusText.textContent = 'Standby';
        statusText.style.color = 'var(--text-muted)';
        
        currentStreamId = null;
    }

    // Fetch Statistics
    async function fetchStats() {
        if (!currentStreamId) return;

        try {
            const response = await fetch(`/stats/${currentStreamId}`);
            const data = await response.json();

            if (!data.active) {
                stopStreamUI();
                return;
            }

            const stats = data.stats;

            // Animate count if it changed
            if (parseInt(statCount.textContent) !== stats.count) {
                statCount.classList.remove('pulse');
                void statCount.offsetWidth; // trigger reflow
                statCount.classList.add('pulse');
            }

            statCount.textContent = stats.count;
            statFrames.textContent = stats.frames;
            statFps.textContent = stats.fps.toFixed(2);

            // Update chart
            chartInstance.data.labels = stats.history.map((_, i) => i);
            chartInstance.data.datasets[0].data = stats.history;
            chartInstance.update();

        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    }
});
