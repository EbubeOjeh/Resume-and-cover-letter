// Drag & Drop Resume Upload
let dropZone = document.getElementById("drop-zone")
let textarea = document.getElementById("resume")
let fileInput = document.getElementById("file-input")

if (dropZone) {

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault()
        dropZone.style.borderColor = "#6366f1"
    })

    dropZone.addEventListener("dragleave", () => {
        dropZone.style.borderColor = "#aaa"
    })

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault()

        let file = e.dataTransfer.files[0]

        if (!file) return

        // Put file into upload input
        if (fileInput) {
            fileInput.files = e.dataTransfer.files
        }

        // Read text files directly into textarea
        if (file.type === "text/plain") {

            let reader = new FileReader()

            reader.onload = function () {
                if (textarea) {
                    textarea.value = reader.result
                }
            }

            reader.readAsText(file)

        }

        dropZone.style.borderColor = "#aaa"
    })

}


// Resume Rewrite AI Feature
let rewriteBtn = document.getElementById("rewriteBtn")

if (rewriteBtn) {

    rewriteBtn.onclick = async function () {

        let resume = document.getElementById("resume").value

        if (!resume) {
            alert("Please paste or upload a resume first.")
            return
        }

        let response = await fetch("/rewrite", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: "resume=" + encodeURIComponent(resume)
        })

        let text = await response.text()

        document.getElementById("rewriteResult").innerText = text

    }

}