const loveIcon = document.getElementById("love-icon")
loveIcon.addEventListener("click", likeBtnClickHandler)
const postLoveCount = document.getElementById("post-love-count")
postIdElement = document.getElementById("post-id")
const data = {postID: parseInt(postIdElement.textContent)}
const commentLikeButtons = document.querySelectorAll(".comment-love-icon")
const commentIds = document.querySelectorAll(".comment-id")
const commentCountLabels = document.querySelectorAll(".comment-like-count")
const ownComments = document.querySelectorAll(".own-comment-True")
const ownCommentsDeleteButtons = document.querySelectorAll(".comment-delete-own-True")
const ownCommentIds = document.querySelectorAll(".own-comment-ids-True")
const postDeleteButton = document.getElementById("delete-btn")

const modal = document.getElementById("modal")
const modalNoBtn = document.getElementById("modal-no-btn")
const modalYesBtn = document.getElementById("modal-yes-btn")

const commentModal = document.getElementById("comment-modal")
const commentModalNoBtn = document.getElementById("comment-modal-no-btn")
const commentModalYesBtn = document.getElementById("comment-modal-yes-btn")

const commentCountLabel = document.getElementById("comment-count")
const postCommentBtn = document.getElementById("post-comment-btn")
const commentField = document.getElementById("comment-input")
const commentListBlock = document.getElementById("comment-list-block")

const actionCommentCount = document.getElementById("action-comment-count")


let nodeToBeDeleted = null

let commentToBeDeletedIndex = -1
let ownCommentIndex = -1

async function likeBtnClickHandler() {
    const res = await fetch("/like_dislike_post", {
        headers: {
            'Content-Type': 'application/json'
        }, method: 'POST', mode: 'cors', body: JSON.stringify(data)
    })
    const jsonResult = await res.json()

    if (jsonResult.message === "liked") {
        loveIcon.src = "../static/love_active.png"
    } else if (jsonResult.message === "unliked") {
        loveIcon.src = "../static/love_inactive.png"
    }
    postLoveCount.innerText = jsonResult.count
}

commentLikeButtons.forEach((btn, index) => {
    btn.addEventListener("click", async () => {
        const data = {comment_id: parseInt(commentIds[index].textContent)}
        const res = await fetch("/comment-like-unlike", {
            headers: {
                'Content-Type': 'application/json'
            }, method: 'POST', mode: 'cors', body: JSON.stringify(data)
        })
        const jsonResponse = await res.json()
        if (jsonResponse.message === "liked") {
            btn.src = "../static/love_active.png"
        } else if (jsonResponse.message === "unliked") {
            btn.src = "../static/love_inactive.png"
        }
        commentCountLabels[index].innerText = jsonResponse.count
    })
})
ownCommentsDeleteButtons.forEach((btn, index) => {
    btn.addEventListener("click", async () => {
        commentToBeDeletedIndex = ownCommentIds[index].textContent
        commentModal.style.visibility = "visible"
        ownCommentIndex = index
    })
})

commentModalNoBtn.addEventListener("click", async () => {
    commentModal.style.visibility = "hidden"
})

commentModalYesBtn.addEventListener("click", async () => {
    const res = await fetch(`/comment-delete/${commentToBeDeletedIndex}`, {
        headers: {
            'Content-Type': 'application/json'
        }, method: 'DELETE', mode: 'cors',
    })
    const jsonResponse = await res.json()
    if (jsonResponse.status === "deleted") {
        if (ownCommentIndex !== -1) {
            ownComments[ownCommentIndex].remove()
        } else {
            if (nodeToBeDeleted) {
                nodeToBeDeleted.remove()
            }
        }
        commentModal.style.visibility = "hidden"
        commentCountLabel.innerHTML = jsonResponse.count + " Comments"
        actionCommentCount.innerHTML = jsonResponse.count
    }
})

if (postDeleteButton) {
    postDeleteButton.addEventListener("click", async () => {
        modal.style.visibility = "visible"
    })
}

modalNoBtn.addEventListener("click", async () => {
    modal.style.visibility = "hidden"
})

