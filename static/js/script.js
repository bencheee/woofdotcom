// ####################
//        EVENTS
// ####################


// Navbar toggle
$(".navbar__toggle").click(function () {
    $(".nav__mobile").slideToggle();
})

// Shows flash message
$(".flash").slideToggle();

// Hides flash message
$("#flash-close").click(function(){
    $(".flash").slideUp();
})

// Toggles password visibility
$("#pass_icon").click(passToggle);

// Toggles Dropdown items on surrender.html
$(".btn--surrender").click(function(){
    $(this).next().slideToggle();
})

// Controls image sizes to 16:9 ratio
$(window).resize(function () {
    resizeImg($(".dog__img"))
})
resizeImg($(".dog__img"))




// ####################
//      FUNCTIONS
// ####################


// Toggles password visibility
function passToggle() {
    let pass = $("#password")[0]
    if (pass.type === "password") {
        pass.type = "text";
        $("#password").css({"font-weight": "100", "letter-spacing": "0"});
        $("#pass_icon").removeClass("fa-eye");
        $("#pass_icon").addClass("fa-eye-slash");
        $("#pass_toggle").text("Hide password");
    } else {
        pass.type = "password";
        $("#password").css({"font-weight": "900", "letter-spacing": "3px"});
        $("#pass_icon").removeClass("fa-eye-slash");
        $("#pass_icon").addClass("fa-eye");
        $("#pass_toggle").text("Show password");
    }
}

// Controls image sizes to 16:9 ratio
function resizeImg(img) {
    width = img.width()
    height = width * 0.5625
    img.css("height", `${height}px`);
}