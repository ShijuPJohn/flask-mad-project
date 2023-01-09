const modal = document.getElementById("modal")
const modalNoBtn = document.getElementById("modal-no-btn")
const modalYesBtn = document.getElementById("modal-yes-btn")

const deleteUserBtn = document.getElementById("delete-user-btn")

const profilePicThumb = document.getElementById("profile-pic-thumb")
const imageModal = document.getElementById("image-modal")
const imageContainer = document.getElementById("modal-img-container")
const modalCloseBtn = document.getElementById("modal-close-btn")
deleteUserBtn.addEventListener("click", () => {
    modal.style.visibility = "visible"
})
modalNoBtn.addEventListener("click", async () => {
    modal.style.visibility = "hidden"
})
modalYesBtn.addEventListener("click", async () => {
    modal.style.visibility = "hidden"
    const res = await fetch(`/delete-user`, {
        headers: {
            'Content-Type': 'application/json'
        }, method: 'DELETE', mode: 'cors',
    })
    const jsonResponse = await res.json()
    if (jsonResponse.status === "deleted") {
        window.location.href = "/login"
    }
})
profilePicThumb.addEventListener("click", () => {
    imageModal.style.visibility = "visible"
    imageContainer.style.visibility = "visible"
})
modalCloseBtn.addEventListener("click", () => {
     imageModal.style.visibility = "hidden"
    imageContainer.style.visibility = "hidden"
})