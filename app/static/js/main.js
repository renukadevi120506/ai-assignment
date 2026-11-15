// Client-side interactions and dynamic UI controls

document.addEventListener("DOMContentLoaded", function () {
    // Show AI loading overlay on form submission if marked
    const evalForms = document.querySelectorAll(".eval-form");
    const overlay = document.getElementById("aiLoadingOverlay");

    evalForms.forEach((form) => {
        form.addEventListener("submit", function () {
            if (overlay) {
                overlay.style.display = "flex";
            }
        });
    });

    // Auto-calculate rubric criteria sum
    const updateRubricSum = () => {
        const markInputs = document.querySelectorAll(".criterion-max-input");
        let total = 0;
        markInputs.forEach((input) => {
            const val = parseFloat(input.value) || 0;
            total += val;
        });

        const sumDisplay = document.getElementById("rubricSumDisplay");
        const targetDisplay = document.getElementById("questionMaxTarget");
        if (sumDisplay) {
            sumDisplay.textContent = total.toFixed(1);
            if (targetDisplay) {
                const target = parseFloat(targetDisplay.getAttribute("data-target")) || 0;
                if (Math.abs(total - target) < 0.01) {
                    sumDisplay.className = "badge bg-success fs-6";
                } else {
                    sumDisplay.className = "badge bg-danger fs-6";
                }
            }
        }
    };

    const criteriaContainer = document.getElementById("criteriaContainer");
    if (criteriaContainer) {
        criteriaContainer.addEventListener("input", function (e) {
            if (e.target.classList.contains("criterion-max-input")) {
                updateRubricSum();
            }
        });
        updateRubricSum();
    }
});

// Dynamic Rubric row addition
function addRubricRow(name = "", maxMarks = 1.0, desc = "", concepts = "", keywords = "", guidelines = "") {
    const container = document.getElementById("criteriaContainer");
    if (!container) return;

    const row = document.createElement("div");
    row.className = "card mb-3 p-3 border criterion-row";
    row.innerHTML = `
        <div class="row g-2 align-items-center mb-2">
            <div class="col-md-7">
                <label class="form-label small fw-bold">Criterion Name</label>
                <input type="text" name="criterion_name[]" class="form-control" value="${name}" placeholder="e.g. Conceptual Definition" required>
            </div>
            <div class="col-md-3">
                <label class="form-label small fw-bold">Max Marks</label>
                <input type="number" step="0.5" min="0.5" name="maximum_marks[]" class="form-control criterion-max-input" value="${maxMarks}" required>
            </div>
            <div class="col-md-2 text-end pt-4">
                <button type="button" class="btn btn-outline-danger btn-sm" onclick="this.closest('.criterion-row').remove(); const evt = new Event('input', {bubbles:true}); document.getElementById('criteriaContainer').dispatchEvent(evt);">
                    <i class="bi bi-trash"></i> Remove
                </button>
            </div>
        </div>
        <div class="row g-2">
            <div class="col-md-6">
                <label class="form-label small">Criterion Description</label>
                <input type="text" name="criterion_description[]" class="form-control form-control-sm" value="${desc}" placeholder="Description of expectations">
            </div>
            <div class="col-md-6">
                <label class="form-label small">Expected Concepts</label>
                <input type="text" name="expected_concepts[]" class="form-control form-control-sm" value="${concepts}" placeholder="Key ideas required">
            </div>
            <div class="col-md-6">
                <label class="form-label small">Important Keywords (Optional)</label>
                <input type="text" name="important_keywords[]" class="form-control form-control-sm" value="${keywords}" placeholder="Comma separated terminology">
            </div>
            <div class="col-md-6">
                <label class="form-label small">Evaluation Guidelines</label>
                <input type="text" name="evaluation_guidelines[]" class="form-control form-control-sm" value="${guidelines}" placeholder="Scoring nuances">
            </div>
        </div>
    `;
    container.appendChild(row);
    row.querySelector(".criterion-max-input").dispatchEvent(new Event("input", { bubbles: true }));
}

// AI Generate Rubric AJAX
async function triggerAiRubricGeneration(questionText, totalMarks, endpointUrl) {
    const btn = document.getElementById("btnAiGenerateRubric");
    const spinner = document.getElementById("aiRubricSpinner");
    if (btn) btn.disabled = true;
    if (spinner) spinner.classList.remove("d-none");

    try {
        const response = await fetch(endpointUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question_text: questionText, total_marks: totalMarks })
        });
        const data = await response.json();
        if (data.success && data.rubric && data.rubric.criteria) {
            const container = document.getElementById("criteriaContainer");
            container.innerHTML = ""; // Clear existing
            data.rubric.criteria.forEach((c) => {
                addRubricRow(
                    c.criterion_name,
                    c.maximum_marks,
                    c.criterion_description || "",
                    c.expected_concepts || "",
                    c.important_keywords || "",
                    c.evaluation_guidelines || ""
                );
            });
            alert("AI Rubric criteria generated successfully! You can refine or save them.");
        } else {
            alert("Could not generate AI rubric: " + (data.error || "Unknown error"));
        }
    } catch (err) {
        alert("Failed to communicate with AI rubric generator: " + err);
    } finally {
        if (btn) btn.disabled = false;
        if (spinner) spinner.classList.add("d-none");
    }
}
