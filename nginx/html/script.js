function showSection(sectionName, documentId = null) {
    document.getElementById('querySection').classList.add('hidden');
    document.getElementById('collectionsSection').classList.add('hidden');
    document.getElementById('documentsSection').classList.add('hidden');
    document.getElementById('uploadFormSection').classList.add('hidden');
    document.getElementById('documentChunksSection').classList.add('hidden');
    document.getElementById(`${sectionName}Section`).classList.remove('hidden');

    // Update active menu item
    document.getElementById('queryLink').classList.remove('bg-gray-700');
    document.getElementById('collectionsLink').classList.remove('bg-gray-700');
    document.getElementById('documentsLink').classList.remove('bg-gray-700');

    if (sectionName === 'query') {
        document.getElementById('queryLink').classList.add('bg-gray-700');
        fetchCollectionsForDropdown();
    } else if (sectionName === 'collections') {
        document.getElementById('collectionsLink').classList.add('bg-gray-700');
        fetchCollections();
    } else if (sectionName === 'documents') {
        document.getElementById('documentsLink').classList.add('bg-gray-700');
        fetchDocuments();
    } else if (sectionName === 'documentChunks' && documentId) {
        document.getElementById('documentsLink').classList.add('bg-gray-700');
        fetchDocumentChunks(documentId);
    }

    console.log(`Showing section: ${sectionName}, Document ID: ${documentId}`);
}



async function performQuery(query, collection) {
    try {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query, collection }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const results = await response.json();
        const queryResultsList = document.getElementById('queryResultsList');
        queryResultsList.innerHTML = results.map(result => `
            <tr class="border-b border-gray-200 hover:bg-gray-100">
                <td class="py-3 px-6 text-left">${result.chunk_number}</td>
                <td class="py-3 px-6 text-left">${result.chunk_content.substring(0, 100)}...</td>
                <td class="py-3 px-6 text-left">${result.distance.toFixed(4)}</td>
                <td class="py-3 px-6 text-left">${result.document_filename}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error performing query:', error);
        showStatus('Error performing query. Please try again.', true);
    }
}

async function fetchDocumentChunks(documentId) {
    console.log(`Fetching chunks for document ID: ${documentId}`);
    try {
        const response = await fetch(`/api/documents/${documentId}/chunks`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Received chunks data:', data);
        const chunksList = document.getElementById('documentChunksList');
        const chunksDocumentTitle = document.getElementById('chunksDocumentTitle');
        
        chunksDocumentTitle.textContent = 'Document Chunks';
        document.getElementById('chunksDocumentFilename').textContent = data.filename;
        
        if (data.chunks.length === 0) {
            chunksList.innerHTML = `<tr><td colspan="4" class="px-4 py-3 text-gray-600">No chunks found for this document.</td></tr>`;
        } else {
            chunksList.innerHTML = data.chunks.map(chunk => `
                <tr class="border-b border-gray-200 hover:bg-gray-100">
                    <td class="py-3 px-6 text-left">${chunk.chunk_number}</td>
                    <td class="py-3 px-6 text-left">${chunk.chunk_start}...</td>
                    <td class="py-3 px-6 text-left">...${chunk.chunk_end}</td>
                    <td class="py-3 px-6 text-left">${chunk.embedding_preview.join(', ')}</td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Error fetching document chunks:', error);
        const chunksList = document.getElementById('documentChunksList');
        chunksList.innerHTML = `<tr><td colspan="4" class="px-4 py-3 text-red-600">Error loading chunks. Please try again later.</td></tr>`;
    }
}

function showNewCollectionPopup() {
    document.getElementById('newCollectionPopup').classList.remove('hidden');
}

function hideNewCollectionPopup() {
    document.getElementById('newCollectionPopup').classList.add('hidden');
    document.getElementById('newCollectionName').value = '';
}

