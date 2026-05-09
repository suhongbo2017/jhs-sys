document.addEventListener('DOMContentLoaded', () => {
    // Initial State
    const state = {
        width: 40,
        height: 40,
        shape: 'circle',
        scale: 0.8,
        month: 'JAN',
        monthPos: 'center',
        monthFontSize: 150,
        monthColor: '#000000',
        year: '2026',
        yearPos: 'bottom',
        yearFontSize: 50,
        yearColor: '#000000',
        shapeColor: '#1e293b',
        gridRows: 1,
        gridCols: 1,
        gridSpacing: 5,
        paperWidth: 'auto',
        paperHeight: 'auto'
    };

    // DOM Elements
    const svg = document.getElementById('tag-svg');
    const previewGroup = document.getElementById('preview-group');
    const canvasWrapper = document.getElementById('canvas-wrapper');
    const shapeScaleInput = document.getElementById('shape-scale');
    const shapeSizeVal = document.getElementById('shape-size-val');
    const monthInput = document.getElementById('month-input');
    const monthPos = document.getElementById('month-pos');
    const monthFontSize = document.getElementById('month-font-size');
    const monthColor = document.getElementById('month-color');
    const yearInput = document.getElementById('year-input');
    const yearPos = document.getElementById('year-pos');
    const yearFontSize = document.getElementById('year-font-size');
    const yearColor = document.getElementById('year-color');
    const shapeColor = document.getElementById('shape-color');
    const gridRowsInput = document.getElementById('grid-rows');
    const gridColsInput = document.getElementById('grid-cols');
    const gridSpacingInput = document.getElementById('grid-spacing');

    function updatePreview() {
        previewGroup.innerHTML = '';

        // Browser standard: 1mm = 96/25.4 px
        const PPM = 96 / 25.4; 
        
        const unitWidth = state.width * PPM;
        const unitHeight = state.height * PPM;
        const spacingPx = state.gridSpacing * PPM;
        
        const gridW = state.gridCols * unitWidth + (state.gridCols - 1) * spacingPx;
        const gridH = state.gridRows * unitHeight + (state.gridRows - 1) * spacingPx;
        
        let canvasW, canvasH, paperW_mm, paperH_mm;
        if (state.paperWidth === 'auto') {
            canvasW = gridW;
            canvasH = gridH;
            paperW_mm = state.width * state.gridCols + state.gridSpacing * (state.gridCols - 1);
            paperH_mm = state.height * state.gridRows + state.gridSpacing * (state.gridRows - 1);
        } else {
            canvasW = state.paperWidth * PPM;
            canvasH = state.paperHeight * PPM;
            paperW_mm = state.paperWidth;
            paperH_mm = state.paperHeight;
        }

        // Apply scaling for display fit
        const maxDisplayWidth = window.innerWidth - 450; 
        const maxDisplayHeight = window.innerHeight - 150;
        const scaleFit = Math.min(1, maxDisplayWidth / canvasW, maxDisplayHeight / canvasH);

        canvasWrapper.style.width = `${paperW_mm}mm`;
        canvasWrapper.style.height = `${paperH_mm}mm`;
        canvasWrapper.style.transform = `scale(${scaleFit})`;
        canvasWrapper.style.transformOrigin = 'center';

        svg.setAttribute('width', canvasW);
        svg.setAttribute('height', canvasH);
        svg.setAttribute('viewBox', `0 0 ${canvasW} ${canvasH}`);

        // Paper Bg
        const paperBg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        paperBg.setAttribute('width', canvasW); paperBg.setAttribute('height', canvasH);
        paperBg.setAttribute('fill', '#ffffff');
        paperBg.setAttribute('stroke', '#cbd5e1');
        paperBg.setAttribute('stroke-width', '0.5');
        previewGroup.appendChild(paperBg);

        const startX = (canvasW - gridW) / 2;
        const startY = (canvasH - gridH) / 2;

        for (let r = 0; r < state.gridRows; r++) {
            for (let c = 0; c < state.gridCols; c++) {
                const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
                const offsetX = startX + c * (unitWidth + spacingPx);
                const offsetY = startY + r * (unitHeight + spacingPx);
                
                const unitScale = (unitWidth / 400); 
                g.setAttribute('transform', `translate(${offsetX}, ${offsetY}) scale(${unitScale})`);
                
                // Debug border (dashed)
                const border = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                border.setAttribute('width', 400);
                border.setAttribute('height', 400 * (state.height / state.width));
                border.setAttribute('fill', 'none');
                border.setAttribute('stroke', '#cbd5e1');
                border.setAttribute('stroke-width', 1);
                border.setAttribute('stroke-dasharray', '4,4');
                border.style.opacity = '0.4';
                g.appendChild(border);

                renderUnit(g, 400, 400 * (state.height / state.width));
                previewGroup.appendChild(g);
            }
        }
    }

    function renderUnit(container, uWidth, uHeight) {
        const centerX = uWidth / 2;
        const centerY = uHeight / 2;
        const maxShapeDim = uWidth * state.scale;
        let sW, sH;

        if (state.shape === 'circle' || state.shape === 'square') {
            sW = sH = maxShapeDim;
        } else {
            const ratio = state.width / state.height;
            if (ratio > 1) { sW = maxShapeDim; sH = maxShapeDim / ratio; }
            else { sH = maxShapeDim; sW = maxShapeDim * ratio; }
        }

        let shapeEl;
        if (state.shape === 'circle') {
            shapeEl = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            shapeEl.setAttribute('cx', centerX); shapeEl.setAttribute('cy', centerY); shapeEl.setAttribute('r', sW / 2);
        } else if (state.shape === 'ellipse') {
            shapeEl = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
            shapeEl.setAttribute('cx', centerX); shapeEl.setAttribute('cy', centerY); shapeEl.setAttribute('rx', sW / 2); shapeEl.setAttribute('ry', sH / 2);
        } else {
            shapeEl = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
            shapeEl.setAttribute('x', centerX - sW / 2); shapeEl.setAttribute('y', centerY - sH / 2); shapeEl.setAttribute('width', sW); shapeEl.setAttribute('height', sH); shapeEl.setAttribute('rx', 4);
        }
        shapeEl.setAttribute('fill', state.shapeColor);
        shapeEl.setAttribute('stroke', state.shapeColor);
        container.appendChild(shapeEl);

        const getCoords = (pos, sw, sh) => {
            switch (pos) {
                case 'center': return { x: centerX, y: centerY };
                case 'top': return { x: centerX, y: centerY - sh / 4 };
                case 'bottom': return { x: centerX, y: centerY + sh / 4 };
                case 'left': return { x: centerX - sw / 4, y: centerY };
                case 'right': return { x: centerX + sw / 4, y: centerY };
                default: return { x: centerX, y: centerY };
            }
        };

        const mText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        const mC = getCoords(state.monthPos, sW, sH);
        mText.setAttribute('x', mC.x); mText.setAttribute('y', mC.y);
        mText.setAttribute('text-anchor', 'middle'); mText.setAttribute('dominant-baseline', 'middle');
        mText.setAttribute('font-size', state.monthFontSize); mText.setAttribute('font-weight', '600');
        mText.setAttribute('fill', state.monthColor);
        mText.setAttribute('stroke', state.monthColor); // Match outline with font color
        mText.setAttribute('stroke-width', '1');
        mText.textContent = state.month;
        container.appendChild(mText);

        const yText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        const yC = getCoords(state.yearPos, sW, sH);
        yText.setAttribute('x', yC.x); yText.setAttribute('y', yC.y);
        yText.setAttribute('text-anchor', 'middle'); yText.setAttribute('dominant-baseline', 'middle');
        yText.setAttribute('font-size', state.yearFontSize);
        yText.setAttribute('fill', state.yearColor);
        yText.setAttribute('stroke', state.yearColor); // Match outline with font color
        yText.setAttribute('stroke-width', '0.5');
        yText.textContent = state.year;
        container.appendChild(yText);
    }

    // Event Listeners
    document.querySelectorAll('.size-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.size-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.width = parseInt(btn.dataset.width);
            state.height = parseInt(btn.dataset.height);
            updatePreview();
        });
    });

    document.querySelectorAll('.shape-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.shape-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.shape = btn.dataset.shape;
            updatePreview();
        });
    });

    shapeScaleInput.addEventListener('input', (e) => {
        state.scale = e.target.value / 100;
        shapeSizeVal.textContent = `${e.target.value}%`;
        updatePreview();
    });

    monthInput.addEventListener('input', (e) => {
        state.month = e.target.value;
        updatePreview();
    });

    monthPos.addEventListener('change', (e) => {
        state.monthPos = e.target.value;
        updatePreview();
    });

    monthFontSize.addEventListener('input', (e) => {
        state.monthFontSize = parseInt(e.target.value) || 24;
        updatePreview();
    });

    yearInput.addEventListener('input', (e) => {
        state.year = e.target.value;
        updatePreview();
    });

    yearPos.addEventListener('change', (e) => {
        state.yearPos = e.target.value;
        updatePreview();
    });

    yearFontSize.addEventListener('input', (e) => {
        state.yearFontSize = parseInt(e.target.value) || 16;
        updatePreview();
    });

    monthColor.addEventListener('input', (e) => {
        state.monthColor = e.target.value;
        updatePreview();
    });

    yearColor.addEventListener('input', (e) => {
        state.yearColor = e.target.value;
        updatePreview();
    });

    shapeColor.addEventListener('input', (e) => {
        state.shapeColor = e.target.value;
        // Update custom chip background if it's the active one
        document.getElementById('custom-color-trigger').style.background = e.target.value;
        updatePreview();
    });

    // Color Palette Logic
    const chips = document.querySelectorAll('.color-chip');
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            if (chip.id === 'custom-color-trigger') {
                shapeColor.click(); // Trigger hidden color input
                return;
            }
            
            chips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            
            state.shapeColor = chip.dataset.color;
            updatePreview();
        });
    });

    gridRowsInput.addEventListener('input', (e) => {
        state.gridRows = parseInt(e.target.value) || 1;
        updatePreview();
    });

    gridColsInput.addEventListener('input', (e) => {
        state.gridCols = parseInt(e.target.value) || 1;
        updatePreview();
    });

    gridSpacingInput.addEventListener('input', (e) => {
        state.gridSpacing = parseInt(e.target.value) || 0;
        updatePreview();
    });

    document.querySelectorAll('.paper-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.paper-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            if (btn.dataset.width === 'auto') {
                state.paperWidth = 'auto';
                state.paperHeight = 'auto';
            } else {
                state.paperWidth = parseInt(btn.dataset.width);
                state.paperHeight = parseInt(btn.dataset.height);
            }
            updatePreview();
        });
    });

    document.getElementById('print-btn').addEventListener('click', () => {
        window.print();
    });

    // Initialize
    updatePreview();
});
