const formData = {
    type_bien: '',
    ville: '',
    quartier: '',
    surface: '',
    nombre_de_chambres: '',
    nombre_de_salles_de_bain: '',
    etage: 0,
    terrasse: 0,
    garage: 0,
    ascenseur: 0,
    piscine: 0,
    securite: 0
};

let currentStep = 1;

// Ces données seront chargées depuis data.js
let typeFeatures = {};
let typesAvecEtage = [];
let typesSansChambres = [];

// Charger les données depuis DATA
if (typeof DATA !== 'undefined') {
    typeFeatures = DATA.type_features || {};
    typesAvecEtage = DATA.types_avec_etage || [];
    typesSansChambres = DATA.types_sans_chambres || [];
}

const featureLabels = {
    'etage': 'Étage',
    'ascenseur': 'Ascenseur',
    'terrasse': 'Terrasse',
    'garage': 'Garage',
    'securite': 'Sécurité',
    'piscine': 'Piscine'
};

// Vérifier que DATA est chargé
if (typeof DATA === 'undefined') {
    document.getElementById('error-container').innerHTML = 
        '<div class="error-msg">⚠️ Erreur: Le fichier data.js n\'a pas été trouvé. Exécutez d\'abord le script extract_data.py</div>';
}

// Charger les villes
function loadVilles() {
    if (typeof DATA === 'undefined') return;
    
    const villeSelect = document.getElementById('ville');
    villeSelect.innerHTML = '<option value="">Sélectionnez une ville</option>';
    
    DATA.villes.forEach(ville => {
        const opt = document.createElement('option');
        opt.value = ville;
        opt.textContent = ville;
        villeSelect.appendChild(opt);
    });
}

function loadQuartiers() {
    const ville = document.getElementById('ville').value;
    formData.ville = ville;
    
    const quartierSelect = document.getElementById('quartier');
    quartierSelect.innerHTML = '<option value="">Sélectionnez un quartier</option>';
    
    if (!ville || typeof DATA === 'undefined') {
        validateStep2();
        return;
    }
    
    const quartiers = DATA.quartiers_par_ville[ville] || [];
    
    if (quartiers.length === 0) {
        quartierSelect.innerHTML = '<option value="">Aucun quartier disponible</option>';
    } else {
        quartiers.forEach(quartier => {
            const opt = document.createElement('option');
            opt.value = quartier;
            opt.textContent = quartier;
            quartierSelect.appendChild(opt);
        });
    }
    
    validateStep2();
}

// Sélection du type de bien
document.querySelectorAll('.type-card').forEach(card => {
    card.addEventListener('click', function() {
        document.querySelectorAll('.type-card').forEach(c => c.classList.remove('selected'));
        this.classList.add('selected');
        formData.type_bien = this.dataset.type;
        document.getElementById('nextBtn1').disabled = false;
    });
});

// Validation des étapes
function validateStep2() {
    const ville = document.getElementById('ville').value;
    const quartier = document.getElementById('quartier').value;
    const valid = ville && quartier;
    document.getElementById('nextBtn2').disabled = !valid;
    if (valid) {
        formData.ville = ville;
        formData.quartier = quartier;
    }
}

function validateStep3() {
    const sansChambres = typesSansChambres.includes(formData.type_bien);
    const surface = document.getElementById('surface').value;
    
    let valid = surface;
    
    if (sansChambres) {
        // Pour les types sans chambres, seule la surface est requise
        formData.surface = parseFloat(surface);
        formData.nombre_de_chambres = 0;
        formData.nombre_de_salles_de_bain = 0;
    } else {
        // Pour les autres types, tous les champs sont requis
        const chambres = document.getElementById('nombre_de_chambres').value;
        const salles = document.getElementById('nombre_de_salles_de_bain').value;
        
        valid = surface && chambres && salles;
        
        if (valid) {
            formData.surface = parseFloat(surface);
            formData.nombre_de_chambres = parseInt(chambres);
            formData.nombre_de_salles_de_bain = parseInt(salles);
        }
    }
    
    document.getElementById('nextBtn3').disabled = !valid;
}

document.getElementById('surface').addEventListener('input', validateStep3);
document.getElementById('nombre_de_chambres').addEventListener('input', validateStep3);
document.getElementById('nombre_de_salles_de_bain').addEventListener('input', validateStep3);

