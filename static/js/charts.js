/**
 * JobLens — Chart & Dashboard JavaScript
 * ==========================================
 * Handles all Plotly.js chart rendering for the dashboard.
 * Uses the dark theme consistent with the CSS design system.
 */

// ─── Plotly Dark Theme Layout ────────────────────────────────────
const PLOTLY_DARK_LAYOUT = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#a0a0c0', family: 'Inter, sans-serif', size: 12 },
    margin: { t: 40, r: 20, b: 50, l: 60 },
    xaxis: {
        gridcolor: 'rgba(255,255,255,0.05)',
        linecolor: 'rgba(255,255,255,0.1)',
        zerolinecolor: 'rgba(255,255,255,0.1)'
    },
    yaxis: {
        gridcolor: 'rgba(255,255,255,0.05)',
        linecolor: 'rgba(255,255,255,0.1)',
        zerolinecolor: 'rgba(255,255,255,0.1)'
    },
    colorway: ['#6c5ce7', '#00cec9', '#a29bfe', '#81ecec', '#74b9ff',
               '#00b894', '#fdcb6e', '#e17055', '#fab1a0', '#55efc4'],
    hoverlabel: {
        bgcolor: '#1a1a3e',
        bordercolor: '#6c5ce7',
        font: { color: '#f0f0f8', family: 'Inter, sans-serif' }
    }
};

const PLOTLY_CONFIG = {
    responsive: true,
    displayModeBar: false
};

// ─── Fetch Market Stats & Render Charts ──────────────────────────
async function loadDashboardCharts() {
    try {
        const response = await fetch('/api/market-stats');
        const data = await response.json();

        if (data.error) {
            console.error('API Error:', data.error);
            return;
        }

        renderSkillsChart(data.top_skills);
        renderSalaryChart(data.salary_by_role);
        renderCityChart(data.jobs_by_city);
        renderCompanyChart(data.top_companies);
        renderTrendChart(data.skill_trends);
        updateMetricCards(data.summary);
        renderRecentJobs(data.recent_jobs);

    } catch (error) {
        console.error('Failed to load dashboard data:', error);
    }
}

// ─── Top Skills Bar Chart ────────────────────────────────────────
function renderSkillsChart(skillsData) {
    if (!skillsData || !document.getElementById('skillsChart')) return;

    const skills = skillsData.map(s => s.skill);
    const counts = skillsData.map(s => s.count);

    const trace = {
        x: counts, y: skills,
        type: 'bar', orientation: 'h',
        marker: {
            color: counts.map((_, i) => {
                const ratio = i / counts.length;
                return `rgba(${108 + ratio * 50}, ${92 + ratio * 100}, ${231 - ratio * 30}, 0.85)`;
            }),
            line: { width: 0 },
            cornerradius: 4
        },
        hovertemplate: '<b>%{y}</b><br>Mentioned in %{x} jobs<extra></extra>'
    };

    const layout = {
        ...PLOTLY_DARK_LAYOUT,
        title: { text: 'Top 10 Most Demanded Skills', font: { size: 14, color: '#f0f0f8' } },
        yaxis: { ...PLOTLY_DARK_LAYOUT.yaxis, autorange: 'reversed' },
        margin: { t: 40, r: 20, b: 30, l: 120 }
    };

    Plotly.newPlot('skillsChart', [trace], layout, PLOTLY_CONFIG);
}

// ─── Salary by Role Bar Chart ────────────────────────────────────
function renderSalaryChart(salaryData) {
    if (!salaryData || !document.getElementById('salaryChart')) return;

    const roles = salaryData.map(s => s.role);
    const salaries = salaryData.map(s => s.avg_salary);

    const trace = {
        x: roles, y: salaries,
        type: 'bar',
        marker: {
            color: 'rgba(0, 206, 201, 0.8)',
            line: { width: 0 },
            cornerradius: 4
        },
        hovertemplate: '<b>%{x}</b><br>Avg Salary: ₹%{y:.1f} LPA<extra></extra>'
    };

    const layout = {
        ...PLOTLY_DARK_LAYOUT,
        title: { text: 'Average Salary by Role (LPA)', font: { size: 14, color: '#f0f0f8' } },
        yaxis: { ...PLOTLY_DARK_LAYOUT.yaxis, title: { text: 'Salary (LPA)', font: { size: 11 } } },
        margin: { t: 40, r: 20, b: 80, l: 60 },
        xaxis: { ...PLOTLY_DARK_LAYOUT.xaxis, tickangle: -30 }
    };

    Plotly.newPlot('salaryChart', [trace], layout, PLOTLY_CONFIG);
}

