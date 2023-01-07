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

async function likeBtnClickHandler() {
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
            },
            method: 'POST',
            mode: 'cors',
            body: JSON.stringify(data)
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
        const cid = ownCommentIds[index].textContent
        const res = await fetch(`/comment-delete/${cid}`, {
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'DELETE',
            mode: 'cors',
        })
        const jsonResponse = await res.json()
        if (jsonResponse.status === "deleted") {
            ownComments[index].remove()
        }
    })
})
