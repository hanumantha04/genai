document.getElementById('uploadForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const fileInput = document.getElementById('fileInput').files[0];
    if (!fileInput) {
        alert("Please upload an image.");
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput);

    document.getElementById('result').classList.add('hidden');

    try {
        const response = await fetch('/extract-text', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.error) {
            document.getElementById('extractedText').innerText = "Error: " + result.error;
            document.getElementById('summary').innerText = "";
        } else {
            document.getElementById('extractedText').innerText = result.extracted_text;
            document.getElementById('summary').innerText = result.summary;
        }

        document.getElementById('result').classList.remove('hidden');
    } catch (error) {
        console.error("Error processing image:", error);
    }
});