async function createNewCollection() {
    const collectionName = document.getElementById('newCollectionName').value.trim();
    if (!collectionName) {
        showStatus('Please enter a collection name', true);
        return;
    }

    try {
        const response = await fetch('/api/collections', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: collectionName }),
        });

        const data = await response.json();

        if (response.ok) {
            showStatus('Collection created successfully');
            hideNewCollectionPopup();
            await fetchCollections();
            await fetchCollectionsForDropdown();
            
            // Refresh the custom select dropdown
            const customSelect = document.querySelector(".custom-select");
            customSelect.querySelector(".select-selected").remove();
            customSelect.querySelector(".select-items").remove();
            initCustomSelect();
        } else {
            showStatus(data.detail || 'Failed to create collection', true);
        }
    } catch (error) {
        console.error('Error:', error);
        showStatus('Error creating collection. Please try again.', true);
    }
}

// Refresh collections dropdown
function refreshCollectionsDropdown() {
    fetchCollectionsForDropdown();
}

// Add event listener to refresh collections when the upload form is shown
document.addEventListener('DOMContentLoaded', () => {
    const uploadButton = document.querySelector('button[onclick="showUploadForm()"]');
    if (uploadButton) {
        uploadButton.addEventListener('click', refreshCollectionsDropdown);
    }
});

async function showUploadForm() {
    try {
        await fetchCollectionsForDropdown();
        document.getElementById('documentsSection').classList.add('hidden');
        document.getElementById('uploadFormSection').classList.remove('hidden');
        state.setUploadStatus(null); // Clear the status when opening the upload form
    } catch (error) {
        console.error('Error fetching collections:', error);
        showStatus('Error loading collections. Please try again.', true);
    }
}

function cancelUpload() {
    document.getElementById('uploadForm').reset();
    document.getElementById('selectedFileName').textContent = '';
    document.getElementById('uploadFormSection').classList.add('hidden');
    document.getElementById('documentsSection').classList.remove('hidden');
}

async function fetchCollections() {
    try {
        const response = await fetch('/api/collections');
        const collections = await response.json();
        const collectionsList = document.getElementById('collectionsList');
        const noCollectionsMessage = document.getElementById('noCollectionsMessage');
        
        if (collections.length === 0) {
            collectionsList.innerHTML = '';
            noCollectionsMessage.classList.remove('hidden');
        } else {
            noCollectionsMessage.classList.add('hidden');
            collectionsList.innerHTML = collections.map(collection => `
                <li class="px-4 py-3 hover:bg-gray-50 transition flex justify-between items-center">
                    <span><i class="fas fa-folder mr-2 text-gray-600"></i>${collection}</span>
                    <button onclick="deleteCollection('${collection}')" class="text-red-600 hover:text-red-800">
                        <i class="fas fa-trash"></i>
                    </button>
                </li>
            `).join('');
        }
    } catch (error) {
        console.error('Error fetching collections:', error);
    }
}