modalYesBtn.addEventListener("click", async () => {
    const res = await fetch(`/delete-post/${postIdElement.textContent}`, {
        headers: {
            'Content-Type': 'application/json'
        }, method: 'DELETE', mode: 'cors',
    })
    const jsonResponse = await res.json()
    if (jsonResponse.status === "deleted") {
        window.location.href = "/all-posts"
    }
})
postCommentBtn.addEventListener("click", async () => {
    const data = {commentBody: commentField.value, postID: parseInt(postIdElement.textContent)}
    const res = await fetch("/create_comment2", {
        headers: {
            'Content-Type': 'application/json'
        },
        method: 'POST',
        mode: 'cors',
        body: JSON.stringify(data)
    })
    const jsonResponse = await res.json()
    console.log(jsonResponse)
    if (jsonResponse.status === "created") {
        const commentCardRootDiv = document.createElement("div")
        commentCardRootDiv.className = "comment-list-card"
        const commentListImageContainer = document.createElement("div")
        commentListImageContainer.className = "comment-list-image-container"
        const commentUserImage = document.createElement("img")
        commentUserImage.src = "/" + jsonResponse.authorImageUrl
        const commentListTextBlock = document.createElement("div")
        commentListTextBlock.className = "comment-list-text-block"
        const commentListTextBlockH3 = document.createElement("h3")
        commentListTextBlockH3.innerHTML = jsonResponse.authorName
        const commentListTextBlockP1 = document.createElement("p")
        commentListTextBlockP1.className = "comment-list-text-block-comment"
        commentListTextBlockP1.innerHTML = commentField.value
        const commentListTextBlockP2 = document.createElement("p")
        commentListTextBlockP2.className = "comment-list-text-block-time"
        commentListTextBlockP2.innerHTML = jsonResponse.time
        const commentLikeBox = document.createElement("div")
        commentLikeBox.className = "comment-like-box"
        const commentLikeIcon = document.createElement("img")
        commentLikeIcon.className = "comment-love-icon"
        commentLikeIcon.src = "/static/love_inactive.png"
        const commentLikeCount = document.createElement("p")
        commentLikeCount.className = "comment-like-count"
        commentLikeCount.innerHTML = jsonResponse.commentLikesCount
        const commentDeleteButton = document.createElement("img")
        commentDeleteButton.src = "/static/delete_icon.png"
        commentDeleteButton.className = "comment-delete-btn"
        commentDeleteButton.alt = "delete comment"
        commentListImageContainer.appendChild(commentUserImage)
        commentCardRootDiv.appendChild(commentListImageContainer)
        commentListTextBlock.appendChild(commentListTextBlockH3)
        commentListTextBlock.appendChild(commentListTextBlockP1)
        commentListTextBlock.appendChild(commentListTextBlockP2)
        commentCardRootDiv.appendChild(commentListTextBlock)
        commentLikeBox.appendChild(commentLikeIcon)
        commentLikeBox.appendChild(commentLikeCount)
        commentListTextBlock.appendChild(commentLikeBox)
        commentCardRootDiv.appendChild(commentDeleteButton)
        commentListBlock.prepend(commentCardRootDiv)
        commentCountLabel.innerHTML = jsonResponse.count + " Comments"
        actionCommentCount.innerText = jsonResponse.count
        commentField.value = ""
        commentDeleteButton.addEventListener("click", () => {
            commentToBeDeletedIndex = jsonResponse.commentID
            commentModal.style.visibility = "visible"
            nodeToBeDeleted = commentCardRootDiv
            ownCommentIndex = -1
        })
        commentLikeIcon.addEventListener("click", async () => {
            const data = {comment_id: jsonResponse.commentID}
            const res = await fetch("/comment-like-unlike", {
                headers: {
                    'Content-Type': 'application/json'
                }, method: 'POST', mode: 'cors', body: JSON.stringify(data)
            })
            const jsonResponseInner = await res.json()
            if (jsonResponseInner.message === "liked") {
                commentLikeIcon.src = "../static/love_active.png"
            } else if (jsonResponseInner.message === "unliked") {
                commentLikeIcon.src = "../static/love_inactive.png"
            }
            commentLikeCount.innerText = jsonResponseInner.count
        })
    }
})