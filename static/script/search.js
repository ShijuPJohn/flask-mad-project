const followUnfollowButtons = document.querySelectorAll(".follow-unfollow-btn")
const userIds = document.querySelectorAll(".user-id")
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
            btn.style.backgroundColor = "#b2667d"
            btn.innerHTML = "Unfollow"
        } else if (jsonResult.status === "unfollowed") {
            btn.style.backgroundColor = "#4f9b4f"
            btn.innerHTML = "Follow"
        }
    })
})