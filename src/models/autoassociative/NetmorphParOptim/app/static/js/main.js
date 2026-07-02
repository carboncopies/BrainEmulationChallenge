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
    const featureMap = {
        'days': 'days',
        'pyramidal': 'pyramidal',
        'minneuronseparation': 'minneuronseparation',
        'shape-radius': 'shape.radius',
        'shape-thickness': 'shape.thickness',
        'dm-weight': 'dm.weight'
    };

    const reverseFeatureMap = {
        'days': 'days',
        'pyramidal': 'pyramidal',
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
            features_to_vary
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

                // Populate results table
                resultsTableBody.innerHTML = '';
                
                if (data.counterfactuals.length === 0) {
                    resultsTableBody.innerHTML = '<tr><td colspan="9" style="text-align: center;">No counterfactuals found matching the criteria. Try expanding permitted ranges or adjusting desired output.</td></tr>';
                } else {
                    data.counterfactuals.forEach((cf, idx) => {
                        const tr = document.createElement('tr');
                        
                        // Compare each feature to see if it changed
                        const cells = [
                            `<td>${idx + 1}</td>`,
                            formatCell('days', cf.days),
                            formatCell('pyramidal', cf.pyramidal),
                            formatCell('minneuronseparation', cf.minneuronseparation),
                            formatCell('shape.radius', cf['shape.radius']),
                            formatCell('shape.thickness', cf['shape.thickness']),
                            formatCell('dm.weight', cf['dm.weight']),
                            `<td>${cf.pred_median.toFixed(2)}</td>`,
                            `<td>${cf.pred_lower.toFixed(2)}</td>`
                        ];
                        
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
        // Use epsilon tolerance for float comparison
        const isChanged = Math.abs(queryVal - val) > 1e-5;
        const displayVal = (featureKey === 'shape.thickness' || featureKey === 'dm.weight') ? val.toFixed(3) : Math.round(val);
        
        if (isChanged) {
            return `<td class="cell-changed" title="Baseline: ${queryVal}">${displayVal}</td>`;
        }
        return `<td>${displayVal}</td>`;
    }
});
