const allPostIds = document.querySelectorAll(".post-id")
const allLoveIcons = document.querySelectorAll(".love-icon")
const allLikesNumbers = document.querySelectorAll(".likes-number")

const ownPostIds = document.querySelectorAll(".own-post-id-True")
const ownPosts = document.querySelectorAll(".own-post-True")
const ownPostsDeleteButtons = document.querySelectorAll(".own-post-True")

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