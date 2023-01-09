const allPostIds = document.querySelectorAll(".post-id")
const allLoveIcons = document.querySelectorAll(".love-icon")
const allLikesNumbers = document.querySelectorAll(".likes-number")

const ownPostIds = document.querySelectorAll(".own-post-id-True")
const ownPosts = document.querySelectorAll(".own-post-True")
const ownPostsDeleteButtons = document.querySelectorAll(".own-post-delete-icon-True")

const modal = document.getElementById("modal")
const modalNoBtn = document.getElementById("modal-no-btn")
const modalYesBtn = document.getElementById("modal-yes-btn")

const ownPostsArchiveButtons = document.querySelectorAll(".archive-post-button")
const archiveModal = document.getElementById("archive-modal")
const archiveModalNoBtn = document.getElementById("archive-modal-no-btn")
const archiveModalYesBtn = document.getElementById("archive-modal-yes-btn")

const archiveModalAllPostsYesButton = document.getElementById("archive-modal-all-yes-btn")

let postIdToDelete = -1
let ownPostIndex = -1

allLoveIcons.forEach((icon, index) => {
    icon.addEventListener("click", async () => {
        const data = {postID: parseInt(allPostIds[index].textContent)}
        const res = await fetch("/like_dislike_post", {
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST',
            mode: 'cors',
            body: JSON.stringify(data)
        })
        const jsonResult = await res.json()

        if (jsonResult.message === "liked") {
            icon.src = "../static/love_active.png"
        } else if (jsonResult.message === "unliked") {
            icon.src = "../static/love_inactive.png"
        }
        allLikesNumbers[index].innerText = jsonResult.count
    })
})
ownPostsDeleteButtons.forEach((btn, index) => {
    const postId = ownPostIds[index].textContent
    btn.addEventListener("click", async () => {
        postIdToDelete = postId
        modal.style.visibility = "visible"
        ownPostIndex = index
        console.log(postIdToDelete)
    })
})

modalNoBtn.addEventListener("click", async () => {
    modal.style.visibility = "hidden"
})

modalYesBtn.addEventListener("click", async () => {
    const res = await fetch(`/delete-post/${postIdToDelete}`, {
        headers: {
            'Content-Type': 'application/json'
        },
        method: 'DELETE',
        mode: 'cors',
    })
    const jsonResponse = await res.json()
    if (jsonResponse.status === "deleted") {
        ownPosts[ownPostIndex].remove()
        modal.style.visibility = "hidden"
    }
})
ownPostsArchiveButtons.forEach((btn, index) => {
    const postId = ownPostIds[index].textContent
    btn.addEventListener("click", async () => {
        postIdToDelete = postId
        archiveModal.style.visibility = "visible"
        ownPostIndex = index
    })
})
archiveModalNoBtn.addEventListener("click", () => {
    archiveModal.style.visibility = "hidden"
})

if (archiveModalYesBtn) {
    archiveModalYesBtn.addEventListener("click", async () => {
        const res = await fetch(`/archive-post/${postIdToDelete}`, {
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'GET',
            mode: 'cors',
        })
        const jsonResponse = await res.json()
        console.log(jsonResponse)
        if (jsonResponse.status === "archived") {
            ownPosts[ownPostIndex].remove()
            archiveModal.style.visibility = "hidden"
        }
    })
}

if (archiveModalAllPostsYesButton) {
    archiveModalAllPostsYesButton.addEventListener("click", async () => {
        const res = await fetch(`/archive-post/${postIdToDelete}`, {
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'GET',
            mode: 'cors',
        })
        const jsonResponse = await res.json()
        console.log(jsonResponse)
        if (jsonResponse.status === "archived") {
            archiveModal.style.visibility = "hidden"
            ownPostsArchiveButtons[ownPostIndex].src = "../static/archive_active.png"
        }
        if (jsonResponse.status === "unarchived") {
            archiveModal.style.visibility = "hidden"
            ownPostsArchiveButtons[ownPostIndex].src = "../static/archive_inactive.png"
        }
    })
}