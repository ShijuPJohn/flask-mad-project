const followUnfollowButtons = document.querySelectorAll(".follow-unfollow-btn")
const userIds = document.querySelectorAll(".user-id")
const followingNotFollowingMessageElement = document.getElementById("follow-unfollow-message")
const followersCountLabel = document.getElementById("followers-count-label")
const profilePicThumb = document.getElementById("profile-pic-thumb")

const imageModal = document.getElementById("image-modal")
const profileImg = document.getElementById("modal-profile-img")
const imageContainer = document.getElementById("modal-img-container")
const modalCloseBtn = document.getElementById("modal-close-btn")
followUnfollowButtons.forEach((btn, index) => {
    btn.addEventListener("click", async () => {
        const data = {userId: parseInt(userIds[index].textContent)}
        const res = await fetch("/follow-unfollow", {
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST',
            mode: 'cors',
            body: JSON.stringify(data)
        })
        const jsonResult = await res.json()
        console.log(jsonResult)
        if (jsonResult.status === "followed") {
            btn.className = "follow-unfollow-btn unfollow-btn"
            followingNotFollowingMessageElement.innerHTML = "You're following this user"
            btn.innerHTML = "Unfollow"
            followersCountLabel.innerHTML = jsonResult.followers_count
        } else if (jsonResult.status === "unfollowed") {
            btn.className = "follow-unfollow-btn follow-btn"
            btn.innerHTML = "Follow"
            followingNotFollowingMessageElement.innerHTML = "You're not following this user"
            followersCountLabel.innerHTML = jsonResult.followers_count
        }
    })
})
profilePicThumb.addEventListener("click", () => {
    imageModal.style.visibility = "visible"
    imageContainer.style.visibility = "visible"
})
modalCloseBtn.addEventListener("click", () => {
     imageModal.style.visibility = "hidden"
    imageContainer.style.visibility = "hidden"
})