function nextStep() {
    if (currentStep === 1) {
        setupCaracteristiques();
    }
    if (currentStep === 3) {
        setupEquipements();
    }
    
    document.getElementById(`section${currentStep}`).classList.remove('active');
    document.getElementById(`step${currentStep}`).classList.remove('active');
    document.getElementById(`step${currentStep}`).classList.add('completed');
    
    currentStep++;
    
    document.getElementById(`section${currentStep}`).classList.add('active');
    document.getElementById(`step${currentStep}`).classList.add('active');
}

function setupCaracteristiques() {
    const sansChambres = typesSansChambres.includes(formData.type_bien);
    
    // Masquer/afficher les champs selon le type de bien
    document.getElementById('chambresGroup').style.display = sansChambres ? 'none' : 'block';
    document.getElementById('sallesGroup').style.display = sansChambres ? 'none' : 'block';
    
    // Si c'est un type sans chambres, mettre des valeurs par défaut
    if (sansChambres) {
        formData.nombre_de_chambres = 0;
        formData.nombre_de_salles_de_bain = 0;
    }
}

function prevStep() {
    document.getElementById(`section${currentStep}`).classList.remove('active');
    document.getElementById(`step${currentStep}`).classList.remove('active');
    
    currentStep--;
    
    document.getElementById(`section${currentStep}`).classList.add('active');
    document.getElementById(`step${currentStep - 1}`).classList.remove('completed');
}

function setupEquipements() {
    const equipDiv = document.getElementById('equipements');
    equipDiv.innerHTML = '';
    
    const features = typeFeatures[formData.type_bien] || [];
    const hasEtage = typesAvecEtage.includes(formData.type_bien);
    
    // Ajouter le champ Étage si nécessaire
    if (hasEtage) {
        const etageGroup = document.createElement('div');
        etageGroup.className = 'form-group';
        const etageLabel = document.createElement('label');
        etageLabel.textContent = 'Numéro d\'étage';
        const etageInput = document.createElement('input');
        etageInput.type = 'number';
        etageInput.id = 'etageInput';
        etageInput.min = '0';
        etageInput.placeholder = 'Ex: 3';
        etageInput.value = '0';
        etageInput.oninput = () => formData.etage = parseInt(etageInput.value) || 0;
        etageGroup.appendChild(etageLabel);
        etageGroup.appendChild(etageInput);
        equipDiv.appendChild(etageGroup);
        formData.etage = 0;
    }
    
    if (features.length === 0 && !hasEtage) {
        equipDiv.innerHTML = '<p style="text-align: center; color: #666;">Aucun équipement supplémentaire pour ce type de bien.</p>';
        return;
    }
    
    // Ajouter les autres équipements (Oui/Non)
    features.forEach(feature => {
        const group = document.createElement('div');
        group.className = 'form-group';
        
        const label = document.createElement('label');
        label.textContent = featureLabels[feature];
        
        const btnGroup = document.createElement('div');
        btnGroup.className = 'boolean-group';
        
        const btnOui = document.createElement('button');
        btnOui.className = 'boolean-btn';
        btnOui.textContent = 'Oui';
        btnOui.type = 'button';
        btnOui.onclick = () => selectBoolean(feature, 1, btnOui, btnNon);
        
        const btnNon = document.createElement('button');
        btnNon.className = 'boolean-btn selected';
        btnNon.textContent = 'Non';
        btnNon.type = 'button';
        btnNon.onclick = () => selectBoolean(feature, 0, btnNon, btnOui);
        
        btnGroup.appendChild(btnOui);
        btnGroup.appendChild(btnNon);
        
        group.appendChild(label);
        group.appendChild(btnGroup);
        equipDiv.appendChild(group);
        
        formData[feature] = 0;
    });
}

function selectBoolean(feature, value, btn1, btn2) {
    btn1.classList.add('selected');
    btn2.classList.remove('selected');
    formData[feature] = value;
}

async function predict() {
    document.getElementById('section4').style.display = 'none';
    document.getElementById('loading').classList.remove('hidden');
    
    try {
        const response = await fetch('http://localhost:8000/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('priceDisplay').textContent = data.formatted_price;
        document.getElementById('result').classList.add('active');
    } catch (error) {
        document.getElementById('loading').classList.add('hidden');
        alert('❌ Erreur lors de la prédiction.\n\nAssurez-vous que :\n1. Votre API FastAPI est lancée (uvicorn main:app --reload)\n2. L\'API tourne sur http://localhost:8000\n3. CORS est configuré dans main.py\n\nErreur: ' + error.message);
        document.getElementById('section4').style.display = 'block';
    }
}

function reset() {
    location.reload();
}

// Initialisation
loadVilles();