// ─── Jobs by City Pie Chart ──────────────────────────────────────
function renderCityChart(cityData) {
    if (!cityData || !document.getElementById('cityChart')) return;

    const trace = {
        labels: cityData.map(c => c.city),
        values: cityData.map(c => c.count),
        type: 'pie',
        hole: 0.5,
        marker: {
            colors: ['#6c5ce7', '#00cec9', '#a29bfe', '#81ecec', '#74b9ff',
                     '#00b894', '#fdcb6e', '#e17055', '#fab1a0', '#55efc4',
                     '#636e72', '#b2bec3', '#dfe6e9', '#2d3436']
        },
        textinfo: 'label+percent',
        textfont: { color: '#f0f0f8', size: 11 },
        hovertemplate: '<b>%{label}</b><br>%{value} jobs (%{percent})<extra></extra>'
    };

    const layout = {
        ...PLOTLY_DARK_LAYOUT,
        title: { text: 'Jobs by City', font: { size: 14, color: '#f0f0f8' } },
        showlegend: false,
        margin: { t: 40, r: 10, b: 10, l: 10 }
    };

    Plotly.newPlot('cityChart', [trace], layout, PLOTLY_CONFIG);
}

// ─── Top Companies Bar Chart ─────────────────────────────────────
function renderCompanyChart(companyData) {
    if (!companyData || !document.getElementById('companyChart')) return;

    const companies = companyData.map(c => c.company);
    const counts = companyData.map(c => c.count);

    const trace = {
        x: counts, y: companies,
        type: 'bar', orientation: 'h',
        marker: {
            color: 'rgba(162, 155, 254, 0.8)',
            cornerradius: 4
        },
        hovertemplate: '<b>%{y}</b><br>%{x} openings<extra></extra>'
    };

    const layout = {
        ...PLOTLY_DARK_LAYOUT,
        title: { text: 'Top Hiring Companies', font: { size: 14, color: '#f0f0f8' } },
        yaxis: { ...PLOTLY_DARK_LAYOUT.yaxis, autorange: 'reversed' },
        margin: { t: 40, r: 20, b: 30, l: 130 }
    };

    Plotly.newPlot('companyChart', [trace], layout, PLOTLY_CONFIG);
}

// ─── Skill Trend Line Chart ─────────────────────────────────────
function renderTrendChart(trendData) {
    if (!trendData || !document.getElementById('trendChart')) return;

    const traces = [];
    const colors = ['#6c5ce7', '#00cec9', '#a29bfe', '#81ecec', '#74b9ff',
                    '#00b894', '#fdcb6e', '#e17055', '#fab1a0', '#55efc4'];

    let i = 0;
    for (const [skill, data] of Object.entries(trendData.skills || {})) {
        traces.push({
            x: trendData.weeks,
            y: data.counts,
            name: skill,
            type: 'scatter', mode: 'lines+markers',
            line: { color: colors[i % colors.length], width: 2 },
            marker: { size: 4 },
            hovertemplate: `<b>${skill}</b><br>Week: %{x}<br>Count: %{y}<extra></extra>`
        });
        i++;
        if (i >= 10) break;
    }

    const layout = {
        ...PLOTLY_DARK_LAYOUT,
        title: { text: 'Skill Demand Trends Over Time', font: { size: 14, color: '#f0f0f8' } },
        legend: { font: { size: 10 }, bgcolor: 'rgba(0,0,0,0)' },
        margin: { t: 40, r: 20, b: 50, l: 50 }
    };

    Plotly.newPlot('trendChart', traces, layout, PLOTLY_CONFIG);
}

// ─── Update Metric Cards ─────────────────────────────────────────
function updateMetricCards(summary) {
    if (!summary) return;
    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    set('totalJobs', summary.total_jobs?.toLocaleString() || '0');
    set('avgSalary', `₹${summary.avg_salary?.toFixed(1) || '0'} LPA`);
    set('topSkill', summary.top_skill || 'N/A');
    set('topCity', summary.top_city || 'N/A');
}

// ─── Render Recent Jobs Table ────────────────────────────────────
function renderRecentJobs(jobs) {
    const tbody = document.getElementById('recentJobsBody');
    if (!tbody || !jobs) return;

    tbody.innerHTML = jobs.map(job => `
        <tr>
            <td style="color:#f0f0f8;font-weight:600">${job.job_title}</td>
            <td>${job.company_name}</td>
            <td>${job.location}</td>
            <td>${job.salary_range}</td>
            <td>${job.experience_required || 'N/A'}</td>
            <td><small>${job.date_posted || 'N/A'}</small></td>
        </tr>
    `).join('');
}

// ─── Upload Zone Drag & Drop ─────────────────────────────────────
function initUploadZone() {
    const zone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('resumeFile');
    if (!zone || !fileInput) return;

    zone.addEventListener('click', () => fileInput.click());

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
    });

    zone.addEventListener('dragleave', () => {
        zone.classList.remove('dragover');
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            updateFileLabel(e.dataTransfer.files[0].name);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) {
            updateFileLabel(fileInput.files[0].name);
        }
    });
}

function updateFileLabel(filename) {
    const label = document.getElementById('fileLabel');
    if (label) {
        label.innerHTML = `<i class="bi bi-file-earmark-check"></i> ${filename}`;
        label.style.color = '#00b894';
    }
}

// ─── Initialize on page load ─────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('skillsChart')) loadDashboardCharts();
    if (document.getElementById('uploadZone')) initUploadZone();
});