async function deleteCollection(collectionName) {
    if (confirm(`Are you sure you want to delete the collection "${collectionName}" and all its documents?`)) {
        try {
            const response = await fetch(`/api/collections/${encodeURIComponent(collectionName)}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                showStatus(`Collection "${collectionName}" deleted successfully`);
                await fetchCollections();
                await fetchCollectionsForDropdown();
            } else {
                const data = await response.json();
                showStatus(data.detail || 'Failed to delete collection', true);
            }
        } catch (error) {
            console.error('Error deleting collection:', error);
            showStatus('Error deleting collection. Please try again.', true);
        }
    }
}

async function fetchDocuments() {
    try {
        const response = await fetch('/api/documents');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const documents = await response.json();
        const documentsList = document.getElementById('documentsList');
        const noDocumentsMessage = document.getElementById('noDocumentsMessage');
        const documentsTable = document.getElementById('documentsTable');
        
        if (documents.length === 0) {
            documentsList.innerHTML = '';
            noDocumentsMessage.classList.remove('hidden');
            documentsTable.classList.add('hidden');
        } else {
            noDocumentsMessage.classList.add('hidden');
            documentsTable.classList.remove('hidden');
            documentsList.innerHTML = documents.map(doc => `
                <tr class="border-b border-gray-200 hover:bg-gray-100 cursor-pointer">
                    <td class="py-3 px-6 text-left document-row" data-document-id="${doc.id}">
                        <i class="fas fa-file-pdf mr-2 text-gray-600"></i>${doc.filename}
                    </td>
                    <td class="py-3 px-6 text-left">${doc.collection_name}</td>
                    <td class="py-3 px-6 text-left">${doc.chunk_count}</td>
                    <td class="py-3 px-6 text-left">
                        <button onclick="deleteDocument(${doc.id})" class="text-red-600 hover:text-red-800">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </td>
                </tr>
            `).join('');

            // Add click event listeners to document rows
            document.querySelectorAll('.document-row').forEach(row => {
                row.addEventListener('click', function() {
                    const documentId = this.getAttribute('data-document-id');
                    showSection('documentChunks', documentId);
                });
            });
        }
    } catch (error) {
        console.error('Error fetching documents:', error);
        const documentsList = document.getElementById('documentsList');
        documentsList.innerHTML = `<tr><td colspan="4" class="px-4 py-3 text-red-600">Error loading documents. Please try again later.</td></tr>`;
    }
}

async function deleteDocument(documentId) {
    if (confirm('Are you sure you want to delete this document?')) {
        try {
            const response = await fetch(`/api/documents/${documentId}`, {
                method: 'DELETE'
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            showStatus('Document deleted successfully');
            await fetchDocuments();
        } catch (error) {
            console.error('Error deleting document:', error);
            showStatus('Error deleting document. Please try again.', true);
        }
    }
}

function searchDocuments() {
    const input = document.getElementById('searchInput');
    const filter = input.value.toUpperCase();
    const tbody = document.getElementById('documentsList');
    const rows = tbody.getElementsByTagName('tr');

    for (let i = 0; i < rows.length; i++) {
        const filenameColumn = rows[i].getElementsByTagName('td')[0];
        const collectionColumn = rows[i].getElementsByTagName('td')[1];
        if (filenameColumn && collectionColumn) {
            const filenameText = filenameColumn.textContent || filenameColumn.innerText;
            const collectionText = collectionColumn.textContent || collectionColumn.innerText;
            if (filenameText.toUpperCase().indexOf(filter) > -1 || collectionText.toUpperCase().indexOf(filter) > -1) {
                rows[i].style.display = '';
            } else {
                rows[i].style.display = 'none';
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // ... (existing code)

    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('keyup', searchDocuments);

    // ... (existing code)
});

// State management
const state = {
    uploadStatus: null,
    setUploadStatus(status) {
        this.uploadStatus = status;
        this.updateUI();
    },
    updateUI() {
        const status = document.getElementById('status');
        const statusText = document.getElementById('statusText');
        if (this.uploadStatus) {
            status.className = `mt-4 py-2 px-4 rounded-md ${this.uploadStatus.isError ? 'bg-red-50' : 'bg-green-50'}`;
            statusText.className = `text-center text-sm ${this.uploadStatus.isError ? 'text-red-600' : 'text-green-600'}`;
            statusText.textContent = this.uploadStatus.message;
            status.classList.remove('hidden');
        } else {
            status.classList.add('hidden');
        }
    }
};

function showStatus(message, isError = false) {
    state.setUploadStatus({ message, isError });
    const status = document.getElementById('status');
    status.classList.remove('hidden');
    // Automatically hide the status message after 5 seconds
    setTimeout(() => {
        state.setUploadStatus(null);
        status.classList.add('hidden');
    }, 5000);
}

async function fetchCollectionsForQueryDropdown() {
    try {
        console.log('fetchCollectionsForQueryDropdown');
        const response = await fetch('/api/collections');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const collections = await response.json();
        const queryCollectionSelect = document.getElementById('queryCollectionSelect');
        queryCollectionSelect.innerHTML = '<option value="Default">Default</option>';
        collections.forEach(collection => {
            if (collection !== 'Default') {
                const option = document.createElement('option');
                option.value = collection;
                option.textContent = collection;
                queryCollectionSelect.appendChild(option);
            }
        });
        initCustomSelect('queryCollectionSelect');
    } catch (error) {
        console.error('Error fetching collections for query:', error);
        showStatus('Error loading collections for query. Please try again.', true);
    }
}

// Fetch collections and populate the dropdown
async function fetchCollectionsForDropdown() {
    try {
        console.log("fetchCollectionsForDropdown");
        const response = await fetch('/api/collections');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const collections = await response.json();
        const queryCollectionSelect = document.getElementById('queryCollectionSelect');
        queryCollectionSelect.innerHTML = '<li><button type="button" class="inline-flex w-full px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-600 dark:hover:text-white" data-value="-">All collections</button></li>';
        collections.forEach(collection => {
            queryCollectionSelect.innerHTML += `<li><button type="button" class="inline-flex w-full px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-600 dark:hover:text-white" data-value="${collection}">${collection}</button></li>`;
        });

        // Add event listeners to the new dropdown items
        const dropdownItems = queryCollectionSelect.querySelectorAll('button');
        dropdownItems.forEach(item => {
            item.addEventListener('click', function() {
                document.getElementById('dropdown-button').textContent = this.textContent;
                document.getElementById('dropdown').classList.add('hidden');
            });
        });

        // Toggle dropdown visibility
        document.getElementById('dropdown-button').addEventListener('click', function(event) {
            event.preventDefault();
            document.getElementById('dropdown').classList.remove('hidden');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function(event) {
            if (!event.target.closest('#dropdown') && !event.target.closest('#dropdown-button')) {
                document.getElementById('dropdown').classList.add('hidden');
            }
        });
    } catch (error) {
        console.error('Error fetching collections:', error);
        showStatus(`Error loading collections: ${error.message}. Please try again.`, true);
    }
}

function initCustomSelect(selectId) {
    const customSelect = document.querySelector(`#${selectId}`).parentNode;
    
    // Remove existing custom select elements
    const existingSelected = customSelect.querySelector(".select-selected");
    const existingItems = customSelect.querySelector(".select-items");
    if (existingSelected) existingSelected.remove();
    if (existingItems) existingItems.remove();

    const select = customSelect.getElementsByTagName("select")[0];
    const selectSelected = document.createElement("DIV");
    selectSelected.setAttribute("class", "select-selected");
    selectSelected.innerHTML = select.options[select.selectedIndex].innerHTML;
    customSelect.appendChild(selectSelected);
    
    const selectItems = document.createElement("DIV");
    selectItems.setAttribute("class", "select-items select-hide");
    
    for (let i = 1; i < select.length; i++) {
        const optionDiv = document.createElement("DIV");
        optionDiv.innerHTML = select.options[i].innerHTML;
        optionDiv.addEventListener("click", function(e) {
            const select = this.parentNode.parentNode.getElementsByTagName("select")[0];
            const selectSelected = this.parentNode.previousSibling;
            for (let j = 0; j < select.length; j++) {
                if (select.options[j].innerHTML == this.innerHTML) {
                    select.selectedIndex = j;
                    selectSelected.innerHTML = this.innerHTML;
                    const sameAsSelected = this.parentNode.getElementsByClassName("same-as-selected");
                    for (let k = 0; k < sameAsSelected.length; k++) {
                        sameAsSelected[k].removeAttribute("class");
                    }
                    this.setAttribute("class", "same-as-selected");
                    break;
                }
            }
            selectSelected.click();
            select.dispatchEvent(new Event('change'));
        });
        selectItems.appendChild(optionDiv);
    }
    customSelect.appendChild(selectItems);
    
    selectSelected.addEventListener("click", function(e) {
        e.stopPropagation();
        closeAllSelect(this);
        this.nextSibling.classList.toggle("select-hide");
        this.classList.toggle("select-arrow-active");
    });
}

function closeAllSelect(elmnt) {
    const selectItems = document.getElementsByClassName("select-items");
    const selectSelected = document.getElementsByClassName("select-selected");
    for (let i = 0; i < selectSelected.length; i++) {
        if (elmnt != selectSelected[i]) {
            selectSelected[i].classList.remove("select-arrow-active");
        }
    }
    for (let i = 0; i < selectItems.length; i++) {
        if (elmnt != selectItems[i] && elmnt != selectSelected[i]) {
            selectItems[i].classList.add("select-hide");
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('uploadForm');
    const dropArea = document.getElementById('dropArea');
    const fileInput = document.getElementById('pdfFile');
    const selectedFileName = document.getElementById('selectedFileName');
    const uploadSpinner = document.getElementById('uploadSpinner');
    const collectionSelect = document.getElementById('collectionSelect');
    const createCollectionBtn = document.getElementById('createCollectionBtn');

    createCollectionBtn.addEventListener('click', createNewCollection);

    document.addEventListener("click", closeAllSelect);

    fetchCollectionsForDropdown();

    dropArea.addEventListener('click', () => fileInput.click());

    dropArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropArea.classList.add('border-indigo-500');
    });

    dropArea.addEventListener('dragleave', () => {
        dropArea.classList.remove('border-indigo-500');
    });

    dropArea.addEventListener('drop', (e) => {
        e.preventDefault();
        dropArea.classList.remove('border-indigo-500');
        const file = e.dataTransfer.files[0];
        if (file && file.type === 'application/pdf') {
            fileInput.files = e.dataTransfer.files;
            selectedFileName.textContent = file.name;
        } else {
            showStatus('Please select a PDF file', true);
        }
    });

    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (file) {
            selectedFileName.textContent = file.name;
        }
    });

    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.classList.add('bg-gray-400', 'cursor-not-allowed');

    function updateSubmitButton() {
        const file = fileInput.files[0];
        const collectionSelected = collectionSelect.value !== "";
        if (file && collectionSelected) {
            submitBtn.disabled = false;
            submitBtn.classList.remove('bg-gray-400', 'cursor-not-allowed');
            submitBtn.classList.add('bg-indigo-600', 'hover:bg-indigo-700');
        } else {
            submitBtn.disabled = true;
            submitBtn.classList.add('bg-gray-400', 'cursor-not-allowed');
            submitBtn.classList.remove('bg-indigo-600', 'hover:bg-indigo-700');
        }
    }

    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (file) {
            selectedFileName.textContent = file.name;
        } else {
            selectedFileName.textContent = '';
        }
        updateSubmitButton();
    });

    collectionSelect.addEventListener('change', updateSubmitButton);

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const collectionId = collectionSelect.value;
        const file = fileInput.files[0];

        if (!collectionId) {
            showStatus('Please select a collection', true);
            return;
        }

        if (!file) {
            showStatus('Please select a PDF file', true);
            return;
        }

        try {
            uploadSpinner.classList.remove('hidden');
            document.getElementById('status').classList.add('hidden');

            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/documents/upload', {
                method: 'POST',
                headers: {
                    'Collection-Name': collectionId,
                },
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                showStatus('Document uploaded successfully');
                form.reset();
                selectedFileName.textContent = '';
                // Refresh the documents list
                fetchDocuments();
            } else {
                showStatus(data.detail || 'Upload failed. Please try again.', true);
            }
        } catch (error) {
            console.error('Error:', error);
            showStatus('Error uploading file. Please check your connection and try again.', true);
        } finally {
            submitBtn.disabled = false;
            uploadSpinner.classList.add('hidden');
        }
    });

    // Clear status when starting a new upload
    form.addEventListener('submit', () => {
        state.setUploadStatus(null);
    });

    const queryForm = document.getElementById('queryForm');
    queryForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = document.getElementById('queryInput').value;
        const collection = document.getElementById('dropdown-button').textContent.trim();
        await performQuery(query, collection);
    });

    // Initially show the query section
    showSection('query');
});
