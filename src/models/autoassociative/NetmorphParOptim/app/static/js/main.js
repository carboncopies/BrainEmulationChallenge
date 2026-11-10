document.addEventListener('DOMContentLoaded', () => {
    // Form and button elements
    const diceForm = document.getElementById('dice-form');
    const btnSubmit = document.getElementById('btn-submit');
    const btnRandomInstance = document.getElementById('btn-random-instance');

    // State panels
    const panelLoading = document.getElementById('loading');
    const panelPlaceholder = document.getElementById('placeholder');
    const panelError = document.getElementById('error-container');
    const errorMessage = document.getElementById('error-message');
    const panelResults = document.getElementById('results-output');

    // Metrics and tables
    const queryPredMedian = document.getElementById('query-pred-median');
    const queryPredLower = document.getElementById('query-pred-lower');
    const resultsTableBody = document.querySelector('#results-table tbody');

    // Global reference for current query instance (to check for changes)
    let currentQueryInstance = {};

    // Map frontend feature IDs to backend names
    const allFeatureMap = {
        'days': 'days',
        'pyramidal': 'pyramidal',
        'interneuron': 'interneuron',
        'minneuronseparation': 'minneuronseparation',
        'shape-radius': 'shape.radius',
        'shape-thickness': 'shape.thickness',
        'dm-weight': 'dm.weight'
    };

    let featureMap = Object.assign({}, allFeatureMap);
    let targetList = [];
    let activeTargets = [];
    let isSynthetic = false;
    const reverseFeatureMap = {
        'days': 'days',
        'pyramidal': 'pyramidal',
        'interneuron': 'interneuron',
        'minneuronseparation': 'minneuronseparation',
        'shape.radius': 'shape-radius',
        'shape.thickness': 'shape-thickness',
        'dm.weight': 'dm-weight'
    };

    // Load default values and random instance on startup
    fetchDefaults();

    // Event listener for Random Instance button
    btnRandomInstance.addEventListener('click', (e) => {
        e.preventDefault();
        fetchDefaults();
    });

    // Form submission
    diceForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await generateCounterfactuals();
    });

    // Function to fetch defaults and pre-populate
    async function fetchDefaults() {
        try {
            btnRandomInstance.disabled = true;
            btnRandomInstance.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Loading...';
            
            const response = await fetch('/api/default_values');
            const data = await response.json();
            
            if (response.ok) {
                currentQueryInstance = data.query_instance;
                setupFeatures(data.features || Object.values(allFeatureMap));
                setupTargets(data.targets || [], data.synthetic);
                
                // Populate query inputs
                for (const [key, value] of Object.entries(currentQueryInstance)) {
                    const elementId = `q-${reverseFeatureMap[key]}`;
                    const element = document.getElementById(elementId);
                    if (element) {
                        element.value = value;
                    }
                }
                
                // Populate optimizer settings
                document.getElementById('threshold').value = data.threshold;
                document.getElementById('desired-min').value = data.desired_range[0];
                document.getElementById('desired-max').value = data.desired_range[1];
                
                // Populate permitted ranges
                for (const [key, range] of Object.entries(data.permitted_ranges)) {
                    const minId = `range-min-${reverseFeatureMap[key]}`;
                    const maxId = `range-max-${reverseFeatureMap[key]}`;
                    const minEl = document.getElementById(minId);
                    const maxEl = document.getElementById(maxId);
                    if (minEl) minEl.value = range[0];
                    if (maxEl) maxEl.value = range[1];
                }
            } else {
                console.error("Failed to load default values");
            }
        } catch (err) {
            console.error("Error fetching default values:", err);
        } finally {
            btnRandomInstance.disabled = false;
            btnRandomInstance.innerHTML = '<i class="fa-solid fa-shuffle"></i> Random Sample';
        }
    }

    // Function to submit optimization task
    async function generateCounterfactuals() {
        // Show loading state
        panelPlaceholder.classList.add('hidden');
        panelError.classList.add('hidden');
        panelResults.classList.add('hidden');
        panelLoading.classList.remove('hidden');
        btnSubmit.disabled = true;
        btnSubmit.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';

        // Collect inputs
        const query_instance = {};
        for (const [key, fieldName] of Object.entries(featureMap)) {
            const inputVal = parseFloat(document.getElementById(`q-${key}`).value);
            query_instance[fieldName] = inputVal;
        }

        // Store query instance locally for difference comparison
        currentQueryInstance = query_instance;

        const total_CFs = parseInt(document.getElementById('total-cfs').value);
        const threshold = parseFloat(document.getElementById('threshold').value);
        const desired_range = [
            parseFloat(document.getElementById('desired-min').value),
            parseFloat(document.getElementById('desired-max').value)
        ];

        const permitted_range = {};
        const features_to_vary = [];

        for (const [key, fieldName] of Object.entries(featureMap)) {
            const minVal = parseFloat(document.getElementById(`range-min-${key}`).value);
            const maxVal = parseFloat(document.getElementById(`range-max-${key}`).value);
            permitted_range[fieldName] = [minVal, maxVal];

            const varyChecked = document.getElementById(`vary-${key}`).checked;
            if (varyChecked) {
                features_to_vary.push(fieldName);
            }
        }

        const payload = {
            query_instance,
            total_CFs,
            desired_range,
            threshold,
            permitted_range,
            features_to_vary,
            targets: collectTargets()
        };

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Populate query prediction values
                queryPredMedian.textContent = data.query_predictions.median.toFixed(2);
                queryPredLower.textContent = data.query_predictions.lower.toFixed(2);

                // Populate results table (dynamic columns: features, then per-target pred, joint margin, bio)
                activeTargets = data.targets || [];
                const feats = data.features || Object.values(allFeatureMap);
                const thead = document.querySelector('#results-table thead');
                let hdr = '<tr><th>#</th>' + feats.map(f => `<th>${f}</th>`).join('');
                activeTargets.forEach(t => { hdr += `<th>${t}<br>median</th><th>${t}<br>lower 2.5%</th>`; });
                hdr += '<th>Joint margin</th><th>Bio (hard/soft)</th><th>Density /mm&sup3;</th></tr>';
                thead.innerHTML = hdr;
                resultsTableBody.innerHTML = '';
                if (data.synthetic) document.getElementById('synthetic-banner').classList.remove('hidden');
                if (data.counterfactuals.length === 0) {
                    resultsTableBody.innerHTML = `<tr><td colspan="${feats.length + 2 * activeTargets.length + 4}" style="text-align: center;">No counterfactuals found satisfying all targets and biological constraints. Relax thresholds or widen permitted ranges.</td></tr>`;
                } else {
                    data.counterfactuals.forEach((cf, idx) => {
                        const tr = document.createElement('tr');
                        let cells = [`<td>${idx + 1}</td>`];
                        feats.forEach(f => cells.push(formatCell(f, cf[f])));
                        activeTargets.forEach(t => {
                            cells.push(`<td>${cf[t + '__pred_median'].toFixed(1)}</td>`);
                            cells.push(`<td>${cf[t + '__pred_lower'].toFixed(1)}</td>`);
                        });
                        cells.push(`<td>${cf.joint_margin.toFixed(2)}</td>`);
                        cells.push(`<td>${cf.bio_hard_violations}/${cf.bio_soft_violations}</td>`);
                        cells.push(`<td>${Math.round(cf.density_per_mm3)}</td>`);
                        tr.innerHTML = cells.join('');
                        resultsTableBody.appendChild(tr);
                    });
                }

                // Transition to results state
                panelLoading.classList.add('hidden');
                panelResults.classList.remove('hidden');
            } else {
                throw new Error(data.error || 'Failed to generate counterfactuals.');
            }
        } catch (err) {
            console.error("Error generating counterfactuals:", err);
            errorMessage.textContent = err.message || 'An error occurred while generating counterfactual explanations.';
            panelLoading.classList.add('hidden');
            panelError.classList.remove('hidden');
        } finally {
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Generate Counterfactuals';
        }
    }

    // Helper function to format cell and apply highlighting if changed
    function formatCell(featureKey, val) {
        const queryVal = currentQueryInstance[featureKey];
        if (val === undefined) return '<td>-</td>';
        // Use epsilon tolerance for float comparison
        const isChanged = Math.abs(queryVal - val) > 1e-5;
        const displayVal = (featureKey === 'dm.weight') ? val.toFixed(3) : Math.round(val);
        
        if (isChanged) {
            return `<td class="cell-changed" title="Baseline: ${queryVal}">${displayVal}</td>`;
        }
        return `<td>${displayVal}</td>`;
    }

    // Show/hide interneuron inputs depending on whether the dataset has that feature
    function setupFeatures(features) {
        featureMap = {};
        for (const [id, name] of Object.entries(allFeatureMap)) {
            if (features.includes(name)) featureMap[id] = name;
        }
        const has = features.includes('interneuron');
        document.getElementById('grp-q-interneuron').classList.toggle('hidden', !has);
        document.getElementById('row-interneuron').classList.toggle('hidden', !has);
        document.getElementById('q-interneuron').required = has;
        // The single threshold / desired range inputs are superseded by the targets table
        ['threshold', 'desired-min'].forEach(id => { document.getElementById(id).closest('.input-group').style.display = 'none'; });
    }

    // Build the targets table (checkbox + min + max per target)
    function setupTargets(targets, synthetic) {
        targetList = targets;
        isSynthetic = !!synthetic;
        document.getElementById('synthetic-banner').classList.toggle('hidden', !isSynthetic);
        const body = document.getElementById('targets-body');
        if (body.dataset.built === '1') return;   // keep user edits on "Random Sample"
        body.dataset.built = '1';
        body.innerHTML = '';
        targets.forEach(t => {
            const tr = document.createElement('tr');
            const r2 = (t.test_r2 === null || t.test_r2 === undefined) ? 'n/a' : t.test_r2.toFixed(2);
            tr.innerHTML = `<td><input type="checkbox" class="tgt-use" data-t="${t.name}" ${t.selected ? 'checked' : ''} ${t.trained ? '' : 'disabled'}></td>` +
                `<td><strong>${t.name}</strong><br><small>${t.label}${t.trained ? '' : ' - not trained (too few labels: ' + t.n_rows + ')'}</small></td>` +
                `<td><input type="number" class="tgt-min" data-t="${t.name}" value="${t.default.min}"></td>` +
                `<td><input type="number" class="tgt-max" data-t="${t.name}" value="${t.default.max === null ? '' : t.default.max}" placeholder="none"></td>` +
                `<td>${r2}</td>`;
            body.appendChild(tr);
        });
    }

    function collectTargets() {
        const out = {};
        document.querySelectorAll('.tgt-use').forEach(cb => {
            if (!cb.checked) return;
            const t = cb.dataset.t;
            const mn = parseFloat(document.querySelector(`.tgt-min[data-t="${t}"]`).value);
            const mxv = document.querySelector(`.tgt-max[data-t="${t}"]`).value;
            out[t] = { min: mn, max: mxv === '' ? null : parseFloat(mxv) };
        });
        return out;
    }
});
