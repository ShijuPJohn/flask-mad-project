const modal = document.getElementById("modal")
const modalNoBtn = document.getElementById("modal-no-btn")
const modalYesBtn = document.getElementById("modal-yes-btn")

const deleteUserBtn = document.getElementById("delete-user-btn")
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