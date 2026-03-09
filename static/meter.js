window.onload = function () {

    let score = document.getElementById("score-text")

    if (!score) return

    let value = parseInt(score.innerText)

    let meter = document.getElementById("meter-fill")

    let degrees = value * 3.6

    setTimeout(() => {
        meter.style.transform = "rotate(" + degrees + "deg)"
    }, 300)